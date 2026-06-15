import React, { useEffect, useState } from 'react';
import { AppLink as Link, useParams } from '../lib/router';
import { toast } from 'sonner';
import { ArrowLeft, Download } from 'lucide-react';
import { api, API } from '../lib/api';
import { PageHeader, Skeleton } from '../components/radar/Common';

export default function ReportDetail() {
    const { id } = useParams();
    const [r, setR] = useState(null);

    useEffect(() => {
        api.get(`/reports/${id}`).then(res => setR(res.data)).catch(() => toast.error('Not found'));
    }, [id]);

    const download = async (kind) => {
        try {
            const token = localStorage.getItem('radar_token');
            const url = `${API}/reports/${id}/download/${kind}`;
            const resp = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
            const blob = await resp.blob();
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = `report-${r?.report_date || id}.${kind === 'xlsx' ? 'xlsx' : kind}`;
            a.click();
        } catch { toast.error('Download failed'); }
    };

    if (!r) return <div><Link to="/reports" className="btn-ghost text-xs"><ArrowLeft className="h-3.5 w-3.5" /> Back</Link><Skeleton className="h-96 mt-3" /></div>;

    return (
        <div>
            <Link to="/reports" className="btn-ghost mb-3 text-xs"><ArrowLeft className="h-3.5 w-3.5" /> Back to Reports</Link>
            <PageHeader
                eyebrow={r.report_date}
                title="Daily Intelligence Report"
                actions={(<>
                    <button onClick={() => download('pdf')} className="btn-secondary"><Download className="h-4 w-4" /> PDF</button>
                    <button onClick={() => download('xlsx')} className="btn-secondary"><Download className="h-4 w-4" /> Excel</button>
                    <button onClick={() => download('csv')} className="btn-secondary"><Download className="h-4 w-4" /> CSV</button>
                </>)}
            />
            <pre className="surface p-5 overflow-auto scrollbar-cred mono text-xs whitespace-pre-wrap">{JSON.stringify(r.report_json, null, 2)}</pre>
        </div>
    );
}
