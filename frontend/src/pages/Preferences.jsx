import React, { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { Save, Bell, Mail } from 'lucide-react';
import { api } from '../lib/api';
import { PageHeader, Skeleton } from '../components/radar/Common';
import { Switch } from '../components/ui/switch';
import { TIDS } from '../constants/testIds';

export default function Preferences() {
    const [prefs, setPrefs] = useState(null);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        api.get('/preferences').then(r => setPrefs(r.data)).catch(() => toast.error('Failed to load preferences'));
    }, []);

    const save = async () => {
        setSaving(true);
        try {
            await api.patch('/preferences', prefs);
            toast.success('Preferences saved');
        } catch {
            toast.error('Failed');
        } finally { setSaving(false); }
    };

    if (!prefs) return <div><PageHeader title="Preferences" /><Skeleton className="h-48" /></div>;

    return (
        <div className="max-w-2xl">
            <PageHeader eyebrow="You" title="Preferences" subtitle="Delivery, notifications, and defaults." />
            <div className="surface p-5 space-y-5">
                <div className="flex items-center justify-between">
                    <div className="flex items-start gap-3">
                        <div className="h-10 w-10 rounded-xl bg-[hsl(var(--canvas-3))] border border-border flex items-center justify-center"><Bell className="h-4 w-4" strokeWidth={1.5} /></div>
                        <div>
                            <div className="heading text-sm font-medium">Daily Report</div>
                            <div className="text-xs text-muted-foreground mt-1">Receive an email each morning with the day’s intelligence.</div>
                        </div>
                    </div>
                    <Switch data-testid={TIDS.prefsDaily} checked={prefs.daily_report_enabled} onCheckedChange={(v) => setPrefs(p => ({ ...p, daily_report_enabled: v }))} />
                </div>
                <div className="flex items-center justify-between">
                    <div className="flex items-start gap-3">
                        <div className="h-10 w-10 rounded-xl bg-[hsl(var(--canvas-3))] border border-border flex items-center justify-center"><Bell className="h-4 w-4" strokeWidth={1.5} /></div>
                        <div>
                            <div className="heading text-sm font-medium">Weekly Roundup</div>
                            <div className="text-xs text-muted-foreground mt-1">A summary of the last 7 days, delivered each Monday.</div>
                        </div>
                    </div>
                    <Switch data-testid={TIDS.prefsWeekly} checked={prefs.weekly_report_enabled} onCheckedChange={(v) => setPrefs(p => ({ ...p, weekly_report_enabled: v }))} />
                </div>
                <div>
                    <label className="eyebrow flex items-center gap-2 mb-2"><Mail className="h-3 w-3" /> Delivery email</label>
                    <input data-testid={TIDS.prefsEmail} className="field-input" value={prefs.delivery_email || ''} onChange={(e) => setPrefs(p => ({ ...p, delivery_email: e.target.value }))} />
                    <p className="text-xs text-muted-foreground mt-2">If email is not configured by admin, reports are still generated in-app.</p>
                </div>
                <div className="flex justify-end">
                    <button data-testid={TIDS.prefsSave} onClick={save} disabled={saving} className="btn-primary"><Save className="h-4 w-4" /> {saving ? 'Saving…' : 'Save preferences'}</button>
                </div>
            </div>
        </div>
    );
}
