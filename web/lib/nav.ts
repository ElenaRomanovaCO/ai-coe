// Curated module navigation model. Mirrors vault/modules.json (id, name, wave,
// enabled) but adds grouping + icons the registry doesn't carry, and the page
// routes that aren't in modules.json's ui_route (Dashboard, Asset Library).
// Enabled items link; disabled items render as muted "coming soon" with a tooltip.

import {
  Activity,
  Award,
  BarChart3,
  BookMarked,
  Boxes,
  Building2,
  ClipboardCheck,
  Code2,
  FileText,
  GraduationCap,
  LayoutDashboard,
  Library,
  Lightbulb,
  type LucideIcon,
  MessagesSquare,
  Package,
  Rss,
  Scale,
  ShieldCheck,
  Sparkles,
  Users,
  Wrench,
} from "lucide-react";

export interface NavItem {
  id: string;
  label: string;
  wave: number;
  icon: LucideIcon;
  route?: string; // present → live link
  enabled: boolean;
  purpose: string; // tooltip for disabled items
}

export interface NavGroup {
  title: string;
  items: NavItem[];
}

export const NAV_GROUPS: NavGroup[] = [
  {
    title: "Home",
    items: [
      {
        id: "module-17",
        label: "Dashboard",
        wave: 1,
        icon: LayoutDashboard,
        route: "/dashboard",
        enabled: true,
        purpose: "Your personalized home view.",
      },
    ],
  },
  {
    title: "Knowledge",
    items: [
      {
        id: "module-2",
        label: "Asset Library",
        wave: 1,
        icon: Library,
        route: "/modules/asset-library",
        enabled: true,
        purpose: "Browse curated AI delivery assets.",
      },
      { id: "module-8", label: "Q&A", wave: 4, icon: MessagesSquare, route: "/modules/qa", enabled: true, purpose: "Cited answers from the vault." },
      { id: "module-26", label: "Universal Asset Q&A", wave: 2, icon: MessagesSquare, enabled: false, purpose: "Ask questions against any asset." },
      { id: "module-7", label: "Tools Repository", wave: 4, icon: Wrench, route: "/modules/tools-repo", enabled: true, purpose: "Tool & framework recommendations." },
      { id: "module-13", label: "Vendor & Model Eval", wave: 4, icon: Boxes, route: "/modules/vendor-eval", enabled: true, purpose: "Compare vendors and models." },
      { id: "module-24", label: "Intelligence Feed", wave: 5, icon: Rss, enabled: false, purpose: "AI news & release radar." },
    ],
  },
  {
    title: "Assess & Govern",
    items: [
      {
        id: "module-1",
        label: "Maturity Assessment",
        wave: 2,
        icon: BarChart3,
        route: "/modules/maturity-assessment",
        enabled: true,
        purpose: "Place a client on the 0–5 AI maturity curve.",
      },
      { id: "module-4", label: "Governance & Risk", wave: 3, icon: ShieldCheck, route: "/modules/governance", enabled: true, purpose: "Check use cases against AI controls." },
      { id: "module-21", label: "Ethics & Bias Checker", wave: 3, icon: Scale, route: "/modules/ethics-checker", enabled: true, purpose: "Flag ethics & bias risks." },
      { id: "module-25", label: "Compliance Tracker", wave: 3, icon: ClipboardCheck, route: "/modules/compliance-tracker", enabled: true, purpose: "Global AI regulation tracker." },
      { id: "module-18", label: "Project Health", wave: 5, icon: Activity, enabled: false, purpose: "Monitor AI project health." },
      { id: "module-22", label: "Benchmark", wave: 5, icon: BarChart3, enabled: false, purpose: "Compare clients to peers." },
    ],
  },
  {
    title: "Build & Deliver",
    items: [
      {
        id: "module-3",
        label: "Kit Builder",
        wave: 2,
        icon: Package,
        route: "/modules/kit-builder",
        enabled: true,
        purpose: "Assemble a tailored engagement kit.",
      },
      { id: "module-11", label: "Prompt Studio", wave: 4, icon: Sparkles, route: "/modules/prompt-studio", enabled: true, purpose: "Build & test prompts." },
      { id: "module-12", label: "Use Case Ideation", wave: 5, icon: Lightbulb, enabled: false, purpose: "Generate & rank AI use cases." },
      { id: "module-27", label: "Code Accelerator", wave: 7, icon: Code2, enabled: false, purpose: "Claude Code delivery accelerator." },
      { id: "module-14", label: "Client Report", wave: 6, icon: FileText, enabled: false, purpose: "Client-facing maturity report." },
      { id: "module-19", label: "Decision Log", wave: 5, icon: BookMarked, enabled: false, purpose: "Capture engagement decisions." },
    ],
  },
  {
    title: "Learn & Community",
    items: [
      { id: "module-6", label: "Community", wave: 6, icon: Users, enabled: false, purpose: "Peer expertise & enablement." },
      { id: "module-5", label: "Contribute", wave: 6, icon: Sparkles, enabled: false, purpose: "Contribute new vault assets." },
      { id: "module-23", label: "Onboarding", wave: 6, icon: GraduationCap, enabled: false, purpose: "Consultant onboarding journey." },
      { id: "module-20", label: "Certification", wave: 6, icon: Award, enabled: false, purpose: "Certification & badging." },
      { id: "module-10", label: "Analytics", wave: 6, icon: Building2, enabled: false, purpose: "Platform usage analytics." },
    ],
  },
];
