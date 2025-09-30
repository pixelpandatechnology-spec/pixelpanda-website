document.addEventListener("DOMContentLoaded", () => {
  const menuToggle = document.querySelector(".menu-toggle");
  const navLinks = document.querySelector(".nav-links");

  // Create overlay
  const overlay = document.createElement("div");
  overlay.classList.add("overlay");
  document.body.appendChild(overlay);


  // -----------------------------
// 📌 DROPDOWN MENU TOGGLE (Mobile)
// -----------------------------

  // Dropdown toggle for mobile
  document.querySelectorAll('.dropdown-toggle').forEach(toggle => {
    toggle.addEventListener('click', function(e) {
      e.preventDefault();
      const parent = this.parentElement;
      
      // Close other dropdowns
      document.querySelectorAll('.dropdown').forEach(drop => {
        if (drop !== parent) {
          drop.classList.remove('active');
        }
      });

      // Toggle current dropdown
      parent.classList.toggle('active');
    });
  });




  // Toggle menu
  menuToggle.addEventListener("click", () => {
    navLinks.classList.toggle("active");
    overlay.classList.toggle("active");

    // Change ☰ to ✖ when open
    if (navLinks.classList.contains("active")) {
      menuToggle.textContent = "✖";
    } else {
      menuToggle.textContent = "☰";
    }
  });

  // Close menu when overlay is clicked
  overlay.addEventListener("click", () => {
    navLinks.classList.remove("active");
    overlay.classList.remove("active");
    menuToggle.textContent = "☰";
  });

  // Close menu when a nav link is clicked (for single page sites)
  document.querySelectorAll(".nav-links a").forEach(link => {
    link.addEventListener("click", () => {
      navLinks.classList.remove("active");
      overlay.classList.remove("active");
      menuToggle.textContent = "☰";
    });
  });

  // Reset on window resize (desktop mode)
  window.addEventListener("resize", () => {
    if (window.innerWidth > 992) { // desktop breakpoint
      navLinks.classList.remove("active");
      overlay.classList.remove("active");
      menuToggle.textContent = "☰";
    }
  });

  // -----------------------------
  // 📌 FORM VALIDATION CODE
  // -----------------------------
  const phoneInput = document.getElementById("phone");
  const emailInput = document.getElementById("email");
  const phoneError = document.getElementById("phone-error");
  const emailError = document.getElementById("email-error");
  const form = document.getElementById("contactForm");

  // 📱 Phone validation
  phoneInput.addEventListener("input", () => {
    let phone = phoneInput.value.trim();

    if (phone.length === 10) {
      let firstDigit = phone[0];
      if (firstDigit >= "6" && firstDigit <= "9") {
        phoneError.textContent = "✔ Valid mobile number";
        phoneError.style.color = "green";
        phoneInput.style.border = "1px solid green";
      } else {
        phoneError.textContent = "❌ Number must start with 6, 7, 8, or 9";
        phoneError.style.color = "red";
        phoneInput.style.border = "1px solid red";
      }
    } else {
      phoneError.textContent = "❌ Must be 10 digits";
      phoneError.style.color = "red";
      phoneInput.style.border = "1px solid red";
    }
  });

  // 📧 Email validation
  emailInput.addEventListener("input", () => {
    let email = emailInput.value.trim();

    if (email.includes("@") && email.includes(".")) {
      emailError.textContent = "✔ Valid email address";
      emailError.style.color = "green";
      emailInput.style.border = "1px solid green";
    } else {
      emailError.textContent = "❌ Invalid email";
      emailError.style.color = "red";
      emailInput.style.border = "1px solid red";
    }
  });

  // ✅ Final check before submit
  form.addEventListener("submit", (e) => {
    if (phoneError.style.color === "red" || emailError.style.color === "red") {
      e.preventDefault();
      alert("Please fix the errors before submitting.");
    }
  });
});


// contacts api 


document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("contactform");
  const msgBox = document.getElementById("form-message");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const data = {
      full_name: document.getElementById("name").value,
      phone: document.getElementById("phone").value,
      email: document.getElementById("email").value,
      business_name: document.getElementById("business").value || "N/A",
      service: document.getElementById("service").value || "other",
      project_details: document.getElementById("project_details").value || ""
    };

    try {
      const res = await fetch("http://localhost:5000/api/contacts", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
      });

      const result = await res.json();

      if (res.ok) {
        msgBox.innerHTML = `<p style="color: green;">Thanks, ${result.full_name}! Your message was saved.</p>`;
        form.reset();
      } else {
        msgBox.innerHTML = `<p style="color: red;">Error: ${result.error || JSON.stringify(result.errors)}</p>`;
      }
    } catch (err) {
      console.error(err);
      msgBox.innerHTML = `<p style="color: red;">Failed to connect to server.</p>`;
    }
  });
});
