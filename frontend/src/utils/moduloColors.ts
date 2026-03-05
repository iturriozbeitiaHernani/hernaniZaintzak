/**
 * Asigna un color determinista a cada nombre de módulo/asignatura.
 * El mismo módulo siempre recibe el mismo color, independientemente del grupo.
 */

// Paleta: [fondo claro, texto oscuro, borde]
const PALETTE: [string, string, string][] = [
  ['bg-blue-100',   'text-blue-800',   'border-blue-300'],
  ['bg-emerald-100','text-emerald-800', 'border-emerald-300'],
  ['bg-violet-100', 'text-violet-800',  'border-violet-300'],
  ['bg-amber-100',  'text-amber-800',   'border-amber-300'],
  ['bg-rose-100',   'text-rose-800',    'border-rose-300'],
  ['bg-cyan-100',   'text-cyan-800',    'border-cyan-300'],
  ['bg-orange-100', 'text-orange-800',  'border-orange-300'],
  ['bg-teal-100',   'text-teal-800',    'border-teal-300'],
  ['bg-pink-100',   'text-pink-800',    'border-pink-300'],
  ['bg-indigo-100', 'text-indigo-800',  'border-indigo-300'],
  ['bg-lime-100',   'text-lime-800',    'border-lime-300'],
  ['bg-fuchsia-100','text-fuchsia-800', 'border-fuchsia-300'],
]

function hashModulo(name: string): number {
  let h = 0
  for (let i = 0; i < name.length; i++) {
    h = (h * 31 + name.charCodeAt(i)) >>> 0
  }
  return h % PALETTE.length
}

export interface ModuloColor {
  bg: string     // e.g. 'bg-blue-100'
  text: string   // e.g. 'text-blue-800'
  border: string // e.g. 'border-blue-300'
}

export function getModuloColor(asignatura: string | null | undefined): ModuloColor {
  if (!asignatura) return { bg: 'bg-gray-100', text: 'text-gray-500', border: 'border-gray-200' }
  const [bg, text, border] = PALETTE[hashModulo(asignatura.toUpperCase().trim())]
  return { bg, text, border }
}
