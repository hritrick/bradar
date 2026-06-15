'use client';

import { Toaster } from 'sonner';
import { AuthProvider } from '../lib/AuthContext';

export default function Providers({ children }) {
    return (
        <AuthProvider>
            <Toaster
                theme="dark"
                position="top-right"
                toastOptions={{
                    style: {
                        background: 'hsl(240 6% 9%)',
                        color: 'hsl(40 20% 96%)',
                        border: '1px solid hsl(240 6% 14%)',
                    },
                }}
            />
            {children}
        </AuthProvider>
    );
}
