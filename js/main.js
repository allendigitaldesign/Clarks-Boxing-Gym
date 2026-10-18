// Clark's Boxing Club — menu, sticky header and contact form

(function () {
  var body = document.body;
  var header = document.querySelector(".site-header");
  var toggle = document.querySelector(".nav-toggle");

  // Mobile menu
  if (toggle) {
    toggle.addEventListener("click", function () {
      var open = body.classList.toggle("nav-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.querySelectorAll(".main-nav a").forEach(function (link) {
      link.addEventListener("click", function () {
        body.classList.remove("nav-open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  // Header shadow once the page scrolls
  function onScroll() {
    if (header) header.classList.toggle("scrolled", window.scrollY > 8);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // Footer year
  document.querySelectorAll("[data-year]").forEach(function (el) {
    el.textContent = new Date().getFullYear();
  });

  // Contact / free-trial form
  var form = document.querySelector("#contact-form");
  if (!form) return;

  // Pre-fill from links like contact.html?type=question or ?plan=Premium%20Monthly
  var params = new URLSearchParams(window.location.search);
  var type = params.get("type");
  var plan = params.get("plan");
  if (type === "question") {
    var q = form.querySelector('input[name="Request"][value="Question"]');
    if (q) q.checked = true;
  }
  if (plan) {
    var planField = form.querySelector('select[name="Interested in"]');
    if (planField) {
      Array.prototype.forEach.call(planField.options, function (opt) {
        if (opt.value === plan) planField.value = plan;
      });
    }
  }

  var status = form.querySelector(".form-status");
  var button = form.querySelector('button[type="submit"]');

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!form.reportValidity()) return;

    var data = new FormData(form);
    var request = data.get("Request") || "Free trial";
    data.append("_subject", "Website: " + request + " request from " + (data.get("Name") || "a visitor"));

    button.disabled = true;
    button.textContent = "Sending…";
    status.className = "form-status";

    fetch(form.action, {
      method: "POST",
      headers: { Accept: "application/json" },
      body: data,
    })
      .then(function (res) { return res.json().then(function (json) { return { ok: res.ok, json: json }; }); })
      .then(function (r) {
        if (!r.ok || String(r.json.success) !== "true") throw new Error(r.json.message || "Send failed");
        form.reset();
        status.textContent = "Thanks! We got your message and will be in touch soon. Want an answer faster? Call (254) 216-1634.";
        status.className = "form-status ok";
      })
      .catch(function () {
        status.innerHTML = 'Sorry, that didn\'t go through. Please call <a href="tel:+12542161634">(254) 216-1634</a> or email <a href="mailto:clarksboxinggym@gmail.com">clarksboxinggym@gmail.com</a>.';
        status.className = "form-status err";
      })
      .finally(function () {
        button.disabled = false;
        button.textContent = "Send";
        status.scrollIntoView({ behavior: "smooth", block: "center" });
      });
  });
})();
