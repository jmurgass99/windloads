"""API REST de windloads (FastAPI) sin servidor: llamadas con `TestClient` a todos los endpoints y errores 400.

Endpoints: `/` (índice), `/api/wind/ec1`, `/api/wind/asce7`, `/api/wind/nsr10`, `/api/wind/components/cc`,
`/api/export` (texto) y `/api/wind/openfoam-pre`. Cada uno envuelve la capa de servicios; los errores de entrada
devuelven 400 con el mensaje de la excepción. La versión de la aplicación es `windloads.__version__` (antes de
1.2.0 la API declaraba 0.1.0). Necesita el extra `api` (fastapi, httpx); sin él el ejemplo lo dice y termina.

Ejecutar:  python examples/rest_api_testclient_ec1_asce7_nsr10_cc_export_openfoam_version_and_400_on_invalid_input.py
"""
import json
import warnings


def main() -> None:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")   # aviso de starlette sobre httpx, ajeno al paquete
            from fastapi.testclient import TestClient
        from windloads.api.app import app
    except ImportError as exc:
        print(f"Extra 'api' no instalado ({exc}); pip install windloads[api]")
        return
    import windloads

    c = TestClient(app)
    print(f"Versión de la API: {app.version} (windloads.__version__ = {windloads.__version__})")
    print(f"GET / → {c.get('/').json()['endpoints']}")

    r = c.post("/api/wind/ec1", json={"vb": 26, "height": 20, "width": 30, "depth": 15, "terrain_category": 3})
    print(f"POST /api/wind/ec1 → {r.status_code}: q_p = {r.json()['qp_kPa']:.4f} kPa, v_m = {r.json()['vm_ms']:.2f} m/s, "
          f"neta {r.json()['summary']['p_net_windward_minus_leeward_kPa']} kPa")
    r = c.post("/api/wind/asce7", json={"V": 115, "height_ft": 60, "width_ft": 80, "depth_ft": 160, "exposure": "B"})
    print(f"POST /api/wind/asce7 → {r.status_code}: q_h = {r.json()['qh_psf']:.2f} psf, neta {r.json()['summary']['net_psf']} psf")
    r = c.post("/api/wind/nsr10", json={"city": "Medellín", "height_m": 40, "width_m": 20, "depth_m": 30, "Iw": 1.15})
    print(f"POST /api/wind/nsr10 → {r.status_code}: V = {r.json()['V_basic_kmh']:.1f} km/h, q_z = {r.json()['qz_kPa']:.4f} kPa")
    r = c.post("/api/wind/components/cc", json={"zone": 5, "area_m2": 2.0, "qh_kPa": 1.1})
    print(f"POST /api/wind/components/cc → {r.status_code}: GCp {r.json()['GCp_positive']:.3f}/{r.json()['GCp_negative']:.3f}")
    r = c.post("/api/export", json={"target": "csv", "height_m": 9, "width_m": 20, "n_stories": 3,
                                    "pressures_per_story": [0.9, 1.0, 1.1]})
    print(f"POST /api/export (csv) → {r.status_code}:\n" + "\n".join("    " + ln for ln in r.text.splitlines()))
    r = c.post("/api/wind/openfoam-pre", json={"building_height_m": 30})
    body = r.json()
    print(f"POST /api/wind/openfoam-pre → {r.status_code}: {', '.join(k for k in body if k != 'mesh_summary')}")

    print("\nEntradas inválidas:")
    for path, payload in (("/api/wind/ec1", {"vb": 26, "height": 10, "width": 10, "depth": 10, "terrain_category": 7}),
                          ("/api/wind/asce7", {"V": 115, "height_ft": 60, "width_ft": 80, "depth_ft": 160, "exposure": "Z"}),
                          ("/api/wind/components/cc", {"zone": 9}),
                          ("/api/export", {"target": "json", "height_m": 9, "width_m": 20, "n_stories": 3}),
                          ("/api/wind/openfoam-pre", {"building_height_m": 200})):
        r = c.post(path, json=payload)
        print(f"  {path:<26} → {r.status_code}: {json.dumps(r.json()['detail'], ensure_ascii=False)[:100]}")


if __name__ == "__main__":
    main()
