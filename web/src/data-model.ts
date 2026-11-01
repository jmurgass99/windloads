export interface EnvelopeZoneMapping {
  storyToPanels: Map<number, number[]>;
  panelToStory: Map<number, number>;
  roofToZones: Map<string, number[]>;
}

export interface WindFacadePanel {
  index: number;
  story: number;
  zone: string;
  zMidM: number;
  heightM: number;
  widthM: number;
  qpKpa: number;
  cpe: number;
  cpi: number;
  netForceKn: number;
}

export interface WindResult {
  panels: WindFacadePanel[];
  mapping: EnvelopeZoneMapping;
  baseShearKn: number;
  overturningMomentKnm: number;
  qpTopKpa: number;
}
