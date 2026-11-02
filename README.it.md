# windloads — azioni del vento su edifici e strutture in Python

[Español](README.md) · [English](README.en.md) · [Português](README.pt.md) · **Italiano**

Pressione cinetica di picco della EN 1991-1-4 con categorie di terreno e orografia dell'Allegato A.3, coefficienti di pressione di pareti e coperture (Tabelle da 7.1 a 7.4) e forze di piano con altezze di riferimento e mancanza di correlazione; pressione cinetica, fattore topografico, forze del MWFRS, i quattro casi di torsione e componenti e rivestimenti della ASCE 7; NSR-10 B.6 con la procedura della ASCE 7-05; fattore di raffica di Davenport, distacco di vortici e galoppo dell'Allegato E; relazioni con handcalcs, API REST ed esportazione verso JSON, CSV, SAP2000, ETABS, modello canonico, DXF e OpenFOAM. Dipendenze: `numpy` e `pydantic`.

[![CI](https://github.com/jmurgass99/windloads/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/windloads/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Quale problema risolve

L'azione del vento su un edificio ordinario si decide con mezza dozzina di tabelle e due o tre formule, ma ogni passo nasconde una scelta che cambia il risultato del 10-50 %: quale altezza di riferimento ha ogni fascia di facciata, se la pressione interna si annulla o no, quanto vale il sottovento per un L/B che non è in tabella, se il fattore di importanza moltiplica la velocità o la pressione. `windloads` fa questi conti con la formula della norma in vista, confronta il risultato con un calcolo a mano all'interno di ogni esempio e segna come «non confrontate» le tabelle che non è stato possibile verificare con la fonte. Nella versione 1.2.0 sono stati corretti, rispetto al testo della EN 1991-1-4 e della ASCE 7, errori che spostavano il taglio alla base della EN 1991-1-4 tra −9 % e +52 %, il coefficiente di orografia sottovento a una collina (1,00 invece di 1,40), il criterio di galoppo e il fattore di importanza della NSR-10 (vedi [CHANGELOG.md](CHANGELOG.md)).

**Usalo quando**

- ti serve q_p(z) della EN 1991-1-4 per qualsiasi categoria di terreno, con c_o di collina o scarpata (Allegato A.3), o q_z della ASCE 7 con K_z e K_zt;
- vuoi le forze del vento per piano di un edificio rettangolare con EN 1991-1-4 (z_e per fasce, D ed E simultanee, fattore di mancanza di correlazione), ASCE 7 o NSR-10, il suo taglio alla base e il ribaltamento, e i quattro casi di torsione della ASCE 7;
- devi ricavare i c_pe di pareti e coperture piane, a una falda o a due falde della EN 1991-1-4, o i GCp di componenti e rivestimenti delle pareti della ASCE 7, interpolati con l'area;
- stai predimensionando un camino, un palo o un architrave nei confronti dei vortici e del galoppo (Allegato E) o il fattore di raffica di una torre flessibile;
- vuoi portare le forze in SAP2000, ETABS, un modello proprio, un disegno DXF o un caso di partenza di OpenFOAM, o esporle tramite una API REST.

**Non usarlo per**

- edifici di forma non rettangolare, coperture a volta, pensiline o strutture reticolari: le tabelle del pacchetto per coperture complesse, cupole, parapetti e inseguitori solari sono indicative e non derivano da alcuna norma verificata;
- l'analisi dinamica di edifici snelli: c_s·c_d vale 1 per impostazione predefinita (con uno stato che lo dichiara non giustificato oltre i 15 m), l'Allegato B si applica solo con `compute_cscd_annex_b=True` (procedura 1, senza smorzamento aerodinamico) e il fattore di Davenport è semplificato;
- scegliere la velocità di base di un sito: le tabelle per città (Colombia, Cile, Spagna) non sono confrontate e non coincidono tra loro; usa la mappa ufficiale e passa la velocità come numero;
- il flutter di impalcati o piastre (il modello a 2 GDL del modulo `aeroelastic` non è valido) né l'interferenza tra cilindri;
- la ASCE 7-22 alla lettera: K_z usa le costanti della ASCE 7-16 e le tabelle di copertura di componenti e rivestimenti non sono confrontate.

## Installazione

```bash
pip install git+https://github.com/jmurgass99/windloads.git
```

Extra: `api` (FastAPI, uvicorn, httpx), `memos` (handcalcs; senza di esso le relazioni restituiscono gli stessi numeri con LaTeX vuoto), `dxf` (ezdxf per il disegno dei carichi), `ui` (Streamlit), `test`. Per lo sviluppo: `git clone`, `pip install -e ".[test,api,memos,dxf]"`, `pytest -q` (39 file di test; `tests/test_examples.py` esegue i 33 esempi come sottoprocessi). Su Windows, se la console non è UTF-8, esegui gli esempi con `python -X utf8 examples/<nome>.py`. Gli esempi scrivono i loro file (JSON, CSV, .s2k, .e2k, DXF, LaTeX, Markdown, caso OpenFOAM) in `examples/out/`, che non è versionata, e l'output di console in `examples/output/`.

## Capacità

| Capacità | Moduli | Norma o riferimento | Casi d'uso |
|---|---|---|---|
| Vento di riferimento: q_p(z) per categoria di terreno, K_z e q_z della ASCE 7, coefficiente di orografia c_o dell'Allegato A.3 e K_zt della ASCE 7, velocità della NSR-10 per zona, città e coordinate, conversione a un altro periodo di ritorno, AS 1170.2, SS EN e NCh 432 | `terrain`, `topography`, `codes.nsr10_b6`, `vb_atlas`, `vb_map`, `mri_generator`, `codes_multi`, `nch432` | EN 1991-1-4 §4.2-4.5, Tabella 4.1, Allegato A.3; ASCE 7-10 Fig. 26.8-1; K_z con le costanti precedenti alla ASCE 7-22 | [6 casi](#1-vento-di-riferimento-pressione-di-picco-terreno-orografia-e-periodo-di-ritorno) |
| Coefficienti di pressione: pareti (zone A-E) e coperture piana, a una falda e a due falde della EN 1991-1-4 con interpolazione in h/d, pendenza e area; Cp delle pareti del MWFRS della ASCE 7; GCp di componenti e rivestimenti con l'area efficace e il minimo di 16 psf; cataloghi indicativi | `pressure`, `components`, `cc_pressure`, `cp_catalog`, `cp_techos_complejos`, `solar_trackers` | EN 1991-1-4 Tabelle 7.1, 7.2, 7.3a, 7.4a, 7.4b, Fig. 7.2, §7.2.9; ASCE 7-16 Fig. 27.3-1, §30.3 | [6 casi](#2-coefficienti-di-pressione-e-componenti-e-rivestimenti) |
| Forze sull'edificio: forze di piano, taglio alla base e ribaltamento con EN 1991-1-4, ASCE 7 e NSR-10, quattro casi di carico del MWFRS con torsione | `codes.ec1_1_4`, `codes.asce7_26`, `codes.nsr10_b6`, `envelope`, `mwfrs_load_cases` | EN 1991-1-4 §5.3, §7.2.2, Fig. 7.4; ASCE 7-16 Fig. 27.3-1 e Fig. 27.3-8; NSR-10 B.6 (ASCE 7-05) | [6 casi](#3-forze-sulledificio-mwfrs) |
| Dinamica e aeroelasticità: fattore di raffica di Davenport, vortici (v_crit, Sc, ampiezza E.7), galoppo (E.18-E.19), numeri di Strouhal, divergenza (E.24) | `davenport`, `vortex_shedding`, `aeroelastic` | EN 1991-1-4 Allegato E (Tabelle E.1, E.2, E.5, E.7); ASCE 7 §26.11 (forma semplificata) | [5 casi](#4-risposta-dinamica-e-aeroelasticità) |
| Relazioni, rapporti, servizi e API REST: relazioni con handcalcs, rapporto Markdown della EN 1991-1-4, livello di servizi e FastAPI | `memos`, `report_ec1`, `services`, `api` | — | [5 casi](#5-relazioni-rapporti-servizi-e-api-rest) |
| Esportazione e integrazioni: schemi per piano verso JSON, CSV, .s2k ed .e2k con ripartizione ai nodi, modello canonico, ponti verso SAP2000, disegno DXF e preprocessore di OpenFOAM | `export`, `sap_bridge`, `integration`, `cfd_pre` | — | [5 casi](#6-esportazione-e-integrazioni) |

I 33 script di `examples/` sono stati eseguiti in un ambiente pulito prima della pubblicazione; il loro output è in `examples/output/` ed è quello riprodotto qui. Quasi tutti rifanno il risultato del pacchetto a mano, con la formula della norma scritta a parte, o con un altro modulo indipendente.

## Casi d'uso

Gli output sono riportati esattamente come li stampano gli script, in spagnolo.

### 1. Vento di riferimento: pressione di picco, terreno, orografia e periodo di ritorno

#### q_p(z) nelle cinque categorie di terreno e la cascata c_r → v_m → I_v → q_p a mano a 10 m

<details><summary>Output reale di <code>python examples/ec1_peak_velocity_pressure_profile_terrain_categories_0_to_iv_and_hand_check_of_the_cascade_at_10_m.py</code></summary>

```text
v_b = 26.0 m/s, q_b = ½·ρ·v_b² = 422.5 Pa

q_p(z) [Pa] y c_e = q_p/q_b por categoría (Tabla 4.1: z0 / z_min)
   z [m]      0 (0.003)       I (0.01)      II (0.05)      III (0.3)       IV (1.0)
       2      903  2.14      793  1.88      601  1.42      541  1.28      497  1.18
       5     1100  2.60     1000  2.37      815  1.93      541  1.28      497  1.18
      10     1261  2.98     1170  2.77      994  2.35      722  1.71      497  1.18
      20     1431  3.39     1351  3.20     1187  2.81      922  2.18      695  1.64
      30     1536  3.64     1463  3.46     1307  3.09     1048  2.48      821  1.94
      50     1672  3.96     1609  3.81     1465  3.47     1215  2.88      990  2.34
     100     1866  4.42     1818  4.30     1693  4.01     1459  3.45     1240  2.93

Comprobación a mano, terreno II, z = 10 m:
  k_r = 0,19·(0,05/0,05)^0,07 = 0.1900;  c_r = k_r·ln(10/0,05) = 1.00668;  v_m = c_r·v_b = 26.174 m/s
  I_v = 1/ln(200) = 0.18874;  q_p = (1 + 7·I_v)·½·ρ·v_m² = 993.84 Pa  (TerrainProfile: 993.84 Pa, diferencia +0.0e+00 Pa);  c_e = 2.3523

A 10 m la categoría 0 da 2.54 veces la q_p de la categoría IV; de II a III la presión baja un 27 %.
Por debajo de z_min la presión es constante: categoría IV, q_p(3 m) = q_p(10 m) = 497 Pa.
No incluye el coeficiente de orografía (ver el ejemplo orography_*), ni c_dir/c_season distintos de 1, ni el anejo nacional: v_b,0 y los parámetros de la Tabla 4.1 son los recomendados.
```

</details>

#### K_z e q_z della ASCE 7 nelle esposizioni B, C e D, e cosa ha cambiato la ASCE 7-22

<details><summary>Output reale di <code>python examples/asce7_velocity_pressure_coefficient_kz_exposures_b_c_d_heights_3_to_150_m_hand_check_and_7_22_profile_note.py</code></summary>

```text
V = 50.0 m/s, K_d = 0,85, K_zt = 1;  q_z = 0,613·K_z·K_zt·K_d·V²
   z [m]   K_z B  q_z B [Pa]   K_z C  q_z C [Pa]   K_z D  q_z D [Pa]
    3.00    0.575        749    0.849       1106    1.030       1342
    4.57    0.575        749    0.849       1106    1.030       1342
    6.00    0.621        809    0.899       1171    1.080       1407
   10.00    0.719        936    1.001       1304    1.180       1538
   15.00    0.807       1051    1.090       1420    1.267       1650
   20.00    0.876       1141    1.158       1509    1.332       1735
   30.00    0.984       1281    1.261       1643    1.429       1861
   50.00    1.138       1483    1.405       1830    1.562       2034
  100.00    1.388       1808    1.625       2117    1.762       2295
  150.00    1.558       2030    1.770       2306    1.891       2463

Comprobación a mano, exposición C, z = 10 m:
  K_z = 2,01·(10/274,32)^(2/9,5) = 1.0009 (TerrainProfile 1.0009);  q_z = 0,613·1.0009·0,85·50² = 1303.8 Pa (TerrainProfile 1303.8 Pa)
  Control: K_z(33 ft = 10,06 m, C) = 1.002, el valor de referencia ≈ 1,0 de la exposición C.

A 10 m la exposición D da 1.64 veces la presión de la B. Por debajo de 4,57 m K_z es constante (B: 0.575 a 3 m y a 4,57 m).
TerrainProfile no aplica el factor de elevación K_e (solo lo acepta la memoria asce7_mwfrs): para emplazamientos altos hay que multiplicar q_z a mano.
```

</details>

#### c_o lungo una collina e una scarpata (Allegato A.3) e K_zt di cresta, scarpata e collina della ASCE 7

<details><summary>Output reale di <code>python examples/orography_factor_en1991_annex_a3_hill_and_escarpment_profiles_hand_check_and_asce7_kzt_ridge_escarpment_hill.py</code></summary>

```text
EN 1991-1-4 A.3: H = 40.0 m, L_u = L_d = 200.0 m, Φ = 0.2, L_e = 200.0 m, z = 10.0 m
   x [m]    x/L  c_o colina  c_o escarpe
    -300  -1.50      1.0075       1.0075
    -200  -1.00      1.0275       1.0275
    -100  -0.50      1.1008       1.1008
     -50  -0.25      1.1927       1.1927
       0   0.00      1.3685       1.3685
      20   0.10      1.3105       1.3424
      50   0.25      1.2401       1.2646
     100   0.50      1.1565       1.2040
     200   1.00      1.0664       1.1420
     400   2.00      1.0120       1.0785
     700   3.50      1.0000       1.0262

A mano, colina a sotavento x = 100 m (X/L_d = 0,5; z/L_e = 0,05):
  (A.12) A = 0.92125; (A.13) B = -1.71340; s = A·e^(B·0,5) = 0.39113; c_o = 1 + 2·s·0,2 = 1.15645 (función 1.15645)
A mano, escarpe a sotavento x = 50 m (X/L_e = 0,25; z/L_e = 0,05 → 0,1 en A.8-A.10):
  A = -0.0202, B = -0.5213, C = 0.3550; s = A·log²(0,25) + B·log(0,25) + C = 0.66153; c_o = 1.26461 (función 1.26461)
En la cresta c_o = 1.369: la presión pico crece del orden de c_o² = 1.87 veces (más exactamente q_p ∝ c_o·(c_o + 7·I_v), porque I_v se divide por c_o).

ASCE 7 Fig. 26.8-1, H = 30 m, L_h = 100 m, exposición C, z = 10 m:
   x [m]  cresta 2-D  escarpe 2-D  colina 3-D
    -150       1.000        1.000       1.000
    -100       1.226        1.137       1.146
     -50       1.476        1.282       1.301
       0       1.748        1.437       1.467
      50       1.476        1.378       1.301
     100       1.226        1.320       1.146
     200       1.000        1.208       1.000
     300       1.000        1.102       1.000
  A mano en la cresta 2-D: K1 = 1,45·0,3 = 0,435; K3 = e^(−3·0,1) = 0.7408; K_zt = (1 + 0,435·0.7408)² = 1.7484
  A 200 m a sotavento el escarpe conserva K_zt = 1.208 (μ = 4) mientras la cresta y la colina ya valen 1,000 (μ = 1,5).
```

</details>

#### Velocità di base della NSR-10: zone, città e coordinate, e le tre tabelle del pacchetto rispetto al massimo della regione 5

<details><summary>Output reale di <code>python examples/nsr10_basic_wind_speed_by_zone_city_and_coordinates_three_package_tables_compared_against_region_limits.py</code></summary>

```text
Regiones NSR-10 (Decreto 1711 de 2021):  B.2.3              B.2.4
  región 1: 17.0 m/s ( 60 km/h)   22.0 m/s ( 75 km/h)
  región 2: 22.0 m/s ( 80 km/h)   28.0 m/s (100 km/h)
  región 3: 28.0 m/s (100 km/h)   35.0 m/s (125 km/h)
  región 4: 33.0 m/s (120 km/h)   42.0 m/s (150 km/h)
  región 5: 36.0 m/s (130 km/h)   46.0 m/s (165 km/h)
  región 6: 44.0 m/s (160 km/h)   56.0 m/s (200 km/h)
  región 7: 49.0 m/s (175 km/h)   61.0 m/s (220 km/h)

  ciudad         nsr10_basic    zona→V  vb_atlas  vb_map  observación
  Barranquilla          45.0    5→36.0      36.0    36.0  dispersión 9 m/s; > 36 m/s (máx. región 5)
  Cartagena             45.0    5→36.0      36.0    36.0  dispersión 9 m/s; > 36 m/s (máx. región 5)
  Santa Marta           40.0    5→36.0      36.0     —    dispersión 4 m/s; > 36 m/s (máx. región 5)
  Riohacha              45.0    5→36.0      36.0     —    dispersión 9 m/s; > 36 m/s (máx. región 5)
  Monteria              30.0    4→33.0      33.0     —    dispersión 3 m/s
  Bogota                27.0    3→28.0      28.0    28.0  dispersión 1 m/s
  Medellin              27.0    3→28.0      28.0    28.0  dispersión 1 m/s
  Cali                  27.0    3→28.0      33.0    33.0  dispersión 6 m/s
  Bucaramanga           30.0    4→33.0      33.0     —    dispersión 3 m/s
  Cucuta                35.0    4→33.0      33.0     —    dispersión 2 m/s
  Villavicencio         27.0    3→28.0      28.0     —    dispersión 1 m/s
  Leticia               25.0    1→17.0      17.0     —    dispersión 8 m/s
  Tumaco                30.0    4→33.0      33.0     —    dispersión 3 m/s

13 de 13 ciudades tienen valores distintos según la tabla; 4 (barranquilla, cartagena, santa_marta, riohacha) reciben de nsr10_basic_wind_speed más de 36 m/s, por encima de la región 5. Para seguir el mapa, pasa use_regional_map_b641=True o la velocidad como número.

Clasificación por coordenadas (rectángulos aproximados de la figura, no polígonos):
  Barranquilla  ( 10.96,  -74.80) → zona 5 → 36 m/s
  Bogotá        (  4.71,  -74.07) → zona 3 → 28 m/s
  Leticia       ( -4.21,  -69.94) → zona 1 → 17 m/s
  Tumaco        (  1.80,  -78.76) → zona 4 → 33 m/s
  Yopal         (  5.34,  -72.39) → zona 3 → 28 m/s
  San Andrés    ( 12.55,  -81.70) → zona 6 → 44 m/s
  Providencia   ( 13.35,  -81.37) → zona 7 → 49 m/s
  Madrid (40,4; -3,7) → ValueError: Coordinates (40.4, -3.7) fall outside Colombia (approx. bbox lat∈[-4.5,13.5], lon∈[-82.0,-66.5]).
```

</details>

#### Un altro periodo di ritorno: c_prob della EN 1991-1-4, tabella «ASCE» e approssimazione AS 1170.2

<details><summary>Output reale di <code>python examples/mean_recurrence_interval_conversion_en1991_cprob_vs_asce_table_and_as1170_approximation_10_to_1700_years.py</code></summary>

```text
V_50 = 26.0 m/s
  T [años]  EN c_prob   V EN  ASCE f  V ASCE   AS f   V AS
        10     0.9025  23.46   0.760   19.76  0.747  19.43
        25     0.9597  24.95   0.840   21.84  0.898  23.36
        50     1.0000  26.00   0.900   23.40  1.000  26.00
       100     1.0385  27.00   0.950   24.70  1.094  28.44
       300     1.0965  28.51   1.030   26.78  1.230  31.99
       700     1.1391  29.62   1.070   27.82  1.328  34.52
      1700     1.1820  30.73   1.130   29.38  1.424  37.02

A mano, EN T = 100 años: c_prob = √[(1 − 0,2·ln(−ln 0,99))/(1 − 0,2·ln(−ln 0,98))] = 1.03848 (función 1.03848); la presión crece con c_prob² = 1.0784.
Tabla «ASCE»: factor en T = 50 años = 0.90, no 1: con V_50 = 26.0 m/s devuelve V(50) = 23.4 m/s (-10 %). Incoherente con su propia definición de entrada.
Inversa (bisección, EN): V = 28 m/s corresponde a T ≈ 206 años con V_50 = 26.0 m/s.
```

</details>

#### Stesso sito con AS 1170.2, SS EN, NCh 432 e le due vie della NSR-10

<details><summary>Output reale di <code>python examples/multi_code_velocity_pressure_as1170_ss_en_nch432_nsr10_same_site_and_unverified_coefficients.py</code></summary>

```text
Altura z = 20.0 m

AS 1170.2, V_R = 45 m/s (M_d = M_s = M_t = 1):
  TC1: M_z,cat = 1.200  V_site = 54.00 m/s  q = 1.750 kPa
  TC2: M_z,cat = 1.000  V_site = 45.00 m/s  q = 1.215 kPa
  TC3: M_z,cat = 0.890  V_site = 40.05 m/s  q = 0.962 kPa
  TC4: M_z,cat = 0.750  V_site = 33.75 m/s  q = 0.683 kPa

SS EN 1991-1-4, v_b = 26 m/s, frente a TerrainProfile (EN 1991-1-4 §4):
    I: c_e = 3.198  q_p = 1.3512 kPa   TerrainProfile 1.3512 kPa  (diferencia +2.2e-16)
   II: c_e = 2.810  q_p = 1.1872 kPa   TerrainProfile 1.1872 kPa  (diferencia +2.2e-16)
  III: c_e = 2.182  q_p = 0.9219 kPa   TerrainProfile 0.9219 kPa  (diferencia +0.0e+00)
   IV: c_e = 1.644  q_p = 0.6947 kPa   TerrainProfile 0.6947 kPa  (diferencia +1.1e-16)

NCh 432 (V_b = 32 m/s, clase II) con las constantes del módulo y K_z con α/z_g de ASCE 7-05:
  A: K_z = 0.519  q_z = 0.277 kN/m²
  B: K_z = 0.553  q_z = 0.295 kN/m²   K_z ASCE 7-05 B: 0.876 (-37 %)
  C: K_z = 0.952  q_z = 0.508 kN/m²   K_z ASCE 7-05 C: 1.158 (-18 %)
  D: K_z = 1.188  q_z = 0.634 kN/m²   K_z ASCE 7-05 D: 1.332 (-11 %)

NSR-10, V = 33 m/s, I = 1,15: evaluate_nsr10_wind (B/C/D) frente a NSR10WindLoad (categorías A-D):
  exposición D → q_z = 0.8692 kPa   NSR10WindLoad categoría A → q_z = 0.8690 kPa  (cociente 0.9997)
  exposición C → q_z = 0.7559 kPa   NSR10WindLoad categoría B → q_z = 0.7558 kPa  (cociente 0.9998)
  exposición B → q_z = 0.5721 kPa   NSR10WindLoad categoría C → q_z = 0.5717 kPa  (cociente 0.9994)
Las dos rutas NSR-10 coinciden con esa equivalencia de letras (el z_g de codes_multi está redondeado al metro); la categoría D de NSR10WindLoad (α = 5, z_g = 457 m) no tiene pareja en las exposiciones B/C/D.
```

</details>

### 2. Coefficienti di pressione e componenti e rivestimenti

#### Tabella 7.1 interpolata, fattore di mancanza di correlazione e pressioni nette del capannone W00483

<details><summary>Output reale di <code>python examples/ec1_wall_pressure_coefficients_table_7_1_zones_a_to_e_vs_h_over_d_local_cpe1_and_net_pressures_with_cpi.py</code></summary>

```text
Tabla 7.1 interpolada (c_pe,10) y factor de falta de correlación §7.2.2(3):
    h/d      A      B      C      D      E    D−E      f
   0.10  -1.20  -0.80  -0.50   0.70  -0.30   1.00  0.850
   0.25  -1.20  -0.80  -0.50   0.70  -0.30   1.00  0.850
   0.50  -1.20  -0.80  -0.50   0.73  -0.37   1.10  0.850
   1.00  -1.20  -0.80  -0.50   0.80  -0.50   1.30  0.850
   2.00  -1.20  -0.80  -0.50   0.80  -0.55   1.35  0.887
   3.00  -1.20  -0.80  -0.50   0.80  -0.60   1.40  0.925
   5.00  -1.20  -0.80  -0.50   0.80  -0.70   1.50  1.000
   8.00  -1.20  -0.80  -0.50   0.80  -0.70   1.50  1.000

Nave W00483: h = 10.0 m, d = 40.0 m, b = 40.0 m, terreno III, v_b = 27 m/s → q_p(10) = 778.75 Pa
  e = min(b, 2h) = 20 m: zona A = e/5 = 4 m, B hasta e = 20 m, C el resto (20 m)
  zona  c_pe,10  w c_pi=+0,2  w c_pi=−0,3  pésima [kPa]
     A    -1.20       -1.090       -0.701        -1.090
     B    -0.80       -0.779       -0.389        -0.779
     C    -0.50       -0.545       -0.156        -0.545
     D     0.70        0.389        0.779         0.779
     E    -0.30       -0.389        0.000        -0.389
  A mano zona A: q_p·(−1,2 − 0,2) = -1.090 kPa (fila A: -1.090). Hasta 1.2.0 la zona A usaba −1,0 y salía -0.934 kPa.

c_pe local de la zona A según el área cargada (Figura 7.2):
  A =  0.5 m²: c_pe = -1.400
  A =  1.0 m²: c_pe = -1.400
  A =  2.0 m²: c_pe = -1.340
  A =  5.0 m²: c_pe = -1.260
  A = 10.0 m²: c_pe = -1.200
  A = 20.0 m²: c_pe = -1.200
Para elementos de más de 10 m² vale c_pe,10; por debajo de 1 m², c_pe,1. Los muros con abertura dominante (c_pi = 0,75 o 0,90·c_pe de esa cara, §7.2.9(3)) no están implementados: EC1WindLoad los rechaza.
```

</details>

#### Coperture piana, a una falda e a due falde: Tabelle 7.2, 7.3a, 7.4a e 7.4b con interpolazione in pendenza e area

<details><summary>Output reale di <code>python examples/ec1_roof_cpe_tables_7_2_flat_7_3a_monopitch_7_4_duopitch_pitch_and_area_interpolation_hand_check.py</code></summary>

```text
Cubierta plana con aleros vivos (Tabla 7.2): c_pe,1 / c_pe,10
  F      A = 1 m²: -2.50   A = 10 m²: -1.80
  G      A = 1 m²: -2.00   A = 10 m²: -1.20
  H      A = 1 m²: -1.20   A = 10 m²: -0.70
  I_neg  A = 1 m²: -0.20   A = 10 m²: -0.20
  I_pos  A = 1 m²:  0.20   A = 10 m²:  0.20

A un agua, Tabla 7.3a, c_pe,10 (A = 10 m²): θ = 0° succión / presión y θ = 180°
     α   F: 0°− 0°+ 180°   G: 0°− 0°+ 180°   H: 0°− 0°+ 180°
     5   -1.7  0.0  -2.3   -1.2  0.0  -1.3   -0.6  0.0  -0.8
    15   -0.9  0.2  -2.5   -0.8  0.2  -1.3   -0.3  0.2  -0.9
    30   -0.5  0.7  -1.1   -0.5  0.7  -0.8   -0.2  0.4  -0.8
    45    0.0  0.7  -0.6    0.0  0.7  -0.5    0.0  0.6  -0.7
    60    0.7  0.7  -0.5    0.7  0.7  -0.5    0.7  0.7  -0.5
    75    0.8  0.8  -0.5    0.8  0.8  -0.5    0.8  0.8  -0.5

A dos aguas, Tabla 7.4a (θ = 0°, succión) y 7.4b (θ = 90°), c_pe,10:
     α      F     G     H     I     J   |  F90   G90   H90   I90
     5   -1.7  -1.2  -0.6  -0.6  -0.6   |  -1.6  -1.3  -0.7  -0.6
    15   -0.9  -0.8  -0.3  -0.4  -1.0   |  -1.3  -1.3  -0.6  -0.5
    30   -0.5  -0.5  -0.2  -0.4  -0.5   |  -1.1  -1.4  -0.8  -0.5
    45    0.0   0.0   0.0  -0.2  -0.3   |  -1.1  -1.4  -0.9  -0.5
    60    0.7   0.7   0.7  -0.2  -0.3   |  -1.1  -1.2  -0.8  -0.5
    75    0.8   0.8   0.8  -0.2  -0.3   |  -1.1  -1.2  -0.8  -0.5

A mano, dos aguas α = 22.5°, zona F θ = 0°: −0,9 + (22,5−15)/15·(−0,5+0,9) = -0.700 (función -0.700)
A mano, un agua α = 15°, θ = 180°, zona F, A = 3.0 m²: c_pe = −2,8 − (−2,8 + 2,5)·log10(3) = -2.6569 (función -2.6569)
En la cubierta a un agua de 15° la succión local pésima de la zona F es -2.8 con θ=180°: la dirección de viento importa y hay que comprobar ambas.
```

</details>

#### Cp sottovento della ASCE 7 interpolato con L/B e pressioni di parete con involucro chiuso e parzialmente chiuso

<details><summary>Output reale di <code>python examples/asce7_mwfrs_wall_cp_leeward_interpolation_with_l_over_b_and_net_pressures_enclosed_vs_partially_enclosed.py</code></summary>

```text
Cp de sotavento frente a L/B:
    L/B   1.2.0  regla anterior  diferencia neta (0,8 − Cp)
    0.5  -0.500           -0.50                       +0.0 %
    1.0  -0.500           -0.50                       +0.0 %
    1.2  -0.460           -0.30                      +14.5 %
    1.5  -0.400           -0.30                       +9.1 %
    2.0  -0.300           -0.30                       +0.0 %
    2.5  -0.275           -0.20                       +7.5 %
    3.0  -0.250           -0.20                       +5.0 %
    4.0  -0.200           -0.20                       +0.0 %
    6.0  -0.200           -0.20                       +0.0 %

Presiones de muro con q = 1200 Pa, G = 0,85, L/B = 1,5:
  enclosed            barlovento +0.600/+1.032 kPa, sotavento -0.624/-0.192 kPa, lateral -0.930/-0.498 kPa
                      neta barlovento − sotavento: 1.224 (+GCpi) y 1.224 kPa (−GCpi) = q·G·(0,8 + 0,4)/1000 = 1.224 kPa
  partially_enclosed  barlovento +0.156/+1.476 kPa, sotavento -1.068/+0.252 kPa, lateral -1.374/-0.054 kPa
                      neta barlovento − sotavento: 1.224 (+GCpi) y 1.224 kPa (−GCpi) = q·G·(0,8 + 0,4)/1000 = 1.224 kPa
La clasificación de cerramiento cambia la presión de cada muro (lo que dimensiona fachada y correas) pero no el cortante total del edificio.
```

</details>

#### GCp di componenti e rivestimenti della ASCE 7 rispetto all'area efficace e al minimo di 16 psf

<details><summary>Output reale di <code>python examples/asce7_components_and_cladding_gcp_walls_zones_4_5_roof_zones_1_2_3_effective_area_and_16_psf_minimum.py</code></summary>

```text
q_h = 1056.1 Pa; franja de esquina a = max(min(0,1·B, 0,4·h), max(0,04·B, 0,9 m)) = 3.00 m
   A [m²]  GCp4+  GCp4−          p4 [Pa]  GCp5−  p5− [Pa]  GCp1−  GCp3−  p3− [Pa]
    0.500   1.00  -1.10    1246/  -1352   -1.40     -1669  -1.70  -3.20     -3570
    0.929   1.00  -1.10    1246/  -1352   -1.40     -1669  -1.70  -3.20     -3570
    2.000   0.94  -1.04    1184/  -1290   -1.28     -1544  -1.58  -3.02     -3383
    5.000   0.87  -0.97    1110/  -1216   -1.14     -1396  -1.44  -2.81     -3161
   10.000   0.82  -0.92    1054/  -1159   -1.04     -1284  -1.34  -2.65     -2992
   20.000   0.77  -0.86     998/  -1103   -0.93     -1172  -1.23  -2.49     -2824
   46.450   0.70  -0.80     929/  -1035   -0.80     -1035  -1.10  -2.30     -2619
  100.000   0.70  -0.80     929/  -1035   -0.80     -1035  -1.10  -2.30     -2619

A mano, zona 5, A = 5 m²: fracción log = 0.4302; GCp = −1,4 + 0.4302·0,6 = -1.1419 (función -1.1419); p = q_h·(GCp − 0,18) = -1396 Pa
Mínimo de 16 psf: con q_h = 600 Pa la zona 4 a 50 m² daría 600·(0,7 + 0,18) = 528 Pa → se eleva a 766 Pa.
cc_pressure.get_cc_pressure (calcula q_h por su cuenta): (1109.9, -1396.0) Pa frente a (1109.9, -1396.0) Pa de components: iguales.
Las presiones de cubierta usan la tabla θ ≤ 7° del paquete sin contrastar; las de muro, la Fig. 30.3-1. Para edificios de h > 60 ft (18,3 m) el paquete no tiene tablas de C&C.
```

</details>

#### Rapporto di componenti e rivestimenti di un capannone con EN 1991-1-4 e ASCE 7

<details><summary>Output reale di <code>python examples/components_and_cladding_report_warehouse_ec1_vs_asce7_both_internal_pressure_signs_and_unverified_sloped_roof_parapet_tables.py</code></summary>

```text
EN 1991-1-4: q_p(8 m) = 935 Pa; franja e/10 = 1.60 m
   zona A [m²]   c_pe  w c_pi=+0,2  w c_pi=−0,3   pésima
      A      1  -1.40        -1496        -1028    -1496
      B      1  -1.10        -1215         -748    -1215
      D      1   1.00          748         1215     1215
      E      1  -0.50         -654         -187     -654
      A     10  -1.20        -1309         -841    -1309
      B     10  -0.80         -935         -467     -935
      D     10   0.80          561         1028     1028
      E     10  -0.50         -654         -187     -654
      F      1  -2.50        -2524        -2056    -2524
      G      1  -2.00        -2056        -1589    -2056
      H      1  -1.20        -1309         -841    -1309
  I_neg      1  -0.20         -374           94     -374
      F     10  -1.80        -1869        -1402    -1869
      G     10  -1.20        -1309         -841    -1309
      H     10  -0.70         -841         -374     -841
  I_neg     10  -0.20         -374           94     -374
  Zona D a 1 m²: con c_pi = −0,3 la presión es 1.62 veces la del informe por defecto (c_pi = +0,2).

ASCE 7: q_h(8 m) = 1008 Pa; franja a = 3.0 m
  zona 4 (wall) A =    1 m²: GCp +0.99/-1.09 → p =  +1183 /  -1284 Pa
  zona 5 (wall) A =    1 m²: GCp +0.99/-1.39 → p =  +1183 /  -1581 Pa
  zona 4 (wall) A =   10 m²: GCp +0.82/-0.92 → p =  +1005 /  -1106 Pa
  zona 5 (wall) A =   10 m²: GCp +0.82/-1.04 → p =  +1005 /  -1225 Pa
  zona 1 (roof) A =    1 m²: GCp +0.30/-1.69 → p =   +766 /  -1883 Pa
  zona 2 (roof) A =    1 m²: GCp +0.30/-2.29 → p =   +766 /  -2486 Pa
  zona 3 (roof) A =    1 m²: GCp +0.30/-3.18 → p =   +766 /  -3389 Pa
  zona 1 (roof) A =   10 m²: GCp +0.24/-1.34 → p =   +766 /  -1527 Pa
  zona 2 (roof) A =   10 m²: GCp +0.24/-1.88 → p =   +766 /  -2070 Pa
  zona 3 (roof) A =   10 m²: GCp +0.24/-2.65 → p =   +766 /  -2855 Pa

Estimaciones con tablas sin contrastar (ASCE 7, A = 1 m²):
  dos aguas 20°: 1 -1383, 2e -2185, 2n -1984, 2r -2385, 3 -2988 Pa
  cúpula f/D = 0,2: A -766, B -1007, C -766 Pa
  antepecho h_p = 1 m: K_p = 1.5 (aproximación propia), GCp −1,10 → -1.65
```

</details>

#### Catalogo di Cp, coperture complesse e inseguitori solari: cosa hanno di indicativo

<details><summary>Output reale di <code>python examples/indicative_cp_catalog_complex_roofs_and_solar_tracker_loads_declared_non_normative_with_missing_kz_check.py</code></summary>

```text
Catálogo: 13 entradas, geometrías box_LB1, box_LB4, cylinder, flat_roof, gable_20deg, open_truss
  box_LB1   ASCE7   barlovento +0.80  sotavento -0.50  lateral -0.70  L/B=1.0
  box_LB1   EN1991  barlovento +0.80  sotavento -0.50  lateral -0.80  
  box_LB1   AS1170  barlovento +0.70  sotavento -0.50  lateral -0.65  
  box_LB4   ASCE7   barlovento +0.80  sotavento -0.20  lateral -0.70  
  box_LB4   EN1991  barlovento +0.80  sotavento -0.30  lateral -0.80  
  cylinder  ASCE7   barlovento +0.80  sotavento -0.50  lateral -0.70  Re > 4e5
  cylinder  EN1991  barlovento +1.00  sotavento -0.40  lateral -0.70  

Techos complejos (el código no altera el resultado):
  arco f/h = 0,2 [EU]: {'barlovento': 0.2, 'cumbrera': -0.8, 'sotavento': -0.4}
  arco f/h = 0,2 [US]: {'barlovento': 0.2, 'cumbrera': -0.8, 'sotavento': -0.4}
  diente de sierra: {'primera_pendiente': 0.3, 'primera_vertical': -1.0, 'intermedia_pendiente': -0.4, 'intermedia_vertical': -0.7, 'ultima_pendiente': -0.6}

Seguidor solar (cuerda 2 m), V = 35 m/s:
  inclinación    0°, altura 2 m: q_z =    638 Pa, sustentación  1.91 kN/m, momento  0.00 kN·m/m (stow_lift_max)
  inclinación    0°, altura 5 m: q_z =    638 Pa, sustentación  1.91 kN/m, momento  0.00 kN·m/m (stow_lift_max)
  inclinación   30°, altura 2 m: q_z =    638 Pa, sustentación  1.44 kN/m, momento  1.11 kN·m/m (operating_torsion_max)
  inclinación   30°, altura 5 m: q_z =    638 Pa, sustentación  1.44 kN/m, momento  1.11 kN·m/m (operating_torsion_max)
  inclinación   60°, altura 2 m: q_z =    638 Pa, sustentación  0.48 kN/m, momento  1.11 kN·m/m (operating_torsion_max)
  inclinación   60°, altura 5 m: q_z =    638 Pa, sustentación  0.48 kN/m, momento  1.11 kN·m/m (operating_torsion_max)
La altura no cambia q_z: falta K_z. En exposición C, K_z(2 m) = 0.849, así que la función sobrestima q_z un 18 % a ras de suelo; en exposición B (0.575) un 74 %. Usa coeficientes de ensayo del fabricante para dimensionar un seguidor.
```

</details>

### 3. Forze sull'edificio (MWFRS)

#### Edificio basso con EN 1991-1-4: z_e = h, mancanza di correlazione e confronto con la regola precedente alla 1.2.0

<details><summary>Output reale di <code>python examples/ec1_mwfrs_low_rise_story_forces_reference_height_and_lack_of_correlation_hand_check_vs_previous_rule.py</code></summary>

```text
Edificio b × d × h = 20 × 12 × 12 m, terreno II, v_b = 26.0 m/s; c_s·c_d = 1.0 (justified_low_rise_h_le_15m (EN 1991-1-4 §6.2(1) Nota 1a))
q_p(12 m) a mano = 1043.28 Pa (paquete 1043.28 Pa)
  planta  z_top   z_e   F [kN]   a mano  regla anterior
       1    3.0  12.0    69.17    69.17           45.73
       2    6.0  12.0    69.17    69.17           56.81
       3    9.0  12.0    69.17    69.17           63.74
       4   12.0  12.0    69.17    69.17           68.86
Cortante basal: 276.68 kN (a mano 0,85·1,3·q_p(12)·20·12 = 276.68 kN); regla anterior 235.13 kN (-15.0 %).
Momento de vuelco en la base: 1660.1 kN·m (fuerzas en el centro de cada planta).
Con z_e = h la presión de barlovento es uniforme; la regla anterior la reducía en las plantas bajas (q_p(3 m) < q_p(12 m)), del lado inseguro en edificios anchos y bajos.
```

</details>

#### Torre di 60 m: altezze di riferimento per fasce, ribaltamento e stato di c_s·c_d

<details><summary>Output reale di <code>python examples/ec1_mwfrs_tall_building_60_m_reference_height_strips_figure_7_4_story_forces_overturning_and_cscd_status.py</code></summary>

```text
h = 60 m, b = 20 m, d = 30 m (h/d = 2.0): c_pe,E = -0.550, f = 0.8875, q_p(h) = 1377 Pa
  planta  z_top   z_e  q_p(z_e)   F [kN]
       1      3    20       994    82.69
       3      9    20       994    82.69
       6     18    20       994    82.69
       7     21    21      1010    83.37
       8     24    24      1054    85.25
      10     30    30      1130    88.46
      13     39    39      1221    92.35
      14     42    60      1377    99.01
      20     60    60      1377    99.01
Cortante basal 1806.6 kN (suma independiente 1806.6 kN); vuelco 56492 kN·m (independiente 56494 kN·m); brazo equivalente 31.3 m.
Con q_p(h) en toda la altura (simplificación habitual) saldría 1980 kN, +10 % sobre el reparto por franjas.
c_s·c_d = 1.0 → estado: unverified_default_h_gt_15m (requiere cálculo dinámico §6.3 o Anexo B/C) (justificado: False).
Con compute_cscd_annex_b=True: c_s·c_d = 0.9464 (computed_en1991_1_4_annex_b); z_s = 36 m, n_1 = 0.767 Hz, L(z_s) = 105 m, B² = 0.569, R² = 0.254, k_p = 3.51
  Ec. (6.1) a mano con I_v(z_s) = 0.2089: 0.9464; cortante basal 1709.8 kN (0.9464 veces el de c_s·c_d = 1).
```

</details>

#### ASCE 7 direzionale: forze di piano in B, C e D e il piano superiore a mano

<details><summary>Output reale di <code>python examples/asce7_mwfrs_directional_story_forces_exposures_b_c_d_and_hand_check_of_the_top_story_force.py</code></summary>

```text
h = 35.0 m, B = 30.0 m, L = 45.0 m (L/B = 1.5), V = 50.0 m/s, K_d = 0,85, G = 0,85
  exp.  q_h [Pa]  V_b [kN]  OTM [kN·m]   Cp_l
     B      1339      1259       23357  -0.40
     C      1697      1647       30136  -0.40
     D      1912      1885       34253  -0.40

A mano, exposición C, planta 10 (z = 35 m = h): q_z = q_h = 1697.3 Pa;
  p = q_z·0,85·0,8 + q_h·0,85·0,4 = 1731.3 Pa; F = p·B·3,5 = 181.78 kN (paquete 181.78 kN)
  Planta 1 (z = 3,5 m → K_z con 4,57 m): F = 139.54 kN; el sotavento a q_h pesa 43 % de esa presión.
La exposición D da 1.50 veces el cortante de la B en este edificio.
Solo muros de barlovento y sotavento: la cubierta, el caso de torsión (Fig. 27.3-8, ver el ejemplo de los cuatro casos) y el factor de ráfaga flexible (Davenport) van aparte.
```

</details>

#### I quattro casi di carico della Fig. 27.3-8 con eccentricità del 15 %

<details><summary>Output reale di <code>python examples/asce7_four_mwfrs_load_cases_figure_27_3_8_torsion_with_15_percent_eccentricity_and_envelope.py</code></summary>

```text
P_x = 1098 kN (B_x = 20 m, L/B = 1.50),  P_y = 1798 kN (B_y = 30 m, L/B = 0.67)
   caso  P_x [kN]  P_y [kN]  M_T [kN·m]
    1-X      1098         0           0
    1-Y         0      1798           0
    2-X       823         0        2470
    2-Y         0      1349        6068
      3       823      1349           0
      4       618      1012        6409

A mano: caso 2-X M_T = 0,75·1098·0,15·20 = 2470 kN·m; caso 4 M_T = 0,563·(1098·3.0 + 1798·4.5) = 6409 kN·m
Envolvente: P_x máx = 1098 kN, P_y máx = 1798 kN, M_T máx = 6409 kN·m (caso 4).
La envolvente de máximos por separado no es una combinación: cada caso se analiza con su P_x, P_y y M_T simultáneos y con los dos signos de la excentricidad.
```

</details>

#### NSR-10 a Barranquilla e Bogotá: fattore di importanza su q_z e lettere del terreno

<details><summary>Output reale di <code>python examples/nsr10_mwfrs_barranquilla_vs_bogota_importance_factor_on_qz_and_terrain_category_letters.py</code></summary>

```text
h = 24.0 m, B = 20.0 m, L = 30.0 m
  caso                                        V [m/s]  q_h [Pa]  V_b [kN]  OTM [kN·m]
  barranquilla terreno A (tabla de ciudad)       45.0      1450       658        8165
  barranquilla terreno A (zona)                  36.0       928       421        5226
  barranquilla terreno B (tabla de ciudad)       45.0      1270       567        7088
  barranquilla terreno B (zona)                  36.0       813       363        4537
  bogota terreno C (tabla de ciudad)             27.0       351       152        1924
  bogota terreno C (zona)                        28.0       377       164        2069
En Barranquilla la tabla de ciudad (45 m/s) da 1.56 veces el cortante de la región 5 (36 m/s).

Factor de importancia con V = 27 m/s: q_h(I = 1,15)/q_h(I = 1) = 1.1500, q_h(0,87)/q_h(1) = 0.8700; V_b 204 → 235 kN.
  Vb_design = √I·V = 28.954 m/s es una velocidad equivalente para reproducir q_z·I, no una velocidad de la norma; con la regla anterior (I·V) la relación habría sido 1,3225.
Categorías extremas con V = 30 m/s: A (costa) q_h = 645 Pa, D (α = 5) q_h = 290 Pa (2.22 veces).
```

</details>

#### Lo stesso edificio di 30 × 20 × 40 m con le tre norme

<details><summary>Output reale di <code>python examples/three_codes_same_building_30x20x40_m_base_shear_overturning_moment_and_story_forces_en1991_asce7_nsr10.py</code></summary>

```text
Edificio 30 × 20 m, H = 40 m, 14 niveles de carga

  norma                                    q(H) [Pa]  V_b [kN]  OTM [kN·m] brazo [m]
  EN 1991-1-4 (v_b = 26 m/s, terreno II)        1395      1950       39276      20.1
  ASCE 7 (V = 40 m/s, exposición C)             1117      1347       28115      20.9
  NSR-10 B.6 (V = 36 m/s, categoría B)           905      1091       22773      20.9

El mayor cortante (EN 1991-1-4) es 1.79 veces el menor (NSR-10 B.6).

Fuerzas por planta [kN] (cuatro niveles superiores, de abajo arriba):
  EN 1991-1-4 (v_b = 26 m/s, terreno II)   150.4, 150.4, 150.4, 50.1
  ASCE 7 (V = 40 m/s, exposición C)        108.4, 109.6, 110.8, 37.0
  NSR-10 B.6 (V = 36 m/s, categoría B)     87.8, 88.8, 89.7, 30.0

EN 1991-1-4: c_s·c_d = 1.0 con estado «unverified_default_h_gt_15m (requiere cálculo dinámico §6.3 o Anexo B/C)»: con 40 m hay que justificarlo (§6.3); ASCE 7 y NSR-10 usan G = 0,85 de edificio rígido sin comprobar la frecuencia.
```

</details>

### 4. Risposta dinamica e aeroelasticità

#### Fattore di raffica di una torre flessibile per periodi da 1 a 6 s e cosa semplifica il modulo

<details><summary>Output reale di <code>python examples/davenport_gust_factor_flexible_tower_periods_1_to_6_s_damping_background_resonant_and_declared_simplifications.py</code></summary>

```text
h = 150.0 m, I_z = 0.2, L_z = 180.0 m, V_z = 40.0 m/s
  T [s]  n1 [Hz]      Q  R β=1%  G_f 1%  R β=2%  G_f 2%
    1.0    1.000  0.731   0.553   0.925   0.391   0.863
    2.0    0.500  0.731   0.953   1.095   0.674   0.966
    3.0    0.333  0.731   1.293   1.252   0.914   1.065
    4.0    0.250  0.731   1.590   1.392   1.125   1.157
    5.0    0.200  0.731   1.853   1.515   1.310   1.239
    6.0    0.167  0.731   2.087   1.624   1.476   1.312
El amortiguamiento del 2 % reduce G_f a T = 6 s de 1.624 a 1.312 (-19.2 %); a T = 1 s la parte resonante pesa menos (-6.6 %).

Término omitido, T = 4.0 s, planta 30 × 30 m: R_B = 0.607, R_L = 0.287, √(R_B·(0,53 + 0,47·R_L)) = 0.635: el R del módulo es 1.57 veces el de la forma completa.
Q con (B + h) = 180 m sería 0.783 frente a 0.731 con (h + h): con B < h la parte de fondo queda del lado inseguro (-6.6 %).
Es un cálculo de predimensionamiento: R del lado seguro, Q del lado inseguro si B < h. Para un edificio esbelto real hay que evaluar I_z, L_z y V_z con la tabla de la norma y usar la forma completa o un ensayo en túnel.
```

</details>

#### Camino in acciaio: v_crit, Scruton, c_lat secondo Reynolds, K_w iterato e ampiezza (E.7)

<details><summary>Output reale di <code>python examples/vortex_shedding_steel_chimney_en1991_annex_e_critical_velocity_scruton_kw_clat_by_reynolds_and_amplitude_e7.py</code></summary>

```text
v_crit = b·n/St = 1.0·1.2/0.18 = 6.67 m/s; v_m(30 m) = 31.6 m/s; 1,25·v_m = 39.5 m/s
  → hay que estudiarlo (E.1: v_crit > 1,25·v_m lo exime)
Re = 4.44e+05 → c_lat,0 = 0.315 (zona de transición de la Figura E.2; el valor fijo del paquete es 0,2)
Sc = 2·0.012·250.0/(1,25·1²) = 4.80;  K_w = 3·(6/30)·[1 − 6/30 + (6/30)²/3] = 0.4880 (≤ 0,6)
y_F,max = b·(1/St²)(1/Sc)·K·K_w·c_lat = 128.6 mm (paquete 128.6 mm), y/b = 0.1286
  Hipótesis L_j = 6·b válida si y/b < 0,1 (Tabla E.4): NO, hay que iterar.
  Iteración con L_j/b = 4,8 + 12·y/b (Tabla E.4): converge en 5 pasos a L_j/b = 6.428, K_w = 0.5149, y_F,max = 135.7 mm.
Con los valores por defecto (K_w = 0,6, c_lat = 0,2): y = 100.3 mm, -26 % respecto al cálculo con c_lat por Reynolds.
Fuerza de inercia en la punta (E.6, Φ = 1): F_w = m·(2πn)²·y = 1929 N/m.
Rango de enganche del paquete: 4.67-8.67 m/s (±30 % con Sc < 5; criterio propio, no de la norma).
```

</details>

#### Galoppo delle sezioni della Tabella E.7 e il criterio v_CG > 1,25·v_m

<details><summary>Output reale di <code>python examples/galloping_onset_velocity_rectangular_and_iced_sections_table_e7_and_criterion_e19_1_25_vm.py</code></summary>

```text
b = 0.5 m, n₁ = 2.0 Hz, m = 150.0 kg/m, δ_s = 0.015 → Sc = 2·0.015·150.0/(1,25·0.5²) = 14.40; v_m = 22.0 m/s
  sección (Tabla E.7)        a_G  v_CG [m/s]  v_CG/(1,25·v_m)  riesgo
  rectángulo d/b = 1/2       0.7       41.14            1.496      no
  hielo sobre cable          1.0       28.80            1.047      no
  cuadrado d/b = 1           1.2       24.00            0.873      sí
  rectángulo d/b = 1,5       1.7       16.94            0.616      sí
  rectángulo d/b = 2         2.0       14.40            0.524      sí
  desconocida (a_G = 10)    10.0        2.88            0.105      sí
Secciones que no cumplen (E.19): cuadrado d/b = 1, rectángulo d/b = 1,5, rectángulo d/b = 2, desconocida (a_G = 10).
Para el rectángulo d/b = 2 haría falta m ≥ 1,25·v_m·a_G·ρ·b²/(4·δ_s·n₁·b) = 286 kg/m (o el amortiguamiento equivalente) para cumplir.
Interacción con torbellinos (E.20): cuadrado, v_crit = 8.33 m/s (St = 0,12), v_CG/v_crit = 2.88 → fuera del intervalo 0,7-1,5.
```

</details>

#### Modulo `aeroelastic`: la trappola del segno di Den Hartog, aggancio e interferenza

<details><summary>Output reale di <code>python examples/aeroelastic_module_den_hartog_sign_convention_vs_en1991_ag_lock_in_range_and_wake_interference_factor.py</code></summary>

```text
Cuadrado, a_G = 1,2 (Tabla E.7), m = 150 kg/m, n = 2 Hz, b = 0,5 m, δ = 0,015:
  vortex_shedding.check_galloping(aG=1.2)             v_CG = 24.00 m/s
  aeroelastic.galloping_critical_velocity(+1.2)       v = inf (lo trata como estable)
  aeroelastic.galloping_critical_velocity(H = −1.2)   v = 24.00 m/s
  Con el signo de Den Hartog ambas funciones coinciden; con el a_G tal cual la función de aeroelastic concluye lo contrario.

Rango de enganche (banda ±20 %, criterio del módulo): 5.33-8.00 m/s; U = 6,5 m/s dentro: True.

Dos chimeneas de b = 1 m, n = 1,2 Hz, m = 250 kg/m, δ = 0,012 (Sc con E.4):
    a/b  factor módulo  crítico  v_CIG (E.23) [m/s]
    1.5          1.500     True                6.51
    2.0          1.500     True                7.51
    2.5          1.500     True                8.40
    3.0          1.500    False         — (a/b ≥ 3)
    5.0          1.441    False         — (a/b ≥ 3)
   10.0          1.294    False         — (a/b ≥ 3)
   20.0          1.000    False         — (a/b ≥ 3)
El factor del módulo no es una magnitud de la norma: úsalo solo como alerta. Con a/b < 3 la referencia de EN 1991-1-4 es la velocidad crítica v_CIG de E.3, que el paquete no calcula.
```

</details>

#### Numeri di Strouhal rispetto alla Tabella E.1, vecchia API dei vortici e divergenza (E.24)

<details><summary>Output reale di <code>python examples/strouhal_numbers_by_section_vs_en1991_table_e1_legacy_vortex_api_and_divergence_velocity_e24.py</code></summary>

```text
b = 0.6 m, n = 1.5 Hz
  sección               paquete  EN Tabla E.1  v_crit [m/s]
  circular                 0.18          0.18          5.00
  square                   0.12          0.12          7.50
  rectangular              0.12             —          7.50
  hexagonal                0.14             —          6.43
  octagonal                0.15             —          6.00
  H_section                0.10          0.11          9.00
  L_section                0.15             —          6.00
  API antigua ST_TABLE: circular 0.18, square_sharp 0.12, rectangular_2_1 0.06, octagonal 0.18
  EN rectángulo d/b = 2: St = 0,06 → v_crit = 15.00 m/s (la mitad de St, el doble de v_crit)

API antigua frente al criterio E.1.2(2), v_m = 20 m/s:
  n = 1.5 Hz: v_crit =   5.00 m/s, «en banda» = False, E.1.2(2) obliga a estudiarlo = True, galope (a_G fijo) = True
  n = 4.0 Hz: v_crit =  13.33 m/s, «en banda» = True , E.1.2(2) obliga a estudiarlo = True, galope (a_G fijo) = True
  n = 8.0 Hz: v_crit =  26.67 m/s, «en banda» = False, E.1.2(2) obliga a estudiarlo = False, galope (a_G fijo) = False

Divergencia (E.24): k_Θ = 40000 N·m/rad por metro, d = 3.0 m, dc_M/dΘ = 1.0 (dato supuesto):
  v_div = √(2·k_Θ/(ρ·d²·dc_M/dΘ)) = 84.33 m/s (función 84.33 m/s). E.4.2 exige además b/d < 0,25 y frecuencias de torsión bajas para que el panel sea propenso; si lo es, hay que consultar a un especialista.
```

</details>

### 5. Relazioni, rapporti, servizi e API REST

#### Relazione del MWFRS della ASCE 7 con handcalcs, a mano e senza handcalcs

<details><summary>Output reale di <code>python examples/memo_asce7_mwfrs_handcalcs_latex_numbers_hand_check_and_fallback_without_handcalcs.py</code></summary>

```text
handcalcs disponible: True; LaTeX de 999 caracteres
  K_z(z=12.0m, exp=C) = 1.040
  q_z = 1147 N/m2 (1.147 kN/m2)
  Cp barlovento = 0.80, Cp sotavento = -0.30
  GCpi = +/-0.18
  p_diseno (combo critico) = 0.986 kN/m2
A mano: K_z = 1.0401, q_z = 1.1468 kN/m², p_diseño = q·(0,85·0,8 + 0,18) = 0.9862 kN/m² (memoria 0.9862)
LaTeX guardado en memoria_asce7_mwfrs.tex (17 líneas); primera ecuación: q_{z} &= 0.613 \cdot K_{z} \cdot K_{zt} \cdot K_{d} \cdot K_{e} \cdot \frac{ \le

Sin handcalcs: _HAS_HANDCALCS = False, LaTeX vacío = True, p_diseño = 0.9862 kN/m² (igual)
```

</details>

#### Relazioni di pressione di picco e di fattore di raffica rispetto ai motori del pacchetto

<details><summary>Output reale di <code>python examples/memo_ec1_peak_pressure_and_davenport_gust_factor_handcalcs_equal_to_the_canonical_engines.py</code></summary>

```text
q_b = ½·1,25·27² = 455.62 Pa
  z =   10 m: c_e = 1.7092, memoria q_p =   778.75 Pa, TerrainProfile   778.75 Pa, LaTeX 238 caracteres
  z =   20 m: c_e = 2.1821, memoria q_p =   994.22 Pa, TerrainProfile   994.22 Pa, LaTeX 238 caracteres
  z =   40 m: c_e = 2.6996, memoria q_p =  1230.00 Pa, TerrainProfile  1230.00 Pa, LaTeX 239 caracteres
  La memoria no calcula c_e: hay que dárselo (Figura 4.2 o TerrainProfile).

Factor de ráfaga: memoria G_f = 1.25466, motor 1.25466 (coinciden); Q = 0.7489, R = 1.2754
  f_1 = 1/T = 0.2857 Hz
  Q (fondo) = 0.7489, R (resonante) = 1.2754
  g_R = 3.8795 (g_Q = g_v = 3.4)
  G_f = 1.2547
```

</details>

#### Rapporto Markdown della EN 1991-1-4 su terreno pianeggiante e sulla cresta di un rilievo

<details><summary>Output reale di <code>python examples/report_ec1_markdown_with_orography_factor_from_annex_a3_and_zmin_of_the_terrain_category.py</code></summary>

```text
# Reporte EC1 - Acciones de Viento (EN 1991-1-4)

## 1. Velocidad basica
- v_b,0 = 26.0 m/s
- v_b = c_dir * c_season * v_b,0 = 26.0 m/s

## 2. Categoria de terreno y orografia
- Categoria 2, z0 = 0.05 m, z_min = 2.0 m
- c_o = 1.000 (LIMITACIÓN: Terreno plano sin efecto orográfico según EN 1991-1-4 §4.3.3. En colinas/acantilados usar windloads.topography.ec1_orography_factor_A3)

## 3. Velocidad media a z=H
- k_r = 0.1900
- c_r(z) = 0.9389
- v_m(z) = 24.41 m/s

## 4. Presion de calculo de la velocidad punta
- q_p(z) = 900.06 Pa = 0.900 kPa

## 5. Coeficientes de presion externa (EC1 §7.2)
- Estructura: edificio rectangular
- Tablas A/B/D/E segun forma. Aplicar cp_ext * q_p para presiones netas.

## 6. Combinaciones
- W_d = gamma_Q * q_p * c_pe * A

Comprobación: TerrainProfile q_p(7 m) = 900.06 Pa (informe 900.06 Pa); con la regla anterior (z = 10 m) habría dado 993.84 Pa (+10 %).
En la cresta de la loma c_o = 1.3644 (Anexo A.3) → q_p = 1413.15 Pa, 1.57 veces el terreno llano.
Línea de orografía del informe con c_o: - c_o = 1.3644 (EN 1991-1-4 §4.3.3 / Anexo A.3)
Ficheros: reporte_ec1_llano.md y reporte_ec1_loma.md en examples/out/.
```

</details>

#### Livello di servizi: ogni risultato ricalcolato con il motore e unità imperiali della ASCE 7

<details><summary>Output reale di <code>python examples/services_layer_ec1_asce7_nsr10_components_delegate_to_the_engines_cross_check_and_units.py</code></summary>

```text
EC1: q_p(24 m) = 1.2405 kPa (motor 1.2405), v_m = 30.50 m/s, c_pe D/E = 0.8/-0.550 (h/d = 2), neta 1.6747 kPa
ASCE 7: q_h = 31.79 psf (TerrainProfile en SI → 31.78 psf), L/B = 1,5 → Cp_l = -0.40, neta = 32.43 psf = q_h·0,85·1.20 (32.43)
        barlovento máx. 27.34 psf (con −GCpi), succión de sotavento máx. -16.53 psf (con +GCpi)
NSR-10 Cali: V = 97.2 km/h, q_h = 0.5510 kPa (NSR10WindLoad 0.5510, incluye I = 1,15), neta 0.6089 kPa = q_h·0,85·1,3
C&C zona 4, A =  0.5 m²: GCp− = -1.100 (asce7_GCp -1.100), p− = -1.320 kPa; Presiones exteriores q_h·GCp; falta restar/sumar q_h·GCpi.
C&C zona 5, A =  5.0 m²: GCp− = -1.142 (asce7_GCp -1.142), p− = -1.370 kPa; Presiones exteriores q_h·GCp; falta restar/sumar q_h·GCpi.
C&C zona 3, A = 20.0 m²: GCp− = -2.494 (asce7_GCp -2.494), p− = -2.993 kPa; roof_type='gable': se usa la tabla θ <= 7° (sin contrastar).
```

</details>

#### API REST senza server: tutti gli endpoint e i 400 per input non valido

<details><summary>Output reale di <code>python examples/rest_api_testclient_ec1_asce7_nsr10_cc_export_openfoam_version_and_400_on_invalid_input.py</code></summary>

```text
Versión de la API: 1.2.0 (windloads.__version__ = 1.2.0)
GET / → ['/api/wind/ec1', '/api/wind/asce7', '/api/wind/nsr10', '/api/wind/components/cc', '/api/export', '/api/wind/openfoam-pre']
POST /api/wind/ec1 → 200: q_p = 0.9219 kPa, v_m = 23.52 m/s, neta 1.2139 kPa
POST /api/wind/asce7 → 200: q_h = 24.58 psf, neta 22.98 psf
POST /api/wind/nsr10 → 200: V = 97.2 km/h, q_z = 0.5854 kPa
POST /api/wind/components/cc → 200: GCp 0.941/-1.282
POST /api/export (csv) → 200:
    story,z_m,pressure_kPa
    1,3.00,0.9000
    2,6.00,1.0000
    3,9.00,1.1000
POST /api/wind/openfoam-pre → 200: blockMeshDict, controlDict, snappyHexMeshDict, building_obj

Entradas inválidas:
  /api/wind/ec1              → 400: "terrain_category debe ser 0..4, recibido 7"
  /api/wind/asce7            → 400: "exposure debe ser B, C o D, recibido 'Z'"
  /api/wind/components/cc    → 400: "zone debe ser 1-5, recibido 9"
  /api/export                → 400: "pressures_per_story es obligatorio (kPa por planta, de abajo arriba); el servicio no inventa presio
  /api/wind/openfoam-pre     → 400: "El edificio es más alto que la altura del túnel de viento."
```

</details>

### 6. Esportazione e integrazioni

#### Forze di piano verso JSON, CSV, .s2k ed .e2k con ripartizione ai nodi per area di influenza

<details><summary>Output reale di <code>python examples/export_story_forces_json_csv_sap2000_s2k_etabs_e2k_with_joint_map_tributary_areas_and_equivalent_pressure.py</code></summary>

```text
V_b = 1949.7 kN; patrón WX+: suma 1949.70 kN
Planta 1: F = 144.82 kN → presión equivalente 1609.1 Pa = F·1000/(30·3) (1609.1); q_p(z_e) = 1307.11 Pa
.s2k planta 1: [24.1367, 48.2733, 48.2733, 24.1367] kN, suma 144.8200 = F de planta 144.82; pesos C1 0.167, E1 0.333, E2 0.333, C2 0.167
Total de cargas en nudos del .s2k: 1949.70 kN (56 líneas)
Fragmentos:
  Joint=C1   LoadPat=WX+   CoordSys=GLOBAL   F1=24.1367   F3=0   M1=0   M2=0   M3=0
  STORYLOAD "Story1"  LOADPAT "WX+"  TYPE  "POINT"  POINT "C1"  DIR "FX"  VALUE 24.1367
Vuelco: patrón (cota superior) 42149.9 kN·m, cálculo (centro de planta) 39275.5 kN·m; diferencia 2874.4 = Σ F·h/2 = 2874.4 kN·m
JSON: 14 niveles; ficheros .json, .csv, .s2k y .e2k en examples/out/
```

</details>

#### Modello canonico: pressione del vento in carico lineare sui pilastri di un portale

<details><summary>Output reale di <code>python examples/canonical_model_sap_bridge_wind_pressure_to_frame_line_loads_pa_to_kn_per_m_portal_frame.py</code></summary>

```text
q_p(7 m) = 900.1 Pa; c_pe,D = 0.70, c_pe,E = -0.30 → p = 630.0 / -270.0 Pa
Barlovento: patrón W_X (Wind), w = 3.780 kN/m = 630.0/1000·6.0
Modelo: 1 patrón(es) ['W_X'], 2 cargas de barra:
  COL_W  w = +3.780 kN/m  GlobalX  (W_X)
  COL_L  w = +1.620 kN/m  GlobalX  (W_X)
Empuje horizontal total = Σ w·H = 37.80 kN; a mano (p_D − p_E)·6·7/1000 = 37.80 kN
El modelo base no cambia (inmutable): 0 cargas. Falta la cubierta (zonas F-I) y c_s·c_d.
```

</details>

#### Ponti verso SAP2000 con un client registratore e l'ipotesi sulle unità

<details><summary>Output reale di <code>python examples/fastsap_bridge_recorder_client_joint_loads_kn_to_n_and_present_units_assumption_without_sap2000.py</code></summary>

```text
Cargas de nudo [kN]: 5=3.825, 6=7.650, 7=7.650, 8=3.825; suma 22.950 = 0,85·27 = 22.950
apply_wind_loads_to_sap: aplicadas 3, fallidas {'8': 'SetLoadForce devolvio 1'}; Aplicadas 3/4 cargas, sumF = (19.1, 0.0) kN
  llamada grabada: ('LoadPatterns.Add', 'W_X_EC1', 8)
  llamada grabada: ('SetLoadForce', '5', 'W_X_EC1', (3825.0, 0.0, 0.0, 0.0, 0.0, 0.0))
  llamada grabada: ('SetLoadForce', '6', 'W_X_EC1', (7650.0, 0.0, 0.0, 0.0, 0.0, 0.0))
Fuerza enviada al nudo 5: 3825.0 (= 3.825 kN × 1000): correcto solo con el modelo en N.

Exportador en seco: {'patterns': ['WX+', 'WY+'], 'n_patterns': 2, 'n_loads': 3, 'dry_run': True}
Exportador con cliente: aplicadas 3, fallidas {}; patrones creados ['WX+', 'WY+'] con tipo 8 (OTHER)
```

</details>

#### Disegno DXF dei carichi per faccia e verifica del verso delle frecce

<details><summary>Output reale di <code>python examples/dxf_wind_plan_pressure_and_suction_arrows_by_face_from_ec1_coefficients_entity_counts_and_arrow_check.py</code></summary>

```text
q_p(12 m) = 0.833 kN/m²; h/d = 0.30: c_pe D = 0.71, E = -0.31, A = -1.20
  windward   c_pe = +0.71  p = q_p·c_pe = +0.589 kN/m²
  leeward    c_pe = -0.31  p = q_p·c_pe = -0.261 kN/m²
  side_left  c_pe = -1.20  p = q_p·c_pe = -1.000 kN/m²
  side_right c_pe = -1.20  p = q_p·c_pe = -1.000 kN/m²
DXF plano_viento_nave_40x16.dxf: LINE@W-PRESS ×3, LINE@W-SUCT ×9, LWPOLYLINE@W-LEGEND ×1, LWPOLYLINE@W-OUTLINE ×1, LWPOLYLINE@W-TITLE ×1, TEXT@W-TEXT ×10
Barlovento (x = 0): flecha de (-10.0, 8.0) a (0.0, 8.0) → apunta hacia el edificio (presión)
Sotavento (x = 40): flecha de (40.0, 8.0) a (50.0, 8.0) → sale del edificio (succión)
El plano es esquemático: una flecha por cara con el c_pe dado, sin las zonas A/B/C a lo largo de las laterales ni las de cubierta; solo reconoce las caras windward/leeward/side_left/side_right de la caja envolvente (otra etiqueta se dibuja en el centro de la planta).
```

</details>

#### Preprocessore di OpenFOAM: dizionari, OBJ, bloccaggio e cosa manca per eseguire

<details><summary>Output reale di <code>python examples/openfoam_cfd_preprocessor_wind_tunnel_dictionaries_obj_geometry_blockage_ratio_and_missing_case_files.py</code></summary>

```text
### Resumen del Túnel de Viento CFD (OpenFOAM)
- **Dominio Virtual**: 300.0m (L) x 160.0m (W) x 72.0m (H).
- **Malla Bounding Box**: 129600 celdas en blockMesh (100x54x24).
- **Obstáculo (Edificio)**: 16.0m (L) x 40.0m (W) x 12.0m (H).
- **Ubicación**: (80.0, 80.0).
- **Solver**: `simpleFoam` corriendo por `2000` pasos/segundos.

Ficheros escritos: ['constant/triSurface/building.obj', 'system/blockMeshDict', 'system/controlDict', 'system/snappyHexMeshDict']
Bloqueo = área frontal/sección del túnel = 40·12/(160·72) = 4.2 %
Distancias: barlovento 72 m = 6.0·H, sotavento 212 m = 17.7·H, techo 60 m = 5.0·H
Celda de fondo 3.0 m: el edificio de 12 m tiene 4.0 celdas de altura antes de refinar.
locationInMesh (1 1 1) queda fuera del edificio.
Faltan para ejecutar: 0/U, 0/p, 0/k, 0/epsilon o 0/omega, constant/transportProperties, constant/momentumTransport, system/fvSchemes, system/fvSolution, system/surfaceFeaturesDict.
```

</details>

## Verifica

- Cascata della EN 1991-1-4 in terreno II, z = 10 m, v_b = 26 m/s: c_r = 1,00668, I_v = 0,18874, q_p = 993,84 Pa, c_e = 2,352, ricavati a mano (`test_golden_ec1_qp_cascade.py`).
- Schede del master (`test_golden_fichas_en1991_1_4.py`): CTE DB SE-AE W00483 (q_b per zone, q_p = 778,75 Pa in terreno III a 10 m, pressioni nette delle zone A-E con c_pi +0,2/−0,3), c_pi della scheda W00249 e IAP-11 della W01375. Il valore di riferimento della zona A fissava −1,0 ed è stato corretto in −1,2 (Tabella 7.1).
- Correzioni della 1.2.0, ciascuna con il suo oracolo (`test_fixes_1_2_0.py`): Tabella 7.1 e fattore di correlazione, altezze di riferimento della Figura 7.4, taglio alla base della EN 1991-1-4 ricalcolato con la formula scritta a parte (276,68 kN su 20 × 12 × 12 m; torre di 60 m per fasce), Cp sottovento della ASCE 7 interpolato, relazione senza handcalcs, Espressioni (A.4)-(A.13) dell'Allegato A.3 riscritte nel test, K_zt con i parametri della Fig. 26.8-1, K = 0,13, St = 0,18 e c_lat dell'Allegato E, Tabelle 7.3a/7.4a/7.4b, z_min del rapporto, pressione equivalente dell'esportazione, verso delle frecce del DXF, I su q_z nella NSR-10, servizi rispetto ai motori e versione unica.
- Conversione Pa → kN/m del ponte verso il modello canonico (`test_wind_bridge_units.py`), ponti SAP2000 con client simulati (`test_fastsap_bridge.py`, `test_fastsap_load_patterns.py`) e invarianti con hypothesis (q_p > 0 e crescente con z, q_z crescente con V, zona 3 più sfavorevole della 1, Barranquilla sopra Bogotá; `test_property_invariants.py`).
- `tests/test_examples.py` esegue i 33 esempi come sottoprocessi su ubuntu e windows × Python 3.11-3.13.

## Limitazioni

- EN 1991-1-4: c_s·c_d vale 1 per impostazione predefinita (il risultato lo segnala come `unverified_default` oltre i 15 m); con `compute_cscd_annex_b=True` si calcola con l'Allegato B, procedura 1, con n_1 = 46/h se non si dà la frequenza e δ = δ_s senza la parte aerodinamica (il caso della torre di 60 m rifà l'Eq. 6.1, non il resto dell'allegato). `EC1WindLoad` accetta `c_o` e `orography_params` dalla 1.3, non confrontati con un caso pubblicato; edifici con apertura dominante non implementati (vengono rifiutati); il rapporto dei componenti usa un solo c_pi (bisogna passare +0,2 e −0,3); le coperture a due falde non coprono pendenze negative né la regola della copertura piana tra −5° e 5°, e quella a una falda non ha la Tabella 7.3b (θ = 90°). Solo valori raccomandati: nessun allegato nazionale.
- ASCE 7: K_z con le costanti della ASCE 7-16 (la ASCE 7-22 ha corretto il profilo); G = 0,85 di edificio rigido senza verificare la frequenza; la copertura del MWFRS non viene calcolata (`asce7_Cp_roof_flat` è una semplificazione non confrontata); i quattro casi di torsione usano l'eccentricità 0,15·B di edificio rigido (la ASCE ne dà un'altra per edifici flessibili); le tabelle di componenti e rivestimenti di copertura (zone 1-3, due falde, una falda, cupola, mansarda) non sono confrontate e quelle di parete (zone 4 e 5) non sono state nuovamente confrontate in questa revisione; la correzione per il parapetto è propria.
- NSR-10: le categorie di terreno A-D di `NSR10WindLoad` non sono le lettere della norma (A ≈ D, B ≈ C, C ≈ B della ASCE 7-05; D senza corrispondenza); `vb_atlas` e `vb_map` seguono ora le zone, ma `NSR10_WIND_SPEED_BY_CITY` (quella usata da `nsr10_basic_wind_speed`) no: quattro città dei Caraibi oltre i 36 m/s della regione 5; le regioni di minaccia (`NSR10_WIND_ZONES`, B.2.3, e `NSR10_WIND_ZONES_B24`) seguono la mappa del Decreto 1711 del 2021, sette regioni con San Andrés (6) e Providencia (7); fattori di importanza non confrontati.
- NCh 432, AS 1170.2 e SS EN: costanti e tabelle di `nch432` e `codes_multi` non confrontate (il K_z della NCh 432 risulta 11-37 % sotto quello della ASCE 7-05). La tabella «ASCE» dei periodi di ritorno dà 0,90 per T = 50 anni.
- Dinamica: il fattore di raffica di Davenport usa (h + h) in Q e omette R_B·(0,53 + 0,47·R_L) in R; I_z, L_z e V_z sono dati di ingresso. Nei vortici, c_lat non si ricava dal numero di Reynolds né si applica la Tabella E.3, e la banda di aggancio è un criterio proprio. `aeroelastic.galloping_critical_velocity` usa il segno di Den Hartog (non l'a_G della Tabella E.7), `flutter_2dof` non è valido e il fattore di interferenza di scia è proprio.
- Esportazione e integrazioni: i frammenti .s2k/.e2k non sono stati importati in SAP2000 né in ETABS; i ponti verso SAP2000 moltiplicano per 1000 supponendo il modello in N (la API usa le unità correnti del modello); il preprocessore di OpenFOAM non genera un caso eseguibile; il disegno DXF è schematico (una freccia per faccia).
- `cp_catalog`, `cp_techos_complejos` e `solar_trackers` sono di ordine di grandezza: senza riferimento normativo, e l'inseguitore solare non applica K_z.

## Norme e riferimenti

- EN 1991-1-4:2005+A1:2010, *Eurocode 1: Actions on structures — Part 1-4: General actions — Wind actions*: §4.2 (c_prob), §4.3-4.5 e Tabella 4.1, §5.3, §7.2.2 (Tabella 7.1, Figure 7.4 e 7.5), §7.2.3-7.2.5 (Tabelle 7.2, 7.3a, 7.4a e 7.4b), §7.2.9 (c_pi), Allegato A.3 (Espressioni A.1-A.13, Tabella A.2), Allegato E (Tabelle E.1, E.2, E.5 ed E.7; Espressioni E.1, E.2, E.4, E.6, E.7, E.18, E.19, E.23 ed E.24).
- ASCE/SEI 7-10 §26.8 e Fig. 26.8-1 (fattore topografico); ASCE/SEI 7-16 Fig. 27.3-1 (Cp delle pareti del MWFRS), §30.3 (fascia d'angolo a) e §27.3.5 / Fig. 27.3-8 (quattro casi di carico con eccentricità ±0,15·B in edifici rigidi; le percentuali del 75 % e del 56,3 % del modulo non sono state confrontate con il testo).
- SEAOG, «ASCE 7-22 wind changes» (2025), sulla correzione del profilo di K_z.
- O. D. Arroyo Amell e L. Ramos Castillo, «Necesidad de revisión de cargas y factores parciales de la NSR-10 para el diseño de estructuras sometidas a acciones de viento», *Ingeniería y Ciencia* 11(21):177-195 (2015), doi:10.17230/ingciencia.11.21.9 (regioni di velocità della NSR-10 e adozione della ASCE 7-05).
- Ministerio de Vivienda, Ciudad y Territorio (Colombia), Decreto 1711 del 13 dicembre 2021, Allegato Tecnico: Figura B.6.4-1 della NSR-10 modificata, «Velocidad del viento básico, zonas de amenaza eólica» (sette regioni, velocità per le combinazioni di B.2.3 e di B.2.4).
- CTE DB SE-AE (scheda W00483 dei test di riferimento).

## Licenza

MIT. Vedi [LICENSE](LICENSE).

---

Parte di **Loadpath**, la raccolta di librerie strutturali open source di [Jesús Murgas](https://github.com/jmurgass99).
