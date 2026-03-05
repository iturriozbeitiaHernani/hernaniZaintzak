import api from './client'

export interface CenterConfig {
  id: number
  nombre_centro: string
  confirmacion_requerida: boolean
  max_sustituciones_diarias_por_profesor: number
}

export const getConfig = async (): Promise<CenterConfig> => {
  const response = await api.get<CenterConfig>('/config')
  return response.data
}

export const updateConfig = async (data: Partial<CenterConfig>): Promise<CenterConfig> => {
  const response = await api.put<CenterConfig>('/config', data)
  return response.data
}
