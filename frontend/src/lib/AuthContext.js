import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { api } from './api';

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        try {
            const raw = window.localStorage.getItem('radar_user');
            setUser(raw ? JSON.parse(raw) : null);
        } catch {
            setUser(null);
        } finally {
            setLoading(false);
        }
    }, []);

    const refresh = useCallback(async () => {
        const token = window.localStorage.getItem('radar_token');
        if (!token) return;
        try {
            const r = await api.get('/auth/me');
            setUser(r.data);
            window.localStorage.setItem('radar_user', JSON.stringify(r.data));
        } catch (e) {
            setUser(null);
            window.localStorage.removeItem('radar_token');
            window.localStorage.removeItem('radar_user');
        }
    }, []);

    useEffect(() => {
        if (!loading) {
            refresh();
        }
    }, [loading, refresh]);

    const login = async (email, password) => {
        setLoading(true);
        try {
            const r = await api.post('/auth/login', { email, password });
            window.localStorage.setItem('radar_token', r.data.access_token);
            window.localStorage.setItem('radar_user', JSON.stringify(r.data.user));
            setUser(r.data.user);
            return r.data;
        } finally {
            setLoading(false);
        }
    };

    const logout = () => {
        window.localStorage.removeItem('radar_token');
        window.localStorage.removeItem('radar_user');
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
