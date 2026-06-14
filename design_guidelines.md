{
  "product": {
    "name": "Business Radar AI",
    "design_personality": {
      "keywords": [
        "premium B2B",
        "calm data-density",
        "trustworthy",
        "fast + keyboard-friendly",
        "India-first (subtle accents)",
        "audit-ready"
      ],
      "north_star": "Linear-like clarity + Attio-like table power + Stripe-like restraint. Dense tables, progressive disclosure, and semantic color only."
    },
    "do_not": [
      "Do not use transparent surfaces with dark text (theme variance).",
      "Do not use purple for AI/chat vibes.",
      "Do not use gradients on text-heavy areas or small UI elements (<100px).",
      "Do not center-align the whole app container.",
      "Do not use transition: all anywhere."
    ]
  },

  "design_tokens": {
    "fonts": {
      "google_fonts_import": "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap",
      "heading": "Space Grotesk",
      "body": "Inter",
      "mono": "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace"
    },

    "typography_scale_tailwind": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight",
      "h2": "text-base md:text-lg font-medium text-muted-foreground",
      "h3": "text-lg font-semibold",
      "body": "text-sm md:text-base",
      "small": "text-xs text-muted-foreground",
      "table": {
        "dense": "text-xs md:text-sm",
        "comfortable": "text-sm"
      }
    },

    "radius": {
      "sm": "6px",
      "md": "10px",
      "lg": "14px",
      "xl": "18px",
      "token": "--radius"
    },

    "shadows": {
      "sm": "0 1px 2px rgba(2, 6, 23, 0.06)",
      "md": "0 8px 24px rgba(2, 6, 23, 0.10)",
      "ring": "0 0 0 3px rgba(37, 99, 235, 0.35)"
    },

    "spacing": {
      "principle": "Use 2–3x more spacing than feels comfortable. Prefer 24/32/40px section padding.",
      "page_padding": "px-4 sm:px-6 lg:px-8",
      "section_gap": "gap-6 lg:gap-8",
      "card_padding": "p-4 sm:p-5",
      "form_section_gap": "space-y-6"
    },

    "color_system": {
      "notes": [
        "Teal-led neutral palette with saffron accent (India cue) used sparingly.",
        "Keep semantic colors distinct from brand teal.",
        "Focus ring uses accessible blue for visibility across light/dark.",
        "All text must meet WCAG AA contrast; never rely on color alone for meaning."
      ],

      "css_variables_light": {
        "--background": "210 40% 98%",
        "--foreground": "222 47% 11%",

        "--card": "0 0% 100%",
        "--card-foreground": "222 47% 11%",

        "--popover": "0 0% 100%",
        "--popover-foreground": "222 47% 11%",

        "--primary": "173 80% 26%",
        "--primary-foreground": "210 40% 98%",

        "--secondary": "210 40% 96%",
        "--secondary-foreground": "222 47% 11%",

        "--muted": "210 40% 96%",
        "--muted-foreground": "215 16% 35%",

        "--accent": "38 92% 50%",
        "--accent-foreground": "222 47% 11%",

        "--destructive": "0 74% 42%",
        "--destructive-foreground": "210 40% 98%",

        "--border": "214 32% 91%",
        "--input": "214 32% 91%",
        "--ring": "217 91% 60%",

        "--chart-1": "173 80% 26%",
        "--chart-2": "199 89% 48%",
        "--chart-3": "38 92% 50%",
        "--chart-4": "142 71% 35%",
        "--chart-5": "0 74% 42%",

        "--radius": "0.625rem"
      },

      "css_variables_dark": {
        "--background": "222 47% 7%",
        "--foreground": "210 40% 98%",

        "--card": "222 47% 9%",
        "--card-foreground": "210 40% 98%",

        "--popover": "222 47% 9%",
        "--popover-foreground": "210 40% 98%",

        "--primary": "173 70% 45%",
        "--primary-foreground": "222 47% 11%",

        "--secondary": "222 47% 13%",
        "--secondary-foreground": "210 40% 98%",

        "--muted": "222 47% 13%",
        "--muted-foreground": "215 20% 70%",

        "--accent": "38 92% 50%",
        "--accent-foreground": "222 47% 11%",

        "--destructive": "0 62% 35%",
        "--destructive-foreground": "210 40% 98%",

        "--border": "222 47% 16%",
        "--input": "222 47% 16%",
        "--ring": "217 91% 60%",

        "--chart-1": "173 70% 45%",
        "--chart-2": "199 89% 55%",
        "--chart-3": "38 92% 55%",
        "--chart-4": "142 60% 45%",
        "--chart-5": "0 62% 45%",

        "--radius": "0.625rem"
      },

      "semantic_status_badges": {
        "lead_hot": {
          "label": "HOT",
          "bg": "bg-red-50 dark:bg-red-950/40",
          "text": "text-red-700 dark:text-red-200",
          "border": "border-red-200/70 dark:border-red-900/60"
        },
        "lead_warm": {
          "label": "WARM",
          "bg": "bg-amber-50 dark:bg-amber-950/35",
          "text": "text-amber-800 dark:text-amber-200",
          "border": "border-amber-200/70 dark:border-amber-900/60"
        },
        "lead_cold": {
          "label": "COLD",
          "bg": "bg-slate-50 dark:bg-slate-900/60",
          "text": "text-slate-700 dark:text-slate-200",
          "border": "border-slate-200/70 dark:border-slate-800"
        },
        "connector_ok": {
          "bg": "bg-emerald-50 dark:bg-emerald-950/35",
          "text": "text-emerald-700 dark:text-emerald-200",
          "border": "border-emerald-200/70 dark:border-emerald-900/60"
        },
        "connector_needs_config": {
          "bg": "bg-slate-50 dark:bg-slate-900/60",
          "text": "text-slate-700 dark:text-slate-200",
          "border": "border-slate-200/70 dark:border-slate-800"
        }
      }
    },

    "texture_and_gradients": {
      "rule": "Gradients only as large section backgrounds or decorative overlays; never on small elements or reading areas; max 20% viewport.",
      "allowed_background_gradient": "bg-[radial-gradient(1200px_circle_at_20%_0%,hsl(var(--primary)/0.12),transparent_55%),radial-gradient(900px_circle_at_90%_10%,hsl(var(--accent)/0.10),transparent_50%)]",
      "noise_overlay_css": ".noise::before{content:'';position:absolute;inset:0;background-image:url('data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22120%22 height=%22120%22%3E%3Cfilter id=%22n%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.9%22 numOctaves=%222%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22120%22 height=%22120%22 filter=%22url(%23n)%22 opacity=%220.08%22/%3E%3C/svg%3E');mix-blend-mode:overlay;pointer-events:none;border-radius:inherit;}"
    }
  },

  "layout_system": {
    "app_shell": {
      "pattern": "Left sidebar + topbar + content area. Sidebar collapses to icon rail on desktop; becomes Drawer on mobile.",
      "grid": {
        "desktop": "grid grid-cols-[260px_1fr]",
        "collapsed": "grid grid-cols-[72px_1fr]",
        "mobile": "topbar fixed + Drawer for nav"
      },
      "content_container": "max-w-[1400px] mx-auto",
      "page_header": {
        "structure": [
          "Breadcrumb (optional)",
          "Title + subtitle",
          "Right-side actions (primary CTA + secondary)"
        ],
        "class": "flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between"
      }
    },

    "responsive_rules": {
      "breakpoints": {
        "sm": "≥640px",
        "md": "≥768px",
        "lg": "≥1024px",
        "xl": "≥1280px"
      },
      "tables_on_mobile": "Convert table rows to stacked cards with key fields + actions; keep search + filters accessible via Sheet.",
      "filters_on_mobile": "Filters live in Sheet/Drawer triggered by a 'Filters' button with active count badge."
    }
  },

  "component_library": {
    "primary": "shadcn/ui (already in /src/components/ui/*.jsx)",
    "icons": "lucide-react",
    "charts": "recharts",
    "motion": "framer-motion (subtle, 120–220ms)"
  },

  "component_path": {
    "app_shell": {
      "sheet_drawer": "src/components/ui/sheet.jsx",
      "drawer": "src/components/ui/drawer.jsx",
      "navigation_menu": "src/components/ui/navigation-menu.jsx",
      "breadcrumb": "src/components/ui/breadcrumb.jsx",
      "separator": "src/components/ui/separator.jsx"
    },
    "forms": {
      "form": "src/components/ui/form.jsx",
      "input": "src/components/ui/input.jsx",
      "textarea": "src/components/ui/textarea.jsx",
      "select": "src/components/ui/select.jsx",
      "checkbox": "src/components/ui/checkbox.jsx",
      "radio_group": "src/components/ui/radio-group.jsx",
      "switch": "src/components/ui/switch.jsx",
      "calendar": "src/components/ui/calendar.jsx",
      "dialog": "src/components/ui/dialog.jsx"
    },
    "data_display": {
      "card": "src/components/ui/card.jsx",
      "badge": "src/components/ui/badge.jsx",
      "tabs": "src/components/ui/tabs.jsx",
      "table": "src/components/ui/table.jsx",
      "pagination": "src/components/ui/pagination.jsx",
      "scroll_area": "src/components/ui/scroll-area.jsx",
      "resizable": "src/components/ui/resizable.jsx",
      "tooltip": "src/components/ui/tooltip.jsx",
      "hover_card": "src/components/ui/hover-card.jsx",
      "progress": "src/components/ui/progress.jsx",
      "skeleton": "src/components/ui/skeleton.jsx"
    },
    "actions_feedback": {
      "button": "src/components/ui/button.jsx",
      "dropdown_menu": "src/components/ui/dropdown-menu.jsx",
      "command_palette": "src/components/ui/command.jsx",
      "alert": "src/components/ui/alert.jsx",
      "alert_dialog": "src/components/ui/alert-dialog.jsx",
      "sonner_toast": "src/components/ui/sonner.jsx"
    }
  },

  "page_anatomy": {
    "/login": {
      "layout": "Split layout: left brand panel (subtle gradient + noise) + right auth card.",
      "components": ["Card", "Button", "Input", "Separator"],
      "details": [
        "Google OAuth button first, then email/password.",
        "Add 'Trust strip' under form: 'India-first coverage • Dedup pipeline • Audit logs'.",
        "Include data-testid on inputs and submit buttons."
      ]
    },

    "/dashboard": {
      "above_fold": [
        "KPI row (4 cards): New businesses, Hot leads, Today's discoveries, Avg lead score",
        "Secondary row: City breakdown (bar) + Category breakdown (donut)"
      ],
      "below_fold": [
        "Recent discoveries table (compact) with quick actions",
        "Daily report preview card (today) with download buttons"
      ],
      "notes": [
        "Prefer 1–2 charts per viewport; keep the rest as tables.",
        "Use Skeleton for KPI and charts while loading."
      ]
    },

    "/businesses": {
      "layout": "Two-pane: left filter sidebar (desktop) + main table. On mobile, filters in Sheet.",
      "table_requirements": [
        "Sticky header",
        "Column sorting",
        "Row selection + bulk actions",
        "Density toggle (Comfortable/Dense)",
        "Export menu (CSV/Excel/PDF)",
        "Search across name/director/phone/email"
      ],
      "recommended_structure": [
        "Topbar: Search input + Filters button (mobile) + Export dropdown + 'New business' CTA",
        "Active filter chips row (scrollable) with 'Clear all'",
        "Table inside ScrollArea with sticky header",
        "Pagination footer with rows-per-page"
      ]
    },

    "/businesses/:id": {
      "layout": "Header with identity + lead badge + actions; content in Tabs.",
      "tabs": ["Overview", "Enrichment", "Predictions", "Lead Score", "Audit History"],
      "actions": [
        "Primary: Re-run AI",
        "Secondary: Edit",
        "Tertiary: Export"
      ],
      "notes": [
        "Use right-side detail panel (Card) for key facts: registration, CIN, GSTIN, directors, contacts.",
        "Audit History is a compact table with filters."
      ]
    },

    "/businesses/new": {
      "layout": "Multi-section form with sticky right summary card (desktop).",
      "sections": ["Identity", "Registration", "Contacts", "Address", "Notes"],
      "notes": [
        "Use Form + field descriptions.",
        "Inline validation + error summary at top."
      ]
    },

    "/businesses/upload": {
      "layout": "Stepper-like flow: Upload → Preview → Dedup Summary → Commit.",
      "components": ["Card", "Progress", "Table", "Alert", "Dialog"],
      "notes": [
        "Drag-drop zone with dashed border; show file requirements.",
        "Preview table uses dense mode.",
        "Dedup summary uses 3 KPI mini-cards: New, Duplicates, Needs review."
      ]
    },

    "/discovery": {
      "layout": "Connector cards grid + run history table.",
      "cards": [
        "OpenCorporates (configured?)",
        "MCA (placeholder)",
        "CSV Upload",
        "Manual Entry"
      ],
      "notes": [
        "Each connector card: status badge, last run, next scheduled, CTA 'Configure' or 'Run now'.",
        "Use AlertDialog for 'Run now' confirmation."
      ]
    },

    "/reports": {
      "layout": "Left: report list; Right: selected report preview (or today's).",
      "notes": [
        "Provide 'Generate report' dialog with filters.",
        "Downloads as Button group: PDF / Excel / CSV.",
        "Use Skeleton for preview rendering."
      ]
    },

    "/preferences": {
      "layout": "Simple settings page with sections.",
      "sections": ["Delivery cadence", "Delivery email", "Default filters"],
      "notes": [
        "Use Switch for daily/weekly.",
        "Default filters saved as chips + 'Edit' opens Sheet."
      ]
    },

    "/admin/*": {
      "layout": "Admin pages share a consistent header with warning tone (subtle).",
      "notes": [
        "Settings: secret masking with 'Reveal' (requires re-auth dialog).",
        "Audit logs: filterable dense table.",
        "Scheduler: status cards + run log table."
      ]
    }
  },

  "data_table_pattern": {
    "density": {
      "dense_row": "h-9",
      "comfortable_row": "h-11",
      "cell": "py-2",
      "dense_cell": "py-1.5"
    },
    "sticky_header": "sticky top-0 z-10 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/70",
    "row_hover": "hover:bg-muted/60",
    "selected_row": "data-[state=selected]:bg-primary/10",
    "empty_state": {
      "title": "No businesses match your filters",
      "body": "Try clearing filters or widening the date range.",
      "cta": "Clear all"
    },
    "bulk_actions": ["Export", "Add to report", "Mark reviewed"],
    "testing": {
      "required_data_testids": [
        "businesses-search-input",
        "businesses-filters-open-button",
        "businesses-export-dropdown-button",
        "businesses-table",
        "businesses-pagination"
      ]
    }
  },

  "forms_pattern": {
    "layout": "Two-column on lg: left fields, right help/summary card. Single column on mobile.",
    "field": {
      "label": "text-sm font-medium",
      "hint": "text-xs text-muted-foreground",
      "error": "text-xs text-destructive"
    },
    "secret_fields": {
      "pattern": "Masked input + reveal button + copy button",
      "security_note": "Reveal requires confirmation dialog; never show secrets by default."
    },
    "testing": {
      "rule": "Every input/select/switch/button must have data-testid in kebab-case describing role."
    }
  },

  "motion_microinteractions": {
    "principles": [
      "Subtle, fast, purposeful (120–220ms).",
      "Use motion to confirm state changes: selection, save, export started, pipeline running.",
      "Respect prefers-reduced-motion."
    ],
    "recommended": {
      "button": "hover: translateY(-1px) + shadow-sm; active: scale(0.98)",
      "table_row": "hover background fade only (no translate)",
      "drawer_sheet": "slide + fade",
      "kpi_cards": "staggered entrance on first load (small y=6, opacity)"
    },
    "framer_motion_scaffold_js": "import { motion, useReducedMotion } from 'framer-motion';\n\nexport function FadeIn({ children, delay = 0 }) {\n  const reduce = useReducedMotion();\n  return (\n    <motion.div\n      initial={reduce ? false : { opacity: 0, y: 6 }}\n      animate={reduce ? false : { opacity: 1, y: 0 }}\n      transition={{ duration: 0.18, ease: 'easeOut', delay }}\n    >\n      {children}\n    </motion.div>\n  );\n}\n"
  },

  "charts_guidelines": {
    "library": "Recharts",
    "style": {
      "grid": "stroke: hsl(var(--border)); strokeDasharray: '3 3'",
      "axis": "tick fill: hsl(var(--muted-foreground))",
      "tooltip": "Use shadcn Card-like tooltip with bg-card and border",
      "colors": [
        "hsl(var(--chart-1))",
        "hsl(var(--chart-2))",
        "hsl(var(--chart-3))",
        "hsl(var(--chart-4))",
        "hsl(var(--chart-5))"
      ]
    },
    "empty_state": "Show a Card with 'No data for selected range' + link to adjust filters."
  },

  "accessibility": {
    "requirements": [
      "WCAG AA contrast for text and UI components.",
      "Keyboard navigation for sidebar, tables, dialogs, tabs.",
      "Visible focus ring using --ring; never remove outline without replacement.",
      "Do not rely on color alone: pair badges with labels (HOT/WARM/COLD) and icons."
    ],
    "focus_class": "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
  },

  "image_urls": {
    "login_brand_panel": [
      {
        "url": "https://images.unsplash.com/photo-1518980120692-3cfe64c152d0?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzF8MHwxfHNlYXJjaHwxfHxhYnN0cmFjdCUyMGRhdGElMjBuZXR3b3JrJTIwbWFwJTIwZG90cyUyMGxpbmVzJTIwc3VidGxlJTIwYmFja2dyb3VuZHxlbnwwfHx8Ymx1ZXwxNzgxNDYyNDg2fDA&ixlib=rb-4.1.0&q=85",
        "description": "Abstract data texture for login left panel (use as low-opacity background image)."
      }
    ],
    "dashboard_header_accent": [
      {
        "url": "https://images.unsplash.com/photo-1647201022486-2282fdb39d2f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjY2NzN8MHwxfHNlYXJjaHwyfHxpbmRpYSUyMGJ1c2luZXNzJTIwc2t5bGluZSUyMG11bWJhaSUyMGNvcnBvcmF0ZSUyMGFic3RyYWN0fGVufDB8fHx0ZWFsfDE3ODE0NjI0ODF8MA&ixlib=rb-4.1.0&q=85",
        "description": "Mumbai architectural cue for subtle India relevance (use as small header thumbnail or empty-state illustration)."
      }
    ],
    "reports_empty_state": [
      {
        "url": "https://images.unsplash.com/photo-1614188973043-4ed7d383de37?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzF8MHwxfHNlYXJjaHw0fHxhYnN0cmFjdCUyMGRhdGElMjBuZXR3b3JrJTIwbWFwJTIwZG90cyUyMGxpbmVzJTIwc3VidGxlJTIwYmFja2dyb3VuZHxlbnwwfHx8Ymx1ZXwxNzgxNDYyNDg2fDA&ixlib=rb-4.1.0&q=85",
        "description": "Dark data-network image for report preview placeholder (use with overlay + blur)."
      }
    ],
    "team_photo_optional": [
      {
        "url": "https://images.unsplash.com/photo-1653503425441-9d975e51ce91?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjBvZmZpY2UlMjBpbmRpYSUyMHRlYW0lMjB3b3JraW5nJTIwbGFwdG9wfGVufDB8fHx8MTc4MTQ2MjQ5NXww&ixlib=rb-4.1.0&q=85",
        "description": "Optional small photo for marketing-like empty states or onboarding panel. Excluding blurred faces, use as generic office context."
      }
    ]
  },

  "instructions_to_main_agent": [
    "Replace CRA default App.css styles; do not use centered .App header layout.",
    "Update index.css :root and .dark tokens to the provided teal+saffron system; keep shadcn variable structure.",
    "Use Space Grotesk for headings and Inter for body via Google Fonts import in index.html or CSS.",
    "Implement AppShell with Sidebar + Topbar; Sidebar uses Sheet on mobile.",
    "All interactive and key informational elements MUST include data-testid attributes (kebab-case).",
    "Use shadcn Table + ScrollArea for dense tables; add sticky header class and density toggle.",
    "Use Sonner for toasts; standardize success/error/info messages.",
    "Use Skeleton for KPI cards, charts, and table loading states.",
    "Use Framer Motion only for page/section entrance and drawers; keep subtle and respect prefers-reduced-motion.",
    "Avoid gradients except the allowed hero/section background overlay; never exceed 20% viewport."
  ],

  "general_ui_ux_design_guidelines_appendix": "<General UI UX Design Guidelines>\n    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.\n</General UI UX Design Guidelines>"
}
