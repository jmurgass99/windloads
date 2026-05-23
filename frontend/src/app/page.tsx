import Link from 'next/link'

export default function HomePage() {
  return (
    <main className="min-h-screen p-8 bg-slate-950 text-slate-100">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-4xl font-bold mb-3">WindLoadJm</h1>
        <p className="text-slate-400 mb-8">
          Cálculo de cargas de viento — EC1, ASCE 7, NSR-10.
        </p>
        <div className="flex gap-3 flex-wrap">
          <Link href="/wind" className="px-5 py-3 rounded bg-blue-600 hover:bg-blue-700 text-white">
            Calcular presiones
          </Link>
          <Link href="/3d" className="px-5 py-3 rounded bg-emerald-600 hover:bg-emerald-700 text-white">
            Visor 3D
          </Link>
        </div>
      </div>
    </main>
  )
}
