import van from "vanjs-core";
import { solveBuildingWindWasm } from "./solver/wasmSolver.ts";
import { fetchWindHealthApi } from "./solver/apiClient.ts";
import { createWindViewer3D } from "./viewer/getViewer3D.ts";
import { renderVelocityPressureChart, renderZoneForcesChart } from "./ui/getWindCharts.ts";

const { div, h2, h3, label, input, span, strong, canvas, button } = van.tags;

const vbMps = van.state(28);
const z0M = van.state(0.05);
const subdivisions = van.state(3);
const cpi = van.state(0.2);

const qpTopText = van.state("0.00 kPa");
const baseShearText = van.state("0.0 kN");
const otmText = van.state("0.0 kN·m");
const panelsText = van.state("0");
const apiStatus = van.state("Modo WASM local");

const viewerWrap = div({ class: "viewer-wrap" });
const qpCanvas = canvas({ class: "chart" });
const zoneCanvas = canvas({ class: "chart" });
const viewer = createWindViewer3D(viewerWrap);

const storyHeights = [4.2, 3.6, 3.6, 3.6, 3.6];

async function recompute() {
  const res = await solveBuildingWindWasm(
    vbMps.val,
    z0M.val,
    24.0,
    18.0,
    storyHeights,
    subdivisions.val,
    cpi.val
  );
  qpTopText.val = `${res.qpTopKpa.toFixed(2)} kPa`;
  baseShearText.val = `${res.baseShearKn.toFixed(1)} kN`;
  otmText.val = `${res.overturningMomentKnm.toFixed(0)} kN·m`;
  panelsText.val = `${res.panels.length}`;
  viewer.update(24.0, 18.0, res);
  renderVelocityPressureChart(qpCanvas, res);
  renderZoneForcesChart(zoneCanvas, res);
}

van.derive(() => {
  void recompute();
});

const app = div(
  { class: "layout" },
  div(
    { class: "panel" },
    h2("WindLoads 3D Envelope"),
    div(
      { class: "control-row" },
      label(() => `Velocidad básica v_b,0 = ${vbMps.val} m/s`),
      input({
        type: "range",
        min: "18",
        max: "48",
        step: "1",
        value: vbMps,
        oninput: (e: Event) => (vbMps.val = Number((e.target as HTMLInputElement).value)),
      })
    ),
    div(
      { class: "control-row" },
      label(() => `Rugosidad z_0 = ${z0M.val.toFixed(2)} m`),
      input({
        type: "range",
        min: "0.01",
        max: "1.00",
        step: "0.02",
        value: z0M,
        oninput: (e: Event) => (z0M.val = Number((e.target as HTMLInputElement).value)),
      })
    ),
    div(
      { class: "control-row" },
      label(() => `Subdivisiones por planta (EnvelopeZoneMapping) = ${subdivisions.val}`),
      input({
        type: "range",
        min: "1",
        max: "8",
        step: "1",
        value: subdivisions,
        oninput: (e: Event) => (subdivisions.val = Number((e.target as HTMLInputElement).value)),
      })
    ),
    div(
      { class: "control-row" },
      label(() => `Coeficiente interior c_pi = ${cpi.val.toFixed(2)}`),
      input({
        type: "range",
        min: "-0.3",
        max: "0.3",
        step: "0.05",
        value: cpi,
        oninput: (e: Event) => (cpi.val = Number((e.target as HTMLInputElement).value)),
      })
    ),
    div(
      { class: "kpi-grid" },
      div({ class: "kpi" }, span("Presión pico q_p(H)"), strong(qpTopText)),
      div({ class: "kpi" }, span("Cortante basal V_w"), strong(baseShearText)),
      div({ class: "kpi" }, span("Momento vuelco M_w"), strong(otmText)),
      div({ class: "kpi" }, span("Paneles activos"), strong(panelsText))
    ),
    button(
      {
        onclick: async () => {
          const ok = await fetchWindHealthApi("http://localhost:8000");
          apiStatus.val = ok ? "FastAPI sincronizado OK" : "FastAPI offline (usando WASM local)";
        },
      },
      "Sincronizar con FastAPI"
    ),
    span({ style: "font-size:0.75rem;color:#94a3b8" }, apiStatus)
  ),
  viewerWrap,
  div(
    { class: "panel" },
    h3("Perfil de Presión Pico q_p(z) (WASM)"),
    qpCanvas,
    h3("Fuerza Resultante por Zona (D, E, F, G, H, I)"),
    zoneCanvas
  )
);

document.getElementById("app")?.appendChild(app);
