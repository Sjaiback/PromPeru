(function () {
  var node = document.getElementById("dashboard-chart-data");
  if (!node || typeof Chart === "undefined") return;
  var data = JSON.parse(node.textContent);
  var red = "#d91023", ink = "#201f1d", muted = "#807d78", paper = "#f4f1ec";
  var palette = [red, "#e87855", "#d7a661", "#7c8a6c", "#667b9b", "#a27278", "#b39557"];
  Chart.defaults.font.family = "DM Sans, Arial, sans-serif";
  Chart.defaults.color = muted;
  Chart.defaults.animation = { duration: 850, easing: "easeOutQuart" };

  function safe(values) { return values && values.length ? values : [0]; }
  function labels(values) { return values && values.length ? values : ["Sin registros"]; }
  function tooltip() { return { backgroundColor: ink, padding: 12, cornerRadius: 10, displayColors: false }; }
  function axis() { return { grid: { color: "rgba(32,31,29,.07)" }, border: { display: false }, ticks: { padding: 8 } }; }
  function canvas(id) { return document.getElementById(id); }
  function bar(id, set, horizontal) {
    var el = canvas(id); if (!el) return;
    new Chart(el, { type: "bar", data: { labels: labels(set.labels), datasets: [{ data: safe(set.values), borderRadius: 9, borderSkipped: false, backgroundColor: palette }] }, options: { indexAxis: horizontal ? "y" : "x", maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: tooltip() }, scales: { x: axis(), y: axis() } } });
  }

  var trend = canvas("trendChart");
  if (trend) new Chart(trend, { type: "line", data: { labels: labels(data.tendencia.labels).map(function (v) { return v === "Sin registros" ? v : new Date(v + "T00:00:00").toLocaleDateString("es-PE", { day:"2-digit", month:"short" }); }), datasets: [{ data: safe(data.tendencia.values), borderColor: red, backgroundColor: "rgba(217,16,35,.12)", fill: true, tension: .42, borderWidth: 3, pointRadius: 3, pointHoverRadius: 6, pointBackgroundColor: "#fff", pointBorderColor: red, pointBorderWidth: 3 }] }, options: { maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: tooltip() }, scales: { x: axis(), y: { ...axis(), beginAtZero: true, precision: 0 } } } });

  var status = canvas("statusChart");
  if (status) new Chart(status, { type: "doughnut", data: { labels: labels(data.estados.labels), datasets: [{ data: safe(data.estados.values), backgroundColor: data.estados.colors && data.estados.colors.length ? data.estados.colors : palette, borderColor: paper, borderWidth: 5, hoverOffset: 7 }] }, options: { cutout: "70%", maintainAspectRatio: false, plugins: { legend: { position: "bottom", labels: { usePointStyle: true, pointStyle: "circle", padding: 16 } }, tooltip: tooltip() } } });
  bar("channelChart", data.canales, false);
  bar("advisorChart", data.responsables, true);
  bar("regionChart", data.regiones, false);
  bar("sectorChart", data.sectores, true);
})();
