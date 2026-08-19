(function () {
  "use strict";
  document.documentElement.classList.add("js-ready");
  function safe(fn, name) {
    try {
      fn();
    } catch (e) {
      /* Las mejoras visuales no bloquean el contenido. */
    }
  }
  function initMenu() {
    var button = document.querySelector("[data-menu]"),
      side = document.getElementById("sidebar"),
      closers = document.querySelectorAll("[data-menu-close]");
    if (!button || !side) return;
    function setMenu(open) {
      side.classList.toggle("open", open);
      document.body.classList.toggle("menu-open", open);
      button.setAttribute("aria-expanded", open ? "true" : "false");
      button.setAttribute("aria-label", open ? "Cerrar menú" : "Abrir menú");
    }
    button.addEventListener("click", function () { setMenu(!side.classList.contains("open")); });
    closers.forEach(function (closer) { closer.addEventListener("click", function () { setMenu(false); }); });
    side.querySelectorAll("nav a").forEach(function (link) { link.addEventListener("click", function () { setMenu(false); }); });
    document.addEventListener("keydown", function (event) { if (event.key === "Escape") setMenu(false); });
    addEventListener("resize", function () { if (innerWidth > 1000) setMenu(false); });
  }
  function initDocumentLookup() {
    var form = document.querySelector("[data-atencion-form]");
    if (!form) return;
    var tipo = form.querySelector("#id_tipo_documento"),
      numero = form.querySelector("#id_numero_documento"),
      estudiante = form.querySelector("#id_es_estudiante"),
      actualizar = form.querySelector("#id_actualizar_datos"),
      hint = form.querySelector("[data-document-hint]"),
      lookupBtn = form.querySelector("[data-lookup]"),
      required = form.querySelector("[data-required-step]"),
      company = form.querySelector("[data-company-step]"),
      toggle = form.querySelector("[data-update-toggle]"),
      studentToggle = form.querySelector("[data-student-toggle]"),
      submit = form.querySelector("[data-submit-row]"),
      mode = form.querySelector("[data-company-mode]"),
      responsable = form.querySelector("#id_responsable"),
      linea = form.querySelector('[data-field="linea"]'),
      lineaTitulo = form.querySelector("[data-linea-titulo]"),
      lineaSelect = form.querySelector("#id_linea");

    var LINEAS_POR_RESPONSABLE = [
      {
        match: ["vasquez"],
        titulo: "Línea: Agronegocios",
        grupos: [
          {
            nombre: null,
            opciones: ["café-cacao y derivados", "funcionales", "procesados"],
          },
        ],
      },
      {
        match: ["campos"],
        titulo: "Línea: Vestimenta",
        grupos: [
          {
            nombre: null,
            opciones: [
              "Vestimenta Alpaca",
              "Vestimenta Algodón",
              "Ropa para Bebé",
              "Home Deco",
              "Calzado",
              "Joyería",
            ],
          },
        ],
      },
      {
        match: ["junior"],
        titulo: "Línea: Manufactura, Acuicola y Digitalizacion",
        grupos: [
          {
            nombre: "Manufacturas",
            opciones: [
              "Equipamiento para la agroindustria",
              "Acabados para la construcción",
              "Proveedores a la minería",
              "Cosmética",
            ],
          },
          {
            nombre: "Servicios",
            opciones: [
              "Software",
              "Marketing digital",
              "Servicios a la minería",
              "Animación 2d y 3d",
              "Franquicias",
            ],
          },
          {
            nombre: "Pesca",
            opciones: ["Acuicultura (trucha)", "Peces tropicales"],
          },
        ],
      },
    ];

    function normalizeText(value) {
      return (value || "")
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/\s+/g, " ")
        .trim();
    }

    function configurarLinea() {
      var texto = "";
      if (responsable && responsable.selectedIndex > -1) {
        texto = normalizeText(
          responsable.options[responsable.selectedIndex].text,
        );
      }
      var config = null;
      LINEAS_POR_RESPONSABLE.forEach(function (item) {
        if (config) return;
        if (item.match.some(function (kw) {
          return texto.indexOf(normalizeText(kw)) !== -1;
        })) config = item;
      });
      if (!config) {
        show(linea, false);
        if (lineaSelect) lineaSelect.value = "";
        return;
      }
      if (lineaSelect) {
        lineaSelect.innerHTML =
          '<option value="">Seleccionar una opción</option>';
        config.grupos.forEach(function (grupo) {
          var parent = lineaSelect;
          if (grupo.nombre) {
            var optgroup = document.createElement("optgroup");
            optgroup.label = grupo.nombre;
            lineaSelect.appendChild(optgroup);
            parent = optgroup;
          }
          grupo.opciones.forEach(function (opcion) {
            var option = document.createElement("option");
            option.value = opcion;
            option.textContent = opcion;
            parent.appendChild(option);
          });
        });
      }
      if (lineaTitulo) lineaTitulo.textContent = config.titulo;
      show(linea, true);
    }

    if (responsable) responsable.addEventListener("change", configurarLinea);

    numero.addEventListener("input", function () {
      if (tipo.value !== "Pasaporte") this.value = this.value.replace(/\D/g, "");
      else this.value = this.value.replace(/[^a-z0-9-]/gi, "").toUpperCase();
      var error = form.querySelector(".document-number .field-error");
      if (error) error.remove();
      hint.textContent =
        "Usaremos el documento únicamente para encontrar tu registro.";
      hint.classList.remove("found");
      hint.classList.remove("invalid");
    });
    function show(el, visible) {
      if (!el) return;
      if (visible) {
        el.hidden = false;
        if (el.hasAttribute("data-step")) {
          el.classList.remove("step-rise");
          void el.offsetWidth;
          el.classList.add("step-rise");
        }
      } else {
        el.hidden = true;
        el.classList.remove("step-rise");
      }
    }
    function fill(data) {
      [
        "nombre",
        "tipo_personeria",
        "nombres_apellidos",
        "cargo",
        "tipo_usuario",
        "telefono",
        "email",
        "sector",
        "region",
        "oferta_producto_servicio",
      ].forEach(function (k) {
        var el = form.querySelector("#id_" + k);
        if (el && data[k] !== undefined) el.value = data[k];
      });
    }
    function chooseByText(select, text) {
      if (!select) return;
      Array.prototype.some.call(select.options, function (option) {
        if (option.text.trim().toLowerCase() === text.toLowerCase()) {
          select.value = option.value;
          return true;
        }
        return false;
      });
    }
    function applyStudentMode() {
      var active = !!(estudiante && estudiante.checked && tipo.value === "DNI");
      ["sector", "oferta_producto_servicio", "tipo_personeria", "tipo_usuario", "cargo", "tipo_atencion", "tema_consulta"].forEach(function (name) {
        var wrapper = form.querySelector('[data-field="' + name + '"]');
        if (wrapper) wrapper.hidden = active;
      });
      var university = form.querySelector('[data-field="nombre"] > span');
      if (university) university.textContent = active ? "UNIVERSIDAD O INSTITUCIÓN" : "NOMBRE DE LA EMPRESA / INSTITUCIÓN / PERSONA NATURAL";
      if (!active) return;
      show(required, true);
      show(company, true);
      show(submit, true);
      var tipoAtencion = form.querySelector("#id_tipo_atencion"),
        sector = form.querySelector("#id_sector"),
        oferta = form.querySelector("#id_oferta_producto_servicio"),
        personeria = form.querySelector("#id_tipo_personeria"),
        usuario = form.querySelector("#id_tipo_usuario"),
        cargo = form.querySelector("#id_cargo"),
        tema = form.querySelector("#id_tema_consulta");
      if (tipoAtencion) tipoAtencion.value = "Presencial";
      chooseByText(sector, "Otros");
      if (oferta) oferta.value = "Otros";
      if (personeria) personeria.value = "Persona Natural";
      if (usuario) usuario.value = "Estudiante";
      if (cargo) cargo.value = "Estudiante";
      if (tema) tema.value = "Otros";
      if (mode) mode.textContent = "Datos del estudiante y su institución.";
    }
    function perform(includeData) {
      var doc = numero.value.trim();
      if (!doc) {
        hint.textContent = "Escribe tu número de documento para continuar.";
        hint.classList.remove("found");
        hint.classList.add("invalid");
        return;
      }
      var invalido = null;
      if (tipo.value === "RUC" && doc.length !== 11) {
        invalido = "El RUC debe tener exactamente 11 dígitos.";
      } else if (tipo.value === "DNI" && doc.length !== 8) {
        invalido = "El DNI debe tener exactamente 8 dígitos.";
      }
      if (invalido) {
        hint.textContent = invalido;
        hint.classList.remove("found");
        hint.classList.add("invalid");
        return;
      }
      lookupBtn.disabled = true;
      fetch(
        "/api/empresa/?tipo=" +
          encodeURIComponent(tipo.value) +
          "&numero=" +
          encodeURIComponent(doc) +
          (includeData ? "&actualizar=1" : ""),
        { credentials: "same-origin" },
      )
        .then(function (r) {
          return r.json();
        })
        .then(function (data) {
          show(required, true);
          show(submit, true);
          if (data.encontrado) {
            hint.textContent =
              "Registro encontrado: " +
              data.resumen +
              ". Solo necesitamos los datos de esta atención.";
            hint.classList.add("found");
            hint.classList.remove("invalid");
            show(toggle, true);
            if (includeData) {
              fill(data);
              show(company, true);
              mode.textContent = "Revisa y actualiza únicamente lo que cambió.";
            } else show(company, false);
          } else {
            hint.textContent = "Completa tus datos.";
            hint.classList.remove("found");
            hint.classList.remove("invalid");
            show(toggle, false);
            actualizar.checked = true;
            show(company, true);
            mode.textContent = "";
          }
          applyStudentMode();
        })
        .catch(function () {
          hint.textContent =
            "No pudimos consultar el documento. Intenta nuevamente.";
        })
        .finally(function () {
          lookupBtn.disabled = false;
        });
    }
    lookupBtn.addEventListener("click", function () {
      perform(false);
    });
    numero.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        perform(false);
      }
    });
    tipo.addEventListener("change", function () {
      show(required, false);
      show(company, false);
      show(submit, false);
      show(toggle, false);
      show(studentToggle, tipo.value === "DNI");
      if (tipo.value !== "DNI" && estudiante) estudiante.checked = false;
      var error = form.querySelector(".document-number .field-error");
      if (error) error.remove();
      hint.textContent =
        "Usaremos el documento únicamente para encontrar tu registro.";
      hint.classList.remove("found");
      hint.classList.remove("invalid");
      applyStudentMode();
    });
    if (estudiante) estudiante.addEventListener("change", applyStudentMode);
    actualizar.addEventListener("change", function () {
      if (actualizar.checked) perform(true);
      else show(company, false);
    });
    function clearPublicForm() {
      form.reset();
      configurarLinea();
      show(required, false);
      show(company, false);
      show(submit, false);
      show(toggle, false);
      show(studentToggle, tipo.value === "DNI");
      hint.textContent = "Usaremos el documento únicamente para encontrar tu registro.";
      hint.classList.remove("found");
      hint.classList.remove("invalid");
    }
    function showConfirmation(responsable) {
      var modal = document.querySelector("[data-confirmation-modal]");
      if (!modal) return;
      var name = modal.querySelector("[data-confirmation-responsable]");
      var countdown = modal.querySelector("[data-confirmation-countdown]");
      var close = modal.querySelector("[data-confirmation-close]");
      var remaining = 10;
      var finish = function () {
        window.clearInterval(timer);
        modal.hidden = true;
        clearPublicForm();
      };
      if (name) name.textContent = responsable || "el equipo correspondiente";
      if (countdown) countdown.textContent = remaining;
      modal.hidden = false;
      var timer = window.setInterval(function () {
        remaining -= 1;
        if (countdown) countdown.textContent = remaining;
        if (remaining <= 0) finish();
      }, 1000);
      if (close) close.onclick = finish;
    }
    if (form.dataset.confirmacionResponsable) {
      showConfirmation(form.dataset.confirmacionResponsable);
    }
    form.addEventListener("submit", function (e) {
      if (form.dataset.publico !== "1") return;
      var submitButton = form.querySelector('[type="submit"]');
      if (submitButton) submitButton.disabled = true;
    });
    if (form.querySelector(".field-error,.errorlist")) {
      show(required, true);
      show(submit, true);
      show(
        company,
        !!(company && company.querySelector(".field-error,.errorlist")),
      );
      show(toggle, true);
      show(studentToggle, tipo.value === "DNI");
      applyStudentMode();
    }
    show(studentToggle, tipo.value === "DNI");
    configurarLinea();
  }
  function initMessages() {
    setTimeout(function () {
      document.querySelectorAll(".message").forEach(function (el) {
        el.style.opacity = "0";
        setTimeout(function () {
          el.remove();
        }, 300);
      });
    }, 4500);
  }
  function initEntrySummary() {
    var modal = document.querySelector("[data-entry-summary]");
    if (!modal) return;
    var closeButtons = modal.querySelectorAll("[data-entry-summary-close]");
    var previousOverflow = document.body.style.overflow;
    function close() {
      modal.classList.add("is-closing");
      document.body.style.overflow = previousOverflow;
      setTimeout(function () { modal.remove(); }, 180);
    }
    document.body.style.overflow = "hidden";
    closeButtons.forEach(function (button) { button.addEventListener("click", close); });
    document.addEventListener("keydown", function onKeydown(event) {
      if (event.key === "Escape" && document.body.contains(modal)) {
        close();
        document.removeEventListener("keydown", onKeydown);
      }
    });
    var focusTarget = modal.querySelector(".entry-summary__close");
    if (focusTarget) focusTarget.focus();
  }
  function initReveal() {
    var items = document.querySelectorAll("[data-reveal]");
    if (!items.length) return;
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-revealed");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.03 },
    );
    items.forEach(function (el, i) {
      el.style.transitionDelay = i * 0.09 + "s";
      io.observe(el);
    });
    setTimeout(function () {
      items.forEach(function (el) {
        el.classList.add("is-revealed");
      });
    }, 6000);
  }
  function initPassword() {
    var button = document.querySelector("[data-password-toggle]");
    if (!button) return;
    var input = button.closest(".password-wrap").querySelector("input");
    button.addEventListener("click", function () {
      var show = input.type === "password";
      input.type = show ? "text" : "password";
      button.textContent = show ? "Ocultar" : "Ver";
      button.setAttribute(
        "aria-label",
        show ? "Ocultar contraseña" : "Mostrar contraseña",
      );
    });
  }
  function initLogin() {
    var scene = document.querySelector("[data-login-scene]");
    if (!scene || matchMedia("(hover:none)").matches) return;
    var image = scene.querySelector(".login-hero");
    scene.addEventListener("mousemove", function (e) {
      var rect = scene.getBoundingClientRect(),
        x = (e.clientX - rect.left) / rect.width - 0.5,
        y = (e.clientY - rect.top) / rect.height - 0.5;
      image.style.transform =
        "scale(1.055) translate3d(" + -x * 10 + "px," + -y * 8 + "px,0)";
    });
    scene.addEventListener("mouseleave", function () {
      image.style.transform = "";
    });
  }
  function initActiveNav() {
    var path = location.pathname;
    document.querySelectorAll(".sidebar nav a").forEach(function (link) {
      if (link.pathname === path) link.classList.add("is-active");
    });
  }
  document.addEventListener("DOMContentLoaded", function () {
    safe(initMenu, "menu");
    safe(initDocumentLookup, "document");
    safe(initMessages, "messages");
    safe(initEntrySummary, "entry-summary");
    safe(initReveal, "reveal");
    safe(initPassword, "password");
    safe(initLogin, "login");
    safe(initActiveNav, "nav");
  });
})();
