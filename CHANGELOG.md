# Changelog

## 1.2.1 — 2026-11-02

Fuente: Decreto 1711 del 13 de diciembre de 2021 (Ministerio de Vivienda, Ciudad y Territorio), Anexo Técnico, que
modifica la Figura B.6.4-1 de la NSR-10.

### Corregido
- `NSR10_WIND_ZONES`: la zona 6 valía 50 m/s (180 km/h), cifra sin fuente. El mapa del decreto tiene siete regiones:
  San Andrés es la región 6, con 44 m/s (160 km/h), y Providencia y Santa Catalina la región 7, con 49 m/s (175 km/h),
  para las combinaciones de B.2.3. Las regiones 1 a 5 (17, 22, 28, 33 y 36 m/s) no cambian y quedan contrastadas.
  `nsr10_zone_from_coords` separa ahora las dos islas; `NSR10_WIND_SPEED_BY_CITY`, `NSR10_CITY_ZONES` y `vb_atlas`
  dan 44 m/s en San Andrés.

### Añadido
- `NSR10_WIND_ZONES_B24` (22, 28, 35, 42, 46, 56 y 61 m/s) y el argumento `combinations="B.2.3" | "B.2.4"` de
  `nsr10_basic_wind_speed`. La tabla por ciudades solo tiene la columna B.2.3, así que una ciudad con `"B.2.4"` exige
  `use_regional_map_b641=True`.

## 1.2.0 — 2026-11-01

Fuentes consultadas para las correcciones: EN 1991-1-4:2005+A1:2010 (texto completo: Tabla 7.1, §7.2.2, Figura 7.4,
Tablas 7.2, 7.3a, 7.3b, 7.4a y 7.4b, Anexo A.3, Anexo E); ASCE 7-10 §26.8 y Fig. 26.8-1; ASCE 7-16 Fig. 27.3-1 (copia
escaneada); SEAOG, «ASCE 7-22 wind changes» (2025); Arroyo Amell y Ramos Castillo, *Ingeniería y Ciencia* 11(21),
2015 (NSR-10).

### Corregido
- `pressure.ec1_cpe_walls`: la zona A valía −1,0; la Tabla 7.1 da c_pe,10 = −1,2 para todo h/d (succión neta de la
  zona A +17 %: nave W00483, −0,934 → −1,090 kPa). Para 1 < h/d ≤ 5 la zona E se quedaba en −0,5; ahora se interpola
  hasta −0,7 (h/d = 3: −0,5 → −0,6). El test dorado `test_golden_fichas_en1991_1_4.py` fijaba A = −1,0 y se ha
  corregido.
- `envelope.MWFRSEnvelope.ec1_story_forces` (y `EC1WindLoad`): la fuerza por planta era q_p(z_sup)·(c_pe,D + 0,3):
  calculaba el c_pe de sotavento y no lo usaba, restaba un c_pi solo en barlovento y no aplicaba ni las alturas de
  referencia z_e de la Figura 7.4 ni el factor de falta de correlación de §7.2.2(3). Ahora
  F = c_s·c_d·f·(c_pe,D·q_p(z_e) − c_pe,E·q_p(h))·b·h_planta. Cortante basal: oficinas 20 × 12 × 12 m 235,1 → 276,7 kN
  (+18 %); torre de 60 m (b = 20, d = 30) +26 %; edificio esbelto h/d = 5 +52 %; nave ancha h/d = 0,25 −9 %; el
  edificio de 30 × 20 × 40 m de los ejemplos 1524,6 → 1949,7 kN (+28 %). `EC1WindLoad` pasa además su `rho`.
- `EC1WindLoad`: aceptaba `enclosure="open_one_face"` y lo ignoraba (c_pi siempre +0,2/−0,3). Ahora lanza
  `ConfigurationError`: con abertura dominante c_pi = 0,75 o 0,90·c_pe (§7.2.9(3)) y el paquete no lo calcula.
- `pressure.asce7_Cp_walls`: el Cp de sotavento iba a saltos (−0,3 ya en L/B = 1,01; −0,2 en 2,01); ahora se interpola
  entre −0,5 (L/B ≤ 1), −0,3 (2) y −0,2 (≥ 4) con la nueva `asce7_leeward_Cp`: presión neta +14,5 % en L/B = 1,2 y
  +9 % en L/B = 1,5. La memoria `memos.asce7_mwfrs` usaba otra recta (−0,4 en L/B = 2 en vez de −0,3) y ahora usa la
  misma función.
- `memos.asce7_mwfrs.mwfrs_directional_memo`: sin handcalcs lanzaba `TypeError` al desempaquetar un número; ahora
  devuelve los mismos resultados con LaTeX vacío (las otras dos memorias ya lo hacían).
- `topography.ec1_orography_factor_A3`: las ramas de sotavento no eran las Expresiones (A.7)-(A.13): la de colina usaba
  el coeficiente A de escarpe con un decaimiento lineal (justo a sotavento de la cresta, c_o = 1,004 en vez de 1,398 con
  Φ = 0,2) y la de escarpe 1/(1 + 0,8·x/L_e). Los escarpes tomaban siempre L_e = L_u (la Tabla A.2 da H/0,3 si Φ > 0,3)
  y fuera de los rangos se extrapolaba en vez de s = 0. Las figuras A.2 (escarpes) y A.3 (colinas) estaban cambiadas
  en los docstrings.
- `topography.asce7_Kzt_simple`: K1 limitado a 0,36 (cresta/colina) o 0,30 (escarpe), la colina 3-D tratada como
  cresta 2-D, γ = 2 y μ = 2,5 en escarpes, sin exposición ni la regla H/L_h > 0,5. Ahora con los parámetros de la
  Fig. 26.8-1 y argumento `exposure` (por defecto C): cresta H/L_h = 0,3 en la cima 1,850 → 2,059; escarpe a
  sotavento x = L_h 1,233 → 1,320; colina 3-D a z = 0,1·L_h 1,605 → 1,467; colina con H/L_h = 0,6 1,565 → 1,828.
- `vortex_shedding.check_galloping`: `at_risk` comparaba v_CG con v_m; EN 1991-1-4 (E.19) exige v_CG > 1,25·v_m.
  `safety_ratio` pasa a ser v_CG/(1,25·v_m). Los valores típicos de a_G del docstring eran erróneos (cuadrado 2,0 →
  1,2 de la Tabla E.7).
- `vortex_shedding.check_vortex_shedding`: K por defecto 1,0 (el docstring decía «1,0 para el modo fundamental»);
  la Tabla E.5 da 0,13 para una ménsula (con K = 1 la amplitud salía 7,7 veces mayor). St de sección
  circular 0,20 → 0,18 (Tabla E.1; v_crit +11 %, amplitud ×1,23); c_lat de rectángulo 1,0 → 1,1 (Tabla E.2). Nuevo
  argumento `clat` para pasar el valor de la Figura E.2 según el número de Reynolds.
- `aeroelastic`: el docstring citaba un «Anexo F» que no trata estos fenómenos (§F.2-§F.5) y llamaba a_G al coeficiente
  de Den Hartog, de signo contrario al a_G de la Tabla E.7 (pasar el a_G de la tabla devuelve «estable»). Se aclaran
  el convenio, las referencias (E.2, E.3, E.4.3) y que `flutter_2dof` no es un análisis de flameo válido.
- `components.ec1_gable_cpe` / `ec1_monopitch_cpe`: las tablas eran una mezcla sin contrastar (dos aguas 15°, F
  c_pe,10 = −1,3, que es el valor de θ = 90°; 45° con c_pe,1 = 0 y c_pe,10 = +0,7 mezclando las dos ramas). Ahora son
  las Tablas 7.4a/7.4b y 7.3a transcritas, con argumentos `wind_dir` (0/90 en dos aguas, 0/180 en un agua) y `case`
  ("neg"/"pos" a θ = 0°). Por defecto, θ = 0° y rama de succión: dos aguas 15° F −1,3 → −0,9; 30° J −1,0 → −0,5.
- `report_ec1.generar_reporte_ec1`: usaba z = max(H, 10 m) en todas las categorías; ahora z_min de la Tabla 4.1
  (H = 7 m, categoría II: q_p 993,84 → 900,06 Pa).
- `export.from_envelope`: `tributary_widths_m` no hacía nada; ahora publica la presión neta equivalente
  F·1000/(B·h_planta).
- `integration.dxf_wind_plan`: las flechas salían al revés (las de presión nacían dentro del edificio).
- `codes.nsr10_b6.NSR10WindLoad`: el factor de importancia multiplicaba V, de modo que q ∝ I² (+32 % en vez de +15 %
  con I = 1,15; −24 % en vez de −13 % con I = 0,87). La NSR-10 adoptó ASCE 7-05, donde I multiplica q_z.
  `Vb_design` es ahora √I·V. `NSR10_WIND_ZONES[5]` 39 → 36 m/s (130 km/h, máximo de la región 5).
- `services`: `compute_asce7` y `compute_nsr10` llamaban a APIs que no existen y caían siempre en cálculos propios
  (NSR-10 con q_z = ½·ρ·(K_z·V)²·I, un K_z inventado y velocidades por ciudad distintas de las del módulo; ASCE 7 con
  Cp de sotavento −0,5 fijo y la presión interior con signos opuestos, neta 0,36·q_h menor); `compute_ec1` devolvía
  como `vm_at_height` la velocidad de pico y coeficientes fijos; `compute_cc` una tabla fija sin área; `export_to`
  inventaba presiones (0,8 − 0,05·i kPa) si no se le pasaban. Ahora delegan en los motores o exigen el dato. La API
  REST hereda los cambios.
- `api.app`: versión 0.1.0 → `windloads.__version__`; el índice lista también `/api/wind/openfoam-pre`.
- Versión única 1.2.0 en `pyproject.toml`, `windloads.__version__` y la API (antes 1.0.0 / 1.1.0 / 0.1.0).
- `tests/test_vortex_shedding.py`: `y_over_D` y `y_max_m` se redondean a 6 decimales por separado; la comparación usa
  esa tolerancia.

### Añadido
- `pressure.ec1_lack_of_correlation_factor`, `pressure.ec1_windward_reference_height`, `pressure.asce7_leeward_Cp`.
- 33 casos de uso ejecutables en `examples/` (seis grupos) con salida en `examples/output/`, `tests/test_examples.py`
  que los ejecuta en CI y `tests/test_fixes_1_2_0.py` con un test por corrección.
- README reescrito con las salidas reales y los límites.

### Eliminado
- `examples/02_three_codes_same_building.py` y `examples/building_30x20x40.py` (absorbidos por los ejemplos nuevos) y
  los ficheros generados que estaban versionados en `examples/out/` (ahora en `.gitignore`).

### Límites documentados (sin cambio de código)
- K_z de ASCE 7 con las constantes de ASCE 7-16 (α = 7,0/9,5/11,5; z_g = 365,76/274,32/213,36 m) aunque el código se
  rotule «ASCE 7-22»: ASCE 7-22 ajustó el perfil (SEAOG 2025: ligera reducción en B y C, sin cambio en D, hasta +20 % en
  estructuras muy altas). G = 0,85 de edificio rígido sin comprobar la frecuencia. Constantes de ráfaga de
  `terrain._ASCE7_EXPOSURE` (ε̄, ℓ, …) no usadas y sin contrastar.
- Tablas de ASCE 7 sin contrastar: cubierta de baja pendiente (zonas 1-3; ASCE 7-16/22 usan 1', 1, 2, 3), dos aguas,
  un agua, cúpula y mansarda (llevan FIXME); el antepecho K_p = min(1 + 0,5·h_p, 1,5) no es el procedimiento de §30.9;
  `asce7_Cp_roof_flat` no sigue la zonificación por distancias de la Fig. 27.3-1 y no se usa. Los GCp de muro
  (zonas 4 y 5) no se han vuelto a contrastar en esta revisión. `mwfrs_load_cases` usa la excentricidad 0,15·B de
  edificio rígido (contrastada); los porcentajes 75 % y 56,3 % no se han contrastado con el texto de la Fig. 27.3-8.
- NSR-10: las categorías A-D de `NSR10WindLoad` no son las letras de la norma (B, C, D de ASCE 7-05): A ≈ D, B ≈ C,
  C ≈ B y D (α = 5) sin pareja. Las tres tablas de ciudades (`NSR10_WIND_SPEED_BY_CITY`, `vb_atlas`, `vb_map`) no
  coinciden entre sí ni se han contrastado con la Figura B.6.4-1; la primera da 40-45 m/s en cuatro ciudades del
  Caribe, por encima de los 36 m/s de la región 5. Zonas 2 y 4 sin contrastar; factores de importancia tomados de
  ASCE 7-05.
- NCh 432: constantes de exposición (α = 4/4,5/7/9) sin contrastar (K_z −11 a −37 % respecto a las de ASCE 7-05).
  AS 1170.2: tabla M_z,cat sin contrastar. SS EN: v_b,0 = 26 m/s por defecto sin contrastar. Tablas de `vb_atlas`
  (Chile, Colombia, España) y `vb_map` sin contrastar; `vb_map` rotula «10 min» velocidades de ASCE 7 (ráfaga de 3 s).
- `mri_generator`: la tabla «ASCE» da 0,90 en T = 50 años (V_50 → 0,9·V_50) y no está contrastada; AS 1170.2 es la
  aproximación (ln T/ln 50)^0,55.
- `davenport.gust_factor_davenport`: Q con (h + h) en lugar de (B + h) y R sin R_B·(0,53 + 0,47·R_L); I_z, L_z y V_z
  son entradas.
- Torbellinos: c_lat no se evalúa con el número de Reynolds (0,2 por defecto, válido entre 5·10⁵ y 5·10⁶) ni se aplica
  la Tabla E.3; la banda de enganche ±20/30 % y la API antigua (`evaluate_vortex_shedding`, a_G = −3 fijo) son
  criterios propios; St de secciones hexagonal, octogonal y en L sin contrastar.
- `aeroelastic`: `flutter_2dof` no es válido; `divergence_critical_velocity` convierte k_Θ = EI/L (pasar EI = k_Θ,
  L = 1 para E.24); `wake_buffeting` usa factores propios.
- EN 1991-1-4: c_s·c_d no se calcula (1,0 con estado `unverified_default` si h > 15 m); `EC1WindLoad` no incorpora el
  c_o de orografía; el informe de C&C usa un solo c_pi; los muros de C&C usan la fila h/d = 1; dos aguas sin
  pendientes negativas ni la regla de cubierta plana entre −5° y 5°; un agua sin la Tabla 7.3b (θ = 90°).
- Fragmentos .s2k/.e2k sin validar en SAP2000/ETABS; el vuelco del patrón exportado usa la cota superior de cada
  planta (mayor que el del cálculo en Σ F·h/2).
- `integration.fastsap_bridge` y `fastsap_load_patterns` multiplican por 1000 suponiendo que el modelo está en N; la
  API de SAP2000 trabaja en las unidades actuales del modelo.
- `cfd_pre` no genera un caso ejecutable (faltan 0/, constant/, fvSchemes, fvSolution, surfaceFeaturesDict).
- `solar_trackers`: sin K_z (la altura no se usa) y GCp de SEAOC PV2 sin contrastar. `cp_catalog` y
  `cp_techos_complejos`: valores indicativos sin referencia (el argumento `code` no cambia nada).
- Servicio de exportación: los destinos «sap» y «etabs» solo escriben la definición del patrón.

## 1.0.0

- Versión publicada como repositorio independiente (copia del paquete del ecosistema).
