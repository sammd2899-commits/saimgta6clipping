import { useMemo, useState } from 'react';
import { Check, Plus, ShieldCheck, Upload, X } from 'lucide-react';
import type { CampaignPreset } from '../../types/studio';
import { parseWhopBrief } from '../../utils/clipLogic';

interface PresetsViewProps {
  presets: CampaignPreset[];
  onActivatePreset: (presetId: string) => Promise<void>;
  onCreatePreset: (preset: Omit<CampaignPreset, 'id' | 'active'>) => Promise<void>;
}

const SAMPLE_BRIEF_PLACEHOLDER = `Paste raw Whop campaign brief here, e.g.:
GTA 6 Vice City Clipping Bounty
Must include #gta6 #Clipup #ViceCity. Max 5 IG tags.
Keep clips live for 30 days retention. Payout unlocks at 3k views ($2.00 / 1K).
Target countries: US, UK, Canada, Australia.`;

export function PresetsView({
  presets,
  onActivatePreset,
  onCreatePreset,
}: PresetsViewProps) {
  const [modalOpen, setModalOpen] = useState(false);
  const [rawBrief, setRawBrief] = useState('');
  const [whopHandle, setWhopHandle] = useState('');
  const [logoDataUrl, setLogoDataUrl] = useState<string | undefined>(undefined);
  const [logoFileName, setLogoFileName] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const parsed = useMemo(() => {
    if (!rawBrief.trim()) return null;
    return parseWhopBrief(rawBrief);
  }, [rawBrief]);

  const handleLogoFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLogoFileName(file.name);
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        setLogoDataUrl(reader.result);
      }
    };
    reader.readAsDataURL(file);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rawBrief.trim() || !parsed) {
      setFormError('Paste a Whop campaign brief to auto-parse compliance rules before saving.');
      return;
    }
    setFormError(null);
    setSaving(true);
    try {
      const label = parsed.name
        .split(/\s+/)
        .slice(0, 2)
        .map((w) => w.slice(0, 3))
        .join('')
        .toUpperCase();

      await onCreatePreset({
        name: parsed.name,
        whop_handle:
          whopHandle.trim() ||
          `whop.com/${parsed.name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`,
        required_hashtags: parsed.required_hashtags,
        max_ig_hashtags: parsed.max_ig_hashtags,
        retention_days: parsed.retention_days,
        target_countries: parsed.target_countries,
        min_views_unlock: parsed.min_views_unlock,
        cpm_rate: parsed.cpm_rate,
        logo_label: label || 'WHOP',
        logo_accent: '#FFE600',
        logo_data_url: logoDataUrl,
        raw_brief: rawBrief.trim(),
      });
      setRawBrief('');
      setWhopHandle('');
      setLogoDataUrl(undefined);
      setLogoFileName(null);
      setModalOpen(false);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto w-full max-w-[1040px] px-4 sm:px-8 py-8 space-y-8">
      {/* Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-[#FAFAFA]">
            Campaign Presets
          </h1>
          <p className="text-xs text-[#A1A1AA] mt-1">
            Whop compliance profiles stored in <span className="font-mono">config/presets/</span>.
          </p>
        </div>

        <button
          type="button"
          onClick={() => setModalOpen(true)}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#FFE600] px-4 py-2 text-xs font-semibold text-[#09090B] hover:bg-[#F5DD00] transition-colors whitespace-nowrap shrink-0 cursor-pointer"
        >
          <Plus className="h-3.5 w-3.5" />
          <span>New Campaign Preset</span>
        </button>
      </div>

      {/* 2-Column Grid of Saved Preset Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {presets.length === 0 ? (
          <div className="col-span-full rounded-xl border border-dashed border-white/[0.08] bg-[#111113]/50 p-12 text-center space-y-1.5">
            <p className="text-sm font-medium text-[#FAFAFA]">No presets saved yet</p>
            <p className="text-xs text-[#71717A] max-w-[420px] mx-auto">
              Click &quot;New Campaign Preset&quot; above to add your Whop campaign rules, sponsor logo, and required hashtags.
            </p>
          </div>
        ) : (
          presets.map((preset) => (
          <article
            key={preset.id}
            data-testid={`preset-card-${preset.id}`}
            className={`flex flex-col justify-between rounded-xl border p-5 transition-colors ${
              preset.active
                ? 'border-white/[0.16] bg-[#111113]'
                : 'border-white/[0.08] bg-[#111113] hover:border-white/[0.14]'
            }`}
          >
            <div className="space-y-4">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3 min-w-0">
                  {/* Campaign Logo Thumbnail */}
                  <div className="flex h-11 w-11 items-center justify-center rounded-lg border border-white/[0.08] bg-[#09090B] shrink-0 overflow-hidden">
                    {preset.logo_data_url ? (
                      <img
                        src={preset.logo_data_url}
                        alt={`${preset.name} logo`}
                        className="h-8 w-8 object-contain"
                      />
                    ) : (
                      <span className="font-mono text-[10px] font-bold tracking-wider text-[#FAFAFA]">
                        {preset.logo_label}
                      </span>
                    )}
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <h2 className="text-sm font-semibold text-[#FAFAFA] truncate">
                        {preset.name}
                      </h2>
                      {preset.active && (
                        <span className="inline-flex items-center gap-1.5 text-[11px] font-medium text-[#22C55E] shrink-0">
                          <span className="h-1.5 w-1.5 rounded-full bg-[#22C55E]" />
                          Active
                        </span>
                      )}
                    </div>
                    <p className="font-mono text-[11px] text-[#71717A] truncate mt-0.5">
                      {preset.whop_handle}
                    </p>
                  </div>
                </div>

                <span className="font-mono text-xs text-[#FAFAFA] tabular-nums shrink-0">
                  {preset.cpm_rate}
                </span>
              </div>

              {/* Quiet Key-Value Rules */}
              <dl className="grid grid-cols-2 gap-y-3 gap-x-4 border-t border-white/[0.06] pt-4 text-xs">
                <div>
                  <dt className="text-[#71717A]">Required Hashtags</dt>
                  <dd className="mt-0.5 font-mono text-[#FAFAFA]">
                    {preset.required_hashtags.join(' ')}
                  </dd>
                </div>
                <div>
                  <dt className="text-[#71717A]">Retention Window</dt>
                  <dd className="mt-0.5 font-mono text-[#FAFAFA] tabular-nums">
                    {preset.retention_days} days · IG ≤ {preset.max_ig_hashtags} tags
                  </dd>
                </div>
                <div>
                  <dt className="text-[#71717A]">Tier-1 Targets</dt>
                  <dd className="mt-0.5 font-mono text-[#A1A1AA]">
                    {preset.target_countries.join(' · ')}
                  </dd>
                </div>
                <div>
                  <dt className="text-[#71717A]">Payout Unlock</dt>
                  <dd className="mt-0.5 font-mono text-[#A1A1AA] tabular-nums">
                    {preset.min_views_unlock.toLocaleString()} views min
                  </dd>
                </div>
              </dl>
            </div>

            <div className="mt-5 pt-4 border-t border-white/[0.06] flex items-center justify-between gap-3">
              <span className="text-[11px] text-[#71717A]">
                Logo lock: 100% duration · Exact ratio
              </span>
              {preset.active ? (
                <span className="inline-flex items-center gap-1.5 text-xs font-medium text-[#22C55E]">
                  <Check className="h-3.5 w-3.5" />
                  <span>Active Campaign</span>
                </span>
              ) : (
                <button
                  type="button"
                  onClick={() => onActivatePreset(preset.id)}
                  className="rounded-lg border border-white/[0.1] bg-white/[0.06] px-3.5 py-1.5 text-xs font-medium text-[#FAFAFA] hover:bg-[#FFE600] hover:text-[#09090B] hover:border-[#FFE600] transition-colors cursor-pointer"
                >
                  Activate
                </button>
              )}
            </div>
          </article>
        ))
      )}
      </div>

      {/* New Campaign Preset Modal */}
      {modalOpen && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="New Campaign Preset"
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
        >
          <button
            type="button"
            aria-label="Close modal"
            onClick={() => setModalOpen(false)}
            className="fixed inset-0 bg-black/75 backdrop-blur-sm"
          />
          <div className="relative z-10 w-full max-w-[620px] rounded-xl border border-white/[0.12] bg-[#111113] overflow-hidden">
            <div className="flex items-center justify-between border-b border-white/[0.08] px-5 py-4">
              <div>
                <h2 className="text-sm font-semibold text-[#FAFAFA]">New Campaign Preset</h2>
                <p className="text-xs text-[#71717A] mt-0.5">
                  Paste any raw Whop brief to auto-parse hashtags, retention, and Tier-1 rules.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                aria-label="Close New Campaign Preset modal"
                className="flex h-8 w-8 items-center justify-center rounded-md text-[#A1A1AA] hover:text-[#FAFAFA]"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleSave} className="p-5 space-y-4 max-h-[80vh] overflow-y-auto">
              <div className="space-y-1.5">
                <label htmlFor="whop-brief-textarea" className="text-xs font-medium text-[#FAFAFA]">
                  Raw Whop Campaign Brief
                </label>
                <textarea
                  id="whop-brief-textarea"
                  rows={5}
                  value={rawBrief}
                  onChange={(e) => {
                    setRawBrief(e.target.value);
                    if (formError) setFormError(null);
                  }}
                  placeholder={SAMPLE_BRIEF_PLACEHOLDER}
                  className="w-full rounded-lg border border-white/[0.08] bg-[#09090B] px-3.5 py-2.5 text-xs leading-relaxed text-[#FAFAFA] placeholder:text-[#71717A] focus:border-[#FFE600]/60 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label htmlFor="whop-handle-input" className="text-xs font-medium text-[#FAFAFA]">
                    Whop Campaign Link (optional)
                  </label>
                  <input
                    id="whop-handle-input"
                    type="text"
                    value={whopHandle}
                    onChange={(e) => setWhopHandle(e.target.value)}
                    placeholder="whop.com/clipup-gta6"
                    className="w-full rounded-lg border border-white/[0.08] bg-[#09090B] px-3 py-2 text-xs text-[#FAFAFA] placeholder:text-[#71717A] focus:border-[#FFE600]/60 focus:outline-none"
                  />
                </div>

                <div className="space-y-1.5">
                  <span className="block text-xs font-medium text-[#FAFAFA]">
                    Campaign Logo PNG
                  </span>
                  <label className="flex items-center justify-between gap-2 rounded-lg border border-dashed border-white/[0.14] bg-[#09090B] px-3 py-2 text-xs text-[#A1A1AA] hover:border-white/[0.24] cursor-pointer">
                    <span className="flex items-center gap-2 truncate">
                      <Upload className="h-3.5 w-3.5 shrink-0" />
                      <span className="truncate">
                        {logoFileName ?? 'Select transparent PNG...'}
                      </span>
                    </span>
                    <input
                      type="file"
                      accept="image/png,image/webp,image/svg+xml"
                      onChange={handleLogoFile}
                      className="sr-only"
                    />
                  </label>
                </div>
              </div>

              {/* Live Auto-Parsed Compliance Preview */}
              {parsed && (
                <div
                  data-testid="parsed-brief-preview"
                  className="rounded-lg border border-white/[0.08] bg-[#09090B] p-4 space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-[#FAFAFA]">
                      Auto-Parsed Compliance Rules
                    </span>
                    <span className="font-mono text-[11px] text-[#22C55E]">Ready to save</span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                    <div>
                      <span className="block text-[11px] text-[#71717A]">Campaign Name</span>
                      <span className="text-[#FAFAFA] font-medium">{parsed.name}</span>
                    </div>
                    <div>
                      <span className="block text-[11px] text-[#71717A]">Required Tags</span>
                      <span className="font-mono text-[#FAFAFA]">
                        {parsed.required_hashtags.join(' ')}
                      </span>
                    </div>
                    <div>
                      <span className="block text-[11px] text-[#71717A]">IG Cap / Retention</span>
                      <span className="font-mono text-[#FAFAFA]">
                        ≤{parsed.max_ig_hashtags} tags · {parsed.retention_days}d
                      </span>
                    </div>
                    <div>
                      <span className="block text-[11px] text-[#71717A]">Tier-1 Countries</span>
                      <span className="font-mono text-[#A1A1AA]">
                        {parsed.target_countries.join(', ')}
                      </span>
                    </div>
                    <div>
                      <span className="block text-[11px] text-[#71717A]">Payout Unlock</span>
                      <span className="font-mono text-[#A1A1AA]">
                        {parsed.min_views_unlock.toLocaleString()} views
                      </span>
                    </div>
                    <div>
                      <span className="block text-[11px] text-[#71717A]">CPM Rate</span>
                      <span className="font-mono text-[#A1A1AA]">{parsed.cpm_rate}</span>
                    </div>
                  </div>
                </div>
              )}

              {formError && (
                <p role="alert" className="text-xs text-[#EF4444]">
                  {formError}
                </p>
              )}

              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-t border-white/[0.06] pt-4">
                <p className="inline-flex items-center gap-1.5 text-[11px] text-[#71717A]">
                  <ShieldCheck className="h-3.5 w-3.5 text-[#A1A1AA] shrink-0" />
                  <span>Whop submissions stay manual to protect your account.</span>
                </p>

                <div className="flex items-center justify-end gap-2 shrink-0">
                  <button
                    type="button"
                    onClick={() => setModalOpen(false)}
                    className="rounded-lg border border-white/[0.08] px-3.5 py-2 text-xs font-medium text-[#A1A1AA] hover:text-[#FAFAFA]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={saving}
                    className="rounded-lg bg-[#FFE600] px-4 py-2 text-xs font-semibold text-[#09090B] hover:bg-[#F5DD00] disabled:opacity-60 transition-colors cursor-pointer"
                  >
                    {saving ? 'Saving...' : 'Save Preset'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
