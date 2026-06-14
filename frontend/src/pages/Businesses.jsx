import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, X, Download, FileSpreadsheet, FileText, Plus, ChevronLeft, ChevronRight } from 'lucide-react';
import { toast } from 'sonner';
import { api, API } from '../lib/api';
import { PageHeader, Skeleton, EmptyState } from '../components/radar/Common';
import { StatusPill } from '../components/radar/StatusPill';
import { TIDS } from '../constants/testIds';
import { Sheet, SheetTrigger, SheetContent } from '../components/ui/sheet';
import { useAuth } from '../lib/AuthContext';

function useDistinct() {
    const [d, setD] = useState({ cities: [], states: [], categories: [], sources: [], predicted_needs: [] });
    useEffect(() => { api.get('/businesses/distinct').then(r => setD(r.data)).catch(() => {}); }, []);
    return d;
}

function FilterPanel({ filters, setFilters, onApply, onClear, distinct }) {
    const update = (k, v) => setFilters((f) => ({ ...f, [k]: v }));
    const toggleArr = (k, v) => {
        setFilters((f) => {
            const cur = new Set(f[k] || []);
            if (cur.has(v)) cur.delete(v); else cur.add(v);
            return { ...f, [k]: Array.from(cur) };
        });
    };
    const MultiPick = ({ label, options, value, k, tid }) => (
        <div>
            <label className="eyebrow block mb-2">{label}</label>
            <div data-testid={tid} className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto scrollbar-cred">
                {options.length === 0 ? <span className="text-xs text-muted-foreground">No options</span> : null}
                {options.map((o) => (
                    <button key={o} type="button" onClick={() => toggleArr(k, o)} className={`pill-base text-[10px] ${value?.includes(o) ? 'pill-hot' : 'pill-neutral'}`}>{o}</button>
                ))}
            </div>
        </div>
    );
    return (
        <div className="space-y-5">
            <div>
                <label className="eyebrow block mb-2">Pincode</label>
                <input data-testid={TIDS.bizFilterPincode} className="field-input" value={filters.pincode || ''} onChange={(e) => update('pincode', e.target.value)} placeholder="400001" />
            </div>
            <MultiPick label="Industry" options={distinct.industries || []} value={filters.industry} k="industry" tid={TIDS.bizFilterIndustry} />
            <MultiPick label="City" options={distinct.cities} value={filters.city} k="city" tid={TIDS.bizFilterCity} />
            <MultiPick label="State" options={distinct.states} value={filters.state} k="state" tid={TIDS.bizFilterState} />
            <MultiPick label="Category" options={distinct.categories} value={filters.category} k="category" tid={TIDS.bizFilterCategory} />
            <MultiPick label="Predicted Need" options={distinct.predicted_needs} value={filters.predicted_need} k="predicted_need" />
            <div>
                <label className="eyebrow block mb-2">Lead Category</label>
                <div data-testid={TIDS.bizFilterLead} className="flex gap-1.5">
                    {['HOT', 'WARM', 'COLD'].map((l) => (
                        <button key={l} type="button" onClick={() => toggleArr('lead_category', l)} className={`pill-base text-[10px] ${filters.lead_category?.includes(l) ? (l === 'HOT' ? 'pill-hot' : l === 'WARM' ? 'pill-warm' : 'pill-cold') : 'pill-neutral'}`}>{l}</button>
                    ))}
                </div>
            </div>
            <div>
                <label className="eyebrow block mb-2">Score range</label>
                <div className="flex gap-2 items-center">
                    <input data-testid={TIDS.bizFilterMinScore} className="field-input mono" type="number" min={0} max={100} placeholder="Min" value={filters.min_score ?? ''} onChange={(e) => update('min_score', e.target.value ? parseInt(e.target.value, 10) : null)} />
                    <span className="text-muted-foreground">—</span>
                    <input data-testid={TIDS.bizFilterMaxScore} className="field-input mono" type="number" min={0} max={100} placeholder="Max" value={filters.max_score ?? ''} onChange={(e) => update('max_score', e.target.value ? parseInt(e.target.value, 10) : null)} />
                </div>
            </div>
            <div>
                <label className="eyebrow block mb-2">Registered date</label>
                <div className="flex gap-2 items-center">
                    <input className="field-input" type="date" value={filters.registered_after || ''} onChange={(e) => update('registered_after', e.target.value || null)} />
                    <span className="text-muted-foreground">—</span>
                    <input className="field-input" type="date" value={filters.registered_before || ''} onChange={(e) => update('registered_before', e.target.value || null)} />
                </div>
            </div>
            <div>
                <label className="eyebrow block mb-2">Source</label>
                <div className="flex flex-wrap gap-1.5">
                    {distinct.sources.map((s) => (
                        <button key={s} type="button" onClick={() => toggleArr('source', s)} className={`pill-base text-[10px] ${filters.source?.includes(s) ? 'pill-hot' : 'pill-neutral'}`}>{s}</button>
                    ))}
                </div>
            </div>
            <div className="flex gap-2 pt-2">
                <button data-testid={TIDS.bizFilterApply} onClick={onApply} className="btn-primary flex-1 justify-center">Apply</button>
                <button data-testid={TIDS.bizFilterClear} onClick={onClear} className="btn-secondary"><X className="h-3.5 w-3.5" /> Clear</button>
            </div>
        </div>
    );
}

export default function Businesses() {
    const { user } = useAuth();
    const canMutate = user?.role === 'Admin' || user?.role === 'Analyst';
    const distinct = useDistinct();
    const [filters, setFilters] = useState({});
    const [applied, setApplied] = useState({});
    const [search, setSearch] = useState('');
    const [searchDeb, setSearchDeb] = useState('');
    const [page, setPage] = useState(1);
    const [pageSize] = useState(25);
    const [data, setData] = useState({ items: [], total: 0, page: 1, page_size: 25 });
    const [loading, setLoading] = useState(true);
    const [mobileFilters, setMobileFilters] = useState(false);

    useEffect(() => {
        const t = setTimeout(() => setSearchDeb(search), 350);
        return () => clearTimeout(t);
    }, [search]);

    const params = useMemo(() => {
        const p = new URLSearchParams();
        p.set('page', String(page));
        p.set('page_size', String(pageSize));
        if (searchDeb) p.set('search', searchDeb);
        if (applied.pincode) p.set('pincode', applied.pincode);
        if (applied.min_score != null) p.set('min_score', String(applied.min_score));
        if (applied.max_score != null) p.set('max_score', String(applied.max_score));
        if (applied.registered_after) p.set('registered_after', applied.registered_after);
        if (applied.registered_before) p.set('registered_before', applied.registered_before);
        (applied.city || []).forEach(v => p.append('city', v));
        (applied.state || []).forEach(v => p.append('state', v));
        (applied.industry || []).forEach(v => p.append('industry', v));
        (applied.category || []).forEach(v => p.append('category', v));
        (applied.source || []).forEach(v => p.append('source', v));
        (applied.predicted_need || []).forEach(v => p.append('predicted_need', v));
        (applied.lead_category || []).forEach(v => p.append('lead_category', v));
        return p.toString();
    }, [applied, page, pageSize, searchDeb]);

    const load = async () => {
        setLoading(true);
        try {
            const r = await api.get(`/businesses?${params}`);
            setData(r.data);
        } catch (e) {
            toast.error('Failed to load businesses');
        } finally {
            setLoading(false);
        }
    };
    useEffect(() => { load(); }, [params]);

    const exportFile = async (kind) => {
        try {
            const token = localStorage.getItem('radar_token');
            const url = `${API}/businesses/export/${kind}`;
            const r = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
            if (!r.ok) throw new Error('Export failed');
            const blob = await r.blob();
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = `businesses.${kind === 'xlsx' ? 'xlsx' : 'csv'}`;
            a.click();
            toast.success(`Downloaded ${kind.toUpperCase()}`);
        } catch (e) {
            toast.error('Export failed');
        }
    };

    const totalPages = Math.max(1, Math.ceil((data.total || 0) / pageSize));

    return (
        <div>
            <PageHeader
                eyebrow="Workspace"
                title="Businesses"
                subtitle="All discovered businesses, enriched and scored."
                actions={(
                    <>
                        <button onClick={() => exportFile('csv')} data-testid={TIDS.bizExportCsv} className="btn-secondary"><FileText className="h-4 w-4" /> CSV</button>
                        <button onClick={() => exportFile('xlsx')} data-testid={TIDS.bizExportXlsx} className="btn-secondary"><FileSpreadsheet className="h-4 w-4" /> Excel</button>
                        {canMutate && <Link to="/businesses/new" className="btn-primary"><Plus className="h-4 w-4" /> Add</Link>}
                    </>
                )}
            />
            <div className="grid lg:grid-cols-[280px_1fr] gap-6">
                {/* Filter rail desktop */}
                <aside className="hidden lg:block surface p-5 h-fit sticky top-20">
                    <div className="flex items-center gap-2 mb-4"><Filter className="h-4 w-4" /><div className="heading text-sm font-medium">Filters</div></div>
                    <FilterPanel filters={filters} setFilters={setFilters} onApply={() => { setApplied(filters); setPage(1); }} onClear={() => { setFilters({}); setApplied({}); setPage(1); }} distinct={distinct} />
                </aside>

                {/* Mobile filters in sheet */}
                <div className="lg:hidden">
                    <Sheet open={mobileFilters} onOpenChange={setMobileFilters}>
                        <SheetTrigger asChild>
                            <button className="btn-secondary w-full justify-center mb-4"><Filter className="h-4 w-4" /> Filters</button>
                        </SheetTrigger>
                        <SheetContent side="right" className="bg-[hsl(var(--canvas-2))] border-l border-border overflow-y-auto">
                            <div className="heading text-base font-semibold mb-4">Filters</div>
                            <FilterPanel filters={filters} setFilters={setFilters} onApply={() => { setApplied(filters); setPage(1); setMobileFilters(false); }} onClear={() => { setFilters({}); setApplied({}); setPage(1); }} distinct={distinct} />
                        </SheetContent>
                    </Sheet>
                </div>

                <div>
                    <div className="surface p-3 mb-4">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <input data-testid={TIDS.bizSearch} className="field-input pl-10" placeholder="Search business name, director, phone, email…" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
                        </div>
                    </div>
                    <div className="surface overflow-hidden">
                        <div className="flex items-center justify-between p-4 text-xs text-muted-foreground border-b border-border/60">
                            <div>{loading ? 'Loading…' : `${data.total} businesses`}</div>
                            <div className="flex items-center gap-2">
                                <span className="hidden sm:inline">Page {data.page} of {totalPages}</span>
                                <button disabled={data.page <= 1} onClick={() => setPage(p => Math.max(1, p - 1))} className="btn-ghost p-1.5 disabled:opacity-40"><ChevronLeft className="h-4 w-4" /></button>
                                <button disabled={data.page >= totalPages} onClick={() => setPage(p => Math.min(totalPages, p + 1))} className="btn-ghost p-1.5 disabled:opacity-40"><ChevronRight className="h-4 w-4" /></button>
                            </div>
                        </div>
                        <div className="overflow-x-auto scrollbar-cred">
                            {loading ? (
                                <div className="p-5 space-y-3">
                                    {Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="h-9" />)}
                                </div>
                            ) : data.items.length === 0 ? (
                                <EmptyState title="No businesses match" description="Try clearing filters, broadening your search, or running a discovery." />
                            ) : (
                                <table className="table-cred" data-testid={TIDS.bizTable}>
                                    <thead>
                                        <tr>
                                            <th>Business</th>
                                            <th className="hidden sm:table-cell">City</th>
                                            <th className="hidden md:table-cell">Industry</th>
                                            <th className="hidden lg:table-cell">Director</th>
                                            <th className="hidden lg:table-cell">Predicted Need</th>
                                            <th>Lead</th>
                                            <th className="hidden md:table-cell">Source</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {data.items.map((b) => (
                                            <tr key={b.id} data-testid={TIDS.bizRow(b.id)}>
                                                <td>
                                                    <Link to={`/businesses/${b.id}`} className="font-medium hover:text-[hsl(var(--primary))]">{b.business_name}</Link>
                                                    <div className="text-xs text-muted-foreground mono mt-1">{b.gst_number || ''} {b.pincode || ''}</div>
                                                </td>
                                                <td className="hidden sm:table-cell">{b.city || '—'}</td>
                                                <td className="hidden md:table-cell">{b.industry || b.category || '—'}</td>
                                                <td className="hidden lg:table-cell">{b.director_name || '—'}</td>
                                                <td className="hidden lg:table-cell text-muted-foreground">{b.latest_predicted_need || '—'}</td>
                                                <td><StatusPill category={b.latest_lead_category} score={b.latest_score} /></td>
                                                <td className="hidden md:table-cell text-muted-foreground mono text-xs">{b.source}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
