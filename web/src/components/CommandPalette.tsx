import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ArrowRight,
  Clapperboard,
  Dna,
  ExternalLink,
  FolderKanban,
  Radio,
  Search,
  Settings2,
  Sparkles,
} from 'lucide-react';
import type { AppView, CampaignPreset } from '../types/studio';

export interface CommandAction {
  id: string;
  label: string;
  category: 'Quick Action' | 'Navigate' | 'Switch Campaign';
  hint?: string;
  icon: typeof Sparkles;
  run: () => void;
}

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
  presets: CampaignPreset[];
  onNavigate: (view: AppView) => void;
  onFocusPasteUrl: () => void;
  onCheckNewStreams: () => void;
  onOpenLiveUrls: () => void;
  onLearnAnalytics: () => void;
  onSwitchCampaign: (presetId: string) => void;
}

export function CommandPalette({
  open,
  onClose,
  presets,
  onNavigate,
  onFocusPasteUrl,
  onCheckNewStreams,
  onOpenLiveUrls,
  onLearnAnalytics,
  onSwitchCampaign,
}: CommandPaletteProps) {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const actions = useMemo<CommandAction[]>(() => {
    const base: CommandAction[] = [
      {
        id: 'paste-url',
        label: 'Paste URL & Create Clip',
        category: 'Quick Action',
        hint: 'Focus input on Create',
        icon: Sparkles,
        run: onFocusPasteUrl,
      },
      {
        id: 'check-streams',
        label: 'Check New Streams',
        category: 'Quick Action',
        hint: 'Scan watched VOD channels',
        icon: Radio,
        run: onCheckNewStreams,
      },
      {
        id: 'fetch-live-urls',
        label: 'Fetch Live URLs for Whop',
        category: 'Quick Action',
        hint: 'Open 30-min submission drawer',
        icon: ExternalLink,
        run: onOpenLiveUrls,
      },
      {
        id: 'learn-analytics',
        label: 'Learn from Analytics (24h/48h/72h)',
        category: 'Quick Action',
        hint: 'Update Viral DNA rules',
        icon: Dna,
        run: onLearnAnalytics,
      },
      {
        id: 'nav-studio',
        label: 'Open Studio Editor',
        category: 'Navigate',
        hint: '9:16 preview & compliance',
        icon: Clapperboard,
        run: () => onNavigate('studio'),
      },
      {
        id: 'nav-presets',
        label: 'Manage Whop Campaign Presets',
        category: 'Navigate',
        hint: 'config/presets/',
        icon: FolderKanban,
        run: () => onNavigate('presets'),
      },
      {
        id: 'nav-setup',
        label: 'Open Setup & System Guide',
        category: 'Navigate',
        hint: 'BYOK keys & onboarding',
        icon: Settings2,
        run: () => onNavigate('setup'),
      },
    ];

    const presetActions: CommandAction[] = presets.map((p) => ({
      id: `switch-${p.id}`,
      label: `Switch Campaign: ${p.name}`,
      category: 'Switch Campaign',
      hint: p.active ? 'Currently Active' : p.required_hashtags.join(' '),
      icon: FolderKanban,
      run: () => onSwitchCampaign(p.id),
    }));

    return [...base, ...presetActions];
  }, [
    presets,
    onFocusPasteUrl,
    onCheckNewStreams,
    onOpenLiveUrls,
    onLearnAnalytics,
    onNavigate,
    onSwitchCampaign,
  ]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return actions;
    return actions.filter(
      (a) =>
        a.label.toLowerCase().includes(q) ||
        a.category.toLowerCase().includes(q) ||
        (a.hint?.toLowerCase().includes(q) ?? false)
    );
  }, [actions, query]);

  useEffect(() => {
    if (open) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 20);
    }
  }, [open]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  if (!open) return null;

  const execute = (action: CommandAction) => {
    action.run();
    onClose();
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Quick Command Palette"
      className="fixed inset-0 z-50 flex items-start justify-center pt-[14vh] px-4"
    >
      <button
        type="button"
        aria-label="Close command palette"
        onClick={onClose}
        className="fixed inset-0 bg-black/75 backdrop-blur-sm"
      />
      <div className="relative z-10 w-full max-w-[560px] rounded-xl border border-white/[0.12] bg-[#111113] overflow-hidden">
        <div className="flex items-center gap-3 border-b border-white/[0.08] px-4 py-3">
          <Search className="h-4 w-4 text-[#71717A] shrink-0" aria-hidden="true" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Escape') {
                e.preventDefault();
                onClose();
              } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                setSelectedIndex((i) => Math.min(filtered.length - 1, i + 1));
              } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                setSelectedIndex((i) => Math.max(0, i - 1));
              } else if (e.key === 'Enter' && filtered[selectedIndex]) {
                e.preventDefault();
                execute(filtered[selectedIndex]);
              }
            }}
            placeholder="Jump to action, view, or campaign..."
            aria-label="Search commands"
            className="w-full bg-transparent text-sm text-[#FAFAFA] placeholder:text-[#71717A] focus:outline-none"
          />
          <kbd className="font-mono text-[11px] text-[#71717A] shrink-0">ESC</kbd>
        </div>

        <div className="max-h-[360px] overflow-y-auto p-2 space-y-0.5">
          {filtered.length === 0 ? (
            <p className="py-8 text-center text-xs text-[#71717A]">
              No matching commands found.
            </p>
          ) : (
            filtered.map((action, idx) => {
              const Icon = action.icon;
              const isSelected = idx === selectedIndex;
              return (
                <button
                  key={action.id}
                  type="button"
                  onMouseEnter={() => setSelectedIndex(idx)}
                  onClick={() => execute(action)}
                  className={`w-full flex items-center justify-between gap-3 rounded-lg px-3 py-2.5 text-left transition-colors ${
                    isSelected
                      ? 'bg-white/[0.08] text-[#FAFAFA]'
                      : 'text-[#A1A1AA] hover:bg-white/[0.04]'
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <Icon
                      className={`h-4 w-4 shrink-0 ${
                        isSelected ? 'text-[#FFE600]' : 'text-[#71717A]'
                      }`}
                      aria-hidden="true"
                    />
                    <div className="min-w-0">
                      <div className="text-sm font-medium text-[#FAFAFA] truncate">
                        {action.label}
                      </div>
                      {action.hint && (
                        <div className="text-xs text-[#71717A] truncate">{action.hint}</div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-[11px] text-[#71717A]">{action.category}</span>
                    {isSelected && <ArrowRight className="h-3.5 w-3.5 text-[#FFE600]" />}
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
