'use client';

import ProtectedLayout from '../../components/auth/ProtectedLayout';

export default function ProtectedRouteLayout({ children }) {
    return <ProtectedLayout>{children}</ProtectedLayout>;
}
