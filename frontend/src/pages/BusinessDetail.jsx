import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { toast } from 'sonner';
import { ArrowLeft, RefreshCw, Building2, Phone, Mail, Globe, MapPin, Briefcase, ChevronRight, Linkedin } from 'lucide-react';
import { api } from '../lib/api';
import { PageHeader, Skeleton } from '../components/radar/Common';
import { StatusPill } from '../components/radar/StatusPill';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs';
import { TIDS } from '../constants/testIds';
import { useAuth } from '../lib/AuthContext';

export default function BusinessDetail() {
    const { id } = useParams();
    const { user } = useAuth();
    const [b, setB] = useState(null);
    const [audits, setAudits] = useState([]);
    const [loading, setLoading] = useState(true);
    const [rerunning, setRerunning] = useState(false);

    const load = async () => {
        setLoading(true);
        try {
            const r = await api.get(`/businesses/${id}`);
            setB(r.data);
            if (user.role === 'Admin') {
                try {
                    const a = await api.get(`/audit-logs?entity_type=business&limit=50`);
                    setAudits((a.data || []).filter(x => x.entity_id === id));
                } catch {}
            }
        } catch (e) {
            toast.error('Failed to load business');
        } finally {
            setLoading(false);
        }
    };
    useEffect(() => { load(); }, [id]);

    const rerun = async () => {
        setRerunning(true);
        try {
            await api.post(`/businesses/${id}/enrich`);
            toast.success('AI re-run complete');
            await load();
        } catch (e) {
            toast.error('AI re-run failed');
        } finally {
            setRerunning(false);
        }
    };

    if (loading || !b) {
        return (
            <div>
                <PageHeader title="Loading…" subtitle=" " />
                <Skeleton className="h-64" />
            </div>
        );
    }

    const latestScore = (b.lead_scores || []).slice().sort((x, y) => new Date(y.created_at) - new Date(x.created_at))[0];
    const latestPred = (b.predictions || []).slice().sort((x, y) => new Date(y.created_at) - new Date(x.created_at))[0];
    const canEdit = user.role === 'Admin' || user.role === 'Analyst';

    return (
        <div>
            <Link to="/businesses" className="btn-ghost mb-3 text-xs"><ArrowLeft className="h-3.5 w-3.5" /> Back to Businesses</Link>
            <PageHeader
                eyebrow={b.source}
                title={b.business_name}
                subtitle={`${b.city || 'Unknown city'} · ${b.category || 'Uncategorized'} · ${b.company_type || ''}`}
                actions={(
                    <>
                        <StatusPill category={latestScore?.lead_category} score={latestScore?.score} />
                        {canEdit && <button onClick={rerun} disabled={rerunning} data-testid={TIDS.bizDetailRerun} className="btn-primary"><RefreshCw className={`h-4 w-4 ${rerunning ? 'animate-spin' : ''}`} /> {rerunning ? 'Running…' : 'Re-run AI'}</button>}
                    </>
                )}
            />

            <Tabs defaultValue="overview">
                <TabsList className="bg-[hsl(var(--canvas-3))] rounded-full p-1 border border-border/60 inline-flex">
                    <TabsTrigger value="overview" data-testid={TIDS.bizDetailTabOverview} className="rounded-full text-xs">Overview</TabsTrigger>
                    <TabsTrigger value="enrichment" data-testid={TIDS.bizDetailTabEnrich} className="rounded-full text-xs">Enrichment</TabsTrigger>
                    <TabsTrigger value="predictions" data-testid={TIDS.bizDetailTabPred} className="rounded-full text-xs">Predictions</TabsTrigger>
                    <TabsTrigger value="score" data-testid={TIDS.bizDetailTabScore} className="rounded-full text-xs">Lead Score</TabsTrigger>
                    {user.role === 'Admin' && <TabsTrigger value="audit" data-testid={TIDS.bizDetailTabAudit} className="rounded-full text-xs">Audit</TabsTrigger>}
                </TabsList>

                <TabsContent value="overview" className="mt-6">
                    <div className="grid lg:grid-cols-3 gap-4">
                        <div className="surface p-5 lg:col-span-2">
                            <div className="eyebrow">Profile</div>
                            <div className="heading text-lg mt-1">{b.business_name}</div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4 text-sm">
                                <Field icon={Briefcase} label="Company Type" value={b.company_type} />
                                <Field icon={Building2} label="Category" value={b.category} />
                                <Field icon={Building2} label="Sub-category" value={b.sub_category} />
                                <Field icon={Phone} label="Phone" value={b.phone} />
                                <Field icon={Mail} label="Email" value={b.email} />
                                <Field icon={Globe} label="Website" value={b.website} link />
                                <Field icon={Linkedin} label="LinkedIn" value={b.linkedin_url} link />
                                <Field icon={Briefcase} label="Director" value={b.director_name} />
                                <Field icon={Briefcase} label="Employees" value={b.employee_estimate} />
                                <Field icon={MapPin} label="Address" value={`${b.address || ''}, ${b.locality || ''}`} />
                                <Field icon={MapPin} label="City / State" value={`${b.city || '—'} / ${b.state || '—'}`} />
                                <Field icon={MapPin} label="Pincode" value={b.pincode} mono />
                                <Field icon={Briefcase} label="Registered" value={b.registration_date} mono />
                                <Field icon={Briefcase} label="Source" value={b.source} />
                            </div>
                        </div>
                        <div className="space-y-4">
                            <div className="surface p-5">
                                <div className="eyebrow">Confidence</div>
                                <div className="heading text-2xl mt-1">{Math.round((b.confidence_score || 0) * 100)}%</div>
                                <div className="h-2 mt-3 rounded-full bg-[hsl(var(--canvas-3))]"><div className="h-full bg-[hsl(var(--primary))] rounded-full" style={{ width: `${Math.round((b.confidence_score || 0) * 100)}%` }} /></div>
                                <div className="text-xs text-muted-foreground mt-2 mono">Enrichment {b.enrichment_status}</div>
                            </div>
                            <div className="surface p-5">
                                <div className="eyebrow">Latest Lead Score</div>
                                <div className="heading text-2xl mt-1 mono">{latestScore?.score ?? '—'}</div>
                                <div className="mt-2"><StatusPill category={latestScore?.lead_category} /></div>
                                {latestScore?.scoring_reason && <p className="text-xs text-muted-foreground mt-3 leading-relaxed">{latestScore.scoring_reason}</p>}
                            </div>
                            <div className="surface p-5">
                                <div className="eyebrow">Likely service need</div>
                                <div className="heading text-lg mt-1">{latestPred?.predicted_need || '—'}</div>
                                <div className="text-xs text-muted-foreground mt-1 mono">prob {latestPred ? (latestPred.probability * 100).toFixed(0) + '%' : '—'}</div>
                                {latestPred?.reasoning && <p className="text-xs text-muted-foreground mt-3 leading-relaxed">{latestPred.reasoning}</p>}
                            </div>
                        </div>
                    </div>
                </TabsContent>

                <TabsContent value="enrichment" className="mt-6">
                    <div className="surface p-5">
                        <div className="eyebrow">AI Enrichment Snapshot</div>
                        <div className="grid sm:grid-cols-2 gap-4 mt-3 text-sm">
                            <Field label="Category" value={b.category} />
                            <Field label="Sub-category" value={b.sub_category} />
                            <Field label="Company Type" value={b.company_type} />
                            <Field label="Employee Estimate" value={b.employee_estimate} mono />
                            <Field label="Confidence Score" value={(b.confidence_score || 0).toFixed(2)} mono />
                            <Field label="Enrichment Status" value={b.enrichment_status} mono />
                        </div>
                    </div>
                </TabsContent>

                <TabsContent value="predictions" className="mt-6">
                    <div className="surface overflow-hidden">
                        <div className="p-5"><div className="eyebrow">Predictions history</div></div>
                        {b.predictions.length === 0 ? <div className="p-6 text-sm text-muted-foreground">No predictions yet.</div> : (
                            <table className="table-cred">
                                <thead><tr><th>Need</th><th>Probability</th><th>Reasoning</th><th>When</th></tr></thead>
                                <tbody>
                                    {b.predictions.slice().sort((a, c) => new Date(c.created_at) - new Date(a.created_at)).map(p => (
                                        <tr key={p.id}>
                                            <td className="font-medium">{p.predicted_need}</td>
                                            <td className="mono">{(p.probability * 100).toFixed(0)}%</td>
                                            <td className="text-muted-foreground">{p.reasoning}</td>
                                            <td className="mono text-xs text-muted-foreground">{new Date(p.created_at).toLocaleString()}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                </TabsContent>

                <TabsContent value="score" className="mt-6">
                    <div className="surface overflow-hidden">
                        <div className="p-5"><div className="eyebrow">Lead score history</div></div>
                        {b.lead_scores.length === 0 ? <div className="p-6 text-sm text-muted-foreground">No scores yet.</div> : (
                            <table className="table-cred">
                                <thead><tr><th>Score</th><th>Category</th><th>Reason</th><th>When</th></tr></thead>
                                <tbody>
                                    {b.lead_scores.slice().sort((a, c) => new Date(c.created_at) - new Date(a.created_at)).map(s => (
                                        <tr key={s.id}>
                                            <td className="mono">{s.score}</td>
                                            <td><StatusPill category={s.lead_category} /></td>
                                            <td className="text-muted-foreground">{s.scoring_reason}</td>
                                            <td className="mono text-xs text-muted-foreground">{new Date(s.created_at).toLocaleString()}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                </TabsContent>

                {user.role === 'Admin' && (
                    <TabsContent value="audit" className="mt-6">
                        <div className="surface overflow-hidden">
                            <div className="p-5"><div className="eyebrow">Audit trail</div></div>
                            {audits.length === 0 ? <div className="p-6 text-sm text-muted-foreground">No audit events.</div> : (
                                <table className="table-cred">
                                    <thead><tr><th>When</th><th>Who</th><th>Action</th><th>Changes</th></tr></thead>
                                    <tbody>
                                        {audits.map(a => (
                                            <tr key={a.id}>
                                                <td className="mono text-xs">{new Date(a.created_at).toLocaleString()}</td>
                                                <td className="mono text-xs">{a.user_email || '—'}</td>
                                                <td>{a.action}</td>
                                                <td className="text-muted-foreground text-xs mono whitespace-pre-wrap">{JSON.stringify(a.after_value || {})}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    </TabsContent>
                )}
            </Tabs>
        </div>
    );
}

function Field({ icon: Icon, label, value, mono, link }) {
    return (
        <div className="flex items-start gap-3">
            {Icon && <div className="h-8 w-8 rounded-lg bg-[hsl(var(--canvas-3))] border border-border/70 flex items-center justify-center mt-0.5"><Icon className="h-3.5 w-3.5 text-muted-foreground" strokeWidth={1.5} /></div>}
            <div className="min-w-0">
                <div className="eyebrow">{label}</div>
                <div className={`mt-1 text-sm truncate ${mono ? 'mono' : ''}`}>
                    {link && value ? <a href={value} target="_blank" rel="noreferrer" className="hover:text-[hsl(var(--primary))]">{value}</a> : (value || '—')}
                </div>
            </div>
        </div>
    );
}
