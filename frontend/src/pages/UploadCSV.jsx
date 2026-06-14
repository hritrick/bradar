import React, { useState } from 'react';
import { toast } from 'sonner';
import { Upload, FileSpreadsheet, CheckCircle2, AlertTriangle } from 'lucide-react';
import { api } from '../lib/api';
import { PageHeader } from '../components/radar/Common';
import { TIDS } from '../constants/testIds';

const SAMPLE_HEADERS = ['business_name','registration_date','company_type','category','sub_category','website','phone','email','director_name','employee_estimate','city','state','pincode','source'];

export default function UploadCSV() {
    const [file, setFile] = useState(null);
    const [drag, setDrag] = useState(false);
    const [preview, setPreview] = useState(null);
    const [committing, setCommitting] = useState(false);
    const [committed, setCommitted] = useState(null);

    const handle = async (f, doCommit = false) => {
        if (!f) return;
        setFile(f);
        const fd = new FormData();
        fd.append('file', f);
        try {
            const r = await api.post(`/businesses/upload-csv?preview=${doCommit ? 'false' : 'true'}`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
            if (doCommit) {
                setCommitted(r.data);
                setPreview(null);
                toast.success(`Inserted ${r.data.inserted}; duplicates ${r.data.duplicates}`);
            } else {
                setPreview(r.data);
            }
        } catch (e) {
            toast.error(e?.response?.data?.detail || 'CSV upload failed');
        }
    };

    const onDrop = (e) => {
        e.preventDefault();
        setDrag(false);
        const f = e.dataTransfer.files?.[0];
        if (f) handle(f);
    };

    const commit = async () => {
        if (!file) return;
        setCommitting(true);
        await handle(file, true);
        setCommitting(false);
    };

    return (
        <div className="max-w-3xl">
            <PageHeader eyebrow="Bulk import" title="Upload CSV" subtitle="Add many businesses at once. We dedupe by name + pincode + phone/email." />

            <div data-testid={TIDS.csvDrop}
                onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
                onDragLeave={() => setDrag(false)}
                onDrop={onDrop}
                className={`surface border-dashed p-10 text-center transition-colors ${drag ? 'border-[hsl(var(--primary))]/40 shadow-[var(--glow-gold)]' : ''}`}>
                <div className="mx-auto h-12 w-12 rounded-full bg-[hsl(var(--canvas-3))] border border-border flex items-center justify-center mb-4"><FileSpreadsheet className="h-5 w-5" strokeWidth={1.5} /></div>
                <div className="heading text-lg">{file ? file.name : 'Drag & drop a CSV here'}</div>
                <div className="text-sm text-muted-foreground mt-2">or</div>
                <label className="btn-primary mt-3 inline-flex cursor-pointer">
                    <Upload className="h-4 w-4" /> Browse file
                    <input type="file" accept=".csv" className="hidden" onChange={(e) => handle(e.target.files?.[0])} />
                </label>
                <div className="text-xs text-muted-foreground mt-5 mono">Headers: {SAMPLE_HEADERS.join(', ')}</div>
            </div>

            {preview && (
                <div className="surface mt-6 overflow-hidden">
                    <div className="p-5 flex items-center justify-between">
                        <div>
                            <div className="eyebrow">Preview</div>
                            <div className="heading text-base">{preview.row_count} rows detected</div>
                        </div>
                        <button data-testid={TIDS.csvCommit} onClick={commit} disabled={committing} className="btn-primary">
                            <CheckCircle2 className="h-4 w-4" /> {committing ? 'Importing…' : 'Commit import'}
                        </button>
                    </div>
                    {preview.sample.length > 0 && (
                        <div className="overflow-x-auto scrollbar-cred">
                            <table className="table-cred">
                                <thead><tr>{Object.keys(preview.sample[0]).map(k => <th key={k}>{k}</th>)}</tr></thead>
                                <tbody>
                                    {preview.sample.map((r, i) => (
                                        <tr key={i}>{Object.values(r).map((v, j) => <td key={j} className="max-w-[200px] truncate">{v}</td>)}</tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}

            {committed && (
                <div className="surface p-5 mt-6">
                    <div className="eyebrow">Import complete</div>
                    <div className="grid grid-cols-3 gap-3 mt-3">
                        <div className="surface-2 p-3"><div className="eyebrow">Inserted</div><div className="heading text-2xl mono mt-1">{committed.inserted}</div></div>
                        <div className="surface-2 p-3"><div className="eyebrow">Duplicates</div><div className="heading text-2xl mono mt-1">{committed.duplicates}</div></div>
                        <div className="surface-2 p-3"><div className="eyebrow">Errors</div><div className="heading text-2xl mono mt-1">{committed.errors?.length || 0}</div></div>
                    </div>
                    {committed.errors?.length > 0 && (
                        <div className="mt-4 text-sm text-muted-foreground space-y-1">
                            {committed.errors.map((er, i) => <div key={i} className="flex items-start gap-2"><AlertTriangle className="h-3.5 w-3.5 mt-0.5 text-[hsl(var(--destructive))]" /> <span className="mono text-xs">{er}</span></div>)}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
