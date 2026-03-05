import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm, useWatch } from 'react-hook-form'
import { X, Bot, Check, ChevronLeft, AlertCircle, Loader2, Star } from 'lucide-react'
import clsx from 'clsx'
import {
  createAbsence,
  previewAbsence,
  type CreateAbsenceRequest,
  type AbsencePreviewResponse,
  type CandidatoPropuesto,
  type SustitutoElegido,
} from '../api/absences'
import { getTeachers, getTeacherSchedule, type Teacher } from '../api/teachers'
import { getModuloColor } from '../utils/moduloColors'

// Horas de cada tramo del centro
const TRAMO_HORAS: Record<number, string> = {
  1: '08:00–09:00',
  2: '09:00–10:00',
  3: '10:00–11:00',
  4: '11:25–12:25',
  5: '12:25–13:25',
  6: '13:25–14:25',
}

/** Convierte YYYY-MM-DD al día de la semana Python (0=Lun … 4=Vie). */
function toPythonWeekday(dateStr: string): number {
  const [y, m, d] = dateStr.split('-').map(Number)
  return (new Date(y, m - 1, d).getDay() + 6) % 7
}

function formatDateEs(dateStr: string): string {
  const [y, m, d] = dateStr.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString('es-ES', {
    weekday: 'long', day: 'numeric', month: 'long',
  })
}

interface FormValues {
  teacher_id: number
  fecha_inicio: string
  fecha_fin: string
  motivo: string
}

interface Props {
  onClose: () => void
  defaultDate?: string
  defaultTeacherId?: number
  defaultTramo?: number
}

// ── Componente de un candidato ────────────────────────────────────────────────
function CandidatoCard({
  candidato,
  selected,
  onSelect,
}: {
  candidato: CandidatoPropuesto
  selected: boolean
  onSelect: () => void
}) {
  const [expanded, setExpanded] = useState(false)
  const bars = Math.round((candidato.puntuacion / 10) * 5)

  return (
    <button
      type="button"
      onClick={onSelect}
      className={clsx(
        'w-full text-left rounded-xl border p-3 transition-all',
        selected
          ? 'border-blue-400 bg-blue-50 ring-1 ring-blue-300'
          : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'
      )}
    >
      <div className="flex items-center gap-2">
        {/* Selector */}
        <span className={clsx(
          'w-4 h-4 rounded-full border-2 shrink-0 flex items-center justify-center',
          selected ? 'border-blue-500 bg-blue-500' : 'border-gray-300'
        )}>
          {selected && <span className="w-1.5 h-1.5 rounded-full bg-white" />}
        </span>

        {/* Nombre */}
        <span className={clsx(
          'text-sm font-medium flex-1',
          selected ? 'text-blue-900' : 'text-gray-800'
        )}>
          {candidato.nombre}
        </span>

        {/* Puntuación en barras */}
        <span className="flex gap-0.5 shrink-0" title={`${candidato.puntuacion.toFixed(1)}/10`}>
          {Array.from({ length: 5 }).map((_, i) => (
            <span
              key={i}
              className={clsx(
                'w-1.5 h-4 rounded-sm',
                i < bars
                  ? selected ? 'bg-blue-500' : 'bg-gray-400'
                  : 'bg-gray-200'
              )}
            />
          ))}
        </span>

        {/* Confianza IA */}
        <Bot
          size={13}
          className={clsx(
            'shrink-0',
            candidato.confianza >= 0.7 ? 'text-purple-500' : 'text-gray-300'
          )}
          title={`Confianza IA: ${Math.round(candidato.confianza * 100)}%`}
        />
      </div>

      {/* Razón principal */}
      <p className="text-xs text-gray-500 mt-1 ml-6 leading-relaxed">
        {candidato.razon_principal}
      </p>

      {/* Pros/contras expandibles */}
      {(candidato.pros.length > 0 || candidato.contras.length > 0) && (
        <button
          type="button"
          onClick={(e) => { e.stopPropagation(); setExpanded(v => !v) }}
          className="ml-6 mt-1 text-xs text-blue-500 hover:underline"
        >
          {expanded ? 'Ocultar detalles' : 'Ver detalles'}
        </button>
      )}
      {expanded && (
        <div className="ml-6 mt-2 space-y-1">
          {candidato.pros.map((p, i) => (
            <p key={i} className="text-xs text-green-700 flex gap-1">
              <span className="shrink-0">+</span>{p}
            </p>
          ))}
          {candidato.contras.map((c, i) => (
            <p key={i} className="text-xs text-red-600 flex gap-1">
              <span className="shrink-0">−</span>{c}
            </p>
          ))}
        </div>
      )}
    </button>
  )
}

// ── Paso 2 — revisión de propuestas ──────────────────────────────────────────
function PreviewStep({
  preview,
  teacherName,
  absentTeacherId,
  fecha,
  teachers,
  onBack,
  onConfirm,
  isPending,
}: {
  preview: AbsencePreviewResponse
  teacherName: string
  absentTeacherId: number
  fecha: string
  teachers: Teacher[]
  onBack: () => void
  onConfirm: (elegidos: SustitutoElegido[]) => void
  isPending: boolean
}) {
  type TramoMode = 'ia' | 'manual'

  // selectedSubstitutes: tramo_horario → candidato elegido (null = sin sustituto)
  const [selected, setSelected] = useState<Record<number, CandidatoPropuesto | null>>(() => {
    const init: Record<number, CandidatoPropuesto | null> = {}
    for (const tramo of preview.tramos) {
      init[tramo.tramo_horario] = tramo.propuestas[0] ?? null
    }
    return init
  })

  // modo por tramo: 'ia' (por defecto) o 'manual'
  const [modes, setModes] = useState<Record<number, TramoMode>>(() => {
    const init: Record<number, TramoMode> = {}
    for (const tramo of preview.tramos) {
      init[tramo.tramo_horario] = 'ia'
    }
    return init
  })

  // selección manual por tramo: tramo_horario → teacher_id | null
  const [manualSel, setManualSel] = useState<Record<number, number | null>>(() => {
    const init: Record<number, number | null> = {}
    for (const tramo of preview.tramos) {
      init[tramo.tramo_horario] = null
    }
    return init
  })

  const setMode = (tramo: number, mode: TramoMode) => {
    setModes(prev => ({ ...prev, [tramo]: mode }))
  }

  const activeTeachersFiltered = teachers.filter(
    t => t.activo && t.id !== absentTeacherId
  )

  const isTramoAssigned = (tramoNum: number): boolean => {
    if (modes[tramoNum] === 'manual') return manualSel[tramoNum] != null
    return selected[tramoNum] != null
  }

  const handleConfirm = () => {
    const elegidos: SustitutoElegido[] = []
    for (const tramo of preview.tramos) {
      const mode = modes[tramo.tramo_horario]
      if (mode === 'ia') {
        const candidato = selected[tramo.tramo_horario]
        if (candidato) {
          elegidos.push({
            tramo_horario: tramo.tramo_horario,
            substitute_teacher_id: candidato.teacher_id,
            razon_principal: candidato.razon_principal,
            ai_confianza: candidato.confianza,
          })
        }
      } else {
        const teacherId = manualSel[tramo.tramo_horario]
        if (teacherId != null) {
          elegidos.push({
            tramo_horario: tramo.tramo_horario,
            substitute_teacher_id: teacherId,
          })
        }
      }
    }
    onConfirm(elegidos)
  }

  const totalTramos = preview.tramos.length
  const tramosConSustituto = preview.tramos.filter(t => isTramoAssigned(t.tramo_horario)).length

  return (
    <div className="flex flex-col min-h-0">
      {/* Sub-cabecera */}
      <div className="px-6 py-3 bg-gray-50 border-b border-gray-100">
        <p className="text-sm font-medium text-gray-800">{teacherName}</p>
        <p className="text-xs text-gray-500 capitalize">{formatDateEs(fecha)}</p>
        <p className="text-xs text-gray-400 mt-0.5">
          {tramosConSustituto}/{totalTramos} tramos con sustituto asignado
        </p>
      </div>

      {/* Lista de tramos */}
      <div className="overflow-y-auto flex-1 p-4 space-y-4">
        {preview.tramos.map((tramo) => {
          const color = getModuloColor(tramo.asignatura)
          const mode = modes[tramo.tramo_horario]

          return (
            <div key={tramo.tramo_horario}>
              {/* Cabecera del tramo */}
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs font-semibold text-gray-500 w-5">
                  {tramo.tramo_horario}ª
                </span>
                <span className="text-xs text-gray-400">
                  {TRAMO_HORAS[tramo.tramo_horario] ?? ''}
                </span>
                <span className={clsx(
                  'text-xs font-medium px-2 py-0.5 rounded-full',
                  color.bg, color.text,
                )}>
                  {tramo.asignatura}
                </span>
                {tramo.aula && (
                  <span className="text-xs text-gray-400">{tramo.aula}</span>
                )}
              </div>

              {/* Toggle modo IA / Manual */}
              <div className="flex pl-7 mb-2">
                <div className="inline-flex rounded-lg border border-gray-200 bg-gray-50 p-0.5 gap-0.5">
                  <button
                    type="button"
                    onClick={() => setMode(tramo.tramo_horario, 'ia')}
                    className={clsx(
                      'flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium transition-colors',
                      mode === 'ia'
                        ? 'bg-white text-purple-700 shadow-sm'
                        : 'text-gray-500 hover:text-gray-700'
                    )}
                  >
                    <Bot size={11} />
                    IA recomienda
                  </button>
                  <button
                    type="button"
                    onClick={() => setMode(tramo.tramo_horario, 'manual')}
                    className={clsx(
                      'flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium transition-colors',
                      mode === 'manual'
                        ? 'bg-white text-blue-700 shadow-sm'
                        : 'text-gray-500 hover:text-gray-700'
                    )}
                  >
                    Manual
                  </button>
                </div>
              </div>

              {/* Modo IA: candidatos */}
              {mode === 'ia' && (
                tramo.propuestas.length > 0 ? (
                  <div className="space-y-1.5 pl-7">
                    {tramo.propuestas.map((candidato) => (
                      <CandidatoCard
                        key={candidato.teacher_id}
                        candidato={candidato}
                        selected={selected[tramo.tramo_horario]?.teacher_id === candidato.teacher_id}
                        onSelect={() =>
                          setSelected(prev => ({
                            ...prev,
                            [tramo.tramo_horario]: candidato,
                          }))
                        }
                      />
                    ))}
                    {/* Opción de dejar sin cubrir */}
                    <button
                      type="button"
                      onClick={() =>
                        setSelected(prev => ({ ...prev, [tramo.tramo_horario]: null }))
                      }
                      className={clsx(
                        'w-full text-left text-xs px-3 py-1.5 rounded-lg border transition-colors',
                        selected[tramo.tramo_horario] == null
                          ? 'border-red-300 bg-red-50 text-red-700'
                          : 'border-gray-200 text-gray-400 hover:bg-gray-50'
                      )}
                    >
                      Dejar sin cubrir este tramo
                    </button>
                  </div>
                ) : (
                  <div className="pl-7 flex items-center gap-1.5 text-xs text-amber-700 bg-amber-50 rounded-lg px-3 py-2">
                    <AlertCircle size={13} />
                    Sin profesores disponibles para este tramo
                  </div>
                )
              )}

              {/* Modo Manual: desplegable */}
              {mode === 'manual' && (
                <div className="pl-7 space-y-1.5">
                  <select
                    value={manualSel[tramo.tramo_horario] ?? ''}
                    onChange={(e) =>
                      setManualSel(prev => ({
                        ...prev,
                        [tramo.tramo_horario]: e.target.value ? Number(e.target.value) : null,
                      }))
                    }
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
                  >
                    <option value="">— Sin sustituto —</option>
                    {activeTeachersFiltered.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.nombre} {t.apellidos}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-400">
                    Selecciona cualquier profesor activo del centro
                  </p>
                </div>
              )}

              {/* Advertencias del tramo */}
              {tramo.advertencias.length > 0 && (
                <div className="pl-7 mt-1 space-y-0.5">
                  {tramo.advertencias.map((adv, i) => (
                    <p key={i} className="text-xs text-amber-600 flex gap-1">
                      <AlertCircle size={11} className="shrink-0 mt-0.5" />
                      {adv}
                    </p>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Acciones */}
      <div className="px-6 py-4 border-t border-gray-200 flex gap-3 shrink-0">
        <button
          type="button"
          onClick={onBack}
          className="flex items-center gap-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-sm hover:bg-gray-50 transition-colors"
        >
          <ChevronLeft size={15} />
          Volver
        </button>
        <button
          type="button"
          onClick={handleConfirm}
          disabled={isPending}
          className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium py-2 rounded-lg text-sm transition-colors flex items-center justify-center gap-2"
        >
          {isPending ? (
            <>
              <Loader2 size={15} className="animate-spin" />
              Guardando...
            </>
          ) : (
            <>
              <Check size={15} />
              Confirmar ausencia
            </>
          )}
        </button>
      </div>
    </div>
  )
}

// ── Modal principal ───────────────────────────────────────────────────────────
export default function NewAbsenceModal({ onClose, defaultDate, defaultTeacherId, defaultTramo }: Props) {
  const queryClient = useQueryClient()

  const [step, setStep] = useState<'form' | 'preview'>('form')
  const [previewData, setPreviewData] = useState<AbsencePreviewResponse | null>(null)
  const [savedFormValues, setSavedFormValues] = useState<FormValues | null>(null)

  const [selectedTramos, setSelectedTramos] = useState<number[]>(
    defaultTramo != null ? [defaultTramo] : []
  )

  const { data: teachers = [] } = useQuery({
    queryKey: ['teachers'],
    queryFn: getTeachers,
  })

  const { register, handleSubmit, formState: { errors }, control } = useForm<FormValues>({
    defaultValues: {
      teacher_id: defaultTeacherId,
      fecha_inicio: defaultDate,
      fecha_fin: defaultDate,
      motivo: '',
    },
  })

  const teacherId = useWatch({ control, name: 'teacher_id' })
  const fechaInicio = useWatch({ control, name: 'fecha_inicio' })
  const fechaFin = useWatch({ control, name: 'fecha_fin' })

  const isSingleDay = !!fechaInicio && fechaInicio === fechaFin

  // Reset tramos cuando cambia el profesor
  useEffect(() => {
    setSelectedTramos(defaultTramo != null ? [defaultTramo] : [])
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [teacherId])

  const { data: teacherSchedule = [], isFetching: loadingSchedule } = useQuery({
    queryKey: ['teacher-schedule', teacherId],
    queryFn: () => getTeacherSchedule(Number(teacherId)),
    enabled: !!teacherId && Number(teacherId) > 0,
  })

  const tramosDelDia = isSingleDay && fechaInicio
    ? teacherSchedule
        .filter(s => s.dia_semana === toPythonWeekday(fechaInicio) && !s.es_libre)
        .sort((a, b) => a.tramo_horario - b.tramo_horario)
    : []

  const toggleTramo = (tramo: number) => {
    setSelectedTramos(prev =>
      prev.includes(tramo)
        ? prev.filter(t => t !== tramo)
        : [...prev, tramo].sort((a, b) => a - b)
    )
  }

  // Mutation: preview (llamada sincrónica a la IA, puede tardar)
  const previewMutation = useMutation({
    mutationFn: previewAbsence,
    onSuccess: (data) => {
      setPreviewData(data)
      setStep('preview')
    },
  })

  // Mutation: crear ausencia definitiva
  const createMutation = useMutation({
    mutationFn: createAbsence,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['absences'] })
      queryClient.invalidateQueries({ queryKey: ['schedule'] })
      onClose()
    },
  })

  // Paso 1 → 2: generar preview
  const onStep1Submit = (data: FormValues) => {
    setSavedFormValues(data)
    previewMutation.mutate({
      teacher_id: Number(data.teacher_id),
      fecha: data.fecha_inicio,
      tramos_afectados: isSingleDay && selectedTramos.length > 0 ? selectedTramos : undefined,
    })
  }

  // Paso 2 → confirmar: crear ausencia con sustitutos elegidos
  const onConfirm = (elegidos: SustitutoElegido[]) => {
    if (!savedFormValues) return
    const payload: CreateAbsenceRequest = {
      teacher_id: Number(savedFormValues.teacher_id),
      fecha_inicio: savedFormValues.fecha_inicio,
      fecha_fin: savedFormValues.fecha_fin,
      motivo: savedFormValues.motivo || undefined,
      tramos_afectados: isSingleDay && selectedTramos.length > 0 ? selectedTramos : undefined,
      sustitutos_elegidos: elegidos.length > 0 ? elegidos : undefined,
    }
    createMutation.mutate(payload)
  }

  const teacherName = teachers.find(t => t.id === Number(teacherId))
    ? `${teachers.find(t => t.id === Number(teacherId))!.nombre} ${teachers.find(t => t.id === Number(teacherId))!.apellidos}`
    : ''

  const activeTeachers = teachers.filter(t => t.activo)

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md max-h-[90vh] flex flex-col">
        {/* Cabecera */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 shrink-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-gray-900">Nueva ausencia</h3>
            {step === 'preview' && (
              <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full flex items-center gap-1">
                <Bot size={11} />
                Propuesta IA
              </span>
            )}
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={20} />
          </button>
        </div>

        {/* ── Paso 1: Formulario ─────────────────────────────────────────────── */}
        {step === 'form' && (
          <form onSubmit={handleSubmit(onStep1Submit)} className="p-6 space-y-4 overflow-y-auto">
            {/* Profesor */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Profesor</label>
              <select
                {...register('teacher_id', { required: 'Selecciona un profesor', valueAsNumber: true })}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Seleccionar...</option>
                {activeTeachers.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.nombre} {t.apellidos}
                  </option>
                ))}
              </select>
              {errors.teacher_id && (
                <p className="text-red-500 text-xs mt-1">{errors.teacher_id.message}</p>
              )}
            </div>

            {/* Fechas */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Fecha inicio</label>
                <input
                  type="date"
                  {...register('fecha_inicio', { required: 'Obligatorio' })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                {errors.fecha_inicio && (
                  <p className="text-red-500 text-xs mt-1">{errors.fecha_inicio.message}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Fecha fin</label>
                <input
                  type="date"
                  {...register('fecha_fin', { required: 'Obligatorio' })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                {errors.fecha_fin && (
                  <p className="text-red-500 text-xs mt-1">{errors.fecha_fin.message}</p>
                )}
              </div>
            </div>

            {/* Tramos — solo en ausencia de un día con profesor seleccionado */}
            {isSingleDay && Number(teacherId) > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tramos afectados
                  <span className="ml-2 text-xs font-normal text-gray-400">
                    {loadingSchedule
                      ? 'Cargando...'
                      : tramosDelDia.length === 0
                      ? '(sin docencia este día)'
                      : selectedTramos.length === 0
                      ? '— sin selección = todos'
                      : `${selectedTramos.length} seleccionado${selectedTramos.length > 1 ? 's' : ''}`}
                  </span>
                </label>

                {tramosDelDia.length > 0 ? (
                  <div className="space-y-1.5">
                    {tramosDelDia.map((slot) => {
                      const checked = selectedTramos.includes(slot.tramo_horario)
                      const color = getModuloColor(slot.asignatura)
                      return (
                        <button
                          key={slot.tramo_horario}
                          type="button"
                          onClick={() => toggleTramo(slot.tramo_horario)}
                          className={clsx(
                            'w-full flex items-center gap-3 px-3 py-2 rounded-lg border text-left transition-colors',
                            checked
                              ? 'border-blue-300 bg-blue-50'
                              : 'border-gray-200 bg-white hover:bg-gray-50'
                          )}
                        >
                          <span className={clsx(
                            'w-4 h-4 rounded border shrink-0 flex items-center justify-center',
                            checked ? 'bg-blue-600 border-blue-600' : 'border-gray-300'
                          )}>
                            {checked && <Check size={10} className="text-white" strokeWidth={3} />}
                          </span>
                          <span className="text-xs text-gray-400 shrink-0 w-24">
                            {slot.tramo_horario}ª · {TRAMO_HORAS[slot.tramo_horario] ?? ''}
                          </span>
                          <span className={clsx(
                            'text-xs font-medium px-1.5 py-0.5 rounded truncate',
                            color.bg, color.text,
                          )}>
                            {slot.asignatura ?? '—'}
                          </span>
                          {slot.aula && (
                            <span className="text-xs text-gray-400 ml-auto shrink-0">{slot.aula}</span>
                          )}
                        </button>
                      )
                    })}
                  </div>
                ) : !loadingSchedule && (
                  <p className="text-xs text-gray-400 italic py-1">
                    Sin docencia este día (fin de semana o sin horario configurado).
                  </p>
                )}
              </div>
            )}

            {/* Motivo */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Motivo <span className="text-gray-400">(opcional)</span>
              </label>
              <input
                type="text"
                {...register('motivo')}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enfermedad, formación..."
              />
            </div>

            {/* Estado carga preview */}
            {previewMutation.isPending && (
              <div className="flex items-center gap-2 text-sm text-purple-700 bg-purple-50 px-3 py-3 rounded-lg">
                <Loader2 size={16} className="animate-spin shrink-0" />
                <span>
                  <span className="font-medium">Consultando a la IA...</span>
                  <span className="text-purple-500 block text-xs mt-0.5">
                    Analizando disponibilidad y generando propuestas. Puede tardar unos segundos.
                  </span>
                </span>
              </div>
            )}

            {previewMutation.isError && (
              <div className="flex items-center gap-2 text-sm text-red-700 bg-red-50 px-3 py-2 rounded-lg">
                <AlertCircle size={15} />
                Error al generar propuestas. Inténtalo de nuevo.
              </div>
            )}

            {/* Acciones */}
            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 border border-gray-300 text-gray-700 font-medium py-2 rounded-lg text-sm hover:bg-gray-50 transition-colors"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={previewMutation.isPending}
                className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium py-2 rounded-lg text-sm transition-colors flex items-center justify-center gap-2"
              >
                {previewMutation.isPending ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    Buscando...
                  </>
                ) : (
                  <>
                    <Star size={14} />
                    Buscar sustituto
                  </>
                )}
              </button>
            </div>
          </form>
        )}

        {/* ── Paso 2: Revisión de propuestas ─────────────────────────────────── */}
        {step === 'preview' && previewData && (
          <PreviewStep
            preview={previewData}
            teacherName={teacherName}
            absentTeacherId={Number(savedFormValues?.teacher_id)}
            fecha={savedFormValues?.fecha_inicio ?? ''}
            teachers={activeTeachers}
            onBack={() => setStep('form')}
            onConfirm={onConfirm}
            isPending={createMutation.isPending}
          />
        )}

        {/* Error al guardar */}
        {createMutation.isError && step === 'preview' && (
          <div className="px-6 pb-4 shrink-0">
            <p className="text-xs text-red-600 bg-red-50 rounded-lg px-3 py-2">
              Error al guardar la ausencia. Comprueba los datos e inténtalo de nuevo.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
