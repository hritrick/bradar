'use client';

import Link from 'next/link';
import { usePathname, useParams as useNextParams, useRouter, useSearchParams } from 'next/navigation';

export function useNavigate() {
    const router = useRouter();
    return (to, options = {}) => {
        if (typeof to === 'number') {
            if (to < 0) router.back();
            return;
        }
        if (options.replace) router.replace(to);
        else router.push(to);
    };
}

export function useParams() {
    return useNextParams();
}

export function useLocation() {
    const pathname = usePathname();
    const searchParams = useSearchParams();
    const search = searchParams?.toString();
    return {
        pathname,
        search: search ? `?${search}` : '',
        hash: '',
    };
}

export function AppLink({ to, children, ...props }) {
    return (
        <Link href={to} {...props}>
            {children}
        </Link>
    );
}

export function NavLink({ to, end, className, children, ...props }) {
    const pathname = usePathname();
    const isActive = end ? pathname === to : pathname === to || pathname.startsWith(`${to}/`);
    const resolvedClassName = typeof className === 'function' ? className({ isActive }) : className;
    return (
        <Link href={to} className={resolvedClassName} {...props}>
            {children}
        </Link>
    );
}
