// Curated module navigation model. Mirrors vault/modules.json (id, name, wave,
// enabled) but adds grouping + icons the registry doesn't carry, and the page
// routes that aren't in modules.json's ui_route (Dashboard, Asset Library).
// Enabled items link; disabled items render as muted "coming soon" with a tooltip.

import {
  Activity,
  Award,
  BadgeCheck,
  BarChart3,
  BookMarked,
  Building2,
  Calculator,
  ClipboardCheck,
  Code2,
  FileSignature,
  FileText,
  Gauge,
  GraduationCap,
  History,
  LayoutDashboard,
  Library,
  Lightbulb,
  type LucideIcon,
  MessagesSquare,
  Package,
  Puzzle,
  Rss,
  Scale,
  ShieldCheck,
  Sparkles,
  Users,
  Video,
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
    title: "Accelerate",
    items: [
      { id: "module-3", label: "Kit Builder", wave: 2, icon: Package, route: "/modules/kit-builder", enabled: true, purpose: "Assemble a tailored engagement kit." },
      { id: "module-11", label: "Prompt Studio", wave: 4, icon: Sparkles, route: "/modules/prompt-studio", enabled: true, purpose: "Build & test prompts." },
      { id: "module-28", label: "Skills & Plugin Exchange", wave: 5, icon: Puzzle, route: "/modules/exchange", enabled: true, purpose: "Reusable agentic-dev skills, MCP servers & configs." },
      { id: "module-27", label: "SDLC Accelerator", wave: 7, icon: Code2, enabled: false, purpose: "Full-SDLC accelerator: design, specs, tests & code (Opus, cost-capped)." },
    ],
  },
  {
    title: "Project's Work",
    items: [
      { id: "module-1", label: "AI Maturity Assessment", wave: 2, icon: BarChart3, route: "/modules/maturity-assessment", enabled: true, purpose: "Place a client on the 0–5 AI maturity curve." },
      { id: "module-12", label: "AI Use Case Ideation", wave: 5, icon: Lightbulb, route: "/modules/ideation", enabled: true, purpose: "Generate & rank AI use cases." },
      { id: "module-29", label: "AI Project ROI Calculator", wave: 5, icon: Calculator, route: "/modules/roi-calculator", enabled: true, purpose: "Estimate cost, value & ROI for an AI project." },
      { id: "module-30", label: "AI SOW Generator", wave: 5, icon: FileSignature, route: "/modules/sow-generator", enabled: true, purpose: "Draft a statement of work for an AI engagement." },
      { id: "module-31", label: "Vendor Vetting", wave: 5, icon: BadgeCheck, route: "/modules/vendor-vetting", enabled: true, purpose: "Vet & manage AI vendors — security, compliance & approval status." },
      { id: "module-4", label: "Governance & Risk", wave: 3, icon: ShieldCheck, route: "/modules/governance", enabled: true, purpose: "Check use cases against AI controls." },
      { id: "module-21", label: "Ethics & Bias Checker", wave: 3, icon: Scale, route: "/modules/ethics-checker", enabled: true, purpose: "Flag ethics & bias risks." },
      { id: "module-25", label: "Compliance Tracker", wave: 3, icon: ClipboardCheck, route: "/modules/compliance-tracker", enabled: true, purpose: "Global AI regulation tracker." },
      { id: "module-18", label: "Project Health", wave: 5, icon: Activity, route: "/modules/project-health", enabled: true, purpose: "Monitor AI project health." },
      { id: "module-16", label: "Retrospectives", wave: 5, icon: History, route: "/modules/retros", enabled: true, purpose: "Capture engagement learnings & extract reusable insights." },
      // Internal CoE tool: kept out of the chat assistant's live module set (modules.json
      // enabled:false) so it isn't surfaced as a client-facing capability.
      { id: "module-19", label: "Decision Log", wave: 5, icon: BookMarked, route: "/modules/decisions", enabled: true, purpose: "Project decision log — capture decisions & rationale; surface precedent." },
      { id: "module-14", label: "Client Report", wave: 6, icon: FileText, route: "/modules/reports", enabled: true, purpose: "Client-facing maturity report." },
    ],
  },
  {
    title: "Knowledge Hub",
    items: [
      { id: "module-8", label: "Q&A", wave: 4, icon: MessagesSquare, route: "/modules/qa", enabled: true, purpose: "Cited answers from the vault." },
      { id: "module-2", label: "Asset Library", wave: 1, icon: Library, route: "/modules/asset-library", enabled: true, purpose: "Browse curated AI delivery assets." },
      { id: "module-7", label: "Tools Repository", wave: 4, icon: Wrench, route: "/modules/tools-repo", enabled: true, purpose: "Tool & framework recommendations." },
      { id: "module-13", label: "Benchmarks", wave: 4, icon: Gauge, route: "/modules/vendor-eval", enabled: true, purpose: "Vendor & model evaluation benchmarks." },
      { id: "module-24", label: "Intelligence Feed", wave: 5, icon: Rss, route: "/modules/intelligence-feed", enabled: true, purpose: "AI news & release radar." },
    ],
  },
  {
    title: "Learn & Community",
    items: [
      { id: "module-6", label: "Community", wave: 6, icon: Users, route: "/modules/community", enabled: true, purpose: "Peer expertise & enablement." },
      { id: "module-5", label: "Contribute", wave: 6, icon: Sparkles, route: "/modules/contribute", enabled: true, purpose: "Contribute new vault assets with AI-assisted anonymization + curator review." },
      { id: "module-32", label: "Trainings", wave: 6, icon: Video, route: "/modules/trainings", enabled: true, purpose: "Hosted trainings + curated external tutorials by theme." },
      { id: "module-23", label: "Onboarding", wave: 6, icon: GraduationCap, enabled: false, purpose: "Consultant onboarding journey." },
      { id: "module-20", label: "Certification", wave: 6, icon: Award, enabled: false, purpose: "Certification & badging." },
      { id: "module-10", label: "Analytics", wave: 6, icon: Building2, enabled: false, purpose: "Platform usage analytics." },
    ],
  },
];
