import {
  ChevronLeft,
  ChevronRight,
  Clapperboard,
  Dna,
  FolderKanban,
  Radio,
  Settings2,
  Sparkles,
  X,
} from 'lucide-react';
import type { AppView } from '../types/studio';

interface SidebarProps {
  activeView: AppView;
  onSelectView: (view: AppView) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
  queuedCount: number;
  unclippedVodsCount: number;
}

const NAV_ITEMS: Array<{
  id: AppView;
  label: string;
  icon: typeof Sparkles;
  shortcut: string;
}> = [
  { id: 'create', label: 'Create', icon: Sparkles, shortcut: '1' },
  { id: 'studio', label: 'Studio', icon: Clapperboard, shortcut: '2' },
  { id: 'live-hunt', label: 'Live Hunt', icon: Radio, shortcut: '3' },
  { id: 'presets', label: 'Presets', icon: FolderKanban, shortcut: '4' },
  { id: 'viral-dna', label: 'Viral DNA', icon: Dna, shortcut: '5' },
  { id: 'setup', label: 'Setup & Guide', icon: Settings2, shortcut: '6' },
];

export function Sidebar({
  activeView,
  onSelectView,
  collapsed,
  onToggleCollapse,
  mobileOpen,
  onCloseMobile,
  queuedCount,
  unclippedVodsCount,
}: SidebarProps) {
  const navList = (isCollapsed: boolean) => (
    <nav aria-label="Primary navigation" className="flex-1 px-2.5 py-3 space-y-1">
      {NAV_ITEMS.map((item) => {
        const Icon = item.icon;
        const isActive = activeView === item.id;
        const count =
          item.id === 'create'
            ? queuedCount
            : item.id === 'live-hunt'
              ? unclippedVodsCount
              : null;

        return (
          <button
            key={item.id}
            type="button"
            onClick={() => {
              onSelectView(item.id);
              onCloseMobile();
            }}
            aria-current={isActive ? 'page' : undefined}
            title={isCollapsed ? item.label : undefined}
            className={`group w-full flex items-center gap-3 rounded-lg px-2.5 py-2 text-sm font-medium transition-colors whitespace-nowrap ${
              isActive
                ? 'bg-[#18181B] text-[#FAFAFA] ring-1 ring-inset ring-white/10'
                : 'text-[#A1A1AA] hover:text-[#FAFAFA] hover:bg-white/[0.04]'
            } ${isCollapsed ? 'justify-center px-0' : ''}`}
          >
            <Icon
              className={`h-4 w-4 shrink-0 transition-colors ${
                isActive ? 'text-[#FFE600]' : 'text-[#71717A] group-hover:text-[#A1A1AA]'
              }`}
              aria-hidden="true"
            />
            {!isCollapsed && (
              <>
                <span className="flex-1 text-left truncate">{item.label}</span>
                {count !== null && count > 0 && (
                  <span className="font-mono text-[11px] text-[#71717A] tabular-nums">
                    {count}
                  </span>
                )}
              </>
            )}
          </button>
        );
      })}
    </nav>
  );

  return (
    <>
      {/* Desktop rail */}
      <aside
        className={`hidden md:flex flex-col shrink-0 border-r border-white/[0.08] bg-[#09090B] transition-[width] duration-200 ease-out ${
          collapsed ? 'w-[64px]' : 'w-[220px]'
        }`}
      >
        <div
          className={`h-[52px] flex items-center border-b border-white/[0.08] ${
            collapsed ? 'justify-center px-2' : 'justify-between px-4'
          }`}
        >
          <button
            type="button"
            onClick={() => onSelectView('create')}
            className="flex items-center gap-2.5 text-left whitespace-nowrap shrink-0"
            aria-label="SaimClip Studio Home"
          >
            <span className="flex h-6 w-6 items-center justify-center rounded-md bg-[#FFE600] text-[#09090B] font-mono text-xs font-bold shrink-0">
              S
            </span>
            {!collapsed && (
              <span className="text-[14px] font-semibold tracking-tight text-[#FAFAFA]">
                SaimClip Studio
              </span>
            )}
          </button>
        </div>

        {navList(collapsed)}

        <div className="border-t border-white/[0.08] p-2.5 flex items-center justify-between">
          {!collapsed && (
            <span className="px-2 font-mono text-[11px] text-[#71717A] truncate">
              saimgta6clipping
            </span>
          )}
          <button
            type="button"
            onClick={onToggleCollapse}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className={`flex h-8 w-8 items-center justify-center rounded-md text-[#71717A] hover:text-[#FAFAFA] hover:bg-white/[0.05] transition-colors ${
              collapsed ? 'mx-auto' : ''
            }`}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>
      </aside>

      {/* Mobile slide-over rail */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          <button
            type="button"
            aria-label="Close navigation menu"
            onClick={onCloseMobile}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm"
          />
          <aside className="relative z-10 flex w-[240px] flex-col bg-[#09090B] border-r border-white/[0.08]">
            <div className="h-[52px] flex items-center justify-between px-4 border-b border-white/[0.08]">
              <span className="flex items-center gap-2.5 text-[14px] font-semibold tracking-tight text-[#FAFAFA]">
                <span className="flex h-6 w-6 items-center justify-center rounded-md bg-[#FFE600] text-[#09090B] font-mono text-xs font-bold">
                  S
                </span>
                SaimClip Studio
              </span>
              <button
                type="button"
                onClick={onCloseMobile}
                aria-label="Close navigation"
                className="flex h-8 w-8 items-center justify-center rounded-md text-[#A1A1AA] hover:text-[#FAFAFA]"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            {navList(false)}
          </aside>
        </div>
      )}
    </>
  );
}
