import React from 'react';
import { Flame, ThermometerSnowflake, Sparkles } from 'lucide-react';

export function StatusPill({ category, score, tid }) {
    if (!category) return <span className="pill-base pill-neutral mono" data-testid={tid}>n/a</span>;
    const cls = category === 'HOT' ? 'pill-hot' : category === 'WARM' ? 'pill-warm' : 'pill-cold';
    const Icon = category === 'HOT' ? Flame : category === 'WARM' ? Sparkles : ThermometerSnowflake;
    return (
        <span className={`pill-base ${cls}`} data-testid={tid}>
            <Icon className="h-3 w-3" strokeWidth={1.8} />
            <span>{category}</span>
            {score != null && <span className="mono ml-1 opacity-90">{score}</span>}
        </span>
    );
}
