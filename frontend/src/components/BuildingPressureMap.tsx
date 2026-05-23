'use client'

import React from 'react'
import type { ZonePressure } from '@/lib/api'

/**
 * Mapa SVG en planta con presiones por zona.
 *
 * Layout (vista en planta, viento → desde la izquierda):
 *
 *    +------------------+
 *    |   Side (top)     |
 *  W |                  | L
 *  i |                  | e
 *  n |    Building      | e
 *  d |                  | w
 *  w |                  | a
 *  a |                  | r
 *  r |                  | d
 *  d |                  |
 *    +------------------+
 *        Side (bottom)
 */

function pressureToColor(p: number, vmax: number): string {
  // p>0 (succión externa positiva hacia el muro): rojo. p<0 (succión): azul.
  const t = Math.min(1, Math.abs(p) / Math.max(vmax, 1e-6))
  if (p >= 0) {
    // amarillo → rojo
    const r = Math.round(255)
    const g = Math.round(255 * (1 - t))
    return `rgb(${r},${g},80)`
  }
  const b = 255
  const g = Math.round(180 * (1 - t))
  return `rgb(80,${g},${b})`
}

export function BuildingPressureMap({ zones }: { zones: ZonePressure[] }) {
  const byZone = Object.fromEntries(zones.map((z) => [z.zone, z]))
  const vmax = Math.max(...zones.map((z) => Math.abs(z.pressure_kPa)), 1)

  const fill = (name: ZonePressure['zone']) =>
    byZone[name] ? pressureToColor(byZone[name].pressure_kPa, vmax) : '#334155'

  const text = (name: ZonePressure['zone']) => {
    const z = byZone[name]
    return z ? `${z.zone}\nCp=${z.cp.toFixed(2)}\n${z.pressure_kPa.toFixed(3)} kPa` : name
  }

  const lines = (name: ZonePressure['zone']) => text(name).split('\n')

  return (
    <div className="w-full max-w-2xl mx-auto bg-slate-900/50 rounded-lg p-4">
      <svg viewBox="0 0 500 400" className="w-full h-auto">
        {/* Wind arrow */}
        <defs>
          <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto">
            <path d="M0,0 L10,5 L0,10 z" fill="#38bdf8" />
          </marker>
        </defs>
        <line x1="10" y1="200" x2="80" y2="200" stroke="#38bdf8" strokeWidth="3" markerEnd="url(#arr)" />
        <text x="10" y="190" fill="#38bdf8" fontSize="12">Wind</text>

        {/* Windward face (left wall of building) */}
        <rect x="90" y="80" width="40" height="240" fill={fill('Windward')} stroke="#0f172a" />
        {/* Body (top down view) */}
        <rect x="130" y="80" width="240" height="240" fill="#1e293b" stroke="#0f172a" />
        {/* Leeward face (right wall) */}
        <rect x="370" y="80" width="40" height="240" fill={fill('Leeward')} stroke="#0f172a" />
        {/* Side top */}
        <rect x="130" y="40" width="240" height="40" fill={fill('Side')} stroke="#0f172a" />
        {/* Side bottom (mirror, same Cp) */}
        <rect x="130" y="320" width="240" height="40" fill={fill('Side')} stroke="#0f172a" />
        {/* Roof indicator (small badge) */}
        <rect x="200" y="160" width="100" height="80" fill={fill('Roof')} stroke="#0f172a" opacity="0.85" />

        {/* Labels */}
        {lines('Windward').map((t, i) => (
          <text key={'w' + i} x="110" y={130 + i * 14} fill="#0f172a" fontSize="10" textAnchor="middle">{t}</text>
        ))}
        {lines('Leeward').map((t, i) => (
          <text key={'l' + i} x="390" y={130 + i * 14} fill="#0f172a" fontSize="10" textAnchor="middle">{t}</text>
        ))}
        {lines('Side').map((t, i) => (
          <text key={'s' + i} x="250" y={55 + i * 12} fill="#0f172a" fontSize="10" textAnchor="middle">{t}</text>
        ))}
        {lines('Roof').map((t, i) => (
          <text key={'r' + i} x="250" y={190 + i * 12} fill="#0f172a" fontSize="10" textAnchor="middle">{t}</text>
        ))}
      </svg>
      <p className="text-xs text-slate-500 mt-2">
        Vista en planta. Colores: rojo = presión positiva (empuje), azul = succión.
      </p>
    </div>
  )
}
