# windloads

[Español](README.md) · **English**

Wind loads on buildings in Python, using EN 1991-1-4, ASCE 7 and NSR-10 B.6.

[![CI](https://github.com/jmurgass99/windloads/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/windloads/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## What it does

- EN 1991-1-4 peak velocity pressure q_p(z) by terrain category, with orography (Annex A.3), and ASCE 7 q_z.
- Pressure coefficients for walls and roofs (Tables 7.1 to 7.4) and ASCE 7 components and cladding.
- Story forces, base shear and overturning of a rectangular building, and the four ASCE 7 torsion cases.
- Davenport gust factor, vortex shedding and galloping (Annex E).
- Export to JSON, CSV, SAP2000 (.s2k), ETABS (.e2k) and DXF; calculation memos with `handcalcs`; optional REST API.

## Install

```bash
pip install git+https://github.com/jmurgass99/windloads.git
```

Optional extras: `api`, `memos`, `dxf`, `ui`. Base dependencies: `numpy` and `pydantic`.

## Example

Peak pressure at 10 m in terrain category II, with v_b = 26 m/s and ρ = 1.25 kg/m³:

```python
from windloads import TerrainProfile

profile = TerrainProfile("EC1", "II")
qp = profile.ec1_peak_velocity_pressure(10.0, 26.0, 1.25)
print(round(qp, 1))   # 993.8 Pa
```

The [`examples/`](examples) folder has 33 more scripts; most of them redo the result by hand with the formula from the code.

## What it does not do

- Non-rectangular buildings, vaulted roofs or lattice structures. The tables for complex roofs, domes and solar trackers are indicative and do not come from a verified code.
- Dynamic analysis of slender buildings: c_s·c_d is 1 by default and the Davenport factor is simplified.
- Choosing the basic wind speed for a site: the per-city tables are not cross-checked. Use the official map and pass the speed as a number.
- ASCE 7-22 to the letter: K_z uses the ASCE 7-16 constants.

Details are in [docs/LIMITACIONES.md](docs/LIMITACIONES.md) (in Spanish).

## Tests

```bash
pip install -e ".[test,api,memos,dxf]"
pytest -q
```

`tests/test_examples.py` runs every example. On Windows, if the console is not UTF-8, use `python -X utf8 examples/<name>.py`.

## License

MIT. See [LICENSE](LICENSE). Author: [Jesús Murgas](https://github.com/jmurgass99).
