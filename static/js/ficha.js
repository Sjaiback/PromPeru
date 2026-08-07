(function () {
  "use strict";
  var form = document.querySelector("[data-ficha-form]");
  if (!form) return;

  function valueOf(code) {
    var checked = form.querySelector('[name="' + code + '"]:checked');
    if (checked) return checked.value;
    var input = form.querySelector('[name="' + code + '"]');
    return input ? input.value : "";
  }
  function updateConditions() {
    form.querySelectorAll("[data-show-if]").forEach(function (box) {
      var parts = box.dataset.showIf.split(":");
      box.hidden = valueOf(parts[0]) !== parts[1];
    });
  }
  form.addEventListener("change", updateConditions);
  updateConditions();

  form.addEventListener("click", function (event) {
    var add = event.target.closest("[data-repeat-add]");
    if (add) {
      var list = form.querySelector('[data-repeat-code="' + add.dataset.repeatAdd + '"]');
      var source = list && list.querySelector(".repeat-row");
      if (!source) return;
      var row = source.cloneNode(true);
      row.querySelectorAll("input,select,textarea").forEach(function (input) {
        input.value = "";
        if (input.type === "checkbox" || input.type === "radio") input.checked = false;
      });
      list.appendChild(row);
    }
    var remove = event.target.closest("[data-repeat-remove]");
    if (remove) {
      var listBox = remove.closest("[data-repeat-list]");
      var rows = listBox.querySelectorAll(".repeat-row");
      var minimum = Number(listBox.dataset.repeatMin || 1);
      if (rows.length > minimum) remove.closest(".repeat-row").remove();
      else rows[0].querySelectorAll("input,select,textarea").forEach(function (input) { input.value = ""; });
    }
  });

  form.querySelectorAll(".blank-toggle input").forEach(function (box) {
    box.addEventListener("change", function () {
      var input = box.closest(".input-with-blank").querySelector("input.form-control");
      input.disabled = box.checked;
      if (box.checked) input.value = "";
    });
  });
})();
