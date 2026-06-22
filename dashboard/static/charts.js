let dispenseChartInst = null;
let moistureChartInst = null;
let historyChartInst = null;
function renderHistoryCharts(history) {
  const labels = history.map(d => {
    const dt = new Date(d.date);
    return (dt.getMonth() + 1) + '/' + dt.getDate();
  });

  const dispensed = history.map(d => parseFloat((d.dispensed || 0).toFixed(2)));
  const rainfall  = history.map(d => parseFloat((d.rainfall || 0).toFixed(2)));
  const ydayRain  = history.map(d => parseFloat((d.yday_rain || 0).toFixed(2)));
  const moisture  = history.map(d => d.moisture != null ? parseFloat(d.moisture.toFixed(1)) : null);
  const et0       = history.map(d => parseFloat((d.et0 || 0).toFixed(2)));

  const rainDay = history.map(d => (d.yday_rain || 0) > 2);

  if (moistureChartInst) moistureChartInst.destroy();
  moistureChartInst = new Chart(document.getElementById('moistureChart'), {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Soil moisture %',
          data: moisture,
          borderColor: '#1D9E75',
          backgroundColor: 'transparent',
          pointBackgroundColor: history.map((_, i) => rainDay[i] ? '#378ADD' : '#1D9E75'),
          pointStyle: history.map((_, i) => rainDay[i] ? 'triangle' : 'circle'),
          pointRadius: history.map((_, i) => rainDay[i] ? 6 : 3),
          borderWidth: 2,
          tension: 0.3,
          yAxisID: 'y',
          spanGaps: true
        },
        {
          label: 'ET₀ mm',
          data: et0,
          borderColor: '#D85A30',
          backgroundColor: 'transparent',
          borderDash: [4, 3],
          pointRadius: 2,
          borderWidth: 1.5,
          tension: 0.3,
          yAxisID: 'y2'
        },
        {
          label: 'Yesterday Rainfall mm',
          data: ydayRain,
          borderColor: '#378ADD',
          backgroundColor: 'transparent',
          borderDash: [2, 2],
          pointRadius: 3,
          borderWidth: 1.5,
          tension: 0.3,
          yAxisID: 'y2'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => {
              switch (ctx.datasetIndex) {
                case 0:
                  return 'Moisture: ' +
                    (ctx.parsed.y != null
                      ? ctx.parsed.y.toFixed(1) + '%'
                      : 'no data');

                case 1:
                  return 'ET₀: ' + ctx.parsed.y.toFixed(2) + 'mm';

                case 2:
                  return 'Yesterday Rain: ' + ctx.parsed.y.toFixed(2) + 'mm';

                default:
                  return '';
              }
            }
          }
        }
      },
      scales: {
        x: {
          ticks: {
            font: { size: 11 },
            color: '#888780',
            maxTicksLimit: 10,
            maxRotation: 45
          },
          grid: {
            color: 'rgba(136,135,128,0.1)'
          }
        },
        y: {
          position: 'left',
          min: 0,
          max: 100,
          ticks: {
            font: { size: 11 },
            color: '#1D9E75',
            callback: v => v + '%'
          },
          grid: {
            color: 'rgba(136,135,128,0.1)'
          }
        },
        y2: {
          position: 'right',
          min: 0,
          max: 8,
          ticks: {
            font: { size: 11 },
            color: '#D85A30',
            callback: v => v + 'mm'
          },
          grid: {
            display: false
          }
        }
      }
    }
  });

  if (historyChartInst) historyChartInst.destroy();
  historyChartInst = new Chart(document.getElementById('historyChart'), {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Dispensed (L)',
          data: dispensed,
          backgroundColor: '#378ADD',
          borderRadius: 3
        },
        {
          label: 'Rainfall (mm)',
          data: rainfall,
          backgroundColor: '#5DCAA5',
          borderRadius: 3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          ticks: {
            font: { size: 11 },
            color: '#888780',
            maxTicksLimit: 12,
            maxRotation: 45
          },
          grid: {
            display: false
          }
        },
        y: {
          ticks: {
            font: { size: 11 },
            color: '#888780'
          },
          grid: {
            color: 'rgba(136,135,128,0.1)'
          }
        }
      }
    }
  });
}