import React, { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { Play, Clock, CheckCircle2, XCircle } from 'lucide-react';
import { api } from '../lib/api';
import { PageHeader, Skeleton } from '../components/radar/Common';
import { TIDS } from '../constants/testIds';

export default function AdminScheduler() {
    const [s, setS] = useState(null);
    const [running, setRunning] = useState(false);

    const load = async () => {
        try { const r = await api.get('/scheduler/status'); setS(r.data); } catch { toast.error('Failed'); }
    };
    useEffect(() => { load(); }, []);

    const runNow = async () => {
        setRunning(true);
        try { await api.post('/scheduler/run-now'); toast.success('Job triggered'); await load(); }
        catch (e) { toast.error(e?.response?.data?.detail || 'Failed'); }
        finally { setRunning(false); }
    };

    if (!s) return <div><PageHeader title="Scheduler" /><Skeleton className="h-64" /></div>;

    return (
        <div>
            <PageHeader eyebrow="Admin" title="Scheduler" subtitle="Background jobs that keep intelligence flowing." actions={<button data-testid={TIDS.schedulerRunNow} onClick={runNow} disabled={running} className="btn-primary"><Play className="h-4 w-4" /> {running ? 'Running…' : 'Run today’s report now'}</button>} />
            <div className="grid sm:grid-cols-3 gap-4 mb-6">
                <Card title="Status" value={s.running ? 'Running' : 'Stopped'} accent={s.running} />
                <Card title="Next run" value={s.next_run ? new Date(s.next_run).toLocaleString() : '—'} mono />
                <Card title="Recent runs" value={(s.recent_runs?.length || 0).toString()} mono />
            </div>
            <div className="surface overflow-hidden">
                <div className="p-5"><div className="eyebrow">Recent runs</div></div>
                {s.recent_runs.length === 0 ? <div className="px-5 pb-5 text-sm text-muted-foreground">No runs yet.</div> : (
                    <div className="overflow-x-auto scrollbar-cred">
                        <table className="table-cred">
                            <thead><tr><th>Job</th><th>Status</th><th>Started</th><th>Finished</th><th>Message</th></tr></thead>
                            <tbody>
                                {s.recent_runs.map(r => (
                                    <tr key={r.id}>
                                        <td className="mono">{r.job_name}</td>
                                        <td>
                                            <span className={`pill-base text-[10px] ${r.status === 'success' ? 'pill-warm' : r.status === 'failed' ? 'pill-cold' : 'pill-hot'}`}>
                                                {r.status === 'success' ? <CheckCircle2 className="h-3 w-3" /> : r.status === 'failed' ? <XCircle className="h-3 w-3" /> : <Clock className="h-3 w-3" />}
                                                {r.status}
                                            </span>
                                        </td>
                                        <td className="mono text-xs">{new Date(r.started_at).toLocaleString()}</td>
                                        <td className="mono text-xs">{r.finished_at ? new Date(r.finished_at).toLocaleString() : '—'}</td>
                                        <td className="text-muted-foreground text-xs">{r.message || '—'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}

function Card({ title, value, accent, mono }) {
    return (
        <div className="surface p-5">
            <div className="eyebrow">{title}</div>
            <div className={`kpi-number text-2xl mt-1 ${accent ? 'text-[hsl(var(--primary))]' : ''} ${mono ? 'mono' : ''}`}>{value}</div>
        </div>
    );
}
