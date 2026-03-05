import api from './client'

export interface Absence {
  id: number
  teacher_id: number
  teacher_nombre: string
  fecha_inicio: string
  fecha_fin: string
  motivo: string | null
  estado: 'pendiente' | 'procesada' | 'cancelada'
  created_at: string
}

// ── Preview ─────────────────────────────────────────────────────────────────────

export interface CandidatoPropuesto {
  teacher_id: number
  nombre: string
  puntuacion: number
  razon_principal: string
  pros: string[]
  contras: string[]
  confianza: number
}

export interface TramoPreview {
  tramo_horario: number
  asignatura: string
  aula: string | null
  propuestas: CandidatoPropuesto[]
  advertencias: string[]
  resumen: string
}

export interface AbsencePreviewRequest {
  teacher_id: number
  fecha: string             // YYYY-MM-DD
  tramos_afectados?: number[]
}

export interface AbsencePreviewResponse {
  tramos: TramoPreview[]
}

// ── Creación ────────────────────────────────────────────────────────────────────

export interface SustitutoElegido {
  tramo_horario: number
  substitute_teacher_id: number
  razon_principal?: string
  ai_confianza?: number
}

export interface CreateAbsenceRequest {
  teacher_id: number
  fecha_inicio: string
  fecha_fin: string
  motivo?: string
  tramos_afectados?: number[]
  sustitutos_elegidos?: SustitutoElegido[]
}

// ── API calls ────────────────────────────────────────────────────────────────────

export const previewAbsence = async (data: AbsencePreviewRequest): Promise<AbsencePreviewResponse> => {
  const response = await api.post<AbsencePreviewResponse>('/absences/preview', data)
  return response.data
}

export const getAbsences = async (params?: {
  fecha_inicio?: string
  fecha_fin?: string
  teacher_id?: number
}): Promise<Absence[]> => {
  const response = await api.get<Absence[]>('/absences', { params })
  return response.data
}

export const createAbsence = async (data: CreateAbsenceRequest): Promise<Absence> => {
  const response = await api.post<Absence>('/absences', data)
  return response.data
}

export const deleteAbsence = async (id: number): Promise<void> => {
  await api.delete(`/absences/${id}`)
}
