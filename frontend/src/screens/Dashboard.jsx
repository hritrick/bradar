import React, { useEffect, useState } from 'react';
import { AppLink as Link } from '../lib/router';
import { Building2, Flame, BarChart3, Target, ArrowRight, RefreshCw } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, BarChart, Bar } from 'recharts';
import { api } from '../lib/api';
import { KpiCard } from '../components/radar/KpiCard';
import { StatusPill } from '../components/radar/StatusPill';
import { PageHeader, Skeleton, EmptyState } from '../components/radar/Common';
import { TIDS } from '../constants/testIds';
import { toast } from 'sonner';

function fmtDate(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    return d.toLocaleString('en-IN', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
}

export default function Dashboard() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    const load = async () => {
        setLoading(true);
        try {
            const r = await api.get('/dashboard');
            setData(r.data);
        } catch (e) {
            toast.error('Failed to load dashboard');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { load(); }, []);

    if (loading || !data) {
        return (
            <div>
                <PageHeader eyebrow="Today" title="Dashboard" subtitle="Live intelligence on newly discovered businesses" />
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-32" />)}
                </div>
                <div className="grid lg:grid-cols-3 gap-4 mt-6">
                    <Skeleton className="h-64 lg:col-span-2" />
                    <Skeleton className="h-64" />
                </div>
            </div>
        );
    }

    const { kpis, seven_days, by_city, by_industry, by_category, by_predicted_need, by_pincode, recent } = data;

    return (
        <div>
            <PageHeader
                eyebrow={`India · ${new Date().toLocaleDateString('en-IN', { weekday: 'long', day: '2-digit', month: 'short' })}`}
                title="Dashboard"
                subtitle="Newly discovered businesses, enriched and scored. Find your next 10 customers, today."
                actions={(
                    <>
                        <button onClick={load} className="btn-secondary"><RefreshCw className="h-4 w-4" /> Refresh</button>
                        <Link to="/reports" className="btn-primary">Today’s Report <ArrowRight className="h-4 w-4" /></Link>
                    </>
                )}
            />

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <KpiCard tid={TIDS.kpiTotal} label="Total Businesses" value={kpis.total_businesses.toLocaleString('en-IN')} icon={Building2} />
                <KpiCard tid={TIDS.kpiToday} label="Today's New" value={kpis.today_new.toLocaleString('en-IN')} icon={Target} />
                <KpiCard tid={TIDS.kpiHot} label="Hot Leads" value={kpis.hot_leads.toLocaleString('en-IN')} icon={Flame} accent />
                <KpiCard tid={TIDS.kpiAvg} label="Avg Lead Score" value={kpis.avg_score} icon={BarChart3} />
            </div>

            <div className="grid lg:grid-cols-3 gap-4 mt-6">
                <div className="surface lg:col-span-2 p-5 sheen-overlay relative overflow-hidden">
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <div className="eyebrow">Last 7 days</div>
                            <div className="heading text-lg mt-1">New Businesses Discovered</div>
                        </div>
                    </div>
                    <div className="h-56">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={seven_days} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="gold" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="0%" stopColor="hsl(42 55% 72%)" stopOpacity={0.35} />
                                        <stop offset="100%" stopColor="hsl(42 55% 72%)" stopOpacity={0.02} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid stroke="hsl(240 6% 14%)" strokeDasharray="3 6" vertical={false} />
                                <XAxis dataKey="date" tick={{ fill: 'hsl(40 8% 72%)', fontSize: 11 }} tickFormatter={(v) => new Date(v).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })} axisLine={false} tickLine={false} />
                                <YAxis tick={{ fill: 'hsl(40 8% 72%)', fontSize: 11 }} axisLine={false} tickLine={false} />
                                <Tooltip cursor={{ stroke: 'hsl(42 55% 72%)', strokeWidth: 1, strokeDasharray: '3 3' }} contentStyle={{ background: 'hsl(240 6% 9%)', border: '1px solid hsl(240 6% 14%)', borderRadius: 12, color: 'hsl(40 20% 96%)' }} />
                                <Area type="monotone" dataKey="count" stroke="hsl(42 55% 72%)" fill="url(#gold)" strokeWidth={2} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="surface p-5">
                    <div className="eyebrow">Lead temperature</div>
                    <div className="heading text-lg mt-1">Distribution</div>
                    <div className="mt-5 space-y-4">
                        {[
                            { label: 'HOT', val: kpis.hot_leads, total: (kpis.hot_leads + kpis.warm_leads + kpis.cold_leads) || 1, cls: 'pill-hot' },
                            { label: 'WARM', val: kpis.warm_leads, total: (kpis.hot_leads + kpis.warm_leads + kpis.cold_leads) || 1, cls: 'pill-warm' },
                            { label: 'COLD', val: kpis.cold_leads, total: (kpis.hot_leads + kpis.warm_leads + kpis.cold_leads) || 1, cls: 'pill-cold' },
                        ].map((row) => (
                            <div key={row.label}>
                                <div className="flex items-center justify-between text-xs mb-1">
                                    <span className={`pill-base ${row.cls}`}>{row.label}</span>
                                    <span className="mono">{row.val}</span>
                                </div>
                                <div className="h-1.5 rounded-full bg-[hsl(var(--canvas-3))] overflow-hidden">
                                    <div className={row.label === 'HOT' ? 'h-full bg-[hsl(var(--primary))]' : row.label === 'WARM' ? 'h-full bg-[hsl(35_22%_78%)]' : 'h-full bg-[hsl(210_10%_62%)]'} style={{ width: `${(row.val * 100) / row.total}%` }} />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            <div className="grid lg:grid-cols-3 gap-4 mt-6">
                <div className="surface p-5">
                    <div className="eyebrow">By City</div>
                    <div className="heading text-lg mt-1">Top regions</div>
                    <div className="mt-4 h-56">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={by_city} margin={{ top: 0, right: 10, left: -20, bottom: 0 }}>
                                <CartesianGrid stroke="hsl(240 6% 14%)" strokeDasharray="3 6" vertical={false} />
                                <XAxis dataKey="city" tick={{ fill: 'hsl(40 8% 72%)', fontSize: 10 }} axisLine={false} tickLine={false} />
                                <YAxis tick={{ fill: 'hsl(40 8% 72%)', fontSize: 11 }} axisLine={false} tickLine={false} />
                                <Tooltip cursor={{ fill: 'hsl(240 6% 9%)' }} contentStyle={{ background: 'hsl(240 6% 9%)', border: '1px solid hsl(240 6% 14%)', borderRadius: 12 }} />
                                <Bar dataKey="count" fill="hsl(42 55% 72%)" radius={[6, 6, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
                <div className="surface p-5">
                    <div className="eyebrow">By Industry</div>
                    <div className="heading text-lg mt-1">Top sectors</div>
                    <div className="mt-4 space-y-3">
                        {(by_industry || []).length === 0 && <div className="text-sm text-muted-foreground">No data yet</div>}
                        {(by_industry || []).map((c) => (
                            <div key={c.industry} className="flex items-center justify-between text-sm">
                                <span className="truncate">{c.industry}</span>
                                <span className="mono text-muted-foreground">{c.count.toLocaleString('en-IN')}</span>
                            </div>
                        ))}
                    </div>
                </div>
                <div className="surface p-5">
                    <div className="eyebrow">Predicted Needs</div>
                    <div className="heading text-lg mt-1">What they'll buy</div>
                    <div className="mt-4 space-y-3">
                        {by_predicted_need.length === 0 && <div className="text-sm text-muted-foreground">No data yet</div>}
                        {by_predicted_need.map((c) => (
                            <div key={c.need} className="flex items-center justify-between text-sm">
                                <span className="truncate">{c.need}</span>
                                <span className="mono text-muted-foreground">{c.count.toLocaleString('en-IN')}</span>
                            </div>
                        ))}
                    </div>
                </div>
                <div className="surface p-5">
                    <div className="eyebrow">Top Pincodes</div>
                    <div className="heading text-lg mt-1">Geo hotspots</div>
                    <div className="mt-4 space-y-3">
                        {(by_pincode || []).length === 0 && <div className="text-sm text-muted-foreground">No data yet</div>}
                        {(by_pincode || []).slice(0, 8).map((c) => (
                            <div key={c.pincode} className="flex items-center justify-between text-sm">
                                <span className="mono">{c.pincode}</span>
                                <span className="mono text-muted-foreground">{c.count.toLocaleString('en-IN')}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            <div className="surface mt-6 overflow-hidden">
                <div className="p-5 flex items-center justify-between">
                    <div>
                        <div className="eyebrow">Live feed</div>
                        <div className="heading text-lg mt-1">Recent Discoveries</div>
                    </div>
                    <Link to="/businesses" className="btn-ghost text-sm">View all <ArrowRight className="h-3.5 w-3.5" /></Link>
                </div>
                <div className="overflow-x-auto scrollbar-cred">
                    {recent.length === 0 ? (
                        <EmptyState title="No businesses yet" description="Trigger Discovery or add a business manually to see them appear here." />
                    ) : (
                        <table className="table-cred">
                            <thead>
                                <tr>
                                    <th>Business</th>
                                    <th>City</th>
                                    <th>Industry</th>
                                    <th>Added</th>
                                    <th>Lead</th>
                                </tr>
                            </thead>
                            <tbody>
                                {recent.map((b) => (
                                    <tr key={b.id}>
                                        <td className="font-medium"><Link to={`/businesses/${b.id}`} className="hover:text-[hsl(var(--primary))]">{b.business_name}</Link></td>
                                        <td>{b.city || '—'}</td>
                                        <td>{b.industry || b.category || '—'}</td>
                                        <td className="mono text-muted-foreground">{fmtDate(b.created_at)}</td>
                                        <td><StatusPill category={b.lead_category} score={b.score} /></td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    );
}
