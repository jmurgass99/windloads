# WindLoadJm — frontend Next.js

Frontend Next.js 14 (App Router) + TypeScript + Tailwind para el cálculo de
cargas de viento (EC1 / ASCE 7 / NSR-10).

## Páginas

| Ruta    | Issue        | Descripción                                                       |
| ------- | ------------ | ----------------------------------------------------------------- |
| `/`     | —            | Landing simple                                                    |
| `/wind` | IDEAS_20 #19 | Form (V_b, exposición, geometría) + mapa SVG planta con presiones |
| `/3d`   | IDEAS_20 #20 | Visor R3F caja con caras coloreadas por Cp + hover                |

## Quickstart

```bash
cd frontend
npm install
npm run dev   # http://localhost:3000
```

Variables:

- `NEXT_PUBLIC_API_URL` — base del backend FastAPI (`windloadjm.api.app`).
  Por defecto `http://localhost:8000`. Las rutas `/api/*` se proxean.

## Dependencias notables

- `next@14.2.5`, `react@18`, `tailwindcss@3`
- `@react-three/fiber@8` + `@react-three/drei@9` + `three@0.166` (visor 3D)
- `axios` para HTTP

## Estado

Verificación visual **pendiente** — los archivos se escribieron sin levantar
`npm run dev` en este lote (limitación de entorno). Tras `npm install`
el usuario debe validar el flow.
