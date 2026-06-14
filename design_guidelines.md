{
  "meta": {
    "product_name": "Business Radar AI",
    "theme": "CRED-inspired premium dark (dark-only)",
    "notes": [
      "Strictly dark-first. Do not build a full light mode.",
      "Gold/cream accents are scarce and intentional (CTAs, active states, key highlights).",
      "No neon. No loud gradients. No purple."
    ]
  },
  "brand_attributes": [
    "premium",
    "minimal-but-rich",
    "trustworthy",
    "operator-grade",
    "quietly-confident"
  ],
  "inspiration_refs": {
    "visual_refs": [
      {
        "title": "CRED UI revamp commentary (dark + premium typography cues)",
        "url": "https://uxplanet.org/thoughts-on-creds-ui-revamp-apr-2022-6d2b4dcfcfc6"
      },
      {
        "title": "Dribbble search: finance app dark theme (table + KPI patterns)",
        "url": "https://dribbble.com/search/finance-app-dark-theme"
      },
      {
        "title": "Dashboard anatomy patterns (sidebar + KPI + tables)",
        "url": "https://www.saasframe.io/blog/the-anatomy-of-high-performance-saas-dashboard-design-2026-trends-patterns"
      }
    ],
    "texture_refs": [
      {
        "title": "Dark grain texture",
        "url": "https://images.unsplash.com/photo-1541816139614-b1c0b6a13f5b?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85"
      }
    ]
  },
  "design_tokens": {
    "css_variables_index_css": {
      "how_to_apply": [
        "Replace the existing :root and .dark tokens in /app/frontend/src/index.css with the block below.",
        "Set <html class=\"dark\"> at app root (or add 'dark' class to body wrapper).",
        "Keep cards explicitly colored (no transparent card backgrounds)."
      ],
      "tokens": "@layer base {\n  :root {\n    /* Dark-only system: keep :root aligned to dark to avoid flash */\n    --background: 240 6% 5%;          /* near-black */\n    --foreground: 40 20% 96%;         /* warm off-white */\n\n    --canvas-2: 240 6% 7%;            /* slightly lifted */\n    --canvas-3: 240 6% 9%;\n\n    --card: 240 6% 7%;\n    --card-foreground: 40 20% 96%;\n\n    --popover: 240 6% 7%;\n    --popover-foreground: 40 20% 96%;\n\n    /* Cream/Gold accent (sparingly) */\n    --primary: 42 55% 72%;            /* muted gold */\n    --primary-foreground: 240 6% 6%;\n\n    --secondary: 240 6% 11%;\n    --secondary-foreground: 40 20% 96%;\n\n    --muted: 240 6% 10%;\n    --muted-foreground: 40 8% 72%;\n\n    --accent: 240 6% 12%;\n    --accent-foreground: 40 20% 96%;\n\n    --destructive: 0 62% 52%;\n    --destructive-foreground: 40 20% 96%;\n\n    --border: 240 6% 14%;             /* hairline dividers */\n    --input: 240 6% 14%;\n\n    /* Focus ring: warm gold halo, subtle */\n    --ring: 42 55% 72%;\n\n    /* Charts (Recharts) */\n    --chart-1: 42 55% 72%;            /* gold */\n    --chart-2: 35 22% 78%;            /* cream */\n    --chart-3: 210 10% 62%;           /* cool gray-blue */\n    --chart-4: 160 18% 58%;           /* muted green */\n    --chart-5: 0 0% 78%;              /* neutral */\n\n    --radius: 0.9rem;                 /* CRED-ish soft geometry */\n\n    /* Extra tokens used by app styles */\n    --shadow-1: 0 1px 0 hsl(0 0% 100% / 0.04), 0 10px 30px hsl(0 0% 0% / 0.45);\n    --shadow-2: 0 1px 0 hsl(0 0% 100% / 0.06), 0 18px 60px hsl(0 0% 0% / 0.55);\n\n    --glow-gold: 0 0 0 1px hsl(42 55% 72% / 0.18), 0 0 24px hsl(42 55% 72% / 0.10);\n\n    --surface-stroke: linear-gradient(180deg, hsl(0 0% 100% / 0.08), hsl(0 0% 100% / 0.02));\n    --surface-sheen: radial-gradient(1200px 600px at 20% 0%, hsl(42 55% 72% / 0.10), transparent 55%);\n\n    /* Allowed gradients (decorative only; keep under 20% viewport) */\n    --bg-hero: radial-gradient(900px 500px at 15% 10%, hsl(42 55% 72% / 0.10), transparent 60%),\n              radial-gradient(700px 420px at 85% 0%, hsl(0 0% 100% / 0.06), transparent 55%);\n\n    --badge-hot: linear-gradient(180deg, hsl(42 70% 70% / 0.22), hsl(42 55% 72% / 0.10));\n    --badge-warm: linear-gradient(180deg, hsl(35 40% 70% / 0.18), hsl(35 22% 78% / 0.08));\n    --badge-cold: linear-gradient(180deg, hsl(210 14% 60% / 0.16), hsl(210 10% 62% / 0.08));\n\n    --noise-url: url('https://images.unsplash.com/photo-1541816139614-b1c0b6a13f5b?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85');\n  }\n\n  .dark {\n    /* keep for shadcn compatibility; same as :root */\n  }\n}\n\n@layer base {\n  body {\n    background: hsl(var(--background));\n    color: hsl(var(--foreground));\n  }\n}\n\n/* Optional: subtle noise overlay (do NOT apply to text-heavy cards) */\n.bg-noise::before {\n  content: '';\n  position: fixed;\n  inset: 0;\n  pointer-events: none;\n  opacity: 0.06;\n  mix-blend-mode: overlay;\n  background-image: var(--noise-url);\n  background-size: 420px 420px;\n  z-index: 0;\n}\n"
    },
    "typography": {
      "google_fonts": [
        {
          "family": "Space Grotesk",
          "weights": ["400", "500", "600", "700"],
          "usage": "UI + headings (modern, premium, not generic)"
        },
        {
          "family": "IBM Plex Sans",
          "weights": ["400", "500", "600"],
          "usage": "Body + forms (high legibility)"
        },
        {
          "family": "IBM Plex Mono",
          "weights": ["400", "500"],
          "usage": "Scores, IDs, numeric columns"
        }
      ],
      "font_stack": {
        "display": "'Space Grotesk', ui-sans-serif, system-ui",
        "body": "'IBM Plex Sans', ui-sans-serif, system-ui",
        "mono": "'IBM Plex Mono', ui-monospace, SFMono-Regular"
      },
      "scale_tailwind": {
        "h1": "text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight",
        "h2": "text-base md:text-lg text-muted-foreground",
        "kpi_number": "text-4xl md:text-5xl font-semibold tracking-tight tabular-nums",
        "section_title": "text-lg font-medium tracking-tight",
        "label_eyebrow": "text-xs uppercase tracking-[0.22em] text-muted-foreground",
        "body": "text-sm md:text-base leading-relaxed text-foreground/90",
        "table_numeric": "font-mono tabular-nums"
      }
    },
    "spacing": {
      "principle": "Use 2–3x more spacing than typical admin dashboards; keep density via typography + alignment, not tight padding.",
      "scale": {
        "xs": "2",
        "sm": "3",
        "md": "4",
        "lg": "6",
        "xl": "8",
        "2xl": "12",
        "3xl": "16"
      },
      "container": {
        "desktop": "max-w-[1280px]",
        "wide": "max-w-[1440px]",
        "padding": "px-4 sm:px-6 lg:px-8"
      }
    },
    "radius": {
      "card": "rounded-2xl",
      "control": "rounded-xl",
      "pill": "rounded-full"
    },
    "elevation": {
      "card": "shadow-[var(--shadow-1)]",
      "modal": "shadow-[var(--shadow-2)]",
      "hairline_border": "border border-border/70"
    }
  },
  "component_path": {
    "shadcn_primary": [
      "/app/frontend/src/components/ui/button.jsx",
      "/app/frontend/src/components/ui/card.jsx",
      "/app/frontend/src/components/ui/badge.jsx",
      "/app/frontend/src/components/ui/table.jsx",
      "/app/frontend/src/components/ui/tabs.jsx",
      "/app/frontend/src/components/ui/sheet.jsx",
      "/app/frontend/src/components/ui/dialog.jsx",
      "/app/frontend/src/components/ui/drawer.jsx",
      "/app/frontend/src/components/ui/input.jsx",
      "/app/frontend/src/components/ui/select.jsx",
      "/app/frontend/src/components/ui/calendar.jsx",
      "/app/frontend/src/components/ui/skeleton.jsx",
      "/app/frontend/src/components/ui/sonner.jsx",
      "/app/frontend/src/components/ui/scroll-area.jsx",
      "/app/frontend/src/components/ui/separator.jsx",
      "/app/frontend/src/components/ui/tooltip.jsx",
      "/app/frontend/src/components/ui/dropdown-menu.jsx"
    ],
    "recommended_new_components_to_create": [
      {
        "path": "/app/frontend/src/components/layout/AppShell.jsx",
        "purpose": "Sidebar + topbar + content grid; mobile drawer behavior"
      },
      {
        "path": "/app/frontend/src/components/radar/KpiCard.jsx",
        "purpose": "CRED-style KPI module with eyebrow, big number, delta, optional ring/gauge"
      },
      {
        "path": "/app/frontend/src/components/radar/StatusPill.jsx",
        "purpose": "HOT/WARM/COLD pill with subtle gradient + glow"
      },
      {
        "path": "/app/frontend/src/components/radar/DataTable.jsx",
        "purpose": "Premium table wrapper: row height, hover sheen, sticky header, empty state"
      },
      {
        "path": "/app/frontend/src/components/radar/FilterRail.jsx",
        "purpose": "Left filter sidebar (desktop) + Sheet/Drawer (mobile)"
      },
      {
        "path": "/app/frontend/src/components/radar/ConnectorCard.jsx",
        "purpose": "Discovery connectors status cards"
      },
      {
        "path": "/app/frontend/src/components/radar/FileDropzone.jsx",
        "purpose": "CSV upload drag-drop zone + preview summary"
      }
    ]
  },
  "layout_system": {
    "global": {
      "app_shell": {
        "desktop_grid": "grid grid-cols-[260px_1fr] min-h-screen",
        "mobile": "Sidebar becomes <Sheet> triggered by icon button in topbar",
        "topbar": "sticky top-0 z-30 backdrop-blur supports-[backdrop-filter]:bg-background/70 border-b border-border/60"
      },
      "sidebar": {
        "style": "compact, glyph-led, hairline dividers, active route has subtle gold sheen",
        "active_item": "bg-[hsl(var(--canvas-3))] border border-border/70 shadow-[0_0_0_1px_hsl(var(--primary)/0.10)]",
        "icons": "lucide-react size-4 stroke-[1.5]"
      },
      "page_header": {
        "pattern": "Left: title + subtitle; Right: primary action + secondary actions",
        "class": "flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between"
      }
    },
    "routes": {
      "/login": {
        "layout": "Split feel without true split-screen: centered column with large welcome + minimal form; subtle hero background gradient (<=20% viewport) behind header only.",
        "key_components": ["Card", "Button", "Input", "Separator"],
        "notes": [
          "Google OAuth button: secondary/outline with icon.",
          "Primary CTA: gold/cream fill on black.",
          "Add trust microcopy under form (muted)."
        ]
      },
      "/force-reset": {
        "layout": "Same as login; add password rules panel as muted card.",
        "key_components": ["Card", "Input", "Button", "Alert"]
      },
      "/dashboard": {
        "layout": "Top KPI strip (4 cards) -> charts row (2) -> recent discoveries feed (table-lite).",
        "key_components": ["KpiCard", "Card", "Tabs", "Table", "Skeleton"],
        "charts": ["Recharts AreaChart (muted fill)", "Recharts BarChart (thin bars)"]
      },
      "/businesses": {
        "layout": "Desktop: left FilterRail (sticky) + right DataTable. Mobile: FilterRail in Sheet.",
        "key_components": ["FilterRail", "DataTable", "Input", "Select", "Calendar", "Button", "DropdownMenu"],
        "table_behavior": [
          "Generous row height (py-4)",
          "Hairline dividers",
          "Hover row highlight via subtle radial sheen",
          "Numeric columns use mono + tabular-nums"
        ]
      },
      "/businesses/:id": {
        "layout": "Header with company name + score pill + actions -> Tabs (Overview/Enrichment/Predictions/Lead Score/Audit).",
        "key_components": ["Tabs", "Card", "StatusPill", "Button", "Table", "Tooltip"],
        "notes": ["Re-run AI is primary CTA; show last-run timestamp in muted mono."]
      },
      "/businesses/new": {
        "layout": "Multi-section form with section cards; sticky footer action bar on mobile.",
        "key_components": ["Card", "Form", "Input", "Select", "Textarea", "Button"]
      },
      "/businesses/upload": {
        "layout": "FileDropzone -> preview table -> dedup summary cards -> commit CTA.",
        "key_components": ["FileDropzone", "Table", "Card", "Button", "Alert"]
      },
      "/discovery": {
        "layout": "ConnectorCard grid (2 cols desktop, 1 col mobile) + run button + logs panel.",
        "key_components": ["ConnectorCard", "Card", "Badge", "Button", "ScrollArea"]
      },
      "/reports": {
        "layout": "Left list (ScrollArea) + right report viewer card; mobile becomes stacked.",
        "key_components": ["ScrollArea", "Card", "Table", "Button", "Tabs"],
        "exports": "Use DropdownMenu for PDF/Excel/CSV"
      },
      "/reports/:id": {
        "layout": "Report header + export actions + content sections as cards.",
        "key_components": ["Card", "Button", "Separator"]
      },
      "/preferences": {
        "layout": "Single column settings cards; toggles and selects.",
        "key_components": ["Card", "Switch", "Select", "Input", "Button"]
      },
      "/admin/users": {
        "layout": "Table + create user dialog; role badges.",
        "key_components": ["DataTable", "Dialog", "Form", "Badge", "Button"]
      },
      "/admin/settings": {
        "layout": "Settings grouped by provider (Google OAuth, SendGrid, SMTP). Mask secrets; reveal via eye icon.",
        "key_components": ["Card", "Input", "Button", "Tabs", "Tooltip"],
        "notes": ["Use Input type=password + reveal toggle; show 'Saved' toast."]
      },
      "/admin/audit-logs": {
        "layout": "Dense table with filters; sticky header.",
        "key_components": ["FilterRail", "DataTable", "Badge"]
      },
      "/admin/scheduler": {
        "layout": "Status cards + timeline/logs; run-now CTA.",
        "key_components": ["Card", "Badge", "Button", "ScrollArea"]
      }
    }
  },
  "component_patterns": {
    "buttons": {
      "variants": {
        "primary": {
          "intent": "Main CTA",
          "className": "rounded-full bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] hover:bg-[hsl(var(--primary)/0.92)] focus-visible:shadow-[var(--glow-gold)]",
          "motion": "hover: translateY(-1px) + subtle glow; press scale 0.98"
        },
        "secondary": {
          "intent": "Secondary actions",
          "className": "rounded-full bg-[hsl(var(--secondary))] text-foreground border border-border/70 hover:bg-[hsl(var(--canvas-3))]",
          "motion": "hover: lift 1px"
        },
        "ghost": {
          "intent": "Toolbar actions",
          "className": "rounded-full bg-transparent text-foreground/90 hover:bg-[hsl(var(--canvas-3))] border border-transparent hover:border-border/60"
        }
      },
      "data_testid_examples": [
        "data-testid=\"login-submit-button\"",
        "data-testid=\"businesses-export-button\"",
        "data-testid=\"business-detail-rerun-ai-button\""
      ]
    },
    "kpi_card": {
      "structure": [
        "Eyebrow label (uppercase tracking)",
        "Big number (tabular-nums)",
        "Delta row (muted) + sparkline optional",
        "Optional ring/gauge for lead score"
      ],
      "card_class": "rounded-2xl bg-[hsl(var(--card))] border border-border/70 shadow-[var(--shadow-1)] relative overflow-hidden",
      "sheen_overlay": "before:content-[''] before:absolute before:inset-0 before:bg-[var(--surface-sheen)] before:opacity-60 before:pointer-events-none",
      "microinteraction": "On hover: subtle parallax (translateY -2) + increase sheen opacity; number count-up on mount.",
      "data_testid": "data-testid=\"dashboard-kpi-total-businesses\""
    },
    "status_pills": {
      "shape": "rounded-full px-3 py-1 text-xs uppercase tracking-[0.18em]",
      "hot": {
        "class": "bg-[var(--badge-hot)] text-[hsl(var(--primary))] border border-[hsl(var(--primary)/0.22)] shadow-[0_0_18px_hsl(var(--primary)/0.10)]"
      },
      "warm": {
        "class": "bg-[var(--badge-warm)] text-[hsl(var(--chart-2))] border border-[hsl(var(--chart-2)/0.18)]"
      },
      "cold": {
        "class": "bg-[var(--badge-cold)] text-[hsl(var(--chart-3))] border border-[hsl(var(--chart-3)/0.18)]"
      },
      "data_testid": "data-testid=\"lead-temperature-pill\""
    },
    "data_table": {
      "wrapper": "rounded-2xl bg-[hsl(var(--card))] border border-border/70 shadow-[var(--shadow-1)] overflow-hidden",
      "header": "bg-[hsl(var(--canvas-3))] text-xs uppercase tracking-[0.22em] text-muted-foreground",
      "row": "hover:bg-[hsl(var(--canvas-3))] transition-colors",
      "cell": "py-4",
      "numeric": "font-mono tabular-nums",
      "empty_state": "Centered card with muted copy + primary CTA; include illustration only if subtle (no bright colors).",
      "data_testid": "data-testid=\"businesses-table\""
    },
    "filter_rail": {
      "desktop": "w-[320px] sticky top-16 h-[calc(100vh-4rem)]",
      "mobile": "Use Sheet from shadcn; trigger button in header",
      "controls": "Use Select, Calendar (date range), Slider (lead score), Input (pincode)",
      "data_testid": "data-testid=\"businesses-filter-rail\""
    },
    "tabs": {
      "style": "TabsList as pill group on dark surface; active tab gets subtle gold underline glow.",
      "class": "bg-[hsl(var(--canvas-3))] rounded-full p-1 border border-border/60"
    },
    "file_dropzone": {
      "zone": "rounded-2xl border border-dashed border-border/70 bg-[hsl(var(--canvas-2))] p-8 text-center",
      "hover": "hover:border-[hsl(var(--primary)/0.35)] hover:shadow-[var(--glow-gold)]",
      "states": ["idle", "dragging", "uploading", "success", "error"],
      "data_testid": "data-testid=\"csv-upload-dropzone\""
    },
    "toasts": {
      "library": "sonner",
      "style": "Dark toast with hairline border; success uses subtle gold dot, not green flood.",
      "data_testid": "data-testid=\"app-toast\""
    }
  },
  "motion": {
    "library": "framer-motion",
    "principles": [
      "Expensive = smooth easing + short durations + local motion.",
      "Avoid bouncy overshoot; use gentle cubic-bezier.",
      "Prefer opacity + translateY; avoid scaling large surfaces."
    ],
    "tokens": {
      "ease": "[0.22, 1, 0.36, 1]",
      "fast": 0.18,
      "base": 0.28,
      "slow": 0.42
    },
    "variants_js_scaffold": {
      "page": "export const pageVariants = {\n  initial: { opacity: 0, y: 10 },\n  animate: { opacity: 1, y: 0, transition: { duration: 0.42, ease: [0.22, 1, 0.36, 1] } },\n  exit: { opacity: 0, y: 8, transition: { duration: 0.18, ease: [0.22, 1, 0.36, 1] } }\n};\n",
      "cardHover": "export const cardHover = {\n  rest: { y: 0 },\n  hover: { y: -2, transition: { duration: 0.18, ease: [0.22, 1, 0.36, 1] } }\n};\n",
      "kpiCountUp": "Use requestAnimationFrame-based count-up (avoid heavy libs). Trigger on mount; respect prefers-reduced-motion."
    }
  },
  "charts": {
    "recharts_guidance": {
      "grid": "stroke=hsl(var(--border)/0.6) strokeDasharray='3 6'",
      "axis": "tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}",
      "series": {
        "primary": "stroke: hsl(var(--chart-1)); fill: hsl(var(--chart-1)/0.12)",
        "secondary": "stroke: hsl(var(--chart-2)); fill: hsl(var(--chart-2)/0.10)"
      },
      "tooltip": "Use shadcn Card-like tooltip: bg card, border hairline, mono numerics"
    }
  },
  "accessibility": {
    "requirements": [
      "WCAG AA contrast: body text must be off-white on near-black; avoid mid-gray on black.",
      "Visible focus: gold halo ring (shadow var(--glow-gold)) + outline-none.",
      "Respect prefers-reduced-motion: disable parallax/count-up and reduce durations.",
      "Tables: ensure row hover does not reduce contrast."
    ]
  },
  "do_dont": {
    "do": [
      "Use near-black canvas with layered charcoal surfaces.",
      "Use gold/cream only for primary actions, active states, and key highlights.",
      "Use uppercase eyebrow labels with generous tracking.",
      "Use mono numerics for scores/IDs and align decimals.",
      "Use hairline dividers and generous row height in tables.",
      "Use subtle sheen overlays and soft glows (never neon)."
    ],
    "dont": [
      "Do not use purple anywhere.",
      "Do not use saturated gradients or gradients on small elements.",
      "Do not use transparent cards on dark background—cards must have explicit surface color.",
      "Do not center-align entire pages; keep left-aligned reading flow.",
      "Do not use emoji icons; use lucide-react only.",
      "Do not use transition: all; transition only specific properties."
    ]
  },
  "image_urls": {
    "hero_background_texture": [
      {
        "category": "global",
        "description": "Optional subtle noise overlay for app shell background only (not on cards).",
        "url": "https://images.unsplash.com/photo-1541816139614-b1c0b6a13f5b?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85"
      }
    ],
    "decorative_abstract": [
      {
        "category": "login_header / dashboard_header",
        "description": "Use as faint masked background image behind header area only (<=20% viewport).",
        "url": "https://images.unsplash.com/photo-1634549709262-508c47d4c229?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85"
      },
      {
        "category": "reports_header",
        "description": "Alternative abstract swirl; keep opacity low (0.08–0.12).",
        "url": "https://images.unsplash.com/photo-1645290099737-23f17b0b7dd8?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85"
      }
    ],
    "contextual_analytics": [
      {
        "category": "empty_state / onboarding",
        "description": "Use sparingly as a small thumbnail in empty states (not full-bleed).",
        "url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?crop=entropy&cs=srgb&fm=jpg&ixlib=rb-4.1.0&q=85"
      }
    ]
  },
  "instructions_to_main_agent": [
    "OVERWRITE /app/frontend/src/index.css tokens with the provided dark-only token block; ensure no light flash.",
    "Remove any centered App header styles from /app/frontend/src/App.css; do not use .App { text-align:center }.",
    "Use shadcn components from /app/frontend/src/components/ui only (Button, Card, Table, Tabs, Sheet, Dialog, Calendar, Skeleton, Sonner).",
    "Implement AppShell with sidebar + topbar; sidebar collapses to Sheet on mobile.",
    "Every interactive element and key info must include data-testid (kebab-case).",
    "Use lucide-react icons with stroke 1.5; keep icon usage restrained.",
    "Use Framer Motion variants provided; respect prefers-reduced-motion.",
    "Charts: Recharts with muted grids and gold/cream series; no rainbow palettes.",
    "Status pills: HOT/WARM/COLD use subtle gradients + hairline borders; HOT gets soft glow only."
  ],
  "General UI UX Design Guidelines": [
    "- You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms",
    "- You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text",
    "- NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json",
    "\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc",
    "\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead.",
    "   ",
    "- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.",
    "\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.",
    "   ",
    "- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals."
  ]
}
