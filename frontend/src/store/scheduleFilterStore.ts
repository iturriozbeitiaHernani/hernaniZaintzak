import { create } from 'zustand'

const todayISO = () => new Date().toISOString().split('T')[0]

interface ScheduleFilterState {
  selectedDate: string
  selectedCiclo: string
  selectedCurso: string
  setDate: (date: string) => void
  setCiclo: (ciclo: string) => void
  setCurso: (curso: string) => void
  clear: () => void
}

export const useScheduleFilterStore = create<ScheduleFilterState>((set) => ({
  selectedDate: todayISO(),
  selectedCiclo: '',
  selectedCurso: '',
  setDate: (date) => set({ selectedDate: date }),
  setCiclo: (ciclo) => set({ selectedCiclo: ciclo, selectedCurso: '' }),
  setCurso: (curso) => set({ selectedCurso: curso }),
  clear: () => set({ selectedCiclo: '', selectedCurso: '' }),
}))
