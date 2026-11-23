import { Command, ExternalLink, Menu, RefreshCw } from 'lucide-react';
import type { CampaignPreset } from '../types/studio';

interface TopBarProps {
  activePreset: CampaignPreset | undefined;
  presets: CampaignPreset[];
  onSwitchPreset: (presetId: string) => void;
  onOpenCommandPalette: () => void;
  onOpenLiveUrlsDrawer: () => void;
  pendingLiveUrlsCount: number;
  backendReachable: boolean;
  onRefreshHealth: () => void;
  onOpenMobileNav: () => void;
}

export function TopBar({
  activePreset,
  presets,
  onSwitchPreset,
  onOpenCommandPalette,
  onOpenLiveUrlsDrawer,
  pendingLiveUrlsCount,
  backendReachable,
  onRefreshHealth,
  onOpenMobileNav,
}: TopBarProps) {
  return (
    <header className="sticky top-0 z-30 h-[52px] shrink-0 border-b border-white/[0.08] bg-[#09090B]/85 backdrop-blur-md px-3 sm:px-5 flex items-center justify-between gap-3">
      {/* Left: Mobile Menu + Active Campaign Selector */}
      <div className="flex items-center gap-2.5 min-w-0">
        <button
          type="button"
          onClick={onOpenMobileNav}
          aria-label="Open navigation menu"
          className="md:hidden flex h-8 w-8 items-center justify-center rounded-md text-[#A1A1AA] hover:text-[#FAFAFA] hover:bg-white/[0.06] shrink-0"
        >
          <Menu className="h-4 w-4" />
        </button>

        <div className="flex items-center gap-2 min-w-0 flex-1 sm:flex-initial">
          <span
            className={`h-1.5 w-1.5 rounded-full shrink-0 ${
              activePreset ? 'bg-[#22C55E]' : 'bg-[#71717A]'
            }`}
            aria-hidden="true"
          />
          <label htmlFor="topbar-campaign-select" className="sr-only">
            Active Campaign
          </label>
          <select
            id="topbar-campaign-select"
            value={activePreset?.id ?? ''}
            onChange={(e) => onSwitchPreset(e.target.value)}
            disabled={presets.length === 0}
            className="w-full max-w-[132px] sm:w-auto sm:max-w-[230px] min-w-0 truncate rounded-md border border-white/[0.08] bg-[#111113] px-2 sm:px-2.5 py-1 text-xs font-medium text-[#FAFAFA] hover:border-white/[0.16] transition-colors cursor-pointer disabled:opacity-50"
          >
            {presets.length === 0 ? (
              <option value="">No Active Campaign</option>
            ) : (
              presets.map((p) => (
                <option key={p.id} value={p.id} className="bg-[#111113] text-[#FAFAFA]">
                  {p.name}
                </option>
              ))
            )}
          </select>
        </div>
      </div>

      {/* Center: Quick Command Palette Trigger */}
      <button
        type="button"
        onClick={onOpenCommandPalette}
        aria-label="Open Command Palette"
        className="hidden sm:flex items-center justify-between gap-6 w-full max-w-[300px] rounded-md border border-white/[0.08] bg-[#111113] px-3 py-1.5 text-xs text-[#71717A] hover:border-white/[0.14] hover:text-[#A1A1AA] transition-colors whitespace-nowrap"
      >
        <span className="flex items-center gap-2 truncate">
          <Command className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
          <span>Quick actions...</span>
        </span>
        <kbd className="font-mono text-[11px] text-[#71717A]">Ctrl+K</kbd>
      </button>

      {/* Right: Whop Live URLs Drawer Trigger + Real Backend Status */}
      <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
        <button
          type="button"
          onClick={onOpenLiveUrlsDrawer}
          className="flex items-center gap-1.5 sm:gap-2 rounded-md border border-white/[0.08] bg-[#111113] px-2 sm:px-3 py-1.5 text-xs font-medium text-[#FAFAFA] hover:border-white/[0.16] transition-colors whitespace-nowrap shrink-0"
        >
          <span
            className={`h-1.5 w-1.5 rounded-full shrink-0 ${
              pendingLiveUrlsCount > 0 ? 'bg-[#F59E0B]' : 'bg-[#22C55E]'
            }`}
            aria-hidden="true"
          />
          <span className="hidden sm:inline">Whop Live URLs</span>
          <span className="sm:hidden">Live URLs</span>
          <span className="font-mono text-[11px] text-[#A1A1AA] tabular-nums">
            {pendingLiveUrlsCount}
          </span>
          <ExternalLink className="h-3 w-3 text-[#71717A] hidden sm:inline" aria-hidden="true" />
        </button>

        {/* Real Live Backend Health Badge */}
        <button
          type="button"
          onClick={onRefreshHealth}
          title={
            backendReachable
              ? 'FastAPI Engine connected at http://127.0.0.1:8765 (Click to re-check)'
              : 'FastAPI Engine offline — launch via start_web.bat (Click to retry)'
          }
          className={`flex items-center gap-1.5 rounded-md border px-2 sm:px-2.5 py-1.5 font-mono text-[11px] transition-colors whitespace-nowrap shrink-0 ${
            backendReachable
              ? 'border-white/[0.08] bg-[#111113] text-[#FAFAFA] hover:border-white/[0.16]'
              : 'border-[#EF4444]/30 bg-[#EF4444]/10 text-[#EF4444] hover:bg-[#EF4444]/15'
          }`}
        >
          <span
            className={`h-1.5 w-1.5 rounded-full shrink-0 ${
              backendReachable ? 'bg-[#22C55E] animate-pulse' : 'bg-[#EF4444]'
            }`}
            aria-hidden="true"
          />
          <span className="hidden sm:inline">
            {backendReachable ? 'Local Engine Online' : 'Engine Offline'}
          </span>
          <span className="sm:hidden">{backendReachable ? 'Online' : 'Offline'}</span>
          <RefreshCw className="h-3 w-3 opacity-60 ml-0.5" />
        </button>
      </div>
    </header>
  );
}
