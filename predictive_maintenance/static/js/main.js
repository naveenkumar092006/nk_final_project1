// main.js — Frontend Utilities & Alarm System

// ─── ALARM SOUND (Web Audio API) ─────────────────────────────────────────────
let alarmCtx = null;
let alarmNodes = [];
let alarmActive = false;

function playAlarm() {
  if (alarmActive) return;
  alarmActive = true;
  alarmCtx = new (window.AudioContext || window.webkitAudioContext)();
  function beep(freq, start, dur) {
    const osc  = alarmCtx.createOscillator();
    const gain = alarmCtx.createGain();
    osc.connect(gain);
    gain.connect(alarmCtx.destination);
    osc.type = 'square';
    osc.frequency.setValueAtTime(freq, alarmCtx.currentTime + start);
    gain.gain.setValueAtTime(0.2, alarmCtx.currentTime + start);
    gain.gain.exponentialRampToValueAtTime(0.001, alarmCtx.currentTime + start + dur);
    osc.start(alarmCtx.currentTime + start);
    osc.stop(alarmCtx.currentTime + start + dur);
    alarmNodes.push(osc);
  }
  // Repeating alarm pattern
  for (let i = 0; i < 6; i++) {
    beep(880, i * 0.5, 0.2);
    beep(660, i * 0.5 + 0.25, 0.2);
  }
  setTimeout(() => { alarmActive = false; }, 4000);
}

function stopAlarm() {
  alarmActive = false;
  alarmNodes.forEach(n => { try { n.stop(); } catch(e){} });
  alarmNodes = [];
}

// ─── CHART DEFAULTS ──────────────────────────────────────────────────────────
Chart.defaults.color = '#6688aa';
Chart.defaults.borderColor = 'rgba(0,212,255,0.1)';
Chart.defaults.font.family = "'Exo 2', sans-serif";

function pmChartDefaults(label, color) {
  return {
    label, fill: true,
    borderColor: color,
    backgroundColor: color.replace('rgb', 'rgba').replace(')', ',0.08)'),
    tension: 0.4, pointRadius: 3,
    pointBackgroundColor: color,
    borderWidth: 2
  };
}

// ─── GAUGE DRAWING ────────────────────────────────────────────────────────────
function drawGauge(canvasId, value, label) {
  const c = document.getElementById(canvasId);
  if (!c) return;
  const ctx = c.getContext('2d');
  const w = c.width, h = c.height;
  ctx.clearRect(0,0,w,h);
  const cx = w/2, cy = h - 10, r = Math.min(w,h*2)*0.42;

  // Background arc
  ctx.beginPath();
  ctx.arc(cx, cy, r, Math.PI, 0);
  ctx.lineWidth = 14; ctx.strokeStyle = 'rgba(255,255,255,0.06)';
  ctx.lineCap = 'round'; ctx.stroke();

  // Value arc
  const pct = Math.min(100, Math.max(0, value)) / 100;
  const color = value > 60 ? '#00ff88' : value > 30 ? '#ffaa00' : '#ff3355';
  ctx.beginPath();
  ctx.arc(cx, cy, r, Math.PI, Math.PI + pct * Math.PI);
  ctx.lineWidth = 14; ctx.strokeStyle = color;
  ctx.lineCap = 'round'; ctx.stroke();

  // Text
  ctx.fillStyle = '#fff';
  ctx.font = `bold ${Math.floor(r*0.45)}px 'Rajdhani', sans-serif`;
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(Math.round(value), cx, cy - 8);

  ctx.fillStyle = '#6688aa';
  ctx.font = `${Math.floor(r*0.22)}px 'Exo 2', sans-serif`;
  ctx.fillText(label, cx, cy + 14);
}

// ─── UTILITY ──────────────────────────────────────────────────────────────────
function statusClass(status) {
  return { Healthy: 'pm-status-healthy', Warning: 'pm-status-warning', Critical: 'pm-status-critical' }[status] || '';
}
function progressClass(status) {
  return { Healthy: 'pm-progress-healthy', Warning: 'pm-progress-warning', Critical: 'pm-progress-critical' }[status] || '';
}
function rulClass(days) {
  return days > 20 ? 'rul-green' : days > 10 ? 'rul-yellow' : 'rul-red';
}

// ─── LIVE SIMULATION ─────────────────────────────────────────────────────────
let simInterval = null;

function startSimulation(machineId, onData) {
  if (simInterval) return;
  simInterval = setInterval(async () => {
    try {
      const res = await fetch(`/api/live-data?machine_id=${machineId}`);
      const data = await res.json();
      onData(data);
    } catch(e) { console.error('Sim error', e); }
  }, 2000);
}

function stopSimulation() {
  if (simInterval) { clearInterval(simInterval); simInterval = null; }
}

// ─── AUTO REFRESH ─────────────────────────────────────────────────────────────
function setupAutoRefresh(ms) {
  setTimeout(() => window.location.reload(), ms);
}
