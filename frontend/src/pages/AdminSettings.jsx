import React, { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { Save, Key, Mail } from 'lucide-react';
import { api } from '../lib/api';
import { PageHeader, Skeleton } from '../components/radar/Common';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs';
import { TIDS } from '../constants/testIds';

const FIELDS = {
    google: [
        ['google_oauth_client_id', 'Google OAuth Client ID', 'text', '1234567890-abcd.apps.googleusercontent.com'],
        ['google_oauth_client_secret', 'Google OAuth Client Secret', 'password', '•••••'],
        ['google_oauth_redirect_uri', 'Google OAuth Redirect URI', 'text', 'https://your-app.com/oauth/google/callback'],
    ],
    email: [
        ['email_provider', 'Provider (sendgrid or smtp)', 'text', 'sendgrid'],
        ['sender_email', 'Sender email', 'text', 'no-reply@yourcompany.com'],
        ['sender_name', 'Sender name', 'text', 'Business Radar AI'],
        ['sendgrid_api_key', 'SendGrid API Key', 'password', 'SG.xxxxxx'],
        ['smtp_host', 'SMTP Host', 'text', 'smtp.gmail.com'],
        ['smtp_port', 'SMTP Port', 'text', '587'],
        ['smtp_user', 'SMTP Username', 'text', ''],
        ['smtp_password', 'SMTP Password', 'password', ''],
    ],
    discovery: [
        ['opencorporates_api_token', 'OpenCorporates API Token', 'password', ''],
    ],
    scheduler: [
        ['daily_report_time', 'Daily report time (IST, HH:MM 24h)', 'text', '08:00'],
    ],
};

export default function AdminSettings() {
    const [settings, setSettings] = useState(null);
    const [form, setForm] = useState({});
    const [saving, setSaving] = useState(false);

    const load = async () => {
        try { const r = await api.get('/settings'); setSettings(r.data); } catch { toast.error('Failed'); }
    };
    useEffect(() => { load(); }, []);

    const save = async () => {
        setSaving(true);
        try {
            const r = await api.patch('/settings', { settings: form });
            setSettings(r.data);
            setForm({});
            toast.success('Settings saved');
        } catch (e) { toast.error('Save failed'); }
        finally { setSaving(false); }
    };

    const Field = ({ k, label, type, placeholder }) => {
        const current = settings?.[k];
        return (
            <div>
                <label className="eyebrow block mb-1">{label}</label>
                <input
                    className="field-input mono text-sm"
                    type={type === 'password' ? 'password' : 'text'}
                    placeholder={current?.value || placeholder}
                    value={form[k] ?? ''}
                    onChange={(e) => setForm({ ...form, [k]: e.target.value })}
                />
                <div className="text-[10px] text-muted-foreground mt-1">Current: {current?.value || (current?.configured ? 'configured' : 'not set')}</div>
            </div>
        );
    };

    if (!settings) return <div><PageHeader title="Settings" /><Skeleton className="h-64" /></div>;

    return (
        <div>
            <PageHeader
                eyebrow="Admin"
                title="Settings"
                subtitle="Configure integrations. Secrets are masked."
                actions={<button data-testid={TIDS.settingsSave} onClick={save} disabled={saving} className="btn-primary"><Save className="h-4 w-4" /> {saving ? 'Saving…' : 'Save changes'}</button>}
            />
            <Tabs defaultValue="google">
                <TabsList className="bg-[hsl(var(--canvas-3))] rounded-full p-1 border border-border/60 inline-flex">
                    <TabsTrigger value="google" className="rounded-full text-xs">Google OAuth</TabsTrigger>
                    <TabsTrigger value="email" className="rounded-full text-xs">Email</TabsTrigger>
                    <TabsTrigger value="discovery" className="rounded-full text-xs">Discovery</TabsTrigger>
                    <TabsTrigger value="scheduler" className="rounded-full text-xs">Scheduler</TabsTrigger>
                </TabsList>
                {Object.entries(FIELDS).map(([key, fields]) => (
                    <TabsContent key={key} value={key} className="mt-5">
                        <div className="surface p-5 grid sm:grid-cols-2 gap-4">
                            {fields.map(([k, label, type, placeholder]) => <Field key={k} k={k} label={label} type={type} placeholder={placeholder} />)}
                        </div>
                    </TabsContent>
                ))}
            </Tabs>
        </div>
    );
}
