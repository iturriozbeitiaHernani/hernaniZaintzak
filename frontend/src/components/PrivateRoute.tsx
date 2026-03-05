import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

interface Props {
  children?: React.ReactNode
  requireAdmin?: boolean
}

export default function PrivateRoute({ children, requireAdmin = false }: Props) {
  const { isAuthenticated, user } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (requireAdmin && user?.rol !== 'admin') {
    return <Navigate to="/today" replace />
  }

  return children ? <>{children}</> : <Outlet />
}
