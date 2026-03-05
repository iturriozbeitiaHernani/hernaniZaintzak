import { useState, useMemo, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getCursos, getWeekSchedule, type DayScheduleEntry } from '../api/schedule'
import { useScheduleFilterStore } from '../store/scheduleFilterStore'
import { Bot, BookOpen, Coffee, ChevronLeft, ChevronRight, Calendar } from 'lucide-react'
import clsx from 'clsx'
import { getModuloColor } from '../utils/moduloColors'

// ─── Horario fijo del centro ──────────────────────────────────────────────────
type SlotTipo = 'clase' | 'recreo'

interface HorarioSlot {
  inicio: string
  fin: string
  tipo: SlotTipo
  tramo?: number
}

const HORARIO_DIARIO: HorarioSlot[] = [
  { inicio: '08:00', fin: '09:00', tipo: 'clase',  tramo: 1 },
  { inicio: '09:00', fin: '10:00', tipo: 'clase',  tramo: 2 },
  { inicio: '10:00', fin: '11:00', tipo: 'clase',  tramo: 3 },
  { inicio: '11:00', fin: '11:25', tipo: 'recreo'            },
  { inicio: '11:25', fin: '12:25', tipo: 'clase',  tramo: 4 },
  { inicio: '12:25', fin: '13:25', tipo: 'clase',  tramo: 5 },
  { inicio: '13:25', fin: '14:25', tipo: 'clase',  tramo: 6 },
]

const DIAS_CORTOS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie']

// ─── Helpers de fecha ─────────────────────────────────────────────────────────
function isoToMonday(dateStr: string): string {
  const [y, m, d] = dateStr.split('-').map(Number)
  const date = new Date(y, m - 1, d)
  const day = date.getDay() // 0=Dom … 6=Sáb
  const back = day === 0 ? 6 : day - 1
  date.setDate(date.getDate() - back)
  return fmtISO(date)
}

function addWeeks(mondayStr: string, delta: number): string {
  const [y, m, d] = mondayStr.split('-').map(Number)
  return fmtISO(new Date(y, m - 1, d + delta * 7))
}

function fmtISO(date: Date): string {
  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, '0'),
    String(date.getDate()).padStart(2, '0'),
  ].join('-')
}

function weekLabel(mondayStr: string): string {
  const [y, m, d] = mondayStr.split('-').map(Number)
  const mon = new Date(y, m - 1, d)
  const fri = new Date(y, m - 1, d + 4)
  const mL = mon.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })
  const fL = fri.toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' })
  return `${mL} – ${fL}`
}

function dayColLabel(mondayStr: string, idx: number): { short: string; num: string } {
  const [y, m, d] = mondayStr.split('-').map(Number)
  const date = new Date(y, m - 1, d + idx)
  return {
    short: DIAS_CORTOS[idx],
    num: date.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' }),
  }
}

function isToday(mondayStr: string, idx: number): boolean {
  const [y, m, d] = mondayStr.split('-').map(Number)
  const date = new Date(y, m - 1, d + idx)
  const today = new Date()
  return (
    date.getFullYear() === today.getFullYear() &&
    date.getMonth() === today.getMonth() &&
    date.getDate() === today.getDate()
  )
}

const THIS_MONDAY = isoToMonday(new Date().toISOString().split('T')[0])

// ─── Helpers de ciclo ─────────────────────────────────────────────────────────
function extractCiclo(curso: string): string {
  if (/ESO/i.test(curso))                           return 'ESO'
  if (/Bach/i.test(curso))                          return 'Bachillerato'
  if (/CFGM|CFGS|DAM|DAW|ASIR|SMR|FP/i.test(curso)) return 'FP'
  if (/Prim|Primaria/i.test(curso))                 return 'Primaria'
  if (/Infantil|EI/i.test(curso))                   return 'Infantil'
  return 'Otros'
}

// ─── Componente principal ─────────────────────────────────────────────────────
export default function WeekPage() {
  const navigate = useNavigate()
  const [weekMonday, setWeekMonday] = useState(THIS_MONDAY)
  const dateInputRef = useRef<HTMLInputElement>(null)
  const { selectedCiclo, selectedCurso, setCiclo, setCurso, clear, setDate } = useScheduleFilterStore()

  const goToDay = (mondayStr: string, dayIdx: number) => {
    const [y, m, d] = mondayStr.split('-').map(Number)
    const date = new Date(y, m - 1, d + dayIdx)
    setDate(fmtISO(date))
    navigate('/today')
  }

  const { data: cursosList = [] } = useQuery({
    queryKey: ['schedule', 'cursos'],
    queryFn: getCursos,
  })

  const ciclos = useMemo(() => Array.from(new Set(cursosList.map(extractCiclo))).sort(), [cursosList])

  const cursosFiltrados = useMemo(
    () => (!selectedCiclo ? cursosList : cursosList.filter((c) => extractCiclo(c) === selectedCiclo)),
    [cursosList, selectedCiclo],
  )

  const handleCicloChange = (ciclo: string) => setCiclo(ciclo)

  const { data: weekData = [], isLoading } = useQuery({
    queryKey: ['schedule', 'week', weekMonday, selectedCurso],
    queryFn: () => getWeekSchedule(weekMonday, selectedCurso),
    enabled: !!selectedCurso,
  })

  // Índice: tramo → dayIdx → entry
  const byTramo = useMemo(() => {
    const map: Record<number, Record<number, DayScheduleEntry>> = {}
    for (let dayIdx = 0; dayIdx < weekData.length; dayIdx++) {
      for (const entry of weekData[dayIdx].tramos) {
        if (!map[entry.tramo]) map[entry.tramo] = {}
        map[entry.tramo][dayIdx] = entry
      }
    }
    return map
  }, [weekData])

  // Recuento de ausencias de la semana
  const totalAusentes = useMemo(() => {
    let count = 0
    for (const day of weekData) count += day.tramos.filter((e) => e.ausente).length
    return count
  }, [weekData])

  const isThisWeek = weekMonday === THIS_MONDAY

  return (
    <div className="p-6">
      {/* Cabecera */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Horario semanal</h2>

        {/* Navegador de semana */}
        <div className="flex items-center gap-1 mt-2">
          <button
            onClick={() => setWeekMonday((m) => addWeeks(m, -1))}
            className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-100 hover:text-gray-800 transition-colors"
            title="Semana anterior"
          >
            <ChevronLeft size={18} />
          </button>

          <span className="text-sm text-gray-600 font-medium min-w-72 text-center select-none capitalize">
            {weekLabel(weekMonday)}
          </span>

          <button
            onClick={() => setWeekMonday((m) => addWeeks(m, 1))}
            className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-100 hover:text-gray-800 transition-colors"
            title="Semana siguiente"
          >
            <ChevronRight size={18} />
          </button>

          {/* Selector de fecha con input nativo oculto */}
          <div className="relative ml-1">
            <button
              onClick={() => dateInputRef.current?.showPicker()}
              className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-700 transition-colors"
              title="Ir a una semana concreta"
            >
              <Calendar size={16} />
            </button>
            <input
              ref={dateInputRef}
              type="date"
              value={weekMonday}
              onChange={(e) => e.target.value && setWeekMonday(isoToMonday(e.target.value))}
              className="absolute inset-0 opacity-0 w-full cursor-pointer"
            />
          </div>

          {!isThisWeek && (
            <button
              onClick={() => setWeekMonday(THIS_MONDAY)}
              className="ml-2 text-xs text-blue-500 hover:text-blue-700 underline underline-offset-2"
            >
              Esta semana
            </button>
          )}
        </div>
      </div>

      {/* Filtros */}
      <div className="flex items-center gap-3 mb-6 flex-wrap">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-600">Ciclo</label>
          <select
            value={selectedCiclo}
            onChange={(e) => handleCicloChange(e.target.value)}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
          >
            <option value="">Todos</option>
            {ciclos.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-600">Curso / Clase</label>
          <select
            value={selectedCurso}
            onChange={(e) => setCurso(e.target.value)}
            disabled={cursosFiltrados.length === 0}
            className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white disabled:opacity-40"
          >
            <option value="">Seleccionar clase...</option>
            {cursosFiltrados.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>

        {(selectedCiclo || selectedCurso) && (
          <button
            onClick={clear}
            className="text-xs text-gray-500 hover:text-gray-800 underline"
          >
            Limpiar
          </button>
        )}
      </div>

      {/* Contenido */}
      {!selectedCurso ? (
        <EmptySelection />
      ) : isLoading ? (
        <div className="flex items-center justify-center h-48 text-gray-500">Cargando...</div>
      ) : (
        <>
          {/* Resumen */}
          <div className="flex items-center gap-3 mb-4">
            <span className="text-sm text-gray-600">
              <span className="font-semibold text-gray-900">{selectedCurso}</span>
              {' — '}semana completa
            </span>
            {totalAusentes > 0 && (
              <span className="text-xs bg-red-50 text-red-700 px-2.5 py-1 rounded-full font-medium">
                {totalAusentes} tramo{totalAusentes > 1 ? 's' : ''} con ausencia
              </span>
            )}
          </div>

          {/* Grid semanal */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left px-4 py-3 font-medium text-gray-500 w-28 text-xs">
                    Hora
                  </th>
                  {[0, 1, 2, 3, 4].map((idx) => {
                    const col = dayColLabel(weekMonday, idx)
                    const today = isToday(weekMonday, idx)
                    return (
                      <th
                        key={idx}
                        className={clsx(
                          'px-3 py-3 font-medium text-xs text-center border-l border-gray-200',
                          today ? 'text-blue-700 bg-blue-50/60' : 'text-gray-600',
                        )}
                      >
                        <button
                          onClick={() => goToDay(weekMonday, idx)}
                          className={clsx(
                            'w-full rounded-md py-0.5 transition-colors',
                            today
                              ? 'hover:bg-blue-100'
                              : 'hover:bg-gray-100',
                          )}
                          title="Ver horario del día"
                        >
                          <div className="font-semibold">{col.short}</div>
                          <div className={clsx('font-normal mt-0.5', today ? 'text-blue-500' : 'text-gray-400')}>
                            {col.num}
                          </div>
                        </button>
                      </th>
                    )
                  })}
                </tr>
              </thead>
              <tbody>
                {HORARIO_DIARIO.map((slot, idx) => {
                  if (slot.tipo === 'recreo') {
                    return (
                      <tr key={idx} className="bg-amber-50/50 border-y border-amber-100">
                        <td className="px-4 py-2">
                          <span className="text-xs text-gray-400 font-medium">
                            {slot.inicio} – {slot.fin}
                          </span>
                        </td>
                        <td colSpan={5} className="px-4 py-2 border-l border-gray-200">
                          <span className="flex items-center gap-1.5 text-xs text-amber-600 font-medium">
                            <Coffee size={12} />
                            Recreo
                          </span>
                        </td>
                      </tr>
                    )
                  }

                  return (
                    <tr key={idx} className="border-b border-gray-100 last:border-0">
                      {/* Hora */}
                      <td className="px-4 py-3">
                        <div className="text-xs text-gray-500 font-medium whitespace-nowrap">
                          {slot.inicio} – {slot.fin}
                        </div>
                        <div className="text-xs text-gray-400">{slot.tramo}ª hora</div>
                      </td>

                      {/* Celda por día */}
                      {[0, 1, 2, 3, 4].map((dayIdx) => {
                        const entry = slot.tramo != null ? byTramo[slot.tramo]?.[dayIdx] : undefined
                        const todayCol = isToday(weekMonday, dayIdx)
                        return (
                          <WeekCell
                            key={dayIdx}
                            entry={entry}
                            isToday={todayCol}
                          />
                        )
                      })}
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Leyenda */}
          <div className="flex items-center gap-4 mt-3 text-xs text-gray-400">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-sm bg-white border border-gray-300 inline-block" />
              Normal
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-sm bg-red-100 inline-block" />
              Ausencia sin cubrir
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-sm bg-yellow-100 inline-block" />
              Ausencia cubierta
            </span>
            <span className="flex items-center gap-1">
              <Bot size={12} className="text-purple-400" />
              Sustituto propuesto por IA
            </span>
          </div>
        </>
      )}
    </div>
  )
}

// ─── Celda del grid ────────────────────────────────────────────────────────────
function WeekCell({
  entry,
  isToday,
}: {
  entry: DayScheduleEntry | undefined
  isToday: boolean
}) {
  const baseBorder = 'border-l border-gray-200'

  if (!entry || !entry.asignatura) {
    return (
      <td className={clsx('px-3 py-3 align-top', baseBorder, isToday && 'bg-blue-50/20')}>
        <span className="text-gray-200 text-xs">—</span>
      </td>
    )
  }

  if (entry.ausente) {
    if (entry.sustituto) {
      // Ausencia cubierta
      const colorCub = getModuloColor(entry.asignatura)
      return (
        <td className={clsx('px-3 py-3 align-top border-l-2', colorCub.border, 'bg-yellow-50')}>
          <span className={clsx(
            'inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium',
            colorCub.bg, colorCub.text,
          )}>
            <BookOpen size={10} className="shrink-0" />
            <span className="truncate max-w-[7rem]">{entry.asignatura}</span>
          </span>
          <div className="flex items-center gap-1 mt-0.5">
            {entry.ai_propuesta && (
              <Bot size={10} className="text-purple-400 shrink-0" title="Propuesto por IA" />
            )}
            <span className="text-xs text-green-700 truncate max-w-[8rem]">
              {entry.sustituto.nombre}
            </span>
          </div>
        </td>
      )
    }
    // Ausencia sin cubrir
    return (
      <td className={clsx('px-3 py-3 align-top', baseBorder, 'bg-red-50')}>
        <div className="text-xs font-medium text-gray-500 truncate max-w-[9rem] line-through">
          {entry.asignatura}
        </div>
        <div className="text-xs text-red-600 font-medium mt-0.5">Sin cubrir</div>
      </td>
    )
  }

  // Normal
  const color = getModuloColor(entry.asignatura)
  return (
    <td className={clsx('px-3 py-3 align-top border-l-2', color.border, isToday && 'bg-blue-50/20')}>
      <div>
        <span className={clsx(
          'inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium',
          color.bg, color.text,
        )}>
          <BookOpen size={10} className="shrink-0" />
          <span className="truncate max-w-[7rem]">{entry.asignatura}</span>
        </span>
        {entry.aula && (
          <div className="text-xs text-gray-400 mt-0.5 pl-0.5">{entry.aula}</div>
        )}
      </div>
    </td>
  )
}

// ─── Estado vacío ─────────────────────────────────────────────────────────────
function EmptySelection() {
  return (
    <div className="flex flex-col items-center justify-center h-64 text-gray-400">
      <BookOpen size={40} className="mb-3 text-gray-300" />
      <p className="text-sm font-medium text-gray-500">Selecciona una clase para ver la semana</p>
      <p className="text-xs mt-1">Elige primero el ciclo y luego el curso / clase</p>
    </div>
  )
}
