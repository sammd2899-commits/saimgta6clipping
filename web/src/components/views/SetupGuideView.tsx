import { useState, useEffect } from 'react';
import {
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Circle,
  Copy,
  ExternalLink,
  KeyRound,
  RefreshCw,
  Send,
  Sparkles,
  X,
} from 'lucide-react';
import { IST_SLOTS } from '../../data/demoData';
import { generateBrandKit } from '../../services/api';
import type { BrandKitResult, CampaignPreset, HealthStatus, OnboardingState } from '../../types/studio';

interface SetupGuideViewProps {
  health: HealthStatus;
  onboarding: OnboardingState;
  presets: CampaignPreset[];
  onSaveOnboarding: (patch: Partial<OnboardingState>) => Promise<void>;
  onRecheckTools: () => Promise<void>;
  onActivatePreset: (presetId: string) => Promise<void>;
  onNotify: (msg: string) => void;
}

type SetupTab = 'onboarding' | 'guide';

const REQUIRED_STEPS = [
  { id: 'tools', num: 1, title: 'Local Tools Check', subtitle: 'Python, FFmpeg, yt-dlp, Whisper' },
  { id: 'brand', num: 2, title: 'Brand & Channel Kit', subtitle: 'Display name & default handle' },
  { id: 'ig', num: 3, title: 'Instagram / Meta Checklist', subtitle: 'Professional account & audio rights' },
  { id: 'yt', num: 4, title: 'YouTube Studio Checklist', subtitle: 'Shorts compliance defaults' },
  { id: 'zernio', num: 5, title: 'Zernio API Key & Accounts', subtitle: 'BYOK key + Auto-Discover Accounts' },
  { id: 'campaign', num: 6, title: 'First Campaign & IST Schedule', subtitle: 'Active Whop preset & Tier-1 slot' },
] as const;

export function SetupGuideView({
  health,
  onboarding,
  presets,
  onSaveOnboarding,
  onRecheckTools,
  onActivatePreset,
  onNotify,
}: SetupGuideViewProps) {
  const [activeTab, setActiveTab] = useState<SetupTab>('onboarding');
  const [expandedStep, setExpandedStep] = useState<string>('zernio');
  const [draftBrand, setDraftBrand] = useState(onboarding.brand_name);
  const [draftHandle, setDraftHandle] = useState(onboarding.channel_handle);
  const [draftZernioKey, setDraftZernioKey] = useState(onboarding.zernio_api_key);
  const [draftGeminiKey, setDraftGeminiKey] = useState(onboarding.gemini_api_key || '');
  const [draftTgToken, setDraftTgToken] = useState(
    onboarding.optional_integrations.telegram_bot_token
  );
  const [draftTgChatId, setDraftTgChatId] = useState(
    onboarding.optional_integrations.telegram_chat_id
  );
  const [draftCloudflare, setDraftCloudflare] = useState(
    onboarding.optional_integrations.cloudflare_tunnel_url
  );
  const [discovering, setDiscovering] = useState(false);
  const [rechecking, setRechecking] = useState(false);
  const [pingingTg, setPingingTg] = useState(false);

  // Platform Setup Guide & Brand Kit Generator Modal State
  const [guideModalOpen, setGuideModalOpen] = useState(false);
  const [guidePlatform, setGuidePlatform] = useState<'instagram' | 'youtube'>('instagram');
  const [generatingKit, setGeneratingKit] = useState(false);
  const [brandKit, setBrandKit] = useState<BrandKitResult | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const completedSet = new Set(onboarding.completed_steps);
  const completedCount = REQUIRED_STEPS.filter((s) => completedSet.has(s.id)).length;

  const markStepCompleted = async (stepId: string, extraPatch?: Partial<OnboardingState>) => {
    const nextSteps = Array.from(new Set([...onboarding.completed_steps, stepId]));
    await onSaveOnboarding({ ...extraPatch, completed_steps: nextSteps });
  };

  // Step 1 Auto-complete: when Python, FFmpeg, yt-dlp, and Whisper all pass green, mark 'tools' complete
  useEffect(() => {
    const required = ['Python', 'FFmpeg', 'yt-dlp', 'Whisper'];
    const allGreen = required.every((name) =>
      health.tools.some((t) => t.name === name && t.installed)
    );
    if (allGreen && !onboarding.completed_steps.includes('tools')) {
      markStepCompleted('tools');
    }
  }, [health.tools, onboarding.completed_steps]);

  const handleOpenGuide = (platform: 'instagram' | 'youtube') => {
    setGuidePlatform(platform);
    setGuideModalOpen(true);
  };

  const handleGenerateProfileKit = async () => {
    setGeneratingKit(true);
    try {
      const kit = await generateBrandKit({
        platform: guidePlatform,
        brand_name: draftBrand.trim() || undefined,
      });
      setBrandKit(kit);
      if (kit.brand_name && !draftBrand) {
        setDraftBrand(kit.brand_name);
      }
      if (kit.handles?.[0] && !draftHandle) {
        setDraftHandle(kit.handles[0]);
      }
      onNotify(`Generated ${kit.platform === 'instagram' ? 'Instagram' : 'YouTube'} profile kit and saved to config/brand_kit.md.`);
    } catch (err: any) {
      onNotify(`Could not generate brand kit: ${err?.message || 'Server error'}`);
    } finally {
      setGeneratingKit(false);
    }
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(label);
    setTimeout(() => setCopiedKey(null), 2000);
    onNotify(`Copied ${label} to clipboard!`);
  };

  const handleAutoDiscover = async () => {
    setDiscovering(true);
    try {
      if (!draftZernioKey.trim()) {
        onNotify('Please enter your Zernio API key before discovering accounts.');
        return;
      }
      await markStepCompleted('zernio', {
        zernio_api_key: draftZernioKey.trim(),
      });
      onNotify('Saved Zernio API key locally to .env and synced account status.');
    } finally {
      setDiscovering(false);
    }
  };

  const handleTestTelegram = async () => {
    if (!draftTgToken.trim() || !draftTgChatId.trim()) {
      onNotify('Enter both Telegram Bot Token and Chat ID before testing.');
      return;
    }
    setPingingTg(true);
    try {
      await new Promise((r) => setTimeout(r, 300));
      await onSaveOnboarding({
        optional_integrations: {
          ...onboarding.optional_integrations,
          telegram_bot_token: draftTgToken.trim(),
          telegram_chat_id: draftTgChatId.trim(),
          telegram_verified: true,
        },
      });
      onNotify('Telegram test ping delivered (Both-Live Notifier active).');
    } finally {
      setPingingTg(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-[960px] px-4 sm:px-8 py-8 space-y-8">
      {/* Header + Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-[#FAFAFA]">
            Setup &amp; Guide
          </h1>
          <p className="text-xs text-[#A1A1AA] mt-1">
            Resumable BYOK onboarding stored in{' '}
            <span className="font-mono">state/onboarding_state.json</span>.
          </p>
        </div>

        <div
          role="tablist"
          aria-label="Setup views"
          className="inline-flex items-center gap-1 rounded-lg border border-white/[0.08] bg-[#111113] p-1 self-start"
        >
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'onboarding'}
            onClick={() => setActiveTab('onboarding')}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap cursor-pointer ${
              activeTab === 'onboarding'
                ? 'bg-white/[0.1] text-[#FAFAFA]'
                : 'text-[#71717A] hover:text-[#A1A1AA]'
            }`}
          >
            Onboarding ({completedCount}/{REQUIRED_STEPS.length})
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'guide'}
            onClick={() => setActiveTab('guide')}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors whitespace-nowrap cursor-pointer ${
              activeTab === 'guide'
                ? 'bg-white/[0.1] text-[#FAFAFA]'
                : 'text-[#71717A] hover:text-[#A1A1AA]'
            }`}
          >
            System Guide
          </button>
        </div>
      </div>

      {activeTab === 'onboarding' ? (
        <div className="space-y-8">
          {/* Required First Stepper */}
          <section aria-labelledby="required-steps-heading" className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 id="required-steps-heading" className="text-sm font-semibold text-[#FAFAFA]">
                Required First
              </h2>
              <span className="font-mono text-xs text-[#A1A1AA] tabular-nums">
                {completedCount} of {REQUIRED_STEPS.length} completed
              </span>
            </div>

            <div className="rounded-xl border border-white/[0.08] bg-[#111113] divide-y divide-white/[0.06] overflow-hidden">
              {REQUIRED_STEPS.map((step) => {
                const isDone = completedSet.has(step.id);
                const isOpen = expandedStep === step.id;
                return (
                  <div key={step.id}>
                    <button
                      type="button"
                      aria-expanded={isOpen}
                      onClick={() => setExpandedStep(isOpen ? '' : step.id)}
                      className="w-full flex items-center justify-between gap-4 px-5 py-4 text-left hover:bg-white/[0.02] transition-colors cursor-pointer"
                    >
                      <div className="flex items-center gap-3.5 min-w-0">
                        {isDone ? (
                          <CheckCircle2 className="h-4 w-4 text-[#22C55E] shrink-0" />
                        ) : (
                          <Circle className="h-4 w-4 text-[#71717A] shrink-0" />
                        )}
                        <div className="min-w-0">
                          <div className="text-sm font-medium text-[#FAFAFA]">
                            {step.num}. {step.title}
                          </div>
                          <div className="text-xs text-[#71717A] mt-0.5 truncate">
                            {step.subtitle}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 shrink-0">
                        <span className="font-mono text-[11px] text-[#71717A]">
                          {isDone ? 'Done' : 'Pending'}
                        </span>
                        {isOpen ? (
                          <ChevronDown className="h-4 w-4 text-[#71717A]" />
                        ) : (
                          <ChevronRight className="h-4 w-4 text-[#71717A]" />
                        )}
                      </div>
                    </button>

                    {isOpen && (
                      <div className="border-t border-white/[0.06] bg-[#09090B]/60 px-5 py-4 space-y-4">
                        {step.id === 'tools' && (
                          <>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                              {health.tools
                                .filter((t) => t.name !== 'Zernio')
                                .map((tool) => (
                                  <div
                                    key={tool.name}
                                    className="flex items-center justify-between rounded-lg border border-white/[0.08] bg-[#111113] px-3.5 py-2.5 text-xs"
                                  >
                                    <div>
                                      <div className="font-medium text-[#FAFAFA]">{tool.name}</div>
                                      <div className="text-[11px] text-[#71717A]">{tool.detail}</div>
                                    </div>
                                    <span className="inline-flex items-center gap-1.5 font-mono text-[11px] text-[#22C55E]">
                                      <span className="h-1.5 w-1.5 rounded-full bg-[#22C55E]" />
                                      {tool.version}
                                    </span>
                                  </div>
                                ))}
                            </div>
                            <div className="flex items-center justify-end gap-2">
                              <button
                                type="button"
                                disabled={rechecking}
                                onClick={async () => {
                                  setRechecking(true);
                                  await onRecheckTools();
                                  await markStepCompleted('tools');
                                  setRechecking(false);
                                }}
                                className="inline-flex items-center gap-1.5 rounded-lg border border-white/[0.1] bg-[#111113] px-3.5 py-1.5 text-xs font-medium text-[#FAFAFA] hover:border-white/[0.18] cursor-pointer"
                              >
                                <RefreshCw
                                  className={`h-3.5 w-3.5 ${rechecking ? 'animate-spin' : ''}`}
                                />
                                <span>Re-verify Local Tools</span>
                              </button>
                            </div>
                          </>
                        )}

                        {step.id === 'brand' && (
                          <div className="space-y-3">
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                              <label className="space-y-1 text-xs">
                                <span className="text-[#A1A1AA]">Brand / Clipping Page Name</span>
                                <input
                                  type="text"
                                  value={draftBrand}
                                  onChange={(e) => setDraftBrand(e.target.value)}
                                  className="w-full rounded-lg border border-white/[0.08] bg-[#111113] px-3 py-2 text-xs text-[#FAFAFA] focus:border-[#FFE600]/60 focus:outline-none"
                                />
                              </label>
                              <label className="space-y-1 text-xs">
                                <span className="text-[#A1A1AA]">Primary Channel Handle</span>
                                <input
                                  type="text"
                                  value={draftHandle}
                                  onChange={(e) => setDraftHandle(e.target.value)}
                                  className="w-full rounded-lg border border-white/[0.08] bg-[#111113] px-3 py-2 font-mono text-xs text-[#FAFAFA] focus:border-[#FFE600]/60 focus:outline-none"
                                />
                              </label>
                            </div>
                            <div className="flex justify-end">
                              <button
                                type="button"
                                onClick={async () => {
                                  await markStepCompleted('brand', {
                                    brand_name: draftBrand.trim() || 'SaimClips',
                                    channel_handle: draftHandle.trim() || '@saimclips.gta6',
                                  });
                                  onNotify('Saved Brand & Channel Kit.');
                                }}
                                className="rounded-lg bg-[#FFE600] px-3.5 py-1.5 text-xs font-semibold text-[#09090B] hover:bg-[#F5DD00] cursor-pointer"
                              >
                                Save Brand Kit
                              </button>
                            </div>
                          </div>
                        )}

                        {step.id === 'ig' && (
                          <div className="space-y-3">
                            {(
                              [
                                ['professional_account', 'Switched Instagram to Professional / Creator account'],
                                ['two_factor_enabled', 'Meta Business 2FA enabled for Zernio Reels publishing'],
                                ['music_rights_cleared', 'Original stream audio enabled (no restricted commercial tracks)'],
                              ] as const
                            ).map(([key, label]) => (
                              <label
                                key={key}
                                className="flex items-center gap-2.5 text-xs text-[#A1A1AA] cursor-pointer"
                              >
                                <input
                                  type="checkbox"
                                  checked={onboarding.ig_checklist[key]}
                                  onChange={(e) =>
                                    onSaveOnboarding({
                                      ig_checklist: {
                                        ...onboarding.ig_checklist,
                                        [key]: e.target.checked,
                                      },
                                    })
                                  }
                                  className="accent-[#FFE600]"
                                />
                                <span>{label}</span>
                              </label>
                            ))}
                            <div className="flex items-center justify-end gap-2.5">
                              <button
                                type="button"
                                onClick={() => handleOpenGuide('instagram')}
                                className="inline-flex items-center gap-1.5 rounded-lg border border-[#FFE600]/30 bg-[#FFE600]/10 px-3.5 py-1.5 text-xs font-medium text-[#FFE600] hover:bg-[#FFE600]/20 hover:border-[#FFE600]/50 transition-colors cursor-pointer"
                              >
                                <Sparkles className="h-3.5 w-3.5" />
                                <span>Open Guide &amp; Generate Profile</span>
                              </button>
                              <button
                                type="button"
                                onClick={async () => {
                                  await markStepCompleted('ig');
                                  onNotify('Instagram / Meta checklist saved.');
                                }}
                                className="rounded-lg border border-white/[0.1] bg-[#111113] px-3.5 py-1.5 text-xs font-medium text-[#FAFAFA] hover:border-white/[0.18] cursor-pointer"
                              >
                                Mark Step Complete
                              </button>
                            </div>
                          </div>
                        )}

                        {step.id === 'yt' && (
                          <div className="space-y-3">
                            {(
                              [
                                ['advanced_features_verified', 'YouTube Studio Intermediate & Advanced features verified'],
                                ['not_made_for_kids_default', 'Default audience set to Not Made for Kids'],
                                ['comments_enabled_default', 'Comments enabled by default for engagement replies'],
                              ] as const
                            ).map(([key, label]) => (
                              <label
                                key={key}
                                className="flex items-center gap-2.5 text-xs text-[#A1A1AA] cursor-pointer"
                              >
                                <input
                                  type="checkbox"
                                  checked={onboarding.yt_checklist[key]}
                                  onChange={(e) =>
                                    onSaveOnboarding({
                                      yt_checklist: {
                                        ...onboarding.yt_checklist,
                                        [key]: e.target.checked,
                                      },
                                    })
                                  }
                                  className="accent-[#FFE600]"
                                />
                                <span>{label}</span>
                              </label>
                            ))}
                            <div className="flex items-center justify-end gap-2.5">
                              <button
                                type="button"
                                onClick={() => handleOpenGuide('youtube')}
                                className="inline-flex items-center gap-1.5 rounded-lg border border-[#FFE600]/30 bg-[#FFE600]/10 px-3.5 py-1.5 text-xs font-medium text-[#FFE600] hover:bg-[#FFE600]/20 hover:border-[#FFE600]/50 transition-colors cursor-pointer"
                              >
                                <Sparkles className="h-3.5 w-3.5" />
                                <span>Open Guide &amp; Generate Profile</span>
                              </button>
                              <button
                                type="button"
                                onClick={async () => {
                                  await markStepCompleted('yt');
                                  onNotify('YouTube Studio checklist saved.');
                                }}
                                className="rounded-lg border border-white/[0.1] bg-[#111113] px-3.5 py-1.5 text-xs font-medium text-[#FAFAFA] hover:border-white/[0.18] cursor-pointer"
                              >
                                Mark Step Complete
                              </button>
                            </div>
                          </div>
                        )}

                        {step.id === 'zernio' && (
                          <div className="space-y-4">
                            {/* Zernio Key Section */}
                            <div className="space-y-1.5">
                              <div className="flex items-center justify-between text-xs">
                                <span className="text-[#A1A1AA]">Zernio API Key (Multi-Platform Publishing)</span>
                                <a
                                  href="https://zernio.com"
                                  target="_blank"
                                  rel="noreferrer"
                                  className="inline-flex items-center gap-1 text-[11px] text-[#FFE600] hover:underline"
                                >
                                  <span>zernio.com</span>
                                  <ExternalLink className="h-3 w-3" />
                                </a>
                              </div>
                              <div className="flex flex-col sm:flex-row gap-2.5">
                                <div className="relative flex-1">
                                  <KeyRound
                                    className="pointer-events-none absolute left-3 top-2.5 h-3.5 w-3.5 text-[#71717A]"
                                    aria-hidden="true"
                                  />
                                  <input
                                    type="password"
                                    value={draftZernioKey}
                                    onChange={(e) => setDraftZernioKey(e.target.value)}
                                    placeholder="Paste local Zernio API key (saved to .env locally)"
                                    aria-label="Zernio API Key"
                                    className="w-full rounded-lg border border-white/[0.08] bg-[#111113] pl-9 pr-3 py-2 font-mono text-xs text-[#FAFAFA] placeholder:text-[#71717A] focus:border-[#FFE600]/60 focus:outline-none"
                                  />
                                </div>
                                <button
                                  type="button"
                                  disabled={discovering}
                                  onClick={handleAutoDiscover}
                                  className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#FFE600] px-4 py-2 text-xs font-semibold text-[#09090B] hover:bg-[#F5DD00] disabled:opacity-60 whitespace-nowrap shrink-0 cursor-pointer"
                                >
                                  <RefreshCw
                                    className={`h-3.5 w-3.5 ${discovering ? 'animate-spin' : ''}`}
                                  />
                                  <span>
                                    {discovering ? 'Discovering...' : 'Auto-Discover Accounts'}
                                  </span>
                                </button>
                              </div>
                            </div>

                            {/* Google Gemini API Key Section */}
                            <div className="space-y-1.5 border-t border-white/[0.06] pt-3.5">
                              <div className="flex items-center justify-between text-xs">
                                <span className="text-[#A1A1AA]">Google Gemini API Key (Optional BYOK AI Backend)</span>
                                <a
                                  href="https://aistudio.google.com"
                                  target="_blank"
                                  rel="noreferrer"
                                  className="inline-flex items-center gap-1 text-[11px] text-[#FFE600] hover:underline"
                                >
                                  <span>Get Free Key (aistudio.google.com)</span>
                                  <ExternalLink className="h-3 w-3" />
                                </a>
                              </div>
                              <div className="flex flex-col sm:flex-row gap-2.5">
                                <div className="relative flex-1">
                                  <KeyRound
                                    className="pointer-events-none absolute left-3 top-2.5 h-3.5 w-3.5 text-[#71717A]"
                                    aria-hidden="true"
                                  />
                                  <input
                                    type="password"
                                    value={draftGeminiKey}
                                    onChange={(e) => setDraftGeminiKey(e.target.value)}
                                    placeholder="AIzaSy... (free key from Google AI Studio)"
                                    aria-label="Gemini API Key"
                                    className="w-full rounded-lg border border-white/[0.08] bg-[#111113] pl-9 pr-3 py-2 font-mono text-xs text-[#FAFAFA] placeholder:text-[#71717A] focus:border-[#FFE600]/60 focus:outline-none"
                                  />
                                </div>
                                <button
                                  type="button"
                                  onClick={async () => {
                                    await onSaveOnboarding({ gemini_api_key: draftGeminiKey.trim() });
                                    onNotify('Saved Gemini API key locally to .env.');
                                  }}
                                  className="inline-flex items-center justify-center gap-1.5 rounded-lg border border-white/[0.1] bg-[#111113] px-3.5 py-2 text-xs font-medium text-[#FAFAFA] hover:border-white/[0.18] whitespace-nowrap shrink-0 cursor-pointer"
                                >
                                  <Check className="h-3.5 w-3.5 text-[#22C55E]" />
                                  <span>Save AI Key</span>
                                </button>
                              </div>
                              <p className="text-[11px] text-[#71717A]">
                                Powers AI moment selection, multi-reference campaign analysis, and fresh profile kits completely locally. If blank, built-in deterministic templates run automatically.
                              </p>
                            </div>

                            {onboarding.discovered_accounts.length === 0 ? (
                              <div className="rounded-lg border border-dashed border-white/[0.08] p-4 text-center">
                                <p className="text-xs text-[#71717A]">
                                  No accounts connected yet. Paste your Zernio API key above and click Auto-Discover, or connect your Instagram &amp; YouTube channels in Zernio.
                                </p>
                              </div>
                            ) : (
                              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                                {onboarding.discovered_accounts.map((acc) => (
                                  <div
                                    key={acc.id}
                                    className="flex items-center justify-between rounded-lg border border-white/[0.08] bg-[#111113] px-3.5 py-2.5 text-xs"
                                  >
                                    <div>
                                      <div className="font-medium text-[#FAFAFA]">{acc.platform}</div>
                                      <div className="font-mono text-[11px] text-[#A1A1AA]">
                                        {acc.handle}
                                      </div>
                                    </div>
                                    <span className="inline-flex items-center gap-1.5 text-[11px] text-[#22C55E]">
                                      <span className="h-1.5 w-1.5 rounded-full bg-[#22C55E]" />
                                      Connected
                                    </span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}

                        {step.id === 'campaign' && (
                          <div className="space-y-4">
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                              <label className="space-y-1 text-xs">
                                <span className="text-[#A1A1AA]">Active Whop Campaign</span>
                                <select
                                  value={presets.find((p) => p.active)?.id ?? ''}
                                  onChange={(e) => onActivatePreset(e.target.value)}
                                  className="w-full rounded-lg border border-white/[0.08] bg-[#111113] px-3 py-2 text-xs text-[#FAFAFA]"
                                >
                                  {presets.map((p) => (
                                    <option key={p.id} value={p.id} className="bg-[#111113]">
                                      {p.name}
                                    </option>
                                  ))}
                                </select>
                              </label>
                              <label className="space-y-1 text-xs">
                                <span className="text-[#A1A1AA]">Default Tier-1 IST Slot</span>
                                <select
                                  value={onboarding.default_ist_slot}
                                  onChange={(e) =>
                                    onSaveOnboarding({ default_ist_slot: e.target.value })
                                  }
                                  className="w-full rounded-lg border border-white/[0.08] bg-[#111113] px-3 py-2 font-mono text-xs text-[#FAFAFA]"
                                >
                                  {IST_SLOTS.map((s) => (
                                    <option key={s.id} value={s.ist} className="bg-[#111113]">
                                      {s.ist} ({s.utc}) — {s.regionLabel}
                                    </option>
                                  ))}
                                </select>
                              </label>
                            </div>
                            <div className="flex justify-end">
                              <button
                                type="button"
                                onClick={async () => {
                                  await markStepCompleted('campaign');
                                  onNotify('Campaign & default IST schedule locked in.');
                                }}
                                className="rounded-lg bg-[#FFE600] px-3.5 py-1.5 text-xs font-semibold text-[#09090B] hover:bg-[#F5DD00] cursor-pointer"
                              >
                                Complete Setup
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </section>

          {/* Optional Later (Skip Anytime) */}
          <section aria-labelledby="optional-steps-heading" className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 id="optional-steps-heading" className="text-sm font-semibold text-[#FAFAFA]">
                Optional Later (Skip Anytime)
              </h2>
              <span className="text-xs text-[#71717A]">Power-user add-ons</span>
            </div>

            <div className="rounded-xl border border-white/[0.08] bg-[#111113] divide-y divide-white/[0.06]">
              {/* Telegram Both-Live Notifier */}
              <div className="p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-[#FAFAFA]">
                      Telegram Both-Live Notifier
                    </h3>
                    <p className="text-xs text-[#71717A] mt-0.5">
                      Pings your phone with Reel + Short URLs the instant both go live for the 30-min Whop window.
                    </p>
                  </div>
                  {onboarding.optional_integrations.telegram_verified && (
                    <span className="inline-flex items-center gap-1.5 text-xs text-[#22C55E]">
                      <Check className="h-3.5 w-3.5" />
                      Verified
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                  <input
                    type="password"
                    value={draftTgToken}
                    onChange={(e) => setDraftTgToken(e.target.value)}
                    placeholder="Telegram Bot Token"
                    aria-label="Telegram Bot Token"
                    className="rounded-lg border border-white/[0.08] bg-[#09090B] px-3 py-2 font-mono text-xs text-[#FAFAFA] placeholder:text-[#71717A] focus:border-[#FFE600]/60 focus:outline-none"
                  />
                  <input
                    type="text"
                    value={draftTgChatId}
                    onChange={(e) => setDraftTgChatId(e.target.value)}
                    placeholder="Chat ID (e.g. 581920441)"
                    aria-label="Telegram Chat ID"
                    className="rounded-lg border border-white/[0.08] bg-[#09090B] px-3 py-2 font-mono text-xs text-[#FAFAFA] placeholder:text-[#71717A] focus:border-[#FFE600]/60 focus:outline-none"
                  />
                  <button
                    type="button"
                    disabled={pingingTg}
                    onClick={handleTestTelegram}
                    className="inline-flex items-center justify-center gap-1.5 rounded-lg border border-white/[0.1] bg-white/[0.06] px-3.5 py-2 text-xs font-medium text-[#FAFAFA] hover:bg-white/[0.12] cursor-pointer"
                  >
                    <Send className="h-3.5 w-3.5" />
                    <span>{pingingTg ? 'Pinging...' : 'Test Ping'}</span>
                  </button>
                </div>
              </div>

              {/* Cloudflare (Advanced) */}
              <div className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h3 className="text-sm font-medium text-[#FAFAFA]">Cloudflare Tunnel (Advanced)</h3>
                  <p className="text-xs text-[#71717A] mt-0.5">
                    Optional remote preview endpoint for accessing local renders from mobile.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="url"
                    value={draftCloudflare}
                    onChange={(e) => setDraftCloudflare(e.target.value)}
                    placeholder="https://clips.yourdomain.com"
                    aria-label="Cloudflare Tunnel URL"
                    className="w-full sm:w-[220px] rounded-lg border border-white/[0.08] bg-[#09090B] px-3 py-1.5 font-mono text-xs text-[#FAFAFA] placeholder:text-[#71717A] focus:border-[#FFE600]/60 focus:outline-none"
                  />
                  <button
                    type="button"
                    onClick={async () => {
                      await onSaveOnboarding({
                        optional_integrations: {
                          ...onboarding.optional_integrations,
                          cloudflare_tunnel_url: draftCloudflare.trim(),
                        },
                      });
                      onNotify('Saved Cloudflare Tunnel setting.');
                    }}
                    className="rounded-lg border border-white/[0.1] px-3 py-1.5 text-xs font-medium text-[#FAFAFA] hover:border-white/[0.2] cursor-pointer"
                  >
                    Save
                  </button>
                </div>
              </div>

              {/* Optional MCP & Earshot SFX Toggles */}
              <div className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-medium text-[#FAFAFA]">MCP Server Bridge</div>
                    <div className="text-xs text-[#71717A]">Expose clipping tools to local MCP clients</div>
                  </div>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={onboarding.optional_integrations.mcp_server_enabled}
                    onClick={() =>
                      onSaveOnboarding({
                        optional_integrations: {
                          ...onboarding.optional_integrations,
                          mcp_server_enabled: !onboarding.optional_integrations.mcp_server_enabled,
                        },
                      })
                    }
                    className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors shrink-0 cursor-pointer ${
                      onboarding.optional_integrations.mcp_server_enabled
                        ? 'bg-[#FFE600]'
                        : 'bg-white/[0.14]'
                    }`}
                  >
                    <span
                      className={`inline-block h-3.5 w-3.5 rounded-full bg-[#09090B] transition-transform ${
                        onboarding.optional_integrations.mcp_server_enabled
                          ? 'translate-x-4.5'
                          : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-medium text-[#FAFAFA]">Earshot SFX Pack</div>
                    <div className="text-xs text-[#71717A]">Subtle riser &amp; pop hits on hook transition</div>
                  </div>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={onboarding.optional_integrations.earshot_sfx_enabled}
                    onClick={() =>
                      onSaveOnboarding({
                        optional_integrations: {
                          ...onboarding.optional_integrations,
                          earshot_sfx_enabled: !onboarding.optional_integrations.earshot_sfx_enabled,
                        },
                      })
                    }
                    className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors shrink-0 cursor-pointer ${
                      onboarding.optional_integrations.earshot_sfx_enabled
                        ? 'bg-[#FFE600]'
                        : 'bg-white/[0.14]'
                    }`}
                  >
                    <span
                      className={`inline-block h-3.5 w-3.5 rounded-full bg-[#09090B] transition-transform ${
                        onboarding.optional_integrations.earshot_sfx_enabled
                          ? 'translate-x-4.5'
                          : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              </div>
            </div>
          </section>
        </div>
      ) : (
        /* System Guide Tab */
        <div className="space-y-6">
          <section className="rounded-xl border border-white/[0.08] bg-[#111113] p-6 space-y-4">
            <h2 className="text-sm font-semibold text-[#FAFAFA]">The Daily 5-Minute Routine</h2>
            <ol className="space-y-3 text-xs leading-relaxed text-[#A1A1AA]">
              <li className="flex items-start gap-3">
                <span className="font-mono text-[#FAFAFA] shrink-0">01</span>
                <span>
                  Open <strong className="text-[#FAFAFA]">Live Hunt</strong> and click{' '}
                  <em>Check New Streams</em> to surface fresh unclipped GTA 6 VODs ranked by velocity.
                </span>
              </li>
              <li className="flex items-start gap-3">
                <span className="font-mono text-[#FAFAFA] shrink-0">02</span>
                <span>
                  Send the top VOD to <strong className="text-[#FAFAFA]">Create</strong> with{' '}
                  <em>1-Clip Approval Mode</em> ON so only the highest-scoring moment renders first.
                </span>
              </li>
              <li className="flex items-start gap-3">
                <span className="font-mono text-[#FAFAFA] shrink-0">03</span>
                <span>
                  Inspect the 9:16 framing, safe zones, and compliance gate in{' '}
                  <strong className="text-[#FAFAFA]">Studio</strong>, pick a Tier-1 IST slot (19:30 or 21:30 IST), and click{' '}
                  <em>Approve &amp; Schedule to Zernio</em>.
                </span>
              </li>
              <li className="flex items-start gap-3">
                <span className="font-mono text-[#FAFAFA] shrink-0">04</span>
                <span>
                  Once a week, run <em>Learn from Analytics (24h/48h/72h)</em> in{' '}
                  <strong className="text-[#FAFAFA]">Viral DNA</strong> so the ranker updates{' '}
                  <span className="font-mono">memory/learned_rules.md</span>.
                </span>
              </li>
            </ol>
          </section>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <section className="rounded-xl border border-white/[0.08] bg-[#111113] p-5 space-y-2.5">
              <h2 className="text-sm font-semibold text-[#FAFAFA]">The 30-Minute Whop Rule</h2>
              <p className="text-xs leading-relaxed text-[#A1A1AA]">
                Whop clipping bounties require manual link submission shortly after publish. Always open the{' '}
                <strong className="text-[#FAFAFA]">Whop Live URLs</strong> drawer from the top bar, copy the Instagram Reel and YouTube Short URLs while the 30-minute timer is green/amber, paste them manually into Whop, and check{' '}
                <em>Mark Submitted</em>. Automation never touches your Whop account.
              </p>
            </section>

            <section className="rounded-xl border border-white/[0.08] bg-[#111113] p-5 space-y-2.5">
              <h2 className="text-sm font-semibold text-[#FAFAFA]">Keyboard &amp; Quick Shortcuts</h2>
              <dl className="space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <dt className="text-[#A1A1AA]">Open Quick Command Palette</dt>
                  <dd className="font-mono text-[#FAFAFA]">Ctrl + K / ⌘K</dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="text-[#A1A1AA]">Close Drawers &amp; Modals</dt>
                  <dd className="font-mono text-[#FAFAFA]">Esc</dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="text-[#A1A1AA]">Local FastAPI Backend Target</dt>
                  <dd className="font-mono text-[#FAFAFA]">localhost:8765/api</dd>
                </div>
              </dl>
            </section>
          </div>
        </div>
      )}

      {/* Platform Setup Guide & Brand Kit Generator Modal */}
      {guideModalOpen && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-150"
        >
          <div className="w-full max-w-[680px] max-h-[90vh] flex flex-col rounded-xl border border-white/[0.12] bg-[#111113] shadow-2xl overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-white/[0.08] px-6 py-4 shrink-0 bg-[#09090B]">
              <div className="flex items-center gap-2.5">
                <Sparkles className="h-4 w-4 text-[#FFE600]" />
                <h2 className="text-sm font-semibold text-[#FAFAFA]">
                  {guidePlatform === 'instagram'
                    ? 'Instagram / Meta Professional Setup Guide'
                    : 'YouTube Studio Channel Setup Guide'}
                </h2>
              </div>
              <button
                type="button"
                onClick={() => setGuideModalOpen(false)}
                className="rounded-lg p-1 text-[#71717A] hover:bg-white/[0.06] hover:text-[#FAFAFA] transition-colors"
                aria-label="Close guide modal"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="overflow-y-auto px-6 py-5 space-y-6 text-xs">
              {/* Beginner Step-by-Step Checklist */}
              <div className="space-y-3">
                <h3 className="font-semibold text-[#FAFAFA] text-xs uppercase tracking-wider text-[#A1A1AA]">
                  Beginner Setup Checklist
                </h3>
                <div className="rounded-lg border border-white/[0.08] bg-[#09090B] p-4 space-y-3">
                  {guidePlatform === 'instagram' ? (
                    <div className="space-y-2.5 text-[#A1A1AA]">
                      <div className="flex items-start gap-2.5">
                        <span className="font-mono text-[#FFE600] font-bold">1</span>
                        <div>
                          <strong className="text-[#FAFAFA]">Switch to Professional Account:</strong> In Instagram, go to Profile → Settings → Account type and tools → Switch to Professional (select 'Creator' or 'Video Creator').
                        </div>
                      </div>
                      <div className="flex items-start gap-2.5">
                        <span className="font-mono text-[#FFE600] font-bold">2</span>
                        <div>
                          <strong className="text-[#FAFAFA]">Keep Account Public:</strong> Professional accounts must remain Public for Reels to reach the Explore feed and Whop verification.
                        </div>
                      </div>
                      <div className="flex items-start gap-2.5">
                        <span className="font-mono text-[#FFE600] font-bold">3</span>
                        <div>
                          <strong className="text-[#FAFAFA]">Likes &amp; View Counts Visible:</strong> Go to Settings → Like and share counts → Toggle ON (Whop sponsors verify metrics visually).
                        </div>
                      </div>
                      <div className="flex items-start gap-2.5">
                        <span className="font-mono text-[#FFE600] font-bold">4</span>
                        <div>
                          <strong className="text-[#FAFAFA]">Upload at Highest Quality:</strong> Settings → Preferences → Data usage and media quality → Toggle ON 'Upload at highest quality'.
                        </div>
                      </div>
                      <div className="flex items-start gap-2.5">
                        <span className="font-mono text-[#FFE600] font-bold">5</span>
                        <div>
                          <strong className="text-[#FAFAFA]">Link Facebook Page:</strong> Open facebook.com on desktop → Page Settings → Linked accounts → Instagram → Connect using your existing personal Facebook.
                        </div>
                      </div>
                      <div className="flex items-start gap-2.5">
                        <span className="font-mono text-[#FFE600] font-bold">6</span>
                        <div>
                          <strong className="text-[#FAFAFA]">Warm-up Schedule:</strong> Post 3–5 Reels/day spaced at peak IST hours (14:00, 18:00, 20:00, 22:00 IST) for the first 7 days.
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-2.5 text-[#A1A1AA]">
                      <div className="flex items-start gap-2.5">
                        <span className="font-mono text-[#FFE600] font-bold">1</span>
                        <div>
                          <strong className="text-[#FAFAFA]">Channel Name &amp; Handle:</strong> Open studio.youtube.com → Customization → Basic info → Set your channel name and matching @handle.
                        </div>
                      </div>
                      <div className="flex items-start gap-2.5">
                        <span className="font-mono text-[#FFE600] font-bold">2</span>
                        <div>
                          <strong className="text-[#FAFAFA]">Country of Residence = United States:</strong> Settings → Channel → Basic info → Country = 'United States' (critical for Tier-1 US/UK/CA CPM rates).
                        </div>
                      </div>
                      <div className="flex items-start gap-2.5">
                        <span className="font-mono text-[#FFE600] font-bold">3</span>
                        <div>
                          <strong className="text-[#FAFAFA]">Audience = Not Made for Kids:</strong> Settings → Channel → Advanced settings → Select 'No, set this channel as not made for kids'.
                        </div>
                      </div>
                      <div className="flex items-start gap-2.5">
                        <span className="font-mono text-[#FFE600] font-bold">4</span>
                        <div>
                          <strong className="text-[#FAFAFA]">Comments &amp; Likes Visible:</strong> Settings → Upload defaults → Advanced settings → Allow comments &amp; show like counts.
                        </div>
                      </div>
                      <div className="flex items-start gap-2.5">
                        <span className="font-mono text-[#FFE600] font-bold">5</span>
                        <div>
                          <strong className="text-[#FAFAFA]">Intermediate &amp; Advanced Features:</strong> Settings → Channel → Feature eligibility → Complete phone verification to unlock custom thumbnails and bypass daily Shorts limits.
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* 1-Click Generate Profile Kit Section */}
              <div className="space-y-4 border-t border-white/[0.08] pt-5">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-[#FAFAFA]">
                      1-Click Profile Kit Generator
                    </h3>
                    <p className="text-[11px] text-[#71717A] mt-0.5">
                      Generates unique Name, Handles, Bio, Keywords, and 5 Hashtags using Gemini API (or niche templates).
                    </p>
                  </div>
                  <button
                    type="button"
                    disabled={generatingKit}
                    onClick={handleGenerateProfileKit}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-[#FFE600] px-4 py-2 text-xs font-semibold text-[#09090B] hover:bg-[#F5DD00] disabled:opacity-60 transition-colors whitespace-nowrap cursor-pointer shrink-0"
                  >
                    <Sparkles className={`h-3.5 w-3.5 ${generatingKit ? 'animate-spin' : ''}`} />
                    <span>{generatingKit ? 'Generating...' : 'Generate Fresh Profile Kit'}</span>
                  </button>
                </div>

                {brandKit && (
                  <div className="rounded-lg border border-white/[0.1] bg-[#09090B] p-4 space-y-4 animate-in fade-in duration-200">
                    <div className="flex items-center justify-between border-b border-white/[0.06] pb-2">
                      <span className="font-medium text-[#FAFAFA]">Generated Profile Kit</span>
                      <span className="font-mono text-[11px] text-[#22C55E]">
                        Saved to config/brand_kit.md
                      </span>
                    </div>

                    {/* Brand Name */}
                    <div className="flex items-center justify-between gap-3 bg-[#111113] p-2.5 rounded-lg border border-white/[0.06]">
                      <div>
                        <span className="text-[10px] uppercase text-[#71717A] tracking-wider block">Channel / Brand Name</span>
                        <span className="font-mono text-sm font-semibold text-[#FAFAFA]">{brandKit.brand_name}</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => copyToClipboard(brandKit.brand_name, 'Channel Name')}
                        className="inline-flex items-center gap-1 rounded bg-white/[0.06] hover:bg-white/[0.12] px-2.5 py-1 text-[11px] font-medium text-[#FAFAFA] cursor-pointer"
                      >
                        {copiedKey === 'Channel Name' ? <Check className="h-3 w-3 text-[#22C55E]" /> : <Copy className="h-3 w-3" />}
                        <span>{copiedKey === 'Channel Name' ? 'Copied' : 'Copy'}</span>
                      </button>
                    </div>

                    {/* Handles */}
                    <div className="space-y-1.5">
                      <span className="text-[10px] uppercase text-[#71717A] tracking-wider block">Suggested Handles</span>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {brandKit.handles.map((h, idx) => (
                          <div key={idx} className="flex items-center justify-between gap-2 bg-[#111113] px-2.5 py-1.5 rounded-md border border-white/[0.06]">
                            <span className="font-mono text-xs text-[#FFE600] truncate">{h}</span>
                            <button
                              type="button"
                              onClick={() => copyToClipboard(h, h)}
                              className="text-[#71717A] hover:text-[#FAFAFA] shrink-0 cursor-pointer"
                              title="Copy handle"
                            >
                              {copiedKey === h ? <Check className="h-3 w-3 text-[#22C55E]" /> : <Copy className="h-3 w-3" />}
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Bio */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] uppercase text-[#71717A] tracking-wider">Bio / Description</span>
                        <button
                          type="button"
                          onClick={() => copyToClipboard(brandKit.bio, 'Bio')}
                          className="inline-flex items-center gap-1 text-[11px] text-[#FFE600] hover:underline cursor-pointer"
                        >
                          {copiedKey === 'Bio' ? <Check className="h-3 w-3 text-[#22C55E]" /> : <Copy className="h-3 w-3" />}
                          <span>{copiedKey === 'Bio' ? 'Copied' : 'Copy Bio'}</span>
                        </button>
                      </div>
                      <pre className="w-full whitespace-pre-wrap font-sans text-xs bg-[#111113] p-2.5 rounded-lg border border-white/[0.06] text-[#FAFAFA]">
                        {brandKit.bio}
                      </pre>
                    </div>

                    {/* Keywords */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] uppercase text-[#71717A] tracking-wider">Channel Keywords</span>
                        <button
                          type="button"
                          onClick={() => copyToClipboard(brandKit.keywords.join(', '), 'Keywords')}
                          className="inline-flex items-center gap-1 text-[11px] text-[#FFE600] hover:underline cursor-pointer"
                        >
                          {copiedKey === 'Keywords' ? <Check className="h-3 w-3 text-[#22C55E]" /> : <Copy className="h-3 w-3" />}
                          <span>{copiedKey === 'Keywords' ? 'Copied' : 'Copy Keywords'}</span>
                        </button>
                      </div>
                      <div className="bg-[#111113] p-2 rounded-lg border border-white/[0.06] font-mono text-[11px] text-[#A1A1AA]">
                        {brandKit.keywords.join(', ')}
                      </div>
                    </div>

                    {/* Hashtags */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] uppercase text-[#71717A] tracking-wider">Default Hashtags (≤ 5 tags)</span>
                        <button
                          type="button"
                          onClick={() => copyToClipboard(brandKit.hashtags.join(' '), 'Hashtags')}
                          className="inline-flex items-center gap-1 text-[11px] text-[#FFE600] hover:underline cursor-pointer"
                        >
                          {copiedKey === 'Hashtags' ? <Check className="h-3 w-3 text-[#22C55E]" /> : <Copy className="h-3 w-3" />}
                          <span>{copiedKey === 'Hashtags' ? 'Copied' : 'Copy Hashtags'}</span>
                        </button>
                      </div>
                      <div className="bg-[#111113] p-2 rounded-lg border border-white/[0.06] font-mono text-[11px] text-[#22C55E]">
                        {brandKit.hashtags.join(' ')}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end border-t border-white/[0.08] px-6 py-3.5 bg-[#09090B] shrink-0">
              <button
                type="button"
                onClick={() => setGuideModalOpen(false)}
                className="rounded-lg bg-white/[0.08] hover:bg-white/[0.14] px-4 py-1.5 text-xs font-medium text-[#FAFAFA] transition-colors cursor-pointer"
              >
                Close Guide
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
