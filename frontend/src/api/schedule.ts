import api from './client'

export interface TeacherBrief {
  id: number
  nombre: string
}

export interface DayScheduleEntry {
  tramo: number
  asignatura: string | null
  aula: string | null
  titular: TeacherBrief | null
  ausente: boolean
  motivo_ausencia: string | null
  sustituto: TeacherBrief | null
  sustitucion_id: number | null
  sustitucion_estado: string | null
  ai_propuesta: boolean
}

export interface WeekDaySchedule {
  fecha: string       // YYYY-MM-DD
  dia_semana: number  // 0=Lunes … 4=Viernes
  tramos: DayScheduleEntry[]
}

export const getCursos = async (): Promise<string[]> => {
  const response = await api.get<string[]>('/schedule/cursos')
  return response.data
}

export const getDaySchedule = async (fecha: string, curso: string): Promise<DayScheduleEntry[]> => {
  const response = await api.get<DayScheduleEntry[]>('/schedule/day', {
    params: { fecha, curso },
  })
  return response.data
}

export const getWeekSchedule = async (fecha: string, curso: string): Promise<WeekDaySchedule[]> => {
  const response = await api.get<WeekDaySchedule[]>('/schedule/week', {
    params: { fecha, curso },
  })
  return response.data
}
