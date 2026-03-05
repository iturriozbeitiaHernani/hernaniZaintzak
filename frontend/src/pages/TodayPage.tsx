import { useMemo, useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { confirmSubstitution, rejectSubstitution } from '../api/substitutions'
import { getConfig } from '../api/config'
import { getCursos, getDaySchedule, type DayScheduleEntry } from '../api/schedule'
import { useScheduleFilterStore } from '../store/scheduleFilterStore'
import NewAbsenceModal from '../components/NewAbsenceModal'
import { Bot, Check, X, BookOpen, Coffee, ChevronLeft, ChevronRight, Calendar, UserMinus, Plus } from 'lucide-react'
import clsx from 'clsx'
import { getModuloColor } from '../utils/moduloColors'

// ─── Horario fijo del centro ──────────────────────────────────────────────────
type SlotTipo = 'clase' | 'recreo'

interface HorarioSlot {
  inicio: string
  fin: string
  tipo: SlotTipo
  tramo?: number   // solo en tipo='clase'
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

// ─── Colores estado sustitución ───────────────────────────────────────────────
const SUSTITUCION_COLORS: Record<string, string> = {
  propuesta:  'bg-yellow-100 text-yellow-800',
  confirmada: 'bg-green-100 text-green-800',
  rechazada:  'bg-red-100 text-red-800',
  completada: 'bg-gray-100 text-gray-800',
}
const SUSTITUCION_LABELS: Record<string, string> = {
  propuesta:  'Propuesta',
  confirmada: 'Confirmada',
  rechazada:  'Rechazada',
  completada: 'Completada',
}

// ─── Helpers ──────────────────────────────────────────────────────────────────
function extractCiclo(curso: string): string {
  if (/ESO/i.test(curso))                      return 'ESO'
  if (/Bach/i.test(curso))                     return 'Bachillerato'
  if (/CFGM|CFGS|DAM|DAW|ASIR|SMR|FP/i.test(curso)) return 'FP'
  if (/Prim|Primaria/i.test(curso))            return 'Primaria'
  if (/Infantil|EI/i.test(curso))              return 'Infantil'
  return 'Otros'
}

// Aritmética de fechas sin problemas de zona horaria
function addDays(dateStr: string, delta: number): string {
  const [y, m, d] = dateStr.split('-').map(Number)
  const date = new Date(y, m - 1, d + delta)
  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, '0'),
    String(date.getDate()).padStart(2, '0'),
  ].join('-')
}

function formatDisplay(dateStr: string): string {
  const [y, m, d] = dateStr.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString('es-ES', {
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
  })
}

const TODAY = new Date().toISOString().split('T')[0]

// ─── Componente principal ─────────────────────────────────────────────────────
// modalPreset: null = cerrado, {} = abierto sin prefill, { teacherId, tramo } = prefill
type ModalPreset = { teacherId?: number; tramo?: number } | null

export default function TodayPage() {
  const queryClient = useQueryClient()
  const dateInputRef = useRef<HTMLInputElement>(null)
  const [modalPreset, setModalPreset] = useState<ModalPreset>(null)
  const { selectedDate, setDate: setSelectedDate, selectedCiclo, selectedCurso, setCiclo, setCurso, clear } = useScheduleFilterStore()

  const { data: config } = useQuery({ queryKey: ['config'], queryFn: getConfig })

  const { data: cursosList = [] } = useQuery({
    queryKey: ['schedule', 'cursos'],
    queryFn: getCursos,
  })

  const ciclos = useMemo(() => {
    const set = new Set(cursosList.map(extractCiclo))
    return Array.from(set).sort()
  }, [cursosList])

  const cursosFiltrados = useMemo(() => {
    if (!selectedCiclo) return cursosList
    return cursosList.filter((c) => extractCiclo(c) === selectedCiclo)
  }, [cursosList, selectedCiclo])

  const handleCicloChange = (ciclo: string) => setCiclo(ciclo)

  const { data: scheduleData = [], isLoading } = useQuery({
    queryKey: ['schedule', 'day', selectedDate, selectedCurso],
    queryFn: () => getDaySchedule(selectedDate, selectedCurso),
    enabled: !!selectedCurso,
  })

  // Indexar por tramo para búsqueda O(1)
  const scheduleByTramo = useMemo(() => {
    const map: Record<number, DayScheduleEntry> = {}
    for (const entry of scheduleData) map[entry.tramo] = entry
    return map
  }, [scheduleData])

  const confirmMutation = useMutation({
    mutationFn: confirmSubstitution,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['schedule', 'day'] }),
  })
  const rejectMutation = useMutation({
    mutationFn: rejectSubstitution,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['schedule', 'day'] }),
  })

  const ausentes = scheduleData.filter((e) => e.ausente).length

  return (
    <div className="p-6">
      {/* Cabecera */}
      <div className="mb-6">
        <div className="flex items-start justify-between">
          <h2 className="text-xl font-semibold text-gray-900">Horario del día</h2>
          <button
            onClick={() => setModalPreset({})}
            className="flex items-center gap-1.5 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 px-3 py-1.5 rounded-lg transition-colors"
            title="Registrar nueva ausencia"
          >
            <UserMinus size={15} />
            <Plus size={13} />
            Nueva ausencia
          </button>
        </div>

        {/* Navegador de fecha */}
        <div className="flex items-center gap-1 mt-2">
          <button
            onClick={() => setSelectedDate((d) => addDays(d, -1))}
            className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-100 hover:text-gray-800 transition-colors"
            title="Día anterior"
          >
            <ChevronLeft size={18} />
          </button>

          <span className="text-sm text-gray-600 capitalize font-medium min-w-60 text-center select-none">
            {formatDisplay(selectedDate)}
          </span>

          <button
            onClick={() => setSelectedDate((d) => addDays(d, 1))}
            className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-100 hover:text-gray-800 transition-colors"
            title="Día siguiente"
          >
            <ChevronRight size={18} />
          </button>

          {/* Selector de fecha con input nativo oculto */}
          <div className="relative ml-1">
            <button
              onClick={() => dateInputRef.current?.showPicker()}
              className="p-1.5 rounded-lg text-gray-400 hover:bg-gray-100 hover:text-gray-700 transition-colors"
              title="Ir a una fecha concreta"
            >
              <Calendar size={16} />
            </button>
            <input
              ref={dateInputRef}
              type="date"
              value={selectedDate}
              onChange={(e) => e.target.value && setSelectedDate(e.target.value)}
              className="absolute inset-0 opacity-0 w-full cursor-pointer"
            />
          </div>

          {selectedDate !== TODAY && (
            <button
              onClick={() => setSelectedDate(TODAY)}
              className="ml-2 text-xs text-blue-500 hover:text-blue-700 underline underline-offset-2"
            >
              Hoy
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
              {' — '}6 horas lectivas
            </span>
            {ausentes > 0 && (
              <span className="text-xs bg-red-50 text-red-700 px-2.5 py-1 rounded-full font-medium">
                {ausentes} ausencia{ausentes > 1 ? 's' : ''}
              </span>
            )}
          </div>

          {/* Tabla horario */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left px-4 py-3 font-medium text-gray-600 w-36">Hora</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Módulo / Asignatura</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600 w-24">Aula</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Titular</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600">Sustituto</th>
                  <th className="text-left px-4 py-3 font-medium text-gray-600 w-28">Estado</th>
                  <th className="px-3 py-3 w-10"></th>
                  {config?.confirmacion_requerida && (
                    <th className="px-4 py-3 w-20"></th>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {HORARIO_DIARIO.map((slot, idx) => {
                  if (slot.tipo === 'recreo') {
                    return (
                      <RecreRow
                        key={idx}
                        inicio={slot.inicio}
                        fin={slot.fin}
                        label="Recreo"
                        colSpan={config?.confirmacion_requerida ? 7 : 6}
                      />
                    )
                  }
                  // tipo === 'clase'
                  const entry = slot.tramo != null ? scheduleByTramo[slot.tramo] : undefined
                  return (
                    <ClaseRow
                      key={idx}
                      slot={slot}
                      entry={entry}
                      confirmacionRequerida={config?.confirmacion_requerida ?? false}
                      onConfirm={(id) => confirmMutation.mutate(id)}
                      onReject={(id) => rejectMutation.mutate(id)}
                      isPending={confirmMutation.isPending || rejectMutation.isPending}
                      onNewAbsence={(teacherId, tramo) => setModalPreset({ teacherId, tramo })}
                    />
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Leyenda */}
          <div className="flex items-center gap-4 mt-3 text-xs text-gray-400">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-green-400 inline-block" />
              Titular presente
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-red-400 inline-block" />
              Titular ausente
            </span>
            <span className="flex items-center gap-1">
              <Bot size={12} className="text-purple-400" />
              Propuesto por IA
            </span>
          </div>
        </>
      )}

      {modalPreset !== null && (
        <NewAbsenceModal
          defaultDate={selectedDate}
          defaultTeacherId={modalPreset.teacherId}
          defaultTramo={modalPreset.tramo}
          onClose={() => setModalPreset(null)}
        />
      )}
    </div>
  )
}

// ─── Fila de recreo / descanso ────────────────────────────────────────────────
function RecreRow({
  inicio, fin, label, colSpan, subtle = false,
}: {
  inicio: string
  fin: string
  label: string
  colSpan: number
  subtle?: boolean
}) {
  return (
    <tr className={clsx(subtle ? 'bg-gray-50/60' : 'bg-amber-50/60')}>
      <td className="px-4 py-2">
        <span className="text-xs text-gray-500 font-medium">{inicio} – {fin}</span>
      </td>
      <td colSpan={colSpan} className="px-4 py-2">
        <span className={clsx(
          'flex items-center gap-1.5 text-xs font-medium',
          subtle ? 'text-gray-400' : 'text-amber-600'
        )}>
          <Coffee size={13} />
          {label}
        </span>
      </td>
    </tr>
  )
}

// ─── Fila de clase ────────────────────────────────────────────────────────────
function ClaseRow({
  slot,
  entry,
  confirmacionRequerida,
  onConfirm,
  onReject,
  isPending,
  onNewAbsence,
}: {
  slot: HorarioSlot
  entry: DayScheduleEntry | undefined
  confirmacionRequerida: boolean
  onConfirm: (id: number) => void
  onReject: (id: number) => void
  isPending: boolean
  onNewAbsence: (teacherId: number, tramo: number) => void
}) {
  const ausente = entry?.ausente ?? false

  return (
    <tr className={clsx(
      'transition-colors',
      ausente ? 'bg-red-50/40 hover:bg-red-50/60' : 'hover:bg-gray-50'
    )}>
      {/* Hora */}
      <td className="px-4 py-3">
        <div className="flex flex-col">
          <span className="text-xs text-gray-500 font-medium">{slot.inicio} – {slot.fin}</span>
          <span className="text-xs text-gray-400">{slot.tramo}ª hora</span>
        </div>
      </td>

      {/* Módulo */}
      <td className="px-4 py-3">
        {entry?.asignatura ? (
          <span className={clsx(
            'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-sm font-medium',
            getModuloColor(entry.asignatura).bg,
            getModuloColor(entry.asignatura).text,
          )}>
            <BookOpen size={13} className="shrink-0" />
            {entry.asignatura}
          </span>
        ) : (
          <span className="text-gray-300 text-xs italic">Sin módulo asignado</span>
        )}
      </td>

      {/* Aula */}
      <td className="px-4 py-3 text-gray-600">
        {entry?.aula ?? <span className="text-gray-300">—</span>}
      </td>

      {/* Titular */}
      <td className="px-4 py-3">
        {entry?.titular ? (
          <span className="flex items-center gap-2 flex-wrap">
            <span className={clsx(
              'w-2 h-2 rounded-full shrink-0',
              ausente ? 'bg-red-400' : 'bg-green-400'
            )} />
            <span className={clsx(ausente ? 'text-gray-400 line-through' : 'text-gray-800')}>
              {entry.titular.nombre}
            </span>
            {ausente && entry.motivo_ausencia && (
              <span className="text-xs text-red-500 bg-red-50 px-1.5 py-0.5 rounded">
                {entry.motivo_ausencia}
              </span>
            )}
          </span>
        ) : (
          <span className="text-gray-300 text-xs italic">Sin profesor asignado</span>
        )}
      </td>

      {/* Sustituto */}
      <td className="px-4 py-3">
        {ausente ? (
          entry?.sustituto ? (
            <span className="flex items-center gap-1.5 text-gray-800">
              {entry.ai_propuesta && (
                <Bot size={14} className="text-purple-500 shrink-0" title="Propuesto por IA" />
              )}
              {entry.sustituto.nombre}
            </span>
          ) : (
            <span className="text-xs text-orange-600 bg-orange-50 px-2 py-0.5 rounded font-medium">
              Sin cubrir
            </span>
          )
        ) : (
          <span className="text-gray-300">—</span>
        )}
      </td>

      {/* Estado */}
      <td className="px-4 py-3">
        {entry?.sustitucion_estado ? (
          <span className={clsx(
            'px-2 py-0.5 rounded-full text-xs font-medium',
            SUSTITUCION_COLORS[entry.sustitucion_estado] ?? 'bg-gray-100 text-gray-700'
          )}>
            {SUSTITUCION_LABELS[entry.sustitucion_estado] ?? entry.sustitucion_estado}
          </span>
        ) : ausente ? (
          <span className="text-xs text-orange-500">Pendiente</span>
        ) : null}
      </td>

      {/* Registrar ausencia en este tramo */}
      <td className="px-3 py-3">
        {!ausente && entry?.titular && (
          <button
            onClick={() => onNewAbsence(entry.titular!.id, slot.tramo!)}
            className="p-1.5 rounded-lg text-gray-300 hover:text-orange-500 hover:bg-orange-50 transition-colors"
            title={`Registrar ausencia — ${entry.titular.nombre}`}
          >
            <UserMinus size={15} />
          </button>
        )}
      </td>

      {/* Confirmar / Rechazar */}
      {confirmacionRequerida && (
        <td className="px-4 py-3">
          {entry?.sustitucion_id && entry.sustitucion_estado === 'propuesta' && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => onConfirm(entry.sustitucion_id!)}
                disabled={isPending}
                className="p-1.5 rounded-lg bg-green-50 text-green-600 hover:bg-green-100 transition-colors"
                title="Confirmar"
              >
                <Check size={14} />
              </button>
              <button
                onClick={() => onReject(entry.sustitucion_id!)}
                disabled={isPending}
                className="p-1.5 rounded-lg bg-red-50 text-red-600 hover:bg-red-100 transition-colors"
                title="Rechazar"
              >
                <X size={14} />
              </button>
            </div>
          )}
        </td>
      )}
    </tr>
  )
}

// ─── Estado vacío ─────────────────────────────────────────────────────────────
function EmptySelection() {
  return (
    <div className="flex flex-col items-center justify-center h-64 text-gray-400">
      <BookOpen size={40} className="mb-3 text-gray-300" />
      <p className="text-sm font-medium text-gray-500">Selecciona una clase para ver su horario</p>
      <p className="text-xs mt-1">Elige primero el ciclo y luego el curso / clase</p>
    </div>
  )
}
