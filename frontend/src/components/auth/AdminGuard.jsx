'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../../lib/AuthContext';

export default function AdminGuard({ children }) {
    const { user, loading } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (!loading && user && user.role !== 'Admin') {
            router.replace('/dashboard');
        }
    }, [loading, router, user]);

    if (loading || !user || user.role !== 'Admin') {
        return null;
    }

    return children;
}
