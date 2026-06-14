import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { api } from './api';

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(() => {
        try {
            const raw = localStorage.getItem('radar_user');
            return raw ? JSON.parse(raw) : null;
        } catch { return null; }
    });
    const [loading, setLoading] = useState(false);

    const refresh = useCallback(async () => {
        const token = localStorage.getItem('radar_token');
        if (!token) return;
        try {
            const r = await api.get('/auth/me');
            setUser(r.data);
            localStorage.setItem('radar_user', JSON.stringify(r.data));
        } catch (e) {
            setUser(null);
            localStorage.removeItem('radar_token');
            localStorage.removeItem('radar_user');
        }
    }, []);

    useEffect(() => { refresh(); }, [refresh]);

    const login = async (email, password) => {
        setLoading(true);
        try {
            const r = await api.post('/auth/login', { email, password });
            localStorage.setItem('radar_token', r.data.access_token);
            localStorage.setItem('radar_user', JSON.stringify(r.data.user));
            setUser(r.data.user);
            return r.data;
        } finally {
            setLoading(false);
        }
    };

    const logout = () => {
        localStorage.removeItem('radar_token');
        localStorage.removeItem('radar_user');
        setUser(null);
        window.location.href = '/login';
    };

    return (
        <AuthCtx.Provider value={{ user, setUser, login, logout, loading, refresh }}>
            {children}
        </AuthCtx.Provider>
    );
}

export function useAuth() {
    const ctx = useContext(AuthCtx);
    if (!ctx) throw new Error('useAuth must be inside AuthProvider');
    return ctx;
}
