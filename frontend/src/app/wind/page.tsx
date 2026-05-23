'use client'

import React, { useState } from 'react'
import { calculateWind, type WindRequest, type WindResponse } from '@/lib/api'
import { BuildingPressureMap } from '@/components/BuildingPressureMap'

export default function WindPage() {
  const [form, setForm] = useState<WindRequest>({
    V_b_ms: 27,
    exposure: 'II',
    building: { width_m: 24, depth_m: 18, height_m: 30 },
    code: 'EC1',
  })
  const [result, setResult] = useState<WindResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true); setError(null); setResult(null)
    try {
      const res = await calculateWind(form)
      setResult(res)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error desconocido')
    } finally { setLoading(false) }
  }

  return (
    <main className="min-h-screen p-8 bg-slate-950 text-slate-100">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Cargas de viento</h1>
        <p className="text-slate-400 mb-6">POST <code>/api/wind/calculate</code></p>

        <form onSubmit={onSubmit} className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-900/50 rounded p-6 mb-6">
          <div>
            <label className="block text-sm mb-1">V<sub>b</sub> (m/s)</label>
            <input type="number" step="0.1" value={form.V_b_ms}
              onChange={(e) => setForm({ ...form, V_b_ms: Number(e.target.value) })}
              className="w-full px-3 py-2 rounded bg-slate-800 border border-slate-700 text-sm" />
          </div>
          <div>
            <label className="block text-sm mb-1">Exposición</label>
            <select value={form.exposure}
              onChange={(e) => setForm({ ...form, exposure: e.target.value as WindRequest['exposure'] })}
              className="w-full px-3 py-2 rounded bg-slate-800 border border-slate-700 text-sm">
              <option>I</option><option>II</option><option>III</option><option>IV</option>
            </select>
          </div>
          <div>
            <label className="block text-sm mb-1">Norma</label>
            <select value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value as WindRequest['code'] })}
              className="w-full px-3 py-2 rounded bg-slate-800 border border-slate-700 text-sm">
              <option value="EC1">EC1</option>
              <option value="ASCE7">ASCE 7</option>
              <option value="NSR10">NSR-10</option>
            </select>
          </div>
          <div>
            <label className="block text-sm mb-1">Ancho B (m)</label>
            <input type="number" step="0.5" value={form.building.width_m}
              onChange={(e) => setForm({ ...form, building: { ...form.building, width_m: Number(e.target.value) } })}
              className="w-full px-3 py-2 rounded bg-slate-800 border border-slate-700 text-sm" />
          </div>
          <div>
            <label className="block text-sm mb-1">Profundidad D (m)</label>
            <input type="number" step="0.5" value={form.building.depth_m}
              onChange={(e) => setForm({ ...form, building: { ...form.building, depth_m: Number(e.target.value) } })}
              className="w-full px-3 py-2 rounded bg-slate-800 border border-slate-700 text-sm" />
          </div>
          <div>
            <label className="block text-sm mb-1">Altura H (m)</label>
            <input type="number" step="0.5" value={form.building.height_m}
              onChange={(e) => setForm({ ...form, building: { ...form.building, height_m: Number(e.target.value) } })}
              className="w-full px-3 py-2 rounded bg-slate-800 border border-slate-700 text-sm" />
          </div>
          <div className="md:col-span-3">
            <button type="submit" disabled={loading}
              className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-sm">
              {loading ? 'Calculando…' : 'Calcular presiones'}
            </button>
          </div>
        </form>

        {error && (
          <div className="bg-red-900/40 border border-red-700 rounded p-3 mb-4 text-sm">{error}</div>
        )}

        {result && (
          <div className="space-y-4">
            <div className="bg-slate-900/50 rounded p-4 text-sm">
              <b>q<sub>p</sub> = {result.q_p_kPa.toFixed(3)} kPa</b>
            </div>
            <BuildingPressureMap zones={result.zones} />
            <table className="w-full text-sm bg-slate-900/50 rounded p-3">
              <thead className="text-slate-400 text-left">
                <tr><th className="p-2">Zona</th><th>Cp</th><th>p (kPa)</th></tr>
              </thead>
              <tbody>
                {result.zones.map((z) => (
                  <tr key={z.zone} className="border-t border-slate-800">
                    <td className="p-2">{z.zone}</td>
                    <td>{z.cp.toFixed(2)}</td>
                    <td>{z.pressure_kPa.toFixed(3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  )
}
