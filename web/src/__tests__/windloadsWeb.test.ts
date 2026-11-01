import assert from "node:assert/strict";
import { solveBuildingWindWasm } from "../solver/wasmSolver.ts";

const heights = [4.0, 3.5, 3.5, 3.5, 3.5];
const res1 = await solveBuildingWindWasm(28, 0.05, 24, 18, heights, 1, 0.2);
const res4 = await solveBuildingWindWasm(28, 0.05, 24, 18, heights, 4, 0.2);

assert.equal(res1.mapping.storyToPanels.get(1)?.length, 2);
assert.equal(res4.mapping.storyToPanels.get(1)?.length, 8);
assert.equal(res4.mapping.roofToZones.size, 4);
assert.ok(res4.baseShearKn > 200, "Wind base shear must exceed 200 kN");
assert.ok(Math.abs(res1.baseShearKn - res4.baseShearKn) / res4.baseShearKn < 0.05);
console.log(
  `WindLoads WASM test OK: qp(H)=${res4.qpTopKpa.toFixed(2)} kPa, V_base=${res4.baseShearKn.toFixed(1)} kN`
);
