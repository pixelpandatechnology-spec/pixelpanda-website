import os
import re
import logging
from datetime import datetime
from flask import Flask, Blueprint, request, jsonify, current_app, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from marshmallow import Schema, fields, validates, ValidationError, validate
from email_validator import validate_email, EmailNotValidError
import phonenumbers
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

# ------------------------
# Configuration
# ------------------------

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:2002@localhost:5432/contacts_db"  # <-- change password if needed
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ALLOWED_SERVICES = os.getenv(
        "ALLOWED_SERVICES",
        "web_development,mobile_app,design,consulting,other"
    ).split(",")
    DEFAULT_PER_PAGE = int(os.getenv("DEFAULT_PER_PAGE", "20"))


# ------------------------
# App, DB and Logger
# ------------------------

db = SQLAlchemy()

logger = logging.getLogger("contact_api")
logger.setLevel(logging.DEBUG if os.getenv("FLASK_ENV") != "production" else logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s - %(message)s"
))
logger.addHandler(handler)


# ------------------------
# Models
# ------------------------

class Contact(db.Model):
    __tablename__ = "contacts"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False, index=True)
    phone = db.Column(db.String(30), nullable=False, unique=True, index=True)
    email = db.Column(db.String(255), nullable=False, unique=True, index=True)
    business_name = db.Column(db.String(255), nullable=False, index=True)
    service = db.Column(db.String(120), nullable=False, index=True)
    project_details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "phone": self.phone,
            "email": self.email,
            "business_name": self.business_name,
            "service": self.service,
            "project_details": self.project_details,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# ------------------------
# Validation Schema
# ------------------------

PHONE_REGEX = re.compile(r"^\+?[0-9\-\s()]+$")

class ContactSchema(Schema):
    id = fields.Int(dump_only=True)
    full_name = fields.Str(required=True, validate=validate.Length(min=2, max=255))
    phone = fields.Str(required=True)
    email = fields.Email(required=True, validate=validate.Length(max=255))
    business_name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    service = fields.Str(required=True)
    project_details = fields.Str(allow_none=True, validate=validate.Length(max=2000))
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    # @validates("phone")
    # def validate_phone(self, value):
    #     if not PHONE_REGEX.match(value):
    #         raise ValidationError("Phone contains invalid characters")

    #     try:
    #         default_region = os.getenv("PHONE_DEFAULT_REGION")
    #         parsed = phonenumbers.parse(value, default_region) if default_region else phonenumbers.parse(value, None)
    #     except phonenumbers.NumberParseException as e:
    #         raise ValidationError("Phone number could not be parsed: %s" % str(e))

    #     if not phonenumbers.is_valid_number(parsed):
    #         raise ValidationError("Phone number is not valid")

    #     return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

    # @validates("email")
    # def validate_email_addr(self, value):
    #     try:
    #         validate_email(value)
    #     except EmailNotValidError as e:
    #         raise ValidationError(str(e))


contact_schema = ContactSchema()
contacts_schema = ContactSchema(many=True)


# ------------------------
# Blueprint / Routes
# ------------------------

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200


# Create Contact
@api_bp.route("/contacts", methods=["POST"])
def create_contact():
    json_data = request.get_json(force=True, silent=True)
    if not json_data:
        return jsonify({"error": "Invalid JSON"}), 400

    try:
        data = contact_schema.load(json_data)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    contact = Contact(
    full_name=data["full_name"],
    phone=data["phone"],
    email=data["email"],  # normalize safely
    business_name=data["business_name"],
    service=data["service"],
    project_details=data.get("project_details")
)

    try:
        db.session.add(contact)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email or phone already exists"}), 409

    return jsonify(contact.to_dict()), 201


# List Contacts
@api_bp.route("/contacts", methods=["GET"])
def list_contacts():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", current_app.config["DEFAULT_PER_PAGE"]))

    contacts = Contact.query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "total": contacts.total,
        "page": contacts.page,
        "per_page": contacts.per_page,
        "pages": contacts.pages,
        "items": [c.to_dict() for c in contacts.items]
    })


# Get One Contact
@api_bp.route("/contacts/<int:id>", methods=["GET"])
def get_contact(id):
    contact = Contact.query.get_or_404(id)
    return jsonify(contact.to_dict())


# Update Contact
@api_bp.route("/contacts/<int:id>", methods=["PUT"])
def update_contact(id):
    contact = Contact.query.get_or_404(id)
    json_data = request.get_json(force=True, silent=True)
    if not json_data:
        return jsonify({"error": "Invalid JSON"}), 400

    try:
        data = ContactSchema(partial=True).load(json_data)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400

    for key, value in data.items():
        setattr(contact, key, value)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Email or phone already exists"}), 409

    return jsonify(contact.to_dict())


# Delete Contact
@api_bp.route("/contacts/<int:id>", methods=["DELETE"])
def delete_contact(id):
    contact = Contact.query.get_or_404(id)
    db.session.delete(contact)
    db.session.commit()
    return jsonify({"status": "deleted"})


# ------------------------
# Application factory
# ------------------------

def create_app(config_object=None):
    app = Flask(__name__)
    
    app.config.from_object(config_object or Config)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
