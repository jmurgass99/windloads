"""FastAPI app exponiendo cálculos de viento multicode."""
from __future__ import annotations

try:
    from fastapi import APIRouter, FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import PlainTextResponse
except ImportError as exc:
    raise ImportError(
        "fastapi requerido: pip install windloads[api]"
    ) from exc

from .. import __version__ as _VERSION
from .._brand import NAME as _BRAND_NAME
from ..services import ec1, asce7, nsr10, components, export_svc


router = APIRouter()


@router.get("/")
def root():
    return {
        "name": _BRAND_NAME,
        "endpoints": [
            "/api/wind/ec1", "/api/wind/asce7", "/api/wind/nsr10",
            "/api/wind/components/cc", "/api/export",
            "/api/wind/openfoam-pre",
        ],
    }


@router.post("/api/wind/ec1", summary="Presión de viento sobre edificios y estructuras según Eurocódigo 1 (EN 1991-1-4)")
def api_ec1(inp: dict):
    try:
        result = ec1.compute_ec1(ec1.EC1Input(**inp))
        return {
            "qp_kPa": result.qp_at_height,
            "vm_ms": result.vm_at_height,
            "cp_windward": result.cp_windward,
            "cp_leeward": result.cp_leeward,
            "p_windward_kPa": result.pressure_windward,
            "p_leeward_kPa": result.pressure_leeward,
            "summary": result.summary,
        }
    except Exception as exc:
        raise HTTPException(400, str(exc))


@router.post("/api/wind/asce7", summary="Presiones de viento MWFRS y C&C según ASCE 7-16 / ASCE 7-22")
def api_asce7(inp: dict):
    try:
        result = asce7.compute_asce7(asce7.ASCE7Input(**inp))
        return {
            "qz_psf": result.qz_at_height_psf,
            "qh_psf": result.qh_psf,
            "Kz": result.Kz_at_height,
            "p_windward_psf": result.p_windward_psf,
            "p_leeward_psf": result.p_leeward_psf,
            "summary": result.summary,
        }
    except Exception as exc:
        raise HTTPException(400, str(exc))


@router.post("/api/wind/nsr10", summary="Fuerzas de viento según Reglamento Colombiano NSR-10 Título B.6")
def api_nsr10(inp: dict):
    try:
        result = nsr10.compute_nsr10(nsr10.NSR10Input(**inp))
        return {
            "V_basic_kmh": result.V_basic_kmh,
            "qz_kPa": result.qz_kPa,
            "p_net_kPa": result.p_net_kPa,
            "summary": result.summary,
        }
    except Exception as exc:
        raise HTTPException(400, str(exc))


@router.post("/api/wind/components/cc", summary="Presiones locales en componentes y cerramientos (C&C) según ASCE 7")
def api_cc(inp: dict):
    try:
        result = components.compute_cc(components.CCInput(**inp))
        return {
            "GCp_positive": result.GCp_positive,
            "GCp_negative": result.GCp_negative,
            "p_positive_kPa": result.p_positive_kPa,
            "p_negative_kPa": result.p_negative_kPa,
            "zone": result.zone,
            "notes": result.notes,
        }
    except Exception as exc:
        raise HTTPException(400, str(exc))


@router.post("/api/export", response_class=PlainTextResponse)
def api_export(inp: dict):
    try:
        result = export_svc.export_to(export_svc.ExportInput(**inp))
        return result.content
    except Exception as exc:
        raise HTTPException(400, str(exc))


@router.post("/api/wind/openfoam-pre", summary="Generación de caso de simulación CFD en OpenFOAM para túnel de viento")
def api_openfoam_pre(inp: dict):
    """Genera los diccionarios de OpenFOAM y geometría OBJ para simulación CFD."""
    from ..cfd_pre import CfdWindTunnelInput, create_cfd_openfoam_pre
    try:
        result = create_cfd_openfoam_pre(CfdWindTunnelInput(**inp))
        return {
            "blockMeshDict": result.blockMeshDict,
            "controlDict": result.controlDict,
            "snappyHexMeshDict": result.snappyHexMeshDict,
            "building_obj": result.building_obj,
            "mesh_summary": result.mesh_summary,
        }
    except Exception as exc:
        raise HTTPException(400, str(exc))


def create_router() -> APIRouter:
    """Devuelve el APIRouter (factory para uniformidad con otros repos)."""
    return router


# ---------------------------------------------------------------------------
# App standalone
# ---------------------------------------------------------------------------
app = FastAPI(title=f"{_BRAND_NAME} API", version=_VERSION)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)
app.include_router(router)
