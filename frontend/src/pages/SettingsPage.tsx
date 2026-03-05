import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getConfig, updateConfig } from '../api/config'
import { useForm } from 'react-hook-form'
import { useEffect } from 'react'
import { Save } from 'lucide-react'

interface FormData {
  nombre_centro: string
  confirmacion_requerida: boolean
  max_sustituciones_diarias_por_profesor: number
}

export default function SettingsPage() {
  const queryClient = useQueryClient()

  const { data: config, isLoading } = useQuery({
    queryKey: ['config'],
    queryFn: getConfig,
  })

  const { register, handleSubmit, reset, watch, formState: { isDirty } } = useForm<FormData>()

  useEffect(() => {
    if (config) reset(config)
  }, [config, reset])

  const mutation = useMutation({
    mutationFn: updateConfig,
    onSuccess: (data) => {
      queryClient.setQueryData(['config'], data)
      reset(data)
    },
  })

  const confirmacionRequerida = watch('confirmacion_requerida')

  if (isLoading) {
    return <div className="p-6 text-gray-500">Cargando...</div>
  }

  return (
    <div className="p-6 max-w-xl">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Configuración</h2>
        <p className="text-sm text-gray-500 mt-0.5">Ajustes del centro educativo</p>
      </div>

      <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-6">
        <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
          <h3 className="font-medium text-gray-900">Centro</h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Nombre del centro
            </label>
            <input
              type="text"
              {...register('nombre_centro')}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
          <h3 className="font-medium text-gray-900">Sustituciones</h3>

          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-700">Confirmación manual requerida</p>
              <p className="text-xs text-gray-500 mt-0.5">
                {confirmacionRequerida
                  ? 'La jefatura debe aprobar cada propuesta de la IA'
                  : 'La IA asigna sustituciones automáticamente'}
              </p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                {...register('confirmacion_requerida')}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Máximo sustituciones diarias por profesor
            </label>
            <input
              type="number"
              min={1}
              max={10}
              {...register('max_sustituciones_diarias_por_profesor', { valueAsNumber: true })}
              className="w-32 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {mutation.isSuccess && (
          <p className="text-green-600 text-sm">Configuración guardada correctamente</p>
        )}

        <button
          type="submit"
          disabled={!isDirty || mutation.isPending}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white font-medium px-4 py-2 rounded-lg text-sm transition-colors"
        >
          <Save size={16} />
          {mutation.isPending ? 'Guardando...' : 'Guardar cambios'}
        </button>
      </form>
    </div>
  )
}
