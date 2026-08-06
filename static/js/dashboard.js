(function () {
  var node = document.getElementById("dashboard-chart-data");
  if (!node || typeof Chart === "undefined") return;
  var data = JSON.parse(node.textContent);
  var red = "#d91023", ink = "#201f1d", muted = "#807d78", paper = "#f4f1ec";
  var palette = [red, "#ec7651", "#d9a455", "#768567", "#607a9f", "#a07178", "#b99b52", "#52656f", "#bf4f68"];
  var territoryColors = {
    "Lima":"#3e82a8", "Callao":"#5799bc", "Ica":"#d69b58", "Arequipa":"#b85f48", "Moquegua":"#c97b58", "Tacna":"#a9574c", "La Libertad":"#c5924a", "Lambayeque":"#d2ad56", "Piura":"#d6b153", "Tumbes":"#e0c467",
    "Junín":"#9a6441", "Pasco":"#8a5b41", "Huancavelica":"#815847", "Ayacucho":"#a96845", "Apurímac":"#966247", "Cusco":"#905442", "Puno":"#765148", "Cajamarca":"#a47339", "Áncash":"#7d674c",
    "Amazonas":"#5a936c", "San Martín":"#4c8c5d", "Loreto":"#3d7d55", "Madre de Dios":"#6d9d55", "Ucayali":"#4b875d"
  };
  Chart.defaults.font.family = "DM Sans, Arial, sans-serif";
  Chart.defaults.color = muted;
  Chart.defaults.animation = { duration: 850, easing: "easeOutQuart" };
  Chart.register({
    id: "valueLabels",
    afterDatasetsDraw: function (chart) {
      if (chart.config.type !== "bar") return;
      var ctx = chart.ctx, horizontal = chart.options.indexAxis === "y";
      ctx.save(); ctx.fillStyle = ink; ctx.font = "600 11px DM Sans, Arial";
      chart.getDatasetMeta(0).data.forEach(function (bar, index) {
        var value = chart.data.datasets[0].data[index];
        if (horizontal) { ctx.textAlign = "left"; ctx.textBaseline = "middle"; ctx.fillText(value, bar.x + 8, bar.y); }
        else { ctx.textAlign = "center"; ctx.textBaseline = "bottom"; ctx.fillText(value, bar.x, bar.y - 8); }
      });
      ctx.restore();
    }
  });

  function safe(values) { return values && values.length ? values : [0]; }
  function labels(values) { return values && values.length ? values : ["Sin registros"]; }
  function tooltip() { return { backgroundColor: ink, padding: 12, cornerRadius: 10, displayColors: true, callbacks: { label: function (item) { return " " + item.formattedValue + " atenciones"; } } }; }
  function axis() { return { grid: { color: "rgba(32,31,29,.07)" }, border: { display: false }, ticks: { padding: 8, precision: 0 } }; }
  function canvas(id) { return document.getElementById(id); }
  function colorsFor(set, regional) { return labels(set.labels).map(function (label, index) { return regional ? (territoryColors[label] || palette[index % palette.length]) : palette[index % palette.length]; }); }
  function renderSummary(name, set, colors) {
    var element = document.querySelector('[data-summary="' + name + '"]'); if (!element) return;
    element.innerHTML = labels(set.labels).map(function (label, index) { return '<span><i style="background:' + colors[index % colors.length] + '"></i>' + label + '<b>' + safe(set.values)[index] + '</b></span>'; }).join("");
  }
  function bar(id, set, horizontal) {
    var el = canvas(id); if (!el) return;
    var colors = colorsFor(set, false); renderSummary(id === "advisorChart" ? "responsables" : "", set, colors);
    new Chart(el, { type: "bar", data: { labels: labels(set.labels), datasets: [{ data: safe(set.values), borderRadius: 9, borderSkipped: false, backgroundColor: colors }] }, options: { indexAxis: horizontal ? "y" : "x", layout: { padding: horizontal ? { right: 32 } : { top: 22 } }, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: tooltip() }, scales: { x: axis(), y: axis() } } });
  }
  function circular(id, set, type, regional, summaryName) {
    var el = canvas(id); if (!el) return;
    var colors = colorsFor(set, regional); renderSummary(summaryName, set, colors);
    new Chart(el, { type: type, data: { labels: labels(set.labels), datasets: [{ data: safe(set.values), backgroundColor: colors, borderColor: paper, borderWidth: type === "doughnut" ? 5 : 2, hoverOffset: 8 }] }, options: { maintainAspectRatio: false, scales: type === "polarArea" ? { r: { ticks: { display: false }, grid: { color: "rgba(32,31,29,.08)" } } } : {}, plugins: { legend: { display: false }, tooltip: tooltip() }, cutout: type === "doughnut" ? "69%" : undefined } });
  }
  function radar(id, set) {
    var el = canvas(id); if (!el) return;
    var colors = colorsFor(set, false); renderSummary("sectores", set, colors);
    new Chart(el, { type: "radar", data: { labels: labels(set.labels), datasets: [{ data: safe(set.values), borderColor: red, backgroundColor: "rgba(217,16,35,.18)", borderWidth: 2.5, pointBackgroundColor: colors, pointBorderColor: "#fff", pointBorderWidth: 2, pointRadius: 4 }] }, options: { maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: tooltip() }, scales: { r: { beginAtZero: true, ticks: { display: false, precision: 0 }, grid: { color: "rgba(32,31,29,.12)" }, angleLines: { color: "rgba(32,31,29,.12)" }, pointLabels: { font: { size: 11 } } } } } });
  }

  var trend = canvas("trendChart"), activePeriod = "dia", trendChart;
  function formatTrendLabel(value, period) {
    var date = new Date(value + "T00:00:00");
    if (period === "mes") return date.toLocaleDateString("es-PE", { month: "short", year: "2-digit" });
    if (period === "semana") return "Sem. " + date.toLocaleDateString("es-PE", { day: "2-digit", month: "short" });
    return date.toLocaleDateString("es-PE", { day:"2-digit", month:"short" });
  }
  function updateTrend(period) {
    activePeriod = period; var serie = data.tendencias[period];
    trendChart.data.labels = labels(serie.labels).map(function (item) { return item === "Sin registros" ? item : formatTrendLabel(item, period); });
    trendChart.data.datasets[0].data = safe(serie.values); trendChart.update();
  }
  if (trend) {
    var ctx = trend.getContext("2d"), gradient = ctx.createLinearGradient(0, 0, 0, 280); gradient.addColorStop(0, "rgba(217,16,35,.28)"); gradient.addColorStop(1, "rgba(217,16,35,.015)");
    trendChart = new Chart(trend, { type: "line", data: { labels: [], datasets: [{ data: [], borderColor: red, backgroundColor: gradient, fill: true, tension: .42, borderWidth: 3, pointRadius: 3, pointHoverRadius: 6, pointBackgroundColor: "#fff", pointBorderColor: red, pointBorderWidth: 3 }] }, options: { maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: tooltip() }, scales: { x: axis(), y: { ...axis(), beginAtZero: true, ticks: { precision:0, stepSize:1 } } } } });
    updateTrend("dia");
    document.querySelectorAll("[data-chart-period]").forEach(function (button) { button.addEventListener("click", function () { document.querySelectorAll("[data-chart-period]").forEach(function (item) { item.classList.remove("is-active"); }); button.classList.add("is-active"); updateTrend(button.dataset.chartPeriod); }); });
  }
  var status = canvas("statusChart");
  if (status) { var stateData = { labels: data.estados.labels, values: data.estados.values }; var stateColors = data.estados.colors && data.estados.colors.length ? data.estados.colors : palette; renderSummary("estados", stateData, stateColors); new Chart(status, { type: "doughnut", data: { labels: labels(stateData.labels), datasets: [{ data: safe(stateData.values), backgroundColor: stateColors, borderColor: paper, borderWidth: 5, hoverOffset: 8 }] }, options: { cutout: "69%", maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: tooltip() } } }); }
  circular("channelChart", data.canales, "doughnut", false, "canales");
  bar("advisorChart", data.responsables, true);
  circular("regionChart", data.regiones, "polarArea", true, "regiones");
  radar("sectorChart", data.sectores);
})();
