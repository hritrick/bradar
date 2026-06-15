'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../lib/AuthContext';

export default function ForceResetGuard({ children }) {
    const { user, loading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (loading) {
            return;
        }
        if (!user) {
            router.replace('/login');
            return;
        }
        if (!user.force_password_reset) {
            router.replace('/dashboard');
        }
    }, [loading, router, user]);

    if (loading || !user || !user.force_password_reset) {
        return null;
    }

    return children;
}
