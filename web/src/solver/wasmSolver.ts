import type { WindResult } from "../data-model.ts";
import { getBuildingWindMesh } from "../mesh/getMesh.ts";

// Binario WebAssembly compilado desde windKernel.cpp
const WASM_B64 =
  "AGFzbQEAAAABEAJgA3x8fAF8YAR8fHx8AXwDAwIAAQUDAQABBygCFHBlYWtWZWxvY2l0eVByZXNzdXJlAAANem9uZVdpbmRGb3JjZQABCjsCKwBEAAAAAAAA4D8gAKIgAaIgAaJEAAAAAAAA8D9EAAAAAAAAHEAgAqKgogsNACAAIAEgAqGiIAOiCw==";

function decodeBase64(b64: string): Uint8Array {
  if (typeof Buffer !== "undefined") {
    return new Uint8Array(Buffer.from(b64, "base64"));
  }
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

export interface WindWasmExports {
  peakVelocityPressure: (rho: number, vm: number, Iv: number) => number;
  zoneWindForce: (qpKpa: number, cpe: number, cpi: number, areaM2: number) => number;
}

let cachedExports: WindWasmExports | null = null;

export async function initWindWasm(): Promise<WindWasmExports> {
  if (cachedExports) return cachedExports;
  const { instance } = await WebAssembly.instantiate(decodeBase64(WASM_B64));
  cachedExports = instance.exports as unknown as WindWasmExports;
  return cachedExports;
}

export async function solveBuildingWindWasm(
  vbMps: number,
  z0M: number,
  widthBM: number,
  depthDM: number,
  storyHeightsM: number[],
  subdivisionsPerStory: number,
  cpi: number
): Promise<WindResult> {
  const wasm = await initWindWasm();
  const { panels, mapping } = getBuildingWindMesh(
    widthBM,
    depthDM,
    storyHeightsM,
    subdivisionsPerStory,
    cpi
  );

  const rho = 1.25;
  const kr = 0.19 * Math.pow(z0M / 0.05, 0.07);
  const zMin = 2.0;

  let baseShearKn = 0;
  let overturningMomentKnm = 0;
  let qpTopKpa = 0;

  for (const p of panels) {
    const zEff = Math.max(p.zMidM, zMin);
    const cr = kr * Math.log(zEff / z0M);
    const vm = cr * vbMps;
    const iv = 1.0 / Math.log(zEff / z0M);
    const qpPa = wasm.peakVelocityPressure(rho, vm, iv);
    p.qpKpa = qpPa / 1000.0;
    const area = p.heightM > 0 ? p.widthM * p.heightM : (widthBM * depthDM) / 4.0;
    p.netForceKn = wasm.zoneWindForce(p.qpKpa, p.cpe, p.cpi, area);

    if (p.zone === "D") {
      baseShearKn += p.netForceKn;
      overturningMomentKnm += p.netForceKn * p.zMidM;
    } else if (p.zone === "E") {
      baseShearKn -= p.netForceKn;
      overturningMomentKnm -= p.netForceKn * p.zMidM;
    }
    if (p.qpKpa > qpTopKpa) qpTopKpa = p.qpKpa;
  }

  return { panels, mapping, baseShearKn, overturningMomentKnm, qpTopKpa };
}
