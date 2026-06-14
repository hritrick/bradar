import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { ShieldCheck, ArrowRight, KeyRound } from 'lucide-react';
import { api } from '../lib/api';
import { useAuth } from '../lib/AuthContext';
import { TIDS } from '../constants/testIds';

export default function ForceReset() {
    const { refresh, user, logout } = useAuth();
    const nav = useNavigate();
    const [current, setCurrent] = useState('');
    const [next, setNext] = useState('');
    const [confirm, setConfirm] = useState('');
    const [loading, setLoading] = useState(false);

    const submit = async (e) => {
        e.preventDefault();
        if (next.length < 8) return toast.error('Password must be at least 8 characters');
        if (next !== confirm) return toast.error('Passwords do not match');
        setLoading(true);
        try {
            await api.post('/auth/reset-password', { current_password: current, new_password: next });
            await refresh();
            toast.success('Password updated');
            nav('/dashboard');
        } catch (err) {
            toast.error(err?.response?.data?.detail || 'Reset failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center p-6">
            <div className="w-full max-w-md surface p-8 sheen-overlay relative overflow-hidden">
                <div className="flex items-center gap-2 mb-2"><KeyRound className="h-5 w-5 text-[hsl(var(--primary))]" /><div className="eyebrow">First sign-in</div></div>
                <h1 className="heading text-2xl font-semibold">Reset your password</h1>
                <p className="text-sm text-muted-foreground mt-2">Welcome {user?.name}. For security, set a new password before continuing.</p>
                <form onSubmit={submit} className="mt-6 space-y-4">
                    <div>
                        <label className="eyebrow block mb-2">Current temporary password</label>
                        <input data-testid={TIDS.resetCurrent} type="password" required value={current} onChange={(e) => setCurrent(e.target.value)} className="field-input" />
                    </div>
                    <div>
                        <label className="eyebrow block mb-2">New password (min 8 chars)</label>
                        <input data-testid={TIDS.resetNew} type="password" required value={next} onChange={(e) => setNext(e.target.value)} className="field-input" />
                    </div>
                    <div>
                        <label className="eyebrow block mb-2">Confirm new password</label>
                        <input type="password" required value={confirm} onChange={(e) => setConfirm(e.target.value)} className="field-input" />
                    </div>
                    <button data-testid={TIDS.resetSubmit} disabled={loading} type="submit" className="btn-primary w-full justify-center">
                        <ShieldCheck className="h-4 w-4" /> {loading ? 'Updating…' : 'Update password'} <ArrowRight className="h-4 w-4" />
                    </button>
                </form>
                <button onClick={logout} className="text-xs text-muted-foreground mt-6 hover:underline">Sign out</button>
            </div>
        </div>
    );
}
