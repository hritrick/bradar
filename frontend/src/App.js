import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider, useAuth } from './lib/AuthContext';
import AppShell from './components/layout/AppShell';
import Login from './pages/Login';
import ForceReset from './pages/ForceReset';
import Dashboard from './pages/Dashboard';
import Businesses from './pages/Businesses';
import BusinessDetail from './pages/BusinessDetail';
import NewBusiness from './pages/NewBusiness';
import UploadCSV from './pages/UploadCSV';
import Discovery from './pages/Discovery';
import Reports from './pages/Reports';
import ReportDetail from './pages/ReportDetail';
import Preferences from './pages/Preferences';
import AdminUsers from './pages/AdminUsers';
import AdminSettings from './pages/AdminSettings';
import AdminAuditLogs from './pages/AdminAuditLogs';
import AdminScheduler from './pages/AdminScheduler';
import './App.css';

function RequireAuth({ children, roles }) {
    const { user } = useAuth();
    if (!user) return <Navigate to="/login" replace />;
    if (user.force_password_reset) return <Navigate to="/force-reset" replace />;
    if (roles && !roles.includes(user.role)) return <Navigate to="/dashboard" replace />;
    return children;
}

function Shell({ children }) {
    return (
        <RequireAuth>
            <AppShell>{children}</AppShell>
        </RequireAuth>
    );
}

export default function App() {
    return (
        <AuthProvider>
            <Toaster theme="dark" position="top-right" toastOptions={{ style: { background: 'hsl(240 6% 9%)', color: 'hsl(40 20% 96%)', border: '1px solid hsl(240 6% 14%)' } }} />
            <BrowserRouter>
                <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route path="/force-reset" element={<RequireAuthForceReset><ForceReset /></RequireAuthForceReset>} />
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    <Route path="/dashboard" element={<Shell><Dashboard /></Shell>} />
                    <Route path="/businesses" element={<Shell><Businesses /></Shell>} />
                    <Route path="/businesses/new" element={<Shell><NewBusiness /></Shell>} />
                    <Route path="/businesses/upload" element={<Shell><UploadCSV /></Shell>} />
                    <Route path="/businesses/:id" element={<Shell><BusinessDetail /></Shell>} />
                    <Route path="/discovery" element={<Shell><Discovery /></Shell>} />
                    <Route path="/reports" element={<Shell><Reports /></Shell>} />
                    <Route path="/reports/:id" element={<Shell><ReportDetail /></Shell>} />
                    <Route path="/preferences" element={<Shell><Preferences /></Shell>} />
                    <Route path="/admin/users" element={<RequireAuth roles={['Admin']}><AppShell><AdminUsers /></AppShell></RequireAuth>} />
                    <Route path="/admin/settings" element={<RequireAuth roles={['Admin']}><AppShell><AdminSettings /></AppShell></RequireAuth>} />
                    <Route path="/admin/audit-logs" element={<RequireAuth roles={['Admin']}><AppShell><AdminAuditLogs /></AppShell></RequireAuth>} />
                    <Route path="/admin/scheduler" element={<RequireAuth roles={['Admin']}><AppShell><AdminScheduler /></AppShell></RequireAuth>} />
                    <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Routes>
            </BrowserRouter>
        </AuthProvider>
    );
}

function RequireAuthForceReset({ children }) {
    const { user } = useAuth();
    if (!user) return <Navigate to="/login" replace />;
    if (!user.force_password_reset) return <Navigate to="/dashboard" replace />;
    return children;
}
