// C++ / WebAssembly kernel para presión dinámica pico EN 1991-1-4 q_p(z) y fuerza neta por panel
extern "C" {
  double peakVelocityPressure(double rho, double vm, double Iv) {
    return 0.5 * rho * vm * vm * (1.0 + 7.0 * Iv);
  }

  double zoneWindForce(double qp_kpa, double cpe, double cpi, double area_m2) {
    return qp_kpa * (cpe - cpi) * area_m2;
  }
}
