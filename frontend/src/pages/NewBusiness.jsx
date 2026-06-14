import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { ArrowLeft, Save, Building2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../lib/api';
import { PageHeader } from '../components/radar/Common';
import { TIDS } from '../constants/testIds';

const INITIAL = {
    business_name: '', gst_number: '', registration_date: '', company_type: 'Private Limited',
    industry: '', category: '', sub_category: '',
    website: '', phone: '', email: '', linkedin_url: '', director_name: '', employee_estimate: '',
    address: '', locality: '', city: '', district: '', state: '', country: 'India', pincode: '',
    source: 'manual',
};

const INDUSTRIES = ['Real Estate', 'Manufacturing', 'Logistics', 'Retail', 'IT Services', 'Healthcare'];

export default function NewBusiness() {
    const [form, setForm] = useState(INITIAL);
    const [saving, setSaving] = useState(false);
    const nav = useNavigate();

    const update = (k, v) => setForm((f) => ({ ...f, [k]: v }));

    const submit = async (e) => {
        e.preventDefault();
        if (!form.business_name) return toast.error('Business name is required');
        setSaving(true);
        try {
            const payload = { ...form };
            if (payload.registration_date === '') payload.registration_date = null;
            if (payload.employee_estimate === '') payload.employee_estimate = null;
            else payload.employee_estimate = parseInt(payload.employee_estimate, 10);
            const r = await api.post('/businesses', payload);
            toast.success('Business saved and enriched');
            nav(`/businesses/${r.data.id}`);
        } catch (err) {
            toast.error(err?.response?.data?.detail || 'Failed to save');
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="max-w-3xl">
            <Link to="/businesses" className="btn-ghost mb-3 text-xs"><ArrowLeft className="h-3.5 w-3.5" /> Back to Businesses</Link>
            <PageHeader eyebrow="Manual entry" title="Add a business" subtitle="It will be enriched, predicted, and scored by AI on save." />
            <form onSubmit={submit} className="space-y-5">
                <div className="surface p-5">
                    <div className="eyebrow mb-4">Basics</div>
                    <div className="grid sm:grid-cols-2 gap-4">
                        <Field label="Business name *"><input data-testid={TIDS.bizNewName} className="field-input" value={form.business_name} onChange={(e) => update('business_name', e.target.value)} /></Field>
                        <Field label="GST number"><input className="field-input mono" value={form.gst_number} onChange={(e) => update('gst_number', e.target.value.toUpperCase())} placeholder="27AABCT1234A1ZX" maxLength={15} /></Field>
                        <Field label="Registration date"><input type="date" className="field-input" value={form.registration_date} onChange={(e) => update('registration_date', e.target.value)} /></Field>
                        <Field label="Company type">
                            <select className="field-input" value={form.company_type} onChange={(e) => update('company_type', e.target.value)}>
                                {['Private Limited', 'LLP', 'Partnership', 'Sole Proprietorship', 'Public Limited', 'OPC'].map(t => <option key={t}>{t}</option>)}
                            </select>
                        </Field>
                        <Field label="Industry">
                            <select className="field-input" value={form.industry} onChange={(e) => update('industry', e.target.value)}>
                                <option value="">— select —</option>
                                {INDUSTRIES.map(t => <option key={t}>{t}</option>)}
                            </select>
                        </Field>
                        <Field label="Category"><input className="field-input" value={form.category} onChange={(e) => update('category', e.target.value)} placeholder="e.g. Technology" /></Field>
                        <Field label="Sub-category"><input className="field-input" value={form.sub_category} onChange={(e) => update('sub_category', e.target.value)} /></Field>
                        <Field label="Director name"><input className="field-input" value={form.director_name} onChange={(e) => update('director_name', e.target.value)} /></Field>
                        <Field label="Employees"><input type="number" className="field-input mono" value={form.employee_estimate} onChange={(e) => update('employee_estimate', e.target.value)} /></Field>
                        <Field label="Source"><input className="field-input" value={form.source} onChange={(e) => update('source', e.target.value)} /></Field>
                    </div>
                </div>
                <div className="surface p-5">
                    <div className="eyebrow mb-4">Contact</div>
                    <div className="grid sm:grid-cols-2 gap-4">
                        <Field label="Website"><input className="field-input" value={form.website} onChange={(e) => update('website', e.target.value)} /></Field>
                        <Field label="Phone"><input className="field-input" value={form.phone} onChange={(e) => update('phone', e.target.value)} /></Field>
                        <Field label="Email"><input className="field-input" value={form.email} onChange={(e) => update('email', e.target.value)} /></Field>
                        <Field label="LinkedIn URL"><input className="field-input" value={form.linkedin_url} onChange={(e) => update('linkedin_url', e.target.value)} /></Field>
                    </div>
                </div>
                <div className="surface p-5">
                    <div className="eyebrow mb-4">Address</div>
                    <div className="grid sm:grid-cols-2 gap-4">
                        <Field label="Address"><input className="field-input" value={form.address} onChange={(e) => update('address', e.target.value)} /></Field>
                        <Field label="Locality"><input className="field-input" value={form.locality} onChange={(e) => update('locality', e.target.value)} /></Field>
                        <Field label="City"><input className="field-input" value={form.city} onChange={(e) => update('city', e.target.value)} placeholder="e.g. Mumbai" /></Field>
                        <Field label="District"><input className="field-input" value={form.district} onChange={(e) => update('district', e.target.value)} /></Field>
                        <Field label="State"><input className="field-input" value={form.state} onChange={(e) => update('state', e.target.value)} placeholder="e.g. Maharashtra" /></Field>
                        <Field label="Pincode"><input className="field-input mono" value={form.pincode} onChange={(e) => update('pincode', e.target.value)} /></Field>
                    </div>
                </div>
                <div className="flex justify-end">
                    <button data-testid={TIDS.bizNewSubmit} type="submit" disabled={saving} className="btn-primary">
                        <Save className="h-4 w-4" /> {saving ? 'Saving & enriching…' : 'Save & Enrich'}
                    </button>
                </div>
            </form>
        </div>
    );
}

function Field({ label, children }) {
    return (<div><label className="eyebrow block mb-2">{label}</label>{children}</div>);
}
