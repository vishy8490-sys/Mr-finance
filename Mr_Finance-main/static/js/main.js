// QuantRisk India Pro — shared utilities

async function fetchJSON(url, opts = {}) {
  const res = await fetch(url, opts);
  return res.json();
}

function showAlert(containerId, msg, type = 'info') {
  const el = document.getElementById(containerId);
  if (!el) return;
  const icons = { success: 'check-circle', error: 'exclamation-circle', info: 'info-circle' };
  el.innerHTML = `<div class="alert alert-${type}"><i class="fas fa-${icons[type] || 'info-circle'}"></i>${msg}</div>`;
  setTimeout(() => { el.innerHTML = ''; }, 4000);
}

function renderPlotly(divId, chartData) {
  const el = document.getElementById(divId);
  if (!el) return;
  if (chartData.error) {
    el.innerHTML = `<div class="empty-state"><i class="fas fa-chart-area"></i><p>${chartData.error}</p></div>`;
    return;
  }
  Plotly.react(divId, chartData.data, chartData.layout, { responsive: true, displayModeBar: false });
}

// Format number as Indian Rupees
function formatINR(value) {
  if (value === undefined || value === null) return '—';
  return '₹' + Number(value).toLocaleString('en-IN', { maximumFractionDigits: 2 });
}
