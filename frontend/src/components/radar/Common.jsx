import React from 'react';

export function Skeleton({ className = '', count = 1 }) {
    return (
        <>
            {Array.from({ length: count }).map((_, i) => (
                <div key={i} className={`skeleton-shimmer ${className}`} />
            ))}
        </>
    );
}

export function PageHeader({ title, subtitle, actions, eyebrow }) {
    return (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between mb-7">
            <div>
                {eyebrow && <div className="eyebrow mb-2">{eyebrow}</div>}
                <h1 className="heading text-2xl md:text-3xl font-semibold tracking-tight">{title}</h1>
                {subtitle && <p className="text-sm text-muted-foreground mt-2 max-w-2xl">{subtitle}</p>}
            </div>
            {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
        </div>
    );
}

export function EmptyState({ title, description, action, icon: Icon }) {
    return (
        <div className="surface p-10 text-center">
            {Icon && <div className="mx-auto h-12 w-12 rounded-full bg-[hsl(var(--canvas-3))] border border-border/70 flex items-center justify-center mb-4"><Icon className="h-5 w-5 text-muted-foreground" strokeWidth={1.5} /></div>}
            <div className="heading text-lg font-medium">{title}</div>
            {description && <div className="text-sm text-muted-foreground mt-2 max-w-md mx-auto">{description}</div>}
            {action && <div className="mt-5 flex justify-center">{action}</div>}
        </div>
    );
}
