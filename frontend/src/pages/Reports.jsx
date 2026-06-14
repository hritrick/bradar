import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { FileText, Calendar, Download, Sparkles, ArrowRight } from 'lucide-react';
import { api, API } from '../lib/api';
import { PageHeader, EmptyState, Skeleton } from '../components/radar/Common';
import { TIDS } from '../constants/testIds';
import { useAuth } from '../lib/AuthContext';

function fmt(d) { return new Date(d).toLocaleString('en-IN', { day: '2-digit', month: 'short', year: '2-digit', hour: '2-digit', minute: '2-digit' }); }

export default function Reports() {
    const { user } = useAuth();
    const [list, setList] = useState(null);
    const [today, setToday] = useState(null);
    const [generating, setGenerating] = useState(false);

    const load = async () => {
        try {
            const [a, b] = await Promise.all([api.get('/reports'), api.get('/reports/today')]);
            setList(a.data);
            setToday(b.data);
        } catch (e) {
            toast.error('Failed to load reports');
            setList([]);
        }
    };
    useEffect(() => { load(); }, []);

    const generate = async () => {
        setGenerating(true);
        try {
            const r = await api.post('/reports/generate', { });
            setToday(r.data);
            await load();
            toast.success('Today’s report generated');
        } catch (e) {
            toast.error(e?.response?.data?.detail || 'Generation failed');
        } finally {
            setGenerating(false);
        }
    };

    const download = async (id, kind) => {
        try {
            const token = localStorage.getItem('radar_token');
            const url = `${API}/reports/${id}/download/${kind}`;
            const r = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
            if (!r.ok) throw new Error('fail');
            const blob = await r.blob();
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            const ext = kind === 'pdf' ? 'pdf' : kind === 'xlsx' ? 'xlsx' : 'csv';
            a.download = `report.${ext}`;
            a.click();
        } catch {
            toast.error('Download failed');
        }
    };

    return (
        <div>
            <PageHeader
                eyebrow="Daily intelligence"
                title="Reports"
                subtitle="Today’s feed of new businesses, hot leads, and predicted needs — ready to share."
                actions={(user.role !== 'Subscriber') && (<button data-testid={TIDS.reportsGenerate} onClick={generate} disabled={generating} className="btn-primary"><Sparkles className="h-4 w-4" /> {generating ? 'Generating…' : 'Generate today’s report'}</button>)}
            />

            <div className="grid lg:grid-cols-[1fr_320px] gap-6">
                {today ? (
                    <div className="surface overflow-hidden">
                        <div className="p-5 flex flex-wrap items-center justify-between gap-3 border-b border-border/60">
                            <div>
                                <div className="eyebrow">Today · {today.report_date}</div>
                                <div className="heading text-lg">Daily Intelligence Report</div>
                            </div>
                            <div className="flex flex-wrap items-center gap-2">
                                <button data-testid={TIDS.reportsDownloadPdf} onClick={() => download(today.id, 'pdf')} className="btn-secondary"><Download className="h-3.5 w-3.5" /> PDF</button>
                                <button data-testid={TIDS.reportsDownloadXlsx} onClick={() => download(today.id, 'xlsx')} className="btn-secondary"><Download className="h-3.5 w-3.5" /> Excel</button>
                                <button data-testid={TIDS.reportsDownloadCsv} onClick={() => download(today.id, 'csv')} className="btn-secondary"><Download className="h-3.5 w-3.5" /> CSV</button>
                            </div>
                        </div>
                        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 p-5">
                            {[
                                ['Total', today.report_json.kpis.total_businesses],
                                ['Today new', today.report_json.kpis.today_new],
                                ['Hot', today.report_json.kpis.hot_leads],
                                ['Warm', today.report_json.kpis.warm_leads],
                                ['Cold', today.report_json.kpis.cold_leads],
                                ['Avg score', today.report_json.kpis.avg_score],
                            ].map(([l, v]) => (
                                <div key={l} className="surface-2 p-3 text-center">
                                    <div className="eyebrow">{l}</div>
                                    <div className="kpi-number text-xl mt-1">{v}</div>
                                </div>
                            ))}
                        </div>
                        <div className="grid lg:grid-cols-3 gap-4 p-5 pt-0">
                            <Block title="Top Cities" items={today.report_json.by_city || []} keyField="city" />
                            <Block title="Top Categories" items={today.report_json.by_category || []} keyField="category" />
                            <Block title="Predicted Needs" items={today.report_json.by_predicted_need || []} keyField="need" />
                        </div>
                        {today.report_json.today_list?.length > 0 && (
                            <div className="px-5 pb-5">
                                <div className="eyebrow mb-2">Today’s discoveries</div>
                                <div className="surface-2 overflow-x-auto scrollbar-cred">
                                    <table className="table-cred">
                                        <thead><tr><th>Business</th><th>City</th><th>Category</th><th>Score</th><th>Lead</th></tr></thead>
                                        <tbody>
                                            {today.report_json.today_list.map((b) => (
                                                <tr key={b.id}>
                                                    <td><Link to={`/businesses/${b.id}`} className="hover:text-[hsl(var(--primary))]">{b.business_name}</Link></td>
                                                    <td>{b.city || '—'}</td>
                                                    <td>{b.category || '—'}</td>
                                                    <td className="mono">{b.score ?? '—'}</td>
                                                    <td>{b.lead_category || '—'}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <Skeleton className="h-96" />
                )}

                <div className="surface overflow-hidden">
                    <div className="p-5 border-b border-border/60"><div className="eyebrow">Past reports</div><div className="heading text-base mt-1">History</div></div>
                    {!list ? <div className="p-5"><Skeleton className="h-12" /></div> :
                        list.length === 0 ? <EmptyState title="No past reports" description="Generate the first one above." />
                            : (
                                <div className="divide-y divide-border/60">
                                    {list.map((r) => (
                                        <Link key={r.id} to={`/reports/${r.id}`} className="flex items-center justify-between p-4 hover:bg-[hsl(var(--canvas-3))]">
                                            <div className="flex items-center gap-3">
                                                <Calendar className="h-4 w-4 text-muted-foreground" strokeWidth={1.5} />
                                                <div>
                                                    <div className="text-sm font-medium">{r.report_date}</div>
                                                    <div className="text-xs text-muted-foreground mono">{fmt(r.created_at)} · {r.generated_by}</div>
                                                </div>
                                            </div>
                                            <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />
                                        </Link>
                                    ))}
                                </div>
                            )}
                </div>
            </div>
        </div>
    );
}

function Block({ title, items, keyField }) {
    return (
        <div className="surface-2 p-4">
            <div className="eyebrow">{title}</div>
            <div className="mt-3 space-y-2">
                {items.length === 0 && <div className="text-xs text-muted-foreground">No data</div>}
                {items.slice(0, 6).map((i) => (
                    <div key={i[keyField]} className="flex items-center justify-between text-sm">
                        <span className="truncate">{i[keyField] || '—'}</span>
                        <span className="mono text-muted-foreground">{i.count}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
