"""Coeficientes de cubierta de EN 1991-1-4: plana (Tabla 7.2), a un agua (Tabla 7.3a) y a dos aguas (Tablas 7.4a y 7.4b).

Funciones `ec1_cpe_local(..., 'flat_roof')`, `ec1_monopitch_cpe` y `ec1_gable_cpe` (valores recomendados transcritos de
EN 1991-1-4:2005+A1:2010, págs. 39, 42, 45 y 46). A θ = 0° las tablas dan una rama de succión y otra de presión
entre 5° y 45°; el argumento `case` las separa. Se interpolan linealmente en la pendiente (solo entre valores del
mismo signo, Nota 2) y en el área con log10(A) (Figura 7.2). Se comprueban a mano dos interpolaciones. No están
implementadas las pendientes negativas ni la Tabla 7.3b (monopitch, θ = 90°).

Ejecutar:  python examples/ec1_roof_cpe_tables_7_2_flat_7_3a_monopitch_7_4_duopitch_pitch_and_area_interpolation_hand_check.py
"""
import math

from windloads import ec1_cpe_local, ec1_gable_cpe, ec1_monopitch_cpe


def main() -> None:
    print("Cubierta plana con aleros vivos (Tabla 7.2): c_pe,1 / c_pe,10")
    for zone in ("F", "G", "H", "I_neg", "I_pos"):
        print(f"  {zone:<6} A = 1 m²: {ec1_cpe_local(zone, 1.0, 'flat_roof'):5.2f}   "
              f"A = 10 m²: {ec1_cpe_local(zone, 10.0, 'flat_roof'):5.2f}")

    print("\nA un agua, Tabla 7.3a, c_pe,10 (A = 10 m²): θ = 0° succión / presión y θ = 180°")
    print(f"  {'α':>4}" + "".join(f"   {z}: 0°− 0°+ 180°" for z in ("F", "G", "H")))
    for a in (5, 15, 30, 45, 60, 75):
        row = ""
        for z in ("F", "G", "H"):
            row += (f"   {ec1_monopitch_cpe(a, z, 10):4.1f} {ec1_monopitch_cpe(a, z, 10, case='pos'):4.1f} "
                    f"{ec1_monopitch_cpe(a, z, 10, wind_dir=180):5.1f}")
        print(f"  {a:4d}{row}")

    print("\nA dos aguas, Tabla 7.4a (θ = 0°, succión) y 7.4b (θ = 90°), c_pe,10:")
    print(f"  {'α':>4}  {'F':>5} {'G':>5} {'H':>5} {'I':>5} {'J':>5}   |  F90   G90   H90   I90")
    for a in (5, 15, 30, 45, 60, 75):
        r0 = " ".join(f"{ec1_gable_cpe(a, z, 10):5.1f}" for z in "FGHIJ")
        r90 = " ".join(f"{ec1_gable_cpe(a, z, 10, wind_dir=90):5.1f}" for z in "FGHI")
        print(f"  {a:4d}  {r0}   | {r90}")

    pitch = 22.5
    hand = -0.9 + (pitch - 15) / 15 * (-0.5 - (-0.9))
    print(f"\nA mano, dos aguas α = {pitch}°, zona F θ = 0°: −0,9 + (22,5−15)/15·(−0,5+0,9) = {hand:.3f} "
          f"(función {ec1_gable_cpe(pitch, 'F', 10):.3f})")
    A = 3.0
    c1, c10 = -2.8, -2.5
    hand_A = c1 - (c1 - c10) * math.log10(A)
    print(f"A mano, un agua α = 15°, θ = 180°, zona F, A = {A} m²: c_pe = −2,8 − (−2,8 + 2,5)·log10(3) = {hand_A:.4f} "
          f"(función {ec1_monopitch_cpe(15, 'F', A, wind_dir=180):.4f})")
    worst = min(("θ=0°", ec1_monopitch_cpe(15, "F", 1.0)), ("θ=180°", ec1_monopitch_cpe(15, "F", 1.0, wind_dir=180)),
                key=lambda t: t[1])
    print(f"En la cubierta a un agua de 15° la succión local pésima de la zona F es {worst[1]:.1f} con {worst[0]}: "
          "la dirección de viento importa y hay que comprobar ambas.")


if __name__ == "__main__":
    main()
