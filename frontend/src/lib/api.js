import axios from 'axios';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || '/_/backend';
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({ baseURL: API, timeout: 60000 });

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('radar_token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

api.interceptors.response.use(
    (r) => r,
    (err) => {
        if (err.response && err.response.status === 401) {
            const path = window.location.pathname;
            if (!path.startsWith('/login')) {
                localStorage.removeItem('radar_token');
                localStorage.removeItem('radar_user');
                window.location.href = '/login';
            }
        }
        return Promise.reject(err);
    }
);
