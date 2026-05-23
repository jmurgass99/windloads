'use client'

import React, { useState } from 'react'
import { WindBox3D, type FaceCp } from '@/components/WindBox3D'

const DEFAULT_FACES: FaceCp[] = [
  { name: 'Front', cp: 0.8 },   // Windward (cara hacia el viento)
  { name: 'Back', cp: -0.5 },   // Leeward
  { name: 'Left', cp: -0.7 },   // Side
  { name: 'Right', cp: -0.7 },  // Side
  { name: 'Top', cp: -1.0 },    // Roof
  { name: 'Bottom', cp: 0.0 },  // Base
]

export default function Wind3DPage() {
  const [faces, setFaces] = useState<FaceCp[]>(DEFAULT_FACES)

  function update(name: FaceCp['name'], cp: number) {
    setFaces((arr) => arr.map((f) => (f.name === name ? { ...f, cp } : f)))
  }

  return (
    <main className="min-h-screen p-8 bg-slate-950 text-slate-100">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Visor 3D — presiones por zona</h1>
        <p className="text-slate-400 mb-6">
          Caja R3F con caras coloreadas según C<sub>p</sub>. Hover sobre cada cara muestra el valor.
        </p>
        <WindBox3D faces={faces} />
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-6">
          {faces.map((f) => (
            <div key={f.name} className="bg-slate-900/50 rounded p-3">
              <label className="block text-xs text-slate-400 mb-1">
                {f.name} — Cp = {f.cp.toFixed(2)}
              </label>
              <input
                type="range" min={-2} max={1} step={0.05}
                value={f.cp}
                onChange={(e) => update(f.name, Number(e.target.value))}
                className="w-full"
              />
            </div>
          ))}
        </div>
      </div>
    </main>
  )
}
