'use client';

import ForceResetGuard from '../../components/auth/ForceResetGuard';
import ForceReset from '../../screens/ForceReset';

export default function ForceResetPage() {
    return (
        <ForceResetGuard>
            <ForceReset />
        </ForceResetGuard>
    );
}
