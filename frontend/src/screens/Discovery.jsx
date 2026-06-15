import React, { useEffect, useState } from 'react';
import { AppLink as Link } from '../lib/router';
import { toast } from 'sonner';
import {
    Compass, Play, ShieldAlert, FileSpreadsheet, KeyRound, ExternalLink, ArrowRight,
    Power, PowerOff, Activity, Zap, Clock, FileText, CheckCircle2, XCircle, Cpu, BarChart3, Building2
} from 'lucide-react';
import { motion } from 'framer-motion';
import { api } from '../lib/api';
import { PageHeader, Skeleton } from '../components/radar/Common';
import { Sheet, SheetContent, SheetTrigger } from '../components/ui/sheet';
import { Switch } from '../components/ui/switch';
import { TIDS } from '../constants/testIds';
import { useAuth } from '../lib/AuthContext';

const ICONS = {
    synthetic: Cpu,
    csv_import: FileSpreadsheet,
    manual: ExternalLink,
    opencorporates: KeyRound,
    mca: ShieldAlert,
    google_business: Compass,
    indiamart: Building2,
    justdial: Compass,
};

function TotalCard({ label, value, icon: Icon, accent, tid }) {
    return (
        <motion.div data-testid={tid} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} whileHover={{ y: -2 }} transition={{ duration: 0.32 }}
            className="surface relative overflow-hidden p-5 sheen-overlay">
            <div className="flex items-start justify-between">
                <div className="eyebrow">{label}</div>
                {Icon && (<div className="h-9 w-9 rounded-xl bg-[hsl(var(--canvas-3))] border border-border/70 flex items-center justify-center"><Icon className="h-4 w-4" strokeWidth={1.5} /></div>)}
            </div>
            <div className={`kpi-number text-3xl mt-3 ${accent ? 'text-[hsl(var(--primary))]' : ''}`}>{value}</div>
        </motion.div>
    );
}

function SourceCard({ s, onToggle, onRunNow, onViewLogs, isAdmin, isAnalyst, running }) {
    const Icon = ICONS[s.name] || Compass;
    const canRun = (s.name === 'synthetic') || s.configured;
    const statusColor = !s.enabled ? 'pill-cold' : !canRun ? 'pill-warm' : 'pill-warm';
    const statusLabel = !s.enabled ? 'Disabled' : !canRun ? 'Setup' : 'Ready';
    return (
        <div className="surface p-5 sheen-overlay relative overflow-hidden">
            <div className="flex items-start gap-3">
                <div className="h-10 w-10 rounded-xl bg-[hsl(var(--canvas-3))] border border-border/70 flex items-center justify-center">
                    <Icon className="h-4 w-4" strokeWidth={1.5} />
                </div>
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                        <div className="heading text-base font-semibold">{s.display_name}</div>
                        <span className={`pill-base text-[10px] ${statusColor}`}>{statusLabel}</span>
                    </div>
                    <div className="text-xs text-muted-foreground mt-1 leading-relaxed">{s.description}</div>
                </div>
                {isAdmin && (
                    <Switch data-testid={TIDS.discoveryEnableToggle(s.name)} checked={s.enabled} onCheckedChange={(v) => onToggle(s, v)} />
                )}
            </div>

            <div className="mt-4 grid grid-cols-3 sm:grid-cols-5 gap-2 text-center">
                <Stat label="Found" value={s.records_found} />
                <Stat label="Added" value={s.records_added} />
                <Stat label="Dupes" value={s.duplicates_removed} />
                <Stat label="Errors" value={s.errors} accent={s.errors > 0} />
                <Stat label="Runs" value={s.runs} />
            </div>

            <div className="mt-4 text-[10px] text-muted-foreground mono flex items-center gap-2">
                <Clock className="h-3 w-3" />
                Last run: {s.last_run_at ? new Date(s.last_run_at).toLocaleString('en-IN') : 'never'}
                {s.last_run_status && <span className={`pill-base text-[9px] ${s.last_run_status === 'success' ? 'pill-warm' : 'pill-cold'}`}>{s.last_run_status}</span>}
            </div>

            <div className="mt-5 flex flex-wrap items-center gap-2">
                {(isAdmin || isAnalyst) && s.supports_run_now !== false && (
                    <button data-testid={TIDS.discoveryRunSource(s.name)} disabled={running === s.id || !s.enabled || !canRun} onClick={() => onRunNow(s)} className="btn-primary text-xs">
                        <Play className="h-3.5 w-3.5" /> {running === s.id ? 'Running…' : 'Run now'}
                    </button>
                )}
                {s.name === 'csv_import' && <Link to="/businesses/upload" className="btn-secondary text-xs">Open CSV upload <ArrowRight className="h-3 w-3" /></Link>}
                {s.name === 'manual' && <Link to="/businesses/new" className="btn-secondary text-xs">Add manually <ArrowRight className="h-3 w-3" /></Link>}
                <Sheet>
                    <SheetTrigger asChild>
                        <button data-testid={TIDS.discoveryViewLogs(s.name)} className="btn-ghost text-xs"><FileText className="h-3.5 w-3.5" /> Logs</button>
                    </SheetTrigger>
                    <SheetContent side="right" className="w-[420px] sm:w-[560px] bg-[hsl(var(--canvas-2))] border-l border-border overflow-y-auto scrollbar-cred">
                        <SourceLogs sourceId={s.id} display_name={s.display_name} />
                    </SheetContent>
                </Sheet>
                {s.requires_config?.length > 0 && !s.configured && (
                    <span className="text-[10px] text-muted-foreground mono">needs: {s.requires_config.join(', ')}</span>
                )}
            </div>
        </div>
    );
}

function Stat({ label, value, accent }) {
    return (
        <div className="surface-2 p-2.5">
            <div className="text-[9px] uppercase tracking-[0.16em] text-muted-foreground">{label}</div>
            <div className={`kpi-number text-base mono mt-0.5 ${accent ? 'text-[hsl(var(--destructive))]' : ''}`}>{value ?? 0}</div>
        </div>
    );
}

function SourceLogs({ sourceId, display_name }) {
    const [runs, setRuns] = useState(null);
    useEffect(() => {
        api.get(`/discovery/sources/${sourceId}/runs`).then(r => setRuns(r.data)).catch(() => setRuns([]));
    }, [sourceId]);
    return (
        <div>
            <div className="eyebrow">Run history</div>
            <div className="heading text-base font-semibold mt-1">{display_name}</div>
            <div className="mt-5 space-y-3">
                {!runs ? <Skeleton className="h-20" /> : runs.length === 0 ? <div className="text-sm text-muted-foreground">No runs yet.</div> :
                    runs.map(r => (
                        <div key={r.id} className="surface-2 p-3">
                            <div className="flex items-center justify-between">
                                <span className={`pill-base text-[10px] ${r.status === 'success' ? 'pill-warm' : r.status === 'failed' ? 'pill-cold' : 'pill-hot'}`}>
                                    {r.status === 'success' ? <CheckCircle2 className="h-3 w-3" /> : r.status === 'failed' ? <XCircle className="h-3 w-3" /> : <Activity className="h-3 w-3" />}
                                    {r.status}
                                </span>
                                <span className="mono text-[10px] text-muted-foreground">{r.started_at ? new Date(r.started_at).toLocaleString('en-IN') : '—'}</span>
                            </div>
                            <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2 text-center">
                                <Stat label="Found" value={r.records_found} />
                                <Stat label="Added" value={r.records_added} />
                                <Stat label="Dupes" value={r.duplicates_removed} />
                                <Stat label="Errors" value={r.errors_count} accent={r.errors_count > 0} />
                            </div>
                            <div className="mt-2 text-[11px] text-muted-foreground">Triggered: <span className="mono">{r.triggered_by || 'scheduler'}</span></div>
                            {r.message && <div className="mt-2 text-[11px] text-muted-foreground italic">{r.message}</div>}
                            {r.errors?.length > 0 && (
                                <ul className="mt-2 text-[11px] text-[hsl(var(--destructive))] mono space-y-0.5">
                                    {r.errors.map((e, i) => <li key={i}>• {e}</li>)}
                                </ul>
                            )}
                        </div>
                    ))
                }
            </div>
        </div>
    );
}

export default function Discovery() {
    const { user } = useAuth();
    const isAdmin = user?.role === 'Admin';
    const isAnalyst = user?.role === 'Analyst';
    const [health, setHealth] = useState(null);
    const [running, setRunning] = useState(null);
    const [queueBusy, setQueueBusy] = useState(false);

    const load = async () => {
        try {
            const r = await api.get('/discovery/health');
            setHealth(r.data);
        } catch (e) {
            toast.error('Failed to load discovery health');
            setHealth({ totals: {}, queue: {}, sources: [] });
        }
    };
    useEffect(() => { load(); }, []);

    const onToggle = async (s, enabled) => {
        try {
            await api.patch(`/discovery/sources/${s.id}`, { enabled });
            toast.success(`${s.display_name} ${enabled ? 'enabled' : 'disabled'}`);
            await load();
        } catch (e) { toast.error('Toggle failed'); }
    };

    const onRunNow = async (s, limit = 20) => {
        setRunning(s.id);
        try {
            const r = await api.post(`/discovery/sources/${s.id}/run`, { limit });
            toast.success(`${s.display_name}: added ${r.data.records_added}, dupes ${r.data.duplicates_removed}, queued ${r.data.enrichment_queued}`);
            await load();
        } catch (e) {
            toast.error(e?.response?.data?.detail || 'Run failed');
        } finally { setRunning(null); }
    };

    const processQueue = async (batch = 5) => {
        setQueueBusy(true);
        try {
            const r = await api.post(`/discovery/queue/process?batch=${batch}`);
            toast.success(`Queue: processed ${r.data.processed}, failed ${r.data.failed}`);
            await load();
        } catch (e) {
            toast.error(e?.response?.data?.detail || 'Queue processing failed');
        } finally { setQueueBusy(false); }
    };

    if (!health) {
        return <div><PageHeader title="Discovery" subtitle="Source health and runs" /><div className="grid grid-cols-2 sm:grid-cols-4 gap-4">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-28" />)}</div></div>;
    }

    return (
        <div>
            <PageHeader
                eyebrow="Sources"
                title="Discovery"
                subtitle="Provider architecture: plug-and-play sources → normalization → dedup (GST / website / phone / name+pincode) → enrichment queue → prediction → scoring → geo → reports."
                actions={(
                    <>
                        <button onClick={() => load()} className="btn-secondary"><Activity className="h-4 w-4" /> Refresh</button>
                        {isAdmin && (
                            <button data-testid={TIDS.discoveryProcessQueue} onClick={() => processQueue(5)} disabled={queueBusy || (health.queue?.queued || 0) === 0} className="btn-primary">
                                <Zap className="h-4 w-4" /> {queueBusy ? 'Processing…' : `Process queue (${health.queue?.queued || 0})`}
                            </button>
                        )}
                    </>
                )}
            />

            <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 mb-6">
                <TotalCard tid={TIDS.discoveryHealthTotal} label="Records Found" value={(health.totals?.records_found || 0).toLocaleString('en-IN')} icon={BarChart3} />
                <TotalCard label="Records Added" value={(health.totals?.records_added || 0).toLocaleString('en-IN')} icon={CheckCircle2} accent />
                <TotalCard label="Duplicates Removed" value={(health.totals?.duplicates_removed || 0).toLocaleString('en-IN')} icon={Activity} />
                <TotalCard label="Errors" value={(health.totals?.errors || 0).toLocaleString('en-IN')} icon={XCircle} />
                <TotalCard label="Sources Enabled" value={`${health.totals?.sources_enabled || 0} / ${health.totals?.sources_total || 0}`} icon={Power} />
            </div>

            <div className="surface p-5 mb-6">
                <div className="flex items-center justify-between gap-3 flex-wrap">
                    <div className="flex items-center gap-3">
                        <div className="h-9 w-9 rounded-xl bg-[hsl(var(--canvas-3))] border border-border/70 flex items-center justify-center"><Zap className="h-4 w-4 text-[hsl(var(--primary))]" /></div>
                        <div>
                            <div className="eyebrow">Enrichment queue</div>
                            <div className="heading text-sm">Background AI pipeline (predict + score)</div>
                        </div>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        <PillStat label="Queued" value={health.queue?.queued} />
                        <PillStat label="Processing" value={health.queue?.processing} />
                        <PillStat label="Done" value={health.queue?.done} />
                        <PillStat label="Failed" value={health.queue?.failed} accent />
                    </div>
                </div>
            </div>

            <div className="grid lg:grid-cols-2 gap-4">
                {health.sources.map((s) => (
                    <SourceCard key={s.id} s={s} onToggle={onToggle} onRunNow={onRunNow} isAdmin={isAdmin} isAnalyst={isAnalyst} running={running} />
                ))}
            </div>
        </div>
    );
}

function PillStat({ label, value, accent }) {
    return (
        <div className="pill-base pill-neutral">
            <span>{label}</span>
            <span className={`mono ${accent ? 'text-[hsl(var(--destructive))]' : ''}`}>{value ?? 0}</span>
        </div>
    );
}
