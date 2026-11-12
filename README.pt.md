# windloads

[Español](README.md) · [English](README.en.md) · **Português**

Cargas de vento em edifícios com Python, segundo EN 1991-1-4, ASCE 7 e NSR-10 B.6.

[![CI](https://github.com/jmurgass99/windloads/actions/workflows/ci.yml)](https://github.com/jmurgass99/windloads/actions/workflows/ci.yml)
[![Licença: MIT](https://img.shields.io/badge/licença-MIT-green)](https://img.shields.io/badge/licença-MIT-green)

## Funcionalidades

- Pressão de velocidade de pico q_p(z) da EN 1991-1-4 por categoria de terreno, com orografia (Anexo A.3), e q_z da ASCE 7.
- Coeficientes de pressão para paredes e coberturas (Tabelas 7.1 a 7.4) e componentes e revestimentos da ASCE 7.
- Forças por pavimento, cortante basal e tombamento de edifícios retangulares, além dos quatro casos de torção da ASCE 7.
- Fator de rajada de Davenport, desprendimento de vórtices e galope (Anexo E).
- Exportação para JSON, CSV, SAP2000 (.s2k), ETABS (.e2k) e DXF; memórias de cálculo com `handcalcs`; API REST opcional.

## Instalação

```bash
pip install git+https://github.com/jmurgass99/windloads.git
```

Extras opcionais: `api`, `memos`, `dxf`, `ui`. Dependências básicas: `numpy` e `pydantic`.

## Exemplo

Pressão de pico a 10 m na categoria de terreno II, com v_b = 26 m/s e ρ = 1,25 kg/m³:

```python
from windloads import TerrainProfile

perfil = TerrainProfile("EC1", "II")
qp = perfil.ec1_peak_velocity_pressure(10.0, 26.0, 1.25)
print(round(qp, 1))   # 993.8 Pa
```

A pasta [`examples/`](examples) contém mais 33 scripts; a maioria refaz o resultado manualmente com a fórmula do código.

## O que não faz

- Edifícios não retangulares, coberturas abobadadas ou estruturas treliçadas. As tabelas para coberturas complexas, cúpulas e rastreadores solares são indicativas e não vêm de uma norma verificada.
- Análise dinâmica de edifícios esbeltos: c_s·c_d é 1 por padrão e o fator de Davenport é simplificado.
- Escolha da velocidade básica do local: as tabelas por cidade não foram verificadas. Use o mapa oficial e informe a velocidade como número.
- ASCE 7-22 em conformidade integral: K_z usa as constantes da ASCE 7-16.

Os detalhes estão em [docs/LIMITACIONES.md](docs/LIMITACIONES.md) (em espanhol).

## Testes

```bash
pip install -e ".[test,api,memos,dxf]"
pytest -q
```

`tests/test_examples.py` executa todos os exemplos. No Windows, se o console não estiver em UTF-8, use `python -X utf8 examples/<nome>.py`.

## Licença

MIT. Consulte [LICENSE](LICENSE). Autor: [Jesús Murgas](https://github.com/jmurgass99).
