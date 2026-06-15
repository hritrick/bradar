'use client';

import { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import AppShell from '../layout/AppShell';
import { useAuth } from '../../lib/AuthContext';

export default function ProtectedLayout({ children }) {
    const { user, loading } = useAuth();
    const pathname = usePathname();
    const router = useRouter();

    useEffect(() => {
        if (loading) {
            return;
        }
        if (!user) {
            router.replace('/login');
            return;
        }
        if (user.force_password_reset && pathname !== '/force-reset') {
            router.replace('/force-reset');
        }
    }, [loading, pathname, router, user]);

    if (loading || !user || user.force_password_reset) {
        return null;
    }

    return <AppShell>{children}</AppShell>;
}
