import React, { useState } from 'react';
import { AppLink as Link, NavLink, useLocation } from '../../lib/router';
import { motion, AnimatePresence } from 'framer-motion';
import {
    LayoutDashboard, Building2, FilePlus2, Upload, Compass, FileText,
    Settings as SettingsIcon, Users, ShieldCheck, Clock, LogOut, Menu, X, User, ChevronDown
} from 'lucide-react';
import { useAuth } from '../../lib/AuthContext';
import { TIDS } from '../../constants/testIds';
import { Sheet, SheetContent, SheetTrigger } from '../ui/sheet';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator, DropdownMenuLabel } from '../ui/dropdown-menu';

const NAV = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', tid: TIDS.navDashboard, roles: ['Admin', 'Analyst', 'Subscriber'] },
    { to: '/businesses', icon: Building2, label: 'Businesses', tid: TIDS.navBusinesses, roles: ['Admin', 'Analyst', 'Subscriber'] },
    { to: '/businesses/new', icon: FilePlus2, label: 'Add Business', tid: TIDS.navManualNew, roles: ['Admin', 'Analyst'] },
    { to: '/businesses/upload', icon: Upload, label: 'CSV Upload', tid: TIDS.navUpload, roles: ['Admin', 'Analyst'] },
    { to: '/discovery', icon: Compass, label: 'Discovery', tid: TIDS.navDiscovery, roles: ['Admin', 'Analyst'] },
    { to: '/reports', icon: FileText, label: 'Reports', tid: TIDS.navReports, roles: ['Admin', 'Analyst', 'Subscriber'] },
    { to: '/preferences', icon: SettingsIcon, label: 'Preferences', tid: TIDS.navPreferences, roles: ['Admin', 'Analyst', 'Subscriber'] },
];

const ADMIN_NAV = [
    { to: '/admin/users', icon: Users, label: 'Users', tid: TIDS.navAdminUsers },
    { to: '/admin/settings', icon: ShieldCheck, label: 'Settings', tid: TIDS.navAdminSettings },
    { to: '/admin/audit-logs', icon: FileText, label: 'Audit Logs', tid: TIDS.navAdminAudit },
    { to: '/admin/scheduler', icon: Clock, label: 'Scheduler', tid: TIDS.navAdminScheduler },
];

function Logo() {
    return (
        <Link to="/dashboard" className="flex items-center gap-2.5 px-1">
            <div className="relative h-9 w-9 rounded-xl bg-gradient-to-br from-[hsl(42_55%_72%)] to-[hsl(35_30%_55%)] flex items-center justify-center shadow-[var(--glow-gold)]">
                <span className="text-[hsl(240_6%_6%)] font-bold text-sm heading">R</span>
            </div>
            <div className="flex flex-col leading-tight">
                <span className="heading text-sm font-semibold tracking-tight">Business Radar</span>
                <span className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground">AI · India</span>
            </div>
        </Link>
    );
}

function NavItem({ to, icon: Icon, label, tid }) {
    return (
        <NavLink to={to} end={to === '/dashboard'} data-testid={tid}
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <Icon className="h-4 w-4" strokeWidth={1.6} />
            <span>{label}</span>
        </NavLink>
    );
}

function SidebarContents({ user }) {
    return (
        <div className="flex h-full flex-col">
            <div className="px-4 pt-5 pb-3">
                <Logo />
            </div>
            <div className="flex-1 overflow-y-auto scrollbar-cred px-3 py-2 space-y-1">
                <div className="px-2 pb-2 pt-1 eyebrow">Workspace</div>
                {NAV.filter(n => n.roles.includes(user.role)).map(n => <NavItem key={n.to} {...n} />)}
                {user.role === 'Admin' && (
                    <>
                        <div className="px-2 pt-5 pb-2 eyebrow">Admin</div>
                        {ADMIN_NAV.map(n => <NavItem key={n.to} {...n} />)}
                    </>
                )}
            </div>
            <div className="p-3 border-t border-border/60">
                <div className="flex items-center gap-3 surface-2 p-3">
                    <div className="h-9 w-9 rounded-full bg-[hsl(var(--canvas-3))] border border-border flex items-center justify-center">
                        <User className="h-4 w-4" strokeWidth={1.6} />
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium truncate">{user.name}</div>
                        <div className="text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{user.role}</div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function AppShell({ children }) {
    const { user, logout } = useAuth();
    const [mobileOpen, setMobileOpen] = useState(false);
    const location = useLocation();

    if (!user) return null;

    return (
        <div className="min-h-screen lg:grid lg:grid-cols-[260px_1fr]">
            {/* Sidebar desktop */}
            <aside className="hidden lg:block border-r border-border/60 bg-[hsl(var(--canvas-2))] sticky top-0 h-screen">
                <SidebarContents user={user} />
            </aside>

            <div className="flex flex-col min-h-screen">
                {/* Topbar */}
                <header className="sticky top-0 z-30 backdrop-blur bg-background/70 border-b border-border/60">
                    <div className="flex items-center gap-3 px-4 sm:px-6 lg:px-8 h-16">
                        {/* mobile menu trigger */}
                        <div className="lg:hidden">
                            <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
                                <SheetTrigger asChild>
                                    <button data-testid={TIDS.sidebarToggle} className="btn-ghost p-2">
                                        <Menu className="h-5 w-5" />
                                    </button>
                                </SheetTrigger>
                                <SheetContent side="left" className="p-0 w-[280px] bg-[hsl(var(--canvas-2))] border-r border-border">
                                    <SidebarContents user={user} />
                                </SheetContent>
                            </Sheet>
                        </div>
                        <div className="lg:hidden"><Logo /></div>
                        <div className="flex-1" />
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <button className="btn-ghost">
                                    <div className="h-7 w-7 rounded-full bg-[hsl(var(--canvas-3))] border border-border flex items-center justify-center">
                                        <User className="h-3.5 w-3.5" strokeWidth={1.6} />
                                    </div>
                                    <span className="hidden sm:inline text-sm font-medium">{user.name}</span>
                                    <ChevronDown className="h-3.5 w-3.5" />
                                </button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent className="min-w-[200px] bg-[hsl(var(--canvas-2))] border-border" align="end">
                                <DropdownMenuLabel className="text-xs">
                                    <div className="font-medium">{user.email}</div>
                                    <div className="text-muted-foreground text-[10px] uppercase tracking-[0.18em] mt-1">{user.role}</div>
                                </DropdownMenuLabel>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem onSelect={() => (window.location.href = '/preferences')}>
                                    <SettingsIcon className="h-4 w-4 mr-2" /> Preferences
                                </DropdownMenuItem>
                                <DropdownMenuItem onSelect={logout} data-testid={TIDS.logoutBtn}>
                                    <LogOut className="h-4 w-4 mr-2" /> Sign out
                                </DropdownMenuItem>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                </header>

                <AnimatePresence mode="wait">
                    <motion.main
                        key={location.pathname}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0, transition: { duration: 0.32, ease: [0.22, 1, 0.36, 1] } }}
                        exit={{ opacity: 0, y: 6, transition: { duration: 0.16 } }}
                        className="flex-1 px-4 sm:px-6 lg:px-8 py-6 lg:py-8 max-w-[1440px] w-full mx-auto">
                        {children}
                    </motion.main>
                </AnimatePresence>
            </div>
        </div>
    );
}
