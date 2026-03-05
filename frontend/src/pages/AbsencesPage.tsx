import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getAbsences, deleteAbsence } from '../api/absences'
import { Plus, Trash2, Bot } from 'lucide-react'
import clsx from 'clsx'
import NewAbsenceModal from '../components/NewAbsenceModal'

export default function AbsencesPage() {
  const [showModal, setShowModal] = useState(false)
  const queryClient = useQueryClient()

  const { data: absences = [], isLoading } = useQuery({
    queryKey: ['absences'],
    queryFn: getAbsences,
  })

  const deleteMutation = useMutation({
    mutationFn: deleteAbsence,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['absences'] }),
  })

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Ausencias</h2>
          <p className="text-sm text-gray-500 mt-0.5">
            {absences.length} registradas
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          <Plus size={16} />
          Nueva ausencia
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-48 text-gray-500">Cargando...</div>
      ) : absences.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-48 text-gray-400">
          <p className="text-sm">No hay ausencias registradas</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left px-4 py-3 font-medium text-gray-600">Profesor</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Desde</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Hasta</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Motivo</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600">Estado</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {absences.map((a) => (
                <tr key={a.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900">{a.teacher_nombre}</td>
                  <td className="px-4 py-3 text-gray-600">{formatDate(a.fecha_inicio)}</td>
                  <td className="px-4 py-3 text-gray-600">{formatDate(a.fecha_fin)}</td>
                  <td className="px-4 py-3 text-gray-600">{a.motivo ?? '—'}</td>
                  <td className="px-4 py-3">
                    <span className={clsx(
                      'flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium w-fit',
                      a.estado === 'procesada' ? 'bg-green-100 text-green-800' :
                      a.estado === 'pendiente' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    )}>
                      {a.estado === 'procesada' && <Bot size={12} />}
                      {a.estado}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {a.estado === 'pendiente' && (
                      <button
                        onClick={() => deleteMutation.mutate(a.id)}
                        className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <NewAbsenceModal onClose={() => setShowModal(false)} />
      )}
    </div>
  )
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('es-ES', {
    day: '2-digit', month: '2-digit', year: 'numeric',
  })
}
