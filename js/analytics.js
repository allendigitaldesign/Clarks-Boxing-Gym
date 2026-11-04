// Clark's Boxing Club: anonymous visitor analytics through PostHog.
// Runs only on the live domain, so local previews are never counted.
// Session recording is off. Nothing typed into the contact form is collected:
// the form has the ph-no-capture class, and main.js reports only worked/failed
// plus the two fixed choices (request type and plan).

(function () {
  // The project key is public by design. It can send events but cannot read them.
  var KEY = "phc_qzJdH5rUSgEbyBsWx5GvE3SPkAKmUkdiC9ueGJVhK4dQ";
  var LIVE_HOSTS = ["clarksboxinggym.com", "www.clarksboxinggym.com"];

  // main.js calls this for the form result. It stays a no-op when tracking is off.
  window.clarksTrack = function () {};

  if (LIVE_HOSTS.indexOf(window.location.hostname) === -1) return;
  if (KEY.indexOf("phc_") !== 0) return;

  // PostHog's standard loader
  !function(t,e){var o,n,p,r;e.__SV||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}(p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host.replace(".i.posthog.com","-assets.i.posthog.com")+"/static/array.js",(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r);var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],u.toString=function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e},u.people.toString=function(){return u.toString(1)+".people (stub)"},o="capture identify alias people.set people.set_once set_config register register_once unregister opt_out_capturing has_opted_out_capturing opt_in_capturing reset".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);

  window.posthog.init(KEY, {
    api_host: "https://us.i.posthog.com",
    person_profiles: "identified_only",
    autocapture: true,
    capture_pageview: true,
    capture_pageleave: true,
    capture_exceptions: true,
    enable_heatmaps: true,
    disable_session_recording: true
  });

  window.clarksTrack = function (name, props) {
    window.posthog.capture(name, props);
  };

  // Named clicks: what was tapped and where on the page it sat.
  function clickLabel(href) {
    if (href.indexOf("tel:") === 0) return "call";
    if (href.indexOf("mailto:") === 0) return "email";
    if (href.indexOf("facebook.com") !== -1) return "facebook";
    if (href.indexOf("instagram.com") !== -1) return "instagram";
    if (href.indexOf("google.com/maps") !== -1) return "directions";
    if (href.indexOf("contact.html") === 0) {
      return href.indexOf("type=question") !== -1 ? "question" : "free_trial";
    }
    return null;
  }

  function clickPlace(link) {
    if (link.closest(".mobile-bar")) return "mobile_bar";
    if (link.closest(".site-header")) return "header";
    if (link.closest(".site-footer")) return "footer";
    if (link.closest(".hero")) return "hero";
    return "page_body";
  }

  document.addEventListener("click", function (e) {
    var link = e.target.closest ? e.target.closest("a[href]") : null;
    if (!link) return;
    var href = link.getAttribute("href");
    var label = clickLabel(href);
    if (!label) return;
    var plan = href.match(/[?&]plan=([^&#]+)/);
    window.posthog.capture("cta_click", {
      label: label,
      place: clickPlace(link),
      text: (link.textContent || "").trim().slice(0, 60),
      plan: plan ? decodeURIComponent(plan[1]) : undefined
    }, { transport: "sendBeacon", send_instantly: true });
  });

  // Attention: seconds each section sat in the middle of the screen.
  // Only the section crossing the screen's center line counts, so one section
  // is timed at a time, even on phones where sections are taller than the screen.
  var sections = Array.prototype.slice.call(document.querySelectorAll("main > section"));
  if (!sections.length || !("IntersectionObserver" in window)) return;

  var MAX_SECONDS = 300; // A tab left open doesn't count as five hours of reading.
  var totals = sections.map(function () { return 0; });
  var active = -1;
  var since = document.hidden ? null : Date.now();

  function sectionName(el, index) {
    // A section without a heading (like the quote on the home page) uses its first words.
    var source = el.querySelector("h1, h2, h3") || el;
    var text = source.textContent.replace(/\s+/g, " ").trim();
    return text ? text.slice(0, 60) : "Section " + (index + 1);
  }

  function addTime() {
    var now = Date.now();
    if (active !== -1 && since !== null) totals[active] += now - since;
    if (since !== null) since = now;
  }

  function sendAttention() {
    addTime();
    totals.forEach(function (ms, i) {
      var seconds = Math.round(ms / 1000);
      if (seconds < 1) return;
      window.posthog.capture("page_attention", {
        section: sectionName(sections[i], i),
        position: i + 1,
        seconds: Math.min(seconds, MAX_SECONDS)
      }, { transport: "sendBeacon", send_instantly: true });
      totals[i] = 0;
    });
  }

  var observer = new IntersectionObserver(function (entries) {
    addTime();
    entries.forEach(function (entry) {
      var i = sections.indexOf(entry.target);
      if (entry.isIntersecting) active = i;
      else if (active === i) active = -1;
    });
  }, { rootMargin: "-50% 0px -50% 0px", threshold: 0 });

  sections.forEach(function (el) { observer.observe(el); });

  document.addEventListener("visibilitychange", function () {
    if (document.hidden) {
      sendAttention();
      since = null;
    } else {
      since = Date.now();
    }
  });
  window.addEventListener("pagehide", sendAttention);
})();
