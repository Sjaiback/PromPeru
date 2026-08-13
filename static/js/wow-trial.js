(function () {
  "use strict";

  function safe(fn) {
    try { fn(); } catch (error) { /* El contenido funciona sin los efectos. */ }
  }

  function initWowReveal() {
    var elements = document.querySelectorAll("[data-wow-reveal]");
    if (!elements.length) return;
    elements.forEach(function (element, index) {
      element.classList.add("wow-prepared");
      element.style.setProperty("--wow-delay", Math.min(index * 70, 350) + "ms");
    });
    if (!("IntersectionObserver" in window)) {
      elements.forEach(function (element) { element.classList.add("wow-visible"); });
      return;
    }
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("wow-visible");
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.03, rootMargin: "0px 0px -2% 0px" });
    elements.forEach(function (element) { observer.observe(element); });
    setTimeout(function () {
      elements.forEach(function (element) { element.classList.add("wow-visible"); });
    }, 6000);
  }

  function initMagneticButtons() {
    if (!matchMedia("(hover: hover) and (pointer: fine)").matches) return;
    document.querySelectorAll(".app-body .btn-primary").forEach(function (button) {
      button.addEventListener("mousemove", function (event) {
        var rect = button.getBoundingClientRect();
        button.style.setProperty("--magnetic-x", ((event.clientX - rect.left - rect.width / 2) * .12) + "px");
        button.style.setProperty("--magnetic-y", ((event.clientY - rect.top - rect.height / 2) * .12) + "px");
      });
      button.addEventListener("mouseleave", function () {
        button.style.setProperty("--magnetic-x", "0px");
        button.style.setProperty("--magnetic-y", "0px");
      });
    });
  }

  function initCardLight() {
    if (!matchMedia("(hover: hover) and (pointer: fine)").matches) return;
    document.querySelectorAll("[data-wow-card]").forEach(function (card) {
      card.addEventListener("mousemove", function (event) {
        var rect = card.getBoundingClientRect();
        card.style.setProperty("--card-x", (event.clientX - rect.left) + "px");
        card.style.setProperty("--card-y", (event.clientY - rect.top) + "px");
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    safe(initWowReveal);
    safe(initMagneticButtons);
    safe(initCardLight);
  });
})();
