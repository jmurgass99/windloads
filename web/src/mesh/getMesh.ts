import type { EnvelopeZoneMapping, WindFacadePanel } from "../data-model.ts";

export function getBuildingWindMesh(
  widthBM: number,
  depthDM: number,
  storyHeightsM: number[],
  subdivisionsPerStory: number,
  cpi: number
): { panels: WindFacadePanel[]; mapping: EnvelopeZoneMapping } {
  const div = Math.max(1, Math.floor(subdivisionsPerStory));
  const storyToPanels = new Map<number, number[]>();
  const panelToStory = new Map<number, number>();
  const roofToZones = new Map<string, number[]>();
  const panels: WindFacadePanel[] = [];

  let zCursor = 0;
  for (let sIdx = 0; sIdx < storyHeightsM.length; sIdx++) {
    const story = sIdx + 1;
    const dh = storyHeightsM[sIdx] / div;
    const indices: number[] = [];
    for (let i = 0; i < div; i++) {
      const zMid = zCursor + 0.5 * dh;
      for (const [zone, cpe] of [
        ["D", 0.8],
        ["E", -0.5],
      ] as const) {
        const idx = panels.length;
        panels.push({
          index: idx,
          story,
          zone,
          zMidM: zMid,
          heightM: dh,
          widthM: widthBM,
          qpKpa: 0,
          cpe,
          cpi,
          netForceKn: 0,
        });
        indices.push(idx);
        panelToStory.set(idx, story);
      }
      zCursor += dh;
    }
    storyToPanels.set(story, indices);
  }

  for (const [zone, cpeR] of [
    ["F", -1.8],
    ["G", -1.2],
    ["H", -0.7],
    ["I", -0.2],
  ] as const) {
    const idx = panels.length;
    panels.push({
      index: idx,
      story: storyHeightsM.length,
      zone,
      zMidM: zCursor,
      heightM: 0,
      widthM: widthBM * 0.5,
      qpKpa: 0,
      cpe: cpeR,
      cpi,
      netForceKn: 0,
    });
    roofToZones.set(zone, [idx]);
  }

  return {
    panels,
    mapping: { storyToPanels, panelToStory, roofToZones },
  };
}
