function getStatus() {
  const h = new Date().getHours();
  if (h < 6)  return { label: 'Waiting',      cls: 'badge-info' };
  if (h < 11) return { label: 'Dispensing',   cls: 'badge-success' };
  if (h < 14) return { label: 'Paused',       cls: 'badge-warning' };
  if (h < 18) return { label: 'Dispensing',   cls: 'badge-success' };
  return       { label: 'Done for today', cls: 'badge-info' };
}

function updateMetrics(today, dispensedSoFar) {
  document.getElementById('m-daily').textContent     = (today.dispensed     || 0).toFixed(2);
  document.getElementById('m-dispensed').textContent = dispensedSoFar.toFixed(2);
  document.getElementById('m-remaining').textContent = Math.max(0, (today.dispensed || 0) - dispensedSoFar).toFixed(2);
  document.getElementById('m-et0').textContent       = (today.et0           || 0).toFixed(2);
  document.getElementById('m-rain').textContent      = (today.rainfall      || 0).toFixed(1);
  document.getElementById('m-forecast').textContent  = (today.forecast_prob || 0).toFixed(0);
}

function updateStatusCard(today) {
  const s = getStatus();
  const badge = document.getElementById('status-badge');
  badge.textContent = s.label;
  badge.className = 'badge ' + s.cls;

  document.getElementById('status-et0').textContent      = (today.et0      || 0).toFixed(2) + ' mm';
  document.getElementById('status-rain').textContent     = (today.rainfall || 0).toFixed(1) + ' mm';
  document.getElementById('status-forecast').textContent = (today.forecast_prob || 0).toFixed(0) + '%';
}

function updateSchedule(today) {
  const tickAmount = ((today.dispensed || 0) / 54).toFixed(3);
  document.getElementById('sched-fetch').textContent     = 'ET\u2080 ' + (today.et0 || 0).toFixed(2) + 'mm \u2192 ' + (today.dispensed || 0).toFixed(2) + 'L scheduled';
  document.getElementById('sched-morning').textContent   = 'Every 10 min \u00b7 ' + tickAmount + 'L per tick';
  document.getElementById('sched-afternoon').textContent = 'Every 10 min \u00b7 ' + tickAmount + 'L per tick';
}

async function load() {
  try {
    const [histRes, tickRes] = await Promise.all([
      fetch('/api/history'),
      fetch('/api/ticks')
    ]);
    const history = await histRes.json();
    const ticks   = await tickRes.json();

    const today          = history.length ? history[history.length - 1] : null;
    const dispensedSoFar = ticks.reduce((s, t) => s + (t.tick_amount || 0), 0);

    if (today) {
      updateMetrics(today, dispensedSoFar);
      updateStatusCard(today);
      updateSchedule(today);
    }

    if (ticks.length)   renderDispenseChart(ticks);
    if (history.length) renderHistoryCharts(history);

    document.getElementById('status-dot').className        = 'online';
    document.getElementById('last-updated').textContent    = 'Updated ' + new Date().toLocaleTimeString();

  } catch (e) {
    document.getElementById('last-updated').textContent = 'Could not reach API';
    console.error(e);
  }
}

load();
setInterval(load, 60000);
