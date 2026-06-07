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

function updateSchedule(today, tickInterval, pumpRate) {
    const totalTicks = (9 * 60) / tickInterval;
    const tickAmount = ((today.dispensed || 0) / totalTicks).toFixed(3);
    const tickDuration = Math.max(Math.round(parseFloat(tickAmount) / pumpRate), 3);

    document.getElementById('sched-fetch').textContent     = `ET₀ ${(today.et0 || 0).toFixed(2)}mm → ${(today.dispensed || 0).toFixed(2)}L scheduled`;
    document.getElementById('sched-morning').textContent   = `Every ${tickInterval} min · ${tickAmount}L per tick (${tickDuration}s)`;
    document.getElementById('sched-afternoon').textContent = `Every ${tickInterval} min · ${tickAmount}L per tick (${tickDuration}s)`;
}

async function load() {
  try {
    const [histRes, tickRes, configRes] = await Promise.all([
        fetch('/api/history'),
        fetch('/api/ticks'),
        fetch('/api/config')
    ]);
    const history = await histRes.json();
    const ticks   = await tickRes.json();
    const config  = await configRes.json();

    const tickInterval = parseInt(config.tick_interval_mins);
    const pumpRate     = parseFloat(config.pump_rate_ls);

    const today          = history.length ? history[history.length - 1] : null;
    const dispensedSoFar = ticks.reduce((s, t) => s + (t.tick_amount || 0), 0);

    if (today) {
        updateMetrics(today, dispensedSoFar);
        updateStatusCard(today);
        updateSchedule(today, tickInterval, pumpRate);
    }

    if (ticks.length)   renderDispenseChart(ticks);
    if (history.length) renderHistoryCharts(history);

    document.getElementById('status-dot').className     = 'online';
    document.getElementById('last-updated').textContent = 'Updated ' + new Date().toLocaleTimeString();

  } catch (e) {
    document.getElementById('last-updated').textContent = 'Could not reach API';
    console.error(e);
  }
}

load();
setInterval(load, 60000);
