import React, { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { Plus, Pencil, Trash2, Copy } from 'lucide-react';
import { api } from '../lib/api';
import { PageHeader, Skeleton } from '../components/radar/Common';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger } from '../components/ui/dialog';
import { TIDS } from '../constants/testIds';

export default function AdminUsers() {
    const [users, setUsers] = useState(null);
    const [open, setOpen] = useState(false);
    const [form, setForm] = useState({ name: '', email: '', role: 'Subscriber' });
    const [creating, setCreating] = useState(false);
    const [createdInfo, setCreatedInfo] = useState(null);

    const load = async () => {
        try { const r = await api.get('/users'); setUsers(r.data); } catch { toast.error('Failed'); setUsers([]); }
    };
    useEffect(() => { load(); }, []);

    const create = async () => {
        setCreating(true);
        try {
            const r = await api.post('/users', form);
            setCreatedInfo(r.data);
            await load();
            toast.success('User created');
        } catch (e) { toast.error(e?.response?.data?.detail || 'Create failed'); }
        finally { setCreating(false); }
    };

    const updateRole = async (id, role) => {
        try { await api.patch(`/users/${id}`, { role }); await load(); toast.success('Role updated'); } catch { toast.error('Failed'); }
    };
    const toggleStatus = async (u) => {
        try { await api.patch(`/users/${u.id}`, { status: u.status === 'Active' ? 'Inactive' : 'Active' }); await load(); } catch { toast.error('Failed'); }
    };
    const del = async (id) => {
        if (!confirm('Delete user?')) return;
        try { await api.delete(`/users/${id}`); await load(); toast.success('Deleted'); } catch { toast.error('Failed'); }
    };

    return (
        <div>
            <PageHeader
                eyebrow="Admin"
                title="Users"
                subtitle="Roles & access management."
                actions={(
                    <Dialog open={open} onOpenChange={(v) => { setOpen(v); if (!v) { setCreatedInfo(null); setForm({ name: '', email: '', role: 'Subscriber' }); } }}>
                        <DialogTrigger asChild>
                            <button data-testid={TIDS.userCreateBtn} className="btn-primary"><Plus className="h-4 w-4" /> New user</button>
                        </DialogTrigger>
                        <DialogContent className="bg-[hsl(var(--canvas-2))] border border-border">
                            <DialogHeader><DialogTitle>Create user</DialogTitle></DialogHeader>
                            {createdInfo ? (
                                <div className="space-y-3">
                                    <div className="text-sm">User created. Share the temporary password:</div>
                                    <div className="surface-2 p-3 flex items-center justify-between gap-3">
                                        <div>
                                            <div className="eyebrow">Email</div><div className="text-sm mono">{createdInfo.user.email}</div>
                                            <div className="eyebrow mt-3">Temp password</div><div className="text-sm mono">{createdInfo.temporary_password}</div>
                                        </div>
                                        <button onClick={() => { navigator.clipboard.writeText(createdInfo.temporary_password); toast.success('Copied'); }} className="btn-ghost"><Copy className="h-4 w-4" /></button>
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    <div><label className="eyebrow block mb-1">Name</label><input data-testid={TIDS.userCreateName} className="field-input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></div>
                                    <div><label className="eyebrow block mb-1">Email</label><input data-testid={TIDS.userCreateEmail} className="field-input" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></div>
                                    <div>
                                        <label className="eyebrow block mb-1">Role</label>
                                        <select data-testid={TIDS.userCreateRole} className="field-input" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                                            <option>Admin</option><option>Analyst</option><option>Subscriber</option>
                                        </select>
                                    </div>
                                </div>
                            )}
                            <DialogFooter>
                                {createdInfo ? (
                                    <button onClick={() => { setOpen(false); setCreatedInfo(null); }} className="btn-primary">Done</button>
                                ) : (
                                    <button data-testid={TIDS.userCreateSubmit} onClick={create} disabled={creating} className="btn-primary">{creating ? 'Creating…' : 'Create user'}</button>
                                )}
                            </DialogFooter>
                        </DialogContent>
                    </Dialog>
                )}
            />

            {!users ? <Skeleton className="h-64" /> : (
                <div className="surface overflow-hidden">
                    <div className="overflow-x-auto scrollbar-cred">
                        <table className="table-cred">
                            <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Created</th><th></th></tr></thead>
                            <tbody>
                                {users.map(u => (
                                    <tr key={u.id} data-testid={TIDS.userRow(u.id)}>
                                        <td className="font-medium">{u.name}</td>
                                        <td className="mono text-sm">{u.email}</td>
                                        <td>
                                            <select className="field-input py-1.5 text-xs" value={u.role} onChange={(e) => updateRole(u.id, e.target.value)}>
                                                <option>Admin</option><option>Analyst</option><option>Subscriber</option>
                                            </select>
                                        </td>
                                        <td><button onClick={() => toggleStatus(u)} className={`pill-base ${u.status === 'Active' ? 'pill-warm' : 'pill-cold'} text-[10px]`}>{u.status}</button></td>
                                        <td className="mono text-xs text-muted-foreground">{new Date(u.created_at).toLocaleDateString()}</td>
                                        <td><button onClick={() => del(u.id)} className="btn-ghost text-[hsl(var(--destructive))]"><Trash2 className="h-4 w-4" /></button></td>
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
