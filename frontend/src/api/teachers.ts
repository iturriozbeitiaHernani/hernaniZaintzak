import api from './client'

export interface Teacher {
  id: number
  nombre: string
  apellidos: string
  email: string
  activo: boolean
  max_sustituciones_semana: number
}

export interface TeacherScheduleSlot {
  id: number
  teacher_id: number
  dia_semana: number     // 0=Lunes … 4=Viernes
  tramo_horario: number  // 1–6
  curso: string | null
  asignatura: string | null
  aula: string | null
  es_libre: boolean
}

export const getTeachers = async (): Promise<Teacher[]> => {
  const response = await api.get<Teacher[]>('/teachers')
  return response.data
}

export const getTeacherSchedule = async (teacherId: number): Promise<TeacherScheduleSlot[]> => {
  const response = await api.get<TeacherScheduleSlot[]>(`/teachers/${teacherId}/schedule`)
  return response.data
}
