import React, { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { Compass, Play, ShieldAlert, FileSpreadsheet, KeyRound, ExternalLink, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api';
import { PageHeader, Skeleton } from '../components/radar/Common';
import { TIDS } from '../constants/testIds';

const META = {
    sample_seed: { title: 'Sample Seed', icon: FileSpreadsheet, accent: true, ridoc: 'For demo & QA. Generates realistic Mumbai/Thane/Navi Mumbai businesses.' },
    opencorporates: { title: 'OpenCorporates', icon: KeyRound, ridoc: 'Public registry API. Configure your API token in Admin Settings.' },
    mca: { title: 'MCA Portal', icon: ShieldAlert, ridoc: 'Placeholder — MCA requires captcha/login. Future integration.' },
    csv_upload: { title: 'CSV Upload', icon: FileSpreadsheet, ridoc: 'Use the “CSV Upload” screen to bulk import.' },
    manual: { title: 'Manual Entry', icon: ExternalLink, ridoc: 'Add businesses one-by-one via the form.' },
};

export default function Discovery() {
    const [connectors, setConnectors] = useState(null);
    const [running, setRunning] = useState(null);
    const [results, setResults] = useState([]);

    const load = async () => {
        try {
            const r = await api.get('/discovery/connectors');
            setConnectors(r.data);
        } catch (e) {
            toast.error('Failed to load connectors');
        }
    };
    useEffect(() => { load(); }, []);

    const run = async (name, limit = 10) => {
        setRunning(name);
        try {
            const r = await api.post('/discovery/run', { source: name, limit });
            const res = r.data;
            setResults((p) => [{ ...res, at: new Date().toISOString() }, ...p].slice(0, 10));
            toast.success(`${name}: inserted ${res.inserted}, duplicates ${res.duplicates}, enriched ${res.enriched}`);
        } catch (e) {
            toast.error(e?.response?.data?.detail || 'Discovery failed');
        } finally {
            setRunning(null);
        }
    };

    return (
        <div>
            <PageHeader eyebrow="Sources" title="Discovery" subtitle="Plug-and-play connectors that flow into the enrichment + scoring pipeline." />
            {!connectors ? (
                <div className="grid sm:grid-cols-2 gap-4">
                    {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-40" />)}
                </div>
            ) : (
                <div className="grid sm:grid-cols-2 gap-4">
                    {connectors.map((c) => {
                        const meta = META[c.name] || { title: c.name, icon: Compass, ridoc: '' };
                        const Icon = meta.icon || Compass;
                        const canRun = c.configured && !['csv_upload', 'manual'].includes(c.name);
                        const tid = c.name === 'sample_seed' ? TIDS.discoveryRunSeed : c.name === 'opencorporates' ? TIDS.discoveryRunOpc : c.name === 'mca' ? TIDS.discoveryRunMca : undefined;
                        return (
                            <div key={c.name} className="surface p-5 sheen-overlay relative overflow-hidden">
                                <div className="flex items-start gap-3">
                                    <div className="h-10 w-10 rounded-xl bg-[hsl(var(--canvas-3))] border border-border/70 flex items-center justify-center">
                                        <Icon className="h-4 w-4" strokeWidth={1.5} />
                                    </div>
                                    <div className="flex-1">
                                        <div className="heading text-base font-semibold">{meta.title}</div>
                                        <div className="text-xs text-muted-foreground mt-1">{meta.ridoc}</div>
                                    </div>
                                    <span className={`pill-base ${c.configured ? 'pill-warm' : 'pill-cold'} text-[10px]`}>{c.configured ? 'Ready' : 'Setup'}</span>
                                </div>
                                <div className="text-xs text-muted-foreground mt-4">{c.description}</div>
                                <div className="flex items-center justify-between mt-5">
                                    {canRun ? (
                                        <button data-testid={tid} disabled={running === c.name} onClick={() => run(c.name, 8)} className="btn-primary">
                                            <Play className="h-4 w-4" /> {running === c.name ? 'Discovering & enriching…' : 'Run discovery'}
                                        </button>
                                    ) : c.name === 'csv_upload' ? (
                                        <Link to="/businesses/upload" className="btn-secondary">Open CSV upload <ArrowRight className="h-3.5 w-3.5" /></Link>
                                    ) : c.name === 'manual' ? (
                                        <Link to="/businesses/new" className="btn-secondary">Add manually <ArrowRight className="h-3.5 w-3.5" /></Link>
                                    ) : (
                                        <span className="text-xs text-muted-foreground">Requires: {c.requires_config.join(', ') || '—'}</span>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            <div className="surface mt-6 overflow-hidden">
                <div className="p-5"><div className="eyebrow">Recent discovery runs</div></div>
                {results.length === 0 ? <div className="px-5 pb-5 text-sm text-muted-foreground">No runs yet in this session.</div> : (
                    <div className="overflow-x-auto scrollbar-cred">
                        <table className="table-cred">
                            <thead><tr><th>When</th><th>Source</th><th>Fetched</th><th>Inserted</th><th>Duplicates</th><th>Enriched</th><th>Errors</th></tr></thead>
                            <tbody>
                                {results.map((r, i) => (
                                    <tr key={i}>
                                        <td className="mono text-xs">{new Date(r.at).toLocaleString()}</td>
                                        <td className="mono">{r.source}</td>
                                        <td className="mono">{r.fetched}</td>
                                        <td className="mono">{r.inserted}</td>
                                        <td className="mono">{r.duplicates}</td>
                                        <td className="mono">{r.enriched}</td>
                                        <td className="mono text-xs text-[hsl(var(--destructive))]">{r.errors?.length || 0}</td>
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
