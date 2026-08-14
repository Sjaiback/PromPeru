(function () {
  var node = document.getElementById("dashboard-chart-data");
  if (!node || typeof Chart === "undefined") return;
  var data = JSON.parse(node.textContent);
  var red = "#d91023", ink = "#201f1d", muted = "#807d78", paper = "#f4f1ec";
  var charts = [];
  function darkMode() { return document.documentElement.dataset.theme === "dark"; }
  function chartInk() { return darkMode() ? "#eee8ea" : ink; }
  function chartMuted() { return darkMode() ? "#aaa2a5" : muted; }
  function chartPaper() { return darkMode() ? "#1d191b" : paper; }
  function chartGrid() { return darkMode() ? "rgba(255,255,255,.09)" : "rgba(32,31,29,.07)"; }
  var palette = [red, "#ec7651", "#d9a455", "#768567", "#607a9f", "#a07178", "#b99b52", "#52656f", "#bf4f68"];
  var territoryColors = {"Lima":"#3e82a8","Callao":"#5799bc","Ica":"#d69b58","Arequipa":"#b85f48","Moquegua":"#c97b58","Tacna":"#a9574c","La Libertad":"#c5924a","Lambayeque":"#d2ad56","Piura":"#d6b153","Tumbes":"#e0c467","Junín":"#9a6441","Pasco":"#8a5b41","Huancavelica":"#815847","Ayacucho":"#a96845","Apurímac":"#966247","Cusco":"#905442","Puno":"#765148","Cajamarca":"#a47339","Áncash":"#7d674c","Amazonas":"#5a936c","San Martín":"#4c8c5d","Loreto":"#3d7d55","Madre de Dios":"#6d9d55","Ucayali":"#4b875d"};
  Chart.defaults.font.family = "DM Sans, Arial, sans-serif";
  Chart.defaults.color = chartMuted();
  Chart.defaults.animation = { duration: 750, easing: "easeOutQuart" };
  Chart.register({ id:"barValues", afterDatasetsDraw:function(chart){ if(chart.config.type !== "bar") return; var context=chart.ctx, horizontal=chart.options.indexAxis === "y"; context.save(); context.fillStyle=chartInk(); context.font="700 11px DM Sans, Arial"; chart.getDatasetMeta(0).data.forEach(function(bar,index){ var value=chart.data.datasets[0].data[index]; if(horizontal){ context.textAlign="left"; context.textBaseline="middle"; context.fillText(value,bar.x+8,bar.y); }else{ context.textAlign="center"; context.textBaseline="bottom"; context.fillText(value,bar.x,bar.y-7); } }); context.restore(); } });
  function safe(values) { return values && values.length ? values : [0]; }
  function labels(values) { return values && values.length ? values : ["Sin registros"]; }
  function tooltip() { return { enabled:true, backgroundColor:darkMode() ? "#f4eff0" : ink, titleColor:darkMode() ? "#171315" : "#fff", bodyColor:darkMode() ? "#171315" : "#fff", padding:13, cornerRadius:10, displayColors:true, callbacks:{ label:function(item){ return " " + item.label + ": " + item.formattedValue + " atenciones"; } } }; }
  function axis() { return { grid:{ color:chartGrid() }, border:{ display:false }, ticks:{ color:chartMuted(), padding:8, precision:0 } }; }
  function colorsFor(set, regional) { return labels(set.labels).map(function(label,index){ return regional ? (territoryColors[label] || palette[index % palette.length]) : palette[index % palette.length]; }); }
  function bar(id, set, horizontal, regional) {
    var el = document.getElementById(id); if (!el) return;
    charts.push(new Chart(el, { type:"bar", data:{ labels:labels(set.labels), datasets:[{ data:safe(set.values), borderRadius:9, borderSkipped:false, backgroundColor:colorsFor(set, regional) }] }, options:{ indexAxis:horizontal ? "y" : "x", layout:{ padding:horizontal ? {right:28} : {top:22} }, maintainAspectRatio:false, interaction:{ mode:"nearest", intersect:true }, plugins:{ legend:{display:false}, tooltip:tooltip() }, scales:{ x:axis(), y:axis() } } }));
  }
  function doughnut(id, set, colors) {
    var el = document.getElementById(id); if (!el) return;
    charts.push(new Chart(el, { type:"doughnut", data:{ labels:labels(set.labels), datasets:[{ data:safe(set.values), backgroundColor:colors, borderColor:chartPaper(), borderWidth:5, hoverOffset:8 }] }, options:{ cutout:"69%", maintainAspectRatio:false, plugins:{ legend:{display:false}, tooltip:tooltip() } } }));
  }
  function formatTrendLabel(value, period) { var date = new Date(value + "T00:00:00"); if (period === "mes") return date.toLocaleDateString("es-PE", {month:"short",year:"2-digit"}); if (period === "semana") return "Sem. " + date.toLocaleDateString("es-PE", {day:"2-digit",month:"short"}); return date.toLocaleDateString("es-PE", {day:"2-digit",month:"short"}); }
  var trendChart;
  function drawTrend(period) {
    var el = document.getElementById("trendChart"), serie = data.tendencias && data.tendencias[period];
    if (!el || !serie) return;
    if (trendChart) {
      charts = charts.filter(function (chart) { return chart !== trendChart; });
      trendChart.destroy();
    }
    var context = el.getContext("2d"), gradient = context.createLinearGradient(0,0,0,280);
    gradient.addColorStop(0,"rgba(217,16,35,.28)"); gradient.addColorStop(1,"rgba(217,16,35,.015)");
    trendChart = new Chart(el, { type:"line", data:{ labels:labels(serie.labels).map(function(value){ return value === "Sin registros" ? value : formatTrendLabel(value,period); }), datasets:[{ data:safe(serie.values), borderColor:red, backgroundColor:gradient, fill:true, tension:.42, borderWidth:3, pointRadius:3, pointHoverRadius:7, pointBackgroundColor:darkMode() ? "#1d191b" : "#fff", pointBorderColor:red, pointBorderWidth:3 }] }, options:{ maintainAspectRatio:false, interaction:{ mode:"index", intersect:false }, plugins:{ legend:{display:false}, tooltip:tooltip() }, scales:{ x:axis(), y:{ ...axis(), beginAtZero:true, ticks:{color:chartMuted(),padding:8,precision:0,stepSize:1} } } } });
    charts.push(trendChart);
  }
  drawTrend("dia");
  document.querySelectorAll("[data-chart-period]").forEach(function(button){ button.addEventListener("click",function(){ var period = button.dataset.chartPeriod; document.querySelectorAll("[data-chart-period]").forEach(function(item){ item.classList.toggle("is-active",item === button); }); drawTrend(period); }); });
  var statusColors = data.estados.colors && data.estados.colors.length ? data.estados.colors : palette;
  doughnut("statusChart", {labels:data.estados.labels,values:data.estados.values}, statusColors);
  var statusLegend = document.getElementById("statusLegend");
  if(statusLegend) statusLegend.innerHTML = labels(data.estados.labels).map(function(label,index){ return '<span><i style="background:'+statusColors[index % statusColors.length]+'"></i>'+label+' <b>'+safe(data.estados.values)[index]+'</b></span>'; }).join("");
  bar("channelChart", data.canales, false, false);
  bar("advisorChart", data.responsables, true, false);
  bar("regionChart", data.regiones, false, true);
  bar("sectorChart", data.sectores, true, false);
  bar("ratingRegionChart", data.rating_regiones, false, true);
  window.addEventListener("promperu:theme", function () {
    Chart.defaults.color = chartMuted();
    charts.forEach(function (chart) {
      if (!chart || !chart.options) return;
      if (chart.options.scales) {
        ["x", "y"].forEach(function (key) {
          var scale = chart.options.scales[key];
          if (!scale) return;
          scale.grid.color = chartGrid();
          scale.ticks.color = chartMuted();
        });
      }
      chart.options.plugins.tooltip = tooltip();
      if (chart.config.type === "doughnut") chart.data.datasets[0].borderColor = chartPaper();
      if (chart.config.type === "line") chart.data.datasets[0].pointBackgroundColor = darkMode() ? "#1d191b" : "#fff";
      chart.update();
    });
  });
})();
