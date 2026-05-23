'use client'

import React, { useMemo, useState } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Html } from '@react-three/drei'
import * as THREE from 'three'

export interface FaceCp {
  name: 'Front' | 'Back' | 'Left' | 'Right' | 'Top' | 'Bottom'
  cp: number
}

function cpToColor(cp: number): string {
  // -2 → azul, 0 → gris, +1 → rojo
  const t = Math.max(-2, Math.min(1, cp))
  if (t >= 0) {
    const r = 255
    const g = Math.round(220 * (1 - t))
    const b = Math.round(220 * (1 - t))
    return `rgb(${r},${g},${b})`
  }
  const s = Math.min(1, -t / 2)
  const r = Math.round(60 * (1 - s))
  const g = Math.round(120 + 80 * (1 - s))
  const b = 255
  return `rgb(${r},${g},${b})`
}

function Box({
  size,
  faces,
  onHover,
}: {
  size: [number, number, number]
  faces: FaceCp[]
  onHover: (f: FaceCp | null) => void
}) {
  const [hoveredFace, setHoveredFace] = useState<number | null>(null)
  const [W, H, D] = size

  // Face order in three: +X (right), -X (left), +Y (top), -Y (bottom), +Z (front), -Z (back)
  const order: FaceCp['name'][] = ['Right', 'Left', 'Top', 'Bottom', 'Front', 'Back']
  const faceMap = Object.fromEntries(faces.map((f) => [f.name, f]))

  const materials = useMemo(
    () =>
      order.map((name) => {
        const f = faceMap[name]
        return new THREE.MeshStandardMaterial({
          color: f ? cpToColor(f.cp) : '#475569',
          metalness: 0.1,
          roughness: 0.7,
        })
      }),
    [faces],
  )

  return (
    <mesh
      onPointerMove={(e) => {
        e.stopPropagation()
        const i = e.faceIndex !== undefined ? Math.floor(e.faceIndex / 2) : null
        if (i !== hoveredFace) {
          setHoveredFace(i)
          if (i !== null) {
            const name = order[i]
            onHover(faceMap[name] ?? null)
          }
        }
      }}
      onPointerOut={() => {
        setHoveredFace(null)
        onHover(null)
      }}
      material={materials}
    >
      <boxGeometry args={[W, H, D]} />
    </mesh>
  )
}

export function WindBox3D({ faces, size = [4, 3, 3] }: { faces: FaceCp[]; size?: [number, number, number] }) {
  const [hover, setHover] = useState<FaceCp | null>(null)

  return (
    <div className="relative w-full h-[500px] bg-slate-900 rounded-lg overflow-hidden">
      <Canvas camera={{ position: [8, 6, 8], fov: 50 }} shadows>
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} intensity={0.8} castShadow />
        <Box size={size} faces={faces} onHover={setHover} />
        <gridHelper args={[20, 20, '#334155', '#475569']} position={[0, -size[1] / 2 - 0.01, 0]} />
        <OrbitControls enableDamping />
        {hover && (
          <Html position={[0, size[1] / 2 + 1, 0]} center>
            <div className="bg-slate-950/90 border border-slate-700 rounded px-3 py-1 text-xs text-slate-100 whitespace-nowrap">
              {hover.name}: Cp = {hover.cp.toFixed(2)}
            </div>
          </Html>
        )}
      </Canvas>
      <div className="absolute top-2 left-2 bg-slate-950/70 text-xs text-slate-300 px-3 py-2 rounded">
        Hover sobre las caras para ver Cp.
      </div>
    </div>
  )
}
