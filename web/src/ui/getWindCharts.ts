import type { WindResult } from "../data-model.ts";

export function renderVelocityPressureChart(canvas: HTMLCanvasElement, res: WindResult): void {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const w = (canvas.width = canvas.clientWidth || 360);
  const h = (canvas.height = canvas.clientHeight || 205);
  ctx.clearRect(0, 0, w, h);

  ctx.strokeStyle = "rgba(148,163,184,0.25)";
  ctx.strokeRect(36, 16, w - 52, h - 38);

  const windward = res.panels.filter((p) => p.zone === "D");
  const maxZ = Math.max(...windward.map((p) => p.zMidM + 0.5 * p.heightM), 1);
  const maxQp = Math.max(res.qpTopKpa, 0.2);

  ctx.strokeStyle = "#38bdf8";
  ctx.lineWidth = 2.4;
  ctx.beginPath();
  windward.forEach((p, idx) => {
    const x = 36 + (p.qpKpa / maxQp) * (w - 56);
    const y = h - 22 - (p.zMidM / maxZ) * (h - 42);
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  ctx.fillStyle = "#e2e8f0";
  ctx.font = "11px Inter, sans-serif";
  ctx.fillText(`Perfil q_p(z) EN 1991-1-4 — q_p(H) = ${res.qpTopKpa.toFixed(2)} kPa`, 42, 30);
}

export function renderZoneForcesChart(canvas: HTMLCanvasElement, res: WindResult): void {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const w = (canvas.width = canvas.clientWidth || 360);
  const h = (canvas.height = canvas.clientHeight || 205);
  ctx.clearRect(0, 0, w, h);

  ctx.strokeStyle = "rgba(148,163,184,0.25)";
  ctx.strokeRect(36, 16, w - 52, h - 38);

  const zones = ["D", "E", "F", "G", "H", "I"];
  const totals = zones.map((z) =>
    res.panels.filter((p) => p.zone === z).reduce((acc, p) => acc + Math.abs(p.netForceKn), 0)
  );
  const maxF = Math.max(...totals, 1);
  const bw = (w - 68) / zones.length;

  totals.forEach((val, idx) => {
    const bh = (val / maxF) * (h - 52);
    const x = 42 + idx * bw;
    ctx.fillStyle = idx === 0 ? "#f97316" : "#38bdf8";
    ctx.fillRect(x, h - 22 - bh, bw - 8, bh);
    ctx.fillStyle = "#e2e8f0";
    ctx.font = "10px Inter, sans-serif";
    ctx.fillText(zones[idx], x + 6, h - 8);
  });
}
