import api from './client'

export interface Substitution {
  id: number
  absence_id: number
  sustituto_id: number | null
  sustituto_nombre: string | null
  tramo: number
  aula: string | null
  curso: string | null
  ausente_nombre: string
  estado: 'propuesta' | 'confirmada' | 'rechazada' | 'completada'
  ai_propuesta: boolean
  ai_confianza: number | null
  ai_razonamiento: string | null
  fecha: string
}

export const getTodaySubstitutions = async (): Promise<Substitution[]> => {
  const response = await api.get<Substitution[]>('/substitutions/today')
  return response.data
}

export const confirmSubstitution = async (id: number): Promise<Substitution> => {
  const response = await api.post<Substitution>(`/substitutions/${id}/confirm`)
  return response.data
}

export const rejectSubstitution = async (id: number): Promise<Substitution> => {
  const response = await api.post<Substitution>(`/substitutions/${id}/reject`)
  return response.data
}
