import React, { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { Filter } from 'lucide-react';
import { api } from '../lib/api';
import { PageHeader, Skeleton, EmptyState } from '../components/radar/Common';

export default function AdminAuditLogs() {
    const [logs, setLogs] = useState(null);
    const [action, setAction] = useState('');
    const [entity, setEntity] = useState('');

    const load = async () => {
        try {
            const params = new URLSearchParams();
            if (action) params.set('action', action);
            if (entity) params.set('entity_type', entity);
            const r = await api.get(`/audit-logs?${params}`);
            setLogs(r.data);
        } catch { toast.error('Failed'); setLogs([]); }
    };
    useEffect(() => { load(); }, []);

    return (
        <div>
            <PageHeader eyebrow="Admin" title="Audit Logs" subtitle="Every mutation, recorded." actions={(<button onClick={load} className="btn-secondary"><Filter className="h-4 w-4" /> Apply</button>)} />
            <div className="surface p-4 mb-4 grid sm:grid-cols-2 gap-3">
                <input className="field-input" placeholder="Action (e.g. login, create_business)" value={action} onChange={e => setAction(e.target.value)} />
                <input className="field-input" placeholder="Entity type (e.g. business, user, settings)" value={entity} onChange={e => setEntity(e.target.value)} />
            </div>
            {!logs ? <Skeleton className="h-64" /> : logs.length === 0 ? <EmptyState title="No matching audit logs" /> : (
                <div className="surface overflow-hidden">
                    <div className="overflow-x-auto scrollbar-cred">
                        <table className="table-cred">
                            <thead><tr><th>When</th><th>User</th><th>Action</th><th>Entity</th><th>ID</th><th>IP</th></tr></thead>
                            <tbody>
                                {logs.map(l => (
                                    <tr key={l.id}>
                                        <td className="mono text-xs">{new Date(l.created_at).toLocaleString()}</td>
                                        <td className="mono text-xs">{l.user_email || '—'}</td>
                                        <td>{l.action}</td>
                                        <td className="text-muted-foreground">{l.entity_type}</td>
                                        <td className="mono text-xs text-muted-foreground">{l.entity_id?.slice(0, 8) || '—'}</td>
                                        <td className="mono text-xs text-muted-foreground">{l.ip_address || '—'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}
