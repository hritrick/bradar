import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import { LogIn, ShieldCheck, ArrowRight } from 'lucide-react';
import { useAuth } from '../lib/AuthContext';
import { api } from '../lib/api';
import { TIDS } from '../constants/testIds';

export default function Login() {
    const { login, user } = useAuth();
    const nav = useNavigate();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [googleStatus, setGoogleStatus] = useState({ configured: false });

    useEffect(() => {
        if (user) {
            if (user.force_password_reset) nav('/force-reset');
            else nav('/dashboard');
        }
        api.get('/auth/google/status').then(r => setGoogleStatus(r.data)).catch(() => {});
    }, [user, nav]);

    const submit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const data = await login(email, password);
            toast.success('Welcome back');
            if (data.force_password_reset) nav('/force-reset');
            else nav('/dashboard');
        } catch (err) {
            toast.error(err?.response?.data?.detail || 'Login failed');
        } finally {
            setLoading(false);
        }
    };

    const googleLogin = async () => {
        if (!googleStatus.configured) {
            toast.message('Google OAuth not yet configured', { description: 'Ask your admin to add Google OAuth credentials in Settings.' });
            return;
        }
        try {
            const r = await api.get('/auth/google/start');
            window.location.href = r.data.url;
        } catch (e) {
            toast.error(e?.response?.data?.detail || 'Google OAuth not available');
        }
    };

    return (
        <div className="min-h-screen flex items-stretch">
            <div className="hidden lg:flex w-1/2 relative overflow-hidden border-r border-border/60">
                <div className="absolute inset-0" style={{ background: 'radial-gradient(900px 600px at 20% 20%, hsl(42 55% 72% / 0.18), transparent 60%), radial-gradient(700px 500px at 80% 80%, hsl(0 0% 100% / 0.05), transparent 60%)' }} />
                <div className="relative z-10 flex flex-col justify-between p-12 w-full">
                    <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-2xl bg-gradient-to-br from-[hsl(42_55%_72%)] to-[hsl(35_30%_55%)] flex items-center justify-center shadow-[var(--glow-gold)]">
                            <span className="text-[hsl(240_6%_6%)] font-bold heading">R</span>
                        </div>
                        <div>
                            <div className="heading text-base font-semibold">Business Radar</div>
                            <div className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground">Intelligence · AI · India</div>
                        </div>
                    </div>
                    <div className="max-w-md">
                        <div className="eyebrow mb-3">Signal over noise</div>
                        <h1 className="heading text-4xl font-semibold tracking-tight leading-tight">Find the next 100 customers before anyone else.</h1>
                        <p className="text-muted-foreground mt-4 text-sm leading-relaxed">India’s newest companies, enriched, predicted and scored for outbound. Daily intelligence, designed for operators.</p>
                        <div className="mt-8 grid grid-cols-3 gap-3">
                            <div className="surface-2 p-4"><div className="eyebrow">Sources</div><div className="heading text-xl mt-1">04</div></div>
                            <div className="surface-2 p-4"><div className="eyebrow">AI Models</div><div className="heading text-xl mt-1">03</div></div>
                            <div className="surface-2 p-4"><div className="eyebrow">Cities</div><div className="heading text-xl mt-1">N+</div></div>
                        </div>
                    </div>
                    <div className="text-xs text-muted-foreground">v1 · Mumbai · Thane · Navi Mumbai</div>
                </div>
            </div>
            <div className="flex-1 flex items-center justify-center p-6">
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.42, ease: [0.22, 1, 0.36, 1] }} className="w-full max-w-sm">
                    <div className="eyebrow mb-3">Welcome back</div>
                    <h2 className="heading text-3xl font-semibold">Sign in</h2>
                    <p className="text-sm text-muted-foreground mt-2">Operator access to Business Radar AI</p>

                    <form onSubmit={submit} className="mt-8 space-y-4">
                        <div>
                            <label className="eyebrow block mb-2">Email</label>
                            <input data-testid={TIDS.loginEmail} type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="field-input" placeholder="you@company.com" autoComplete="email" />
                        </div>
                        <div>
                            <label className="eyebrow block mb-2">Password</label>
                            <input data-testid={TIDS.loginPassword} type="password" required value={password} onChange={(e) => setPassword(e.target.value)} className="field-input" placeholder="••••••••" autoComplete="current-password" />
                        </div>
                        <button data-testid={TIDS.loginSubmit} disabled={loading} type="submit" className="btn-primary w-full">
                            <LogIn className="h-4 w-4" /> {loading ? 'Signing in…' : 'Sign in'} <ArrowRight className="h-4 w-4" />
                        </button>
                    </form>

                    <div className="flex items-center gap-3 my-6">
                        <div className="flex-1 h-px bg-border/60" />
                        <div className="text-xs text-muted-foreground">or</div>
                        <div className="flex-1 h-px bg-border/60" />
                    </div>

                    <button data-testid={TIDS.loginGoogle} type="button" onClick={googleLogin} className="btn-secondary w-full justify-center">
                        <svg className="h-4 w-4" viewBox="0 0 24 24"><path fill="#fff" opacity="0.9" d="M21.6 12.23c0-.7-.06-1.36-.18-2H12v3.79h5.4c-.23 1.24-.93 2.29-1.97 2.99v2.49h3.18c1.86-1.71 2.94-4.24 2.94-7.27z"/><path fill="#fff" opacity="0.7" d="M12 22c2.7 0 4.96-.9 6.62-2.43l-3.18-2.49c-.88.59-2.01.94-3.44.94-2.65 0-4.9-1.79-5.7-4.19H3.04v2.6A9.99 9.99 0 0 0 12 22z"/><path fill="#fff" opacity="0.55" d="M6.3 13.83A6 6 0 0 1 6 12c0-.64.11-1.25.3-1.83V7.57H3.04A10 10 0 0 0 2 12c0 1.6.39 3.12 1.04 4.43L6.3 13.83z"/><path fill="#fff" opacity="0.4" d="M12 6.04c1.47 0 2.78.5 3.81 1.49l2.85-2.85C16.95 3.18 14.7 2.27 12 2.27a9.99 9.99 0 0 0-8.96 5.3l3.26 2.6C7.1 7.83 9.35 6.04 12 6.04z"/></svg>
                        Continue with Google
                        {!googleStatus.configured && <span className="text-[10px] ml-2 text-muted-foreground">(setup in Settings)</span>}
                    </button>

                    <div className="mt-8 text-xs text-muted-foreground flex items-center gap-2">
                        <ShieldCheck className="h-3.5 w-3.5" /> Test admin: test.admin@businessradar.ai / RadarTest@2025
                    </div>
                </motion.div>
            </div>
        </div>
    );
}
