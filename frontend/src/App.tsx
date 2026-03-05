import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import PrivateRoute from './components/PrivateRoute'
import LoginPage from './pages/LoginPage'
import TodayPage from './pages/TodayPage'
import WeekPage from './pages/WeekPage'
import AbsencesPage from './pages/AbsencesPage'
import SettingsPage from './pages/SettingsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route element={<PrivateRoute />}>
          <Route element={<Layout />}>
            <Route path="/today" element={<TodayPage />} />
            <Route path="/week" element={<WeekPage />} />
            <Route path="/absences" element={<AbsencesPage />} />
            <Route
              path="/settings"
              element={<PrivateRoute requireAdmin><SettingsPage /></PrivateRoute>}
            />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/today" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
