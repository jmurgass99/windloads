import axios from 'axios'

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || '',
  headers: { 'Content-Type': 'application/json' },
})

export interface WindRequest {
  V_b_ms: number
  exposure: 'I' | 'II' | 'III' | 'IV'
  building: {
    width_m: number
    depth_m: number
    height_m: number
  }
  code: 'EC1' | 'ASCE7' | 'NSR10'
}

export interface ZonePressure {
  zone: 'Windward' | 'Leeward' | 'Side' | 'Roof'
  cp: number
  pressure_kPa: number
}

export interface WindResponse {
  q_p_kPa: number
  zones: ZonePressure[]
  notes?: string[]
}

export async function calculateWind(req: WindRequest): Promise<WindResponse> {
  const { data } = await api.post<WindResponse>('/api/wind/calculate', req)
  return data
}
