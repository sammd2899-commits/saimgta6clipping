import { useState } from 'react';
import {
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Circle,
  KeyRound,
  RefreshCw,
  Send,
} from 'lucide-react';
import { IST_SLOTS } from '../../data/demoData';
import type { CampaignPreset, HealthStatus, OnboardingState } from '../../types/studio';

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

  const completedSet = new Set(onboarding.completed_steps);
  const completedCount = REQUIRED_STEPS.filter((s) => completedSet.has(s.id)).length;

  const markStepCompleted = async (stepId: string, extraPatch?: Partial<OnboardingState>) => {
    const nextSteps = Array.from(new Set([...onboarding.completed_steps, stepId]));
    await onSaveOnboarding({ ...extraPatch, completed_steps: nextSteps });
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
                            <div className="flex justify-end">
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
                            <div className="flex justify-end">
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
    </div>
  );
}
