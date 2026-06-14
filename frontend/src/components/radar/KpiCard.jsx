import React from 'react';
import { motion } from 'framer-motion';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

export function KpiCard({ label, value, delta, deltaLabel, icon: Icon, accent, tid }) {
    return (
        <motion.div
            data-testid={tid}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            whileHover={{ y: -2 }}
            transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
            className="surface relative overflow-hidden p-5 sheen-overlay"
        >
            <div className="flex items-start justify-between gap-3">
                <div className="eyebrow">{label}</div>
                {Icon && (
                    <div className="h-9 w-9 rounded-xl bg-[hsl(var(--canvas-3))] border border-border/70 flex items-center justify-center text-foreground/80">
                        <Icon className="h-4 w-4" strokeWidth={1.5} />
                    </div>
                )}
            </div>
            <div className={`kpi-number text-4xl mt-3 ${accent ? 'text-[hsl(var(--primary))]' : ''}`}>{value}</div>
            {delta != null && (
                <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
                    {delta >= 0 ? (
                        <span className="inline-flex items-center gap-1 text-[hsl(var(--primary))]"><ArrowUpRight className="h-3.5 w-3.5" />{Math.abs(delta).toFixed(0)}%</span>
                    ) : (
                        <span className="inline-flex items-center gap-1 text-[hsl(var(--destructive))]"><ArrowDownRight className="h-3.5 w-3.5" />{Math.abs(delta).toFixed(0)}%</span>
                    )}
                    <span>{deltaLabel || 'vs prev period'}</span>
                </div>
            )}
        </motion.div>
    );
}
