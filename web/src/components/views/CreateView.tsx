import { useRef, useState } from 'react';
import {
  ChevronDown,
  ChevronUp,
  Clock,
  Film,
  Link2,
  Play,
  SkipForward,
  Terminal,
  Wand2,
} from 'lucide-react';
import type {
  ActiveJobProgress,
  CampaignPreset,
  ClipJob,
  JobStageId,
} from '../../types/studio';
import { validateJobInput } from '../../utils/clipLogic';

interface CreateViewProps {
  url: string;
  onUrlChange: (value: string) => void;
  timestampRange: string;
  onTimestampRangeChange: (value: string) => void;
  presets: CampaignPreset[];
  activePresetId: string;
  onSelectPreset: (presetId: string) => void;
  clips: ClipJob[];
  activeJob: ActiveJobProgress | null;
  onStartPlanJob: (payload: {
    url: string;
    timestamp_range: string;
    clip_count: number;
    preset_id: string;
    one_clip_approval: boolean;
  }) => Promise<void>;
  onRenderClip: (clipId: string) => Promise<void>;
  onReviewClip: (clipId: string) => void;
  onSkipClip: (clipId: string) => Promise<void>;
  urlInputRef: React.RefObject<HTMLInputElement | null>;
}

const STAGES: Array<{ id: JobStageId; label: string }> = [
  { id: 'download', label: 'Download' },
  { id: 'transcribe', label: 'Transcribe & Rank' },
  { id: 'edit', label: 'Edit 9:16' },
  { id: 'schedule', label: 'Schedule' },
];

function getStatusMeta(status: ClipJob['status']) {
  switch (status) {
    case 'ready':
      return { dot: 'bg-[#22C55E]', text: 'Ready' };
    case 'scheduled':
      return { dot: 'bg-[#22C55E]', text: 'Scheduled' };
    case 'rendering':
      return { dot: 'bg-[#F59E0B]', text: 'Rendering' };
    case 'queued':
      return { dot: 'bg-[#F59E0B]', text: 'Queued' };
    case 'error':
      return { dot: 'bg-[#EF4444]', text: 'Error' };
    case 'skipped':
      return { dot: 'bg-[#71717A]', text: 'Skipped' };
  }
}

export function CreateView({
  url,
  onUrlChange,
  timestampRange,
  onTimestampRangeChange,
  presets,
  activePresetId,
  onSelectPreset,
  clips,
  activeJob,
  onStartPlanJob,
  onRenderClip,
  onReviewClip,
  onSkipClip,
  urlInputRef,
}: CreateViewProps) {
  const [clipCount, setClipCount] = useState(5);
  const [oneClipApproval, setOneClipApproval] = useState(true);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [showConsole, setShowConsole] = useState(false);
  const [renderingId, setRenderingId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'scheduled'>('all');
  const formRef = useRef<HTMLFormElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const check = validateJobInput(url, timestampRange, clipCount);
    if (!check.valid) {
      setValidationError(check.error);
      return;
    }
    setValidationError(null);
    setSubmitting(true);
    try {
      await onStartPlanJob({
        url: url.trim(),
        timestamp_range: timestampRange.trim(),
        clip_count: clipCount,
        preset_id: activePresetId,
        one_clip_approval: oneClipApproval,
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleRender = async (clipId: string) => {
    setRenderingId(clipId);
    try {
      await onRenderClip(clipId);
    } finally {
      setRenderingId(null);
    }
  };

  const filteredClips = clips.filter((c) => {
    if (statusFilter === 'active') return c.status !== 'skipped' && c.status !== 'scheduled';
    if (statusFilter === 'scheduled') return c.status === 'scheduled';
    return true;
  });

  return (
    <div className="mx-auto w-full max-w-[1040px] px-4 sm:px-8 py-8 sm:py-12 space-y-10">
      {/* Hero Input Workspace */}
      <section aria-labelledby="create-heading" className="mx-auto max-w-[820px] space-y-5">
        <div className="text-center space-y-1.5">
          <h1
            id="create-heading"
            className="text-2xl sm:text-[28px] font-semibold tracking-tight text-[#FAFAFA] [text-wrap:balance]"
          >
            Turn long streams into compliant 9:16 clips
          </h1>
          <p className="text-sm text-[#A1A1AA]">
            Paste a YouTube, Twitch, or Kick VOD link to rank viral moments against your active Whop preset.
          </p>
        </div>

        <form ref={formRef} onSubmit={handleSubmit} className="space-y-3" noValidate>
          <div className="rounded-xl border border-white/[0.08] bg-[#111113] p-2 transition-colors focus-within:border-[#FFE600]/60">
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
              <div className="flex items-center gap-3 flex-1 px-3 py-2 min-w-0">
                <Link2 className="h-4 w-4 text-[#71717A] shrink-0" aria-hidden="true" />
                <label htmlFor="vod-url-input" className="sr-only">
                  Stream or VOD URL
                </label>
                <input
                  ref={urlInputRef}
                  id="vod-url-input"
                  type="url"
                  value={url}
                  onChange={(e) => {
                    onUrlChange(e.target.value);
                    if (validationError) setValidationError(null);
                  }}
                  placeholder="Paste YouTube, Twitch, or Kick VOD URL..."
                  className="w-full bg-transparent text-sm text-[#FAFAFA] placeholder:text-[#71717A] focus:outline-none"
                />
              </div>
              <button
                type="submit"
                disabled={submitting}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#FFE600] px-5 py-2.5 text-sm font-semibold text-[#09090B] hover:bg-[#F5DD00] disabled:opacity-60 transition-colors whitespace-nowrap shrink-0 cursor-pointer"
              >
                <Wand2 className="h-4 w-4" aria-hidden="true" />
                <span>{submitting ? 'Planning...' : 'Create'}</span>
              </button>
            </div>
          </div>

          {validationError && (
            <p role="alert" className="px-1 text-xs text-[#EF4444]">
              {validationError}
            </p>
          )}

          {/* Inline Control Row */}
          <div className="flex flex-wrap items-center justify-between gap-2.5 px-1 pt-0.5 text-xs">
            <div className="flex flex-wrap items-center gap-2">
              {/* Optional Timestamp Range */}
              <label className="inline-flex items-center gap-2 rounded-lg border border-white/[0.08] bg-[#111113] px-3 py-1.5 text-[#A1A1AA] focus-within:border-white/[0.2]">
                <Clock className="h-3.5 w-3.5 text-[#71717A] shrink-0" aria-hidden="true" />
                <span className="sr-only">Timestamp range</span>
                <input
                  type="text"
                  value={timestampRange}
                  onChange={(e) => {
                    onTimestampRangeChange(e.target.value);
                    if (validationError) setValidationError(null);
                  }}
                  placeholder="1:10:00-1:40:00"
                  aria-label="Optional timestamp range"
                  className="w-[126px] bg-transparent font-mono text-xs text-[#FAFAFA] placeholder:text-[#71717A] focus:outline-none tabular-nums"
                />
              </label>

              {/* Clip Count 1-10 */}
              <label className="inline-flex items-center gap-2 rounded-lg border border-white/[0.08] bg-[#111113] px-3 py-1.5 text-[#A1A1AA]">
                <Film className="h-3.5 w-3.5 text-[#71717A] shrink-0" aria-hidden="true" />
                <span>Clips</span>
                <select
                  aria-label="Clip count"
                  value={clipCount}
                  onChange={(e) => setClipCount(Number(e.target.value))}
                  className="bg-transparent font-mono text-xs text-[#FAFAFA] focus:outline-none cursor-pointer tabular-nums"
                >
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                    <option key={n} value={n} className="bg-[#111113] text-[#FAFAFA]">
                      {n}
                    </option>
                  ))}
                </select>
              </label>

              {/* Active Campaign Preset Selector */}
              <label className="inline-flex items-center gap-2 rounded-lg border border-white/[0.08] bg-[#111113] px-3 py-1.5 text-[#A1A1AA]">
                <span>Preset</span>
                <select
                  aria-label="Campaign preset"
                  value={activePresetId}
                  onChange={(e) => onSelectPreset(e.target.value)}
                  className="max-w-[165px] truncate bg-transparent text-xs font-medium text-[#FAFAFA] focus:outline-none cursor-pointer"
                >
                  {presets.map((p) => (
                    <option key={p.id} value={p.id} className="bg-[#111113] text-[#FAFAFA]">
                      {p.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            {/* 1-Clip Approval Mode Switch */}
            <button
              type="button"
              role="switch"
              aria-checked={oneClipApproval}
              onClick={() => setOneClipApproval((v) => !v)}
              className="inline-flex items-center gap-2.5 rounded-lg border border-white/[0.08] bg-[#111113] px-3 py-1.5 text-xs text-[#A1A1AA] hover:border-white/[0.14] transition-colors whitespace-nowrap"
            >
              <span>1-Clip Approval Mode</span>
              <span
                className={`relative inline-flex h-4 w-7 items-center rounded-full transition-colors ${
                  oneClipApproval ? 'bg-[#FFE600]' : 'bg-white/[0.14]'
                }`}
              >
                <span
                  className={`inline-block h-3 w-3 rounded-full bg-[#09090B] transition-transform ${
                    oneClipApproval ? 'translate-x-3.5' : 'translate-x-0.5'
                  }`}
                />
              </span>
            </button>
          </div>
        </form>

        {/* Expandable 4-Step Progress Strip (visible only when a job is active) */}
        {activeJob && (
          <div
            data-testid="active-job-strip"
            className="rounded-xl border border-white/[0.08] bg-[#111113] p-4 space-y-3"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2 min-w-0">
                <span
                  className={`h-1.5 w-1.5 rounded-full shrink-0 ${
                    activeJob.active ? 'bg-[#F59E0B]' : 'bg-[#22C55E]'
                  }`}
                  aria-hidden="true"
                />
                <span className="text-xs font-medium text-[#FAFAFA] truncate">
                  {activeJob.active ? 'Pipeline running' : 'Job queued & top clip ready'}
                </span>
                <span className="font-mono text-[11px] text-[#71717A] tabular-nums">
                  {activeJob.progress_pct}%
                </span>
              </div>
              <button
                type="button"
                onClick={() => setShowConsole((v) => !v)}
                className="inline-flex items-center gap-1.5 text-xs text-[#A1A1AA] hover:text-[#FAFAFA] transition-colors"
              >
                <Terminal className="h-3.5 w-3.5" aria-hidden="true" />
                <span>Console log</span>
                {showConsole ? (
                  <ChevronUp className="h-3.5 w-3.5" />
                ) : (
                  <ChevronDown className="h-3.5 w-3.5" />
                )}
              </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {STAGES.map((stage, idx) => {
                const isDone = activeJob.completed_stages.includes(stage.id);
                const isCurrent = activeJob.current_stage === stage.id && activeJob.active;
                return (
                  <div key={stage.id} className="space-y-1.5">
                    <div className="h-1 w-full rounded-full bg-white/[0.08] overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-300 ${
                          isDone
                            ? 'w-full bg-[#22C55E]'
                            : isCurrent
                              ? 'w-2/3 bg-[#FFE600]'
                              : 'w-0'
                        }`}
                      />
                    </div>
                    <div className="flex items-center justify-between text-[11px]">
                      <span
                        className={
                          isDone || isCurrent ? 'text-[#FAFAFA] font-medium' : 'text-[#71717A]'
                        }
                      >
                        {idx + 1}. {stage.label}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            {showConsole && (
              <div className="rounded-lg border border-white/[0.06] bg-[#09090B] p-3 font-mono text-[11px] leading-relaxed text-[#A1A1AA] space-y-1 max-h-[160px] overflow-y-auto">
                {activeJob.logs.map((line, idx) => (
                  <div key={idx}>{line}</div>
                ))}
              </div>
            )}
          </div>
        )}
      </section>

      {/* Ranked Queue List (state/job_queue.json) */}
      <section aria-labelledby="queue-heading" className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 id="queue-heading" className="text-sm font-semibold text-[#FAFAFA]">
              Ranked Clip Queue
            </h2>
            <p className="text-xs text-[#71717A] mt-0.5">
              Sorted by predicted viral score · <span className="font-mono">state/job_queue.json</span>
            </p>
          </div>

          <div
            role="tablist"
            aria-label="Filter clip queue"
            className="inline-flex items-center gap-1 rounded-lg border border-white/[0.08] bg-[#111113] p-1"
          >
            {(
              [
                ['all', `All (${clips.length})`],
                [
                  'active',
                  `Active (${clips.filter((c) => c.status !== 'skipped' && c.status !== 'scheduled').length})`,
                ],
                [
                  'scheduled',
                  `Scheduled (${clips.filter((c) => c.status === 'scheduled').length})`,
                ],
              ] as const
            ).map(([key, label]) => (
              <button
                key={key}
                type="button"
                role="tab"
                aria-selected={statusFilter === key}
                onClick={() => setStatusFilter(key)}
                className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors whitespace-nowrap ${
                  statusFilter === key
                    ? 'bg-white/[0.1] text-[#FAFAFA]'
                    : 'text-[#71717A] hover:text-[#A1A1AA]'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-white/[0.08] bg-[#111113] divide-y divide-white/[0.06] overflow-hidden">
          {clips.length === 0 ? (
            <div className="p-10 text-center space-y-1">
              <p className="text-sm font-medium text-[#FAFAFA]">No clips queued yet</p>
              <p className="text-xs text-[#71717A]">
                Paste a YouTube or Twitch stream URL above to plan and rank vertical moments.
              </p>
            </div>
          ) : filteredClips.length === 0 ? (
            <div className="p-10 text-center space-y-1">
              <p className="text-sm font-medium text-[#FAFAFA]">No clips in this filter</p>
              <p className="text-xs text-[#71717A]">
                Switch queue filters to view your active or scheduled moments.
              </p>
            </div>
          ) : (
            filteredClips.map((clip) => {
              const statusMeta = getStatusMeta(clip.status);
              const isRendering = renderingId === clip.clip_id;
              return (
                <div
                  key={clip.clip_id}
                  data-testid={`queue-row-${clip.clip_id}`}
                  className={`flex flex-col lg:flex-row lg:items-center justify-between gap-4 px-4 sm:px-5 py-3.5 transition-colors hover:bg-white/[0.02] ${
                    clip.status === 'skipped' ? 'opacity-50' : ''
                  }`}
                >
                  {/* Left: Clip #, Viral Score, Title + Metadata */}
                  <div className="flex items-start sm:items-center gap-4 min-w-0 flex-1">
                    <span className="font-mono text-xs text-[#71717A] tabular-nums w-8 shrink-0">
                      #{clip.clip_number}
                    </span>

                    <div
                      className="flex flex-col items-center justify-center rounded-md border border-white/[0.08] bg-[#09090B] w-11 h-10 shrink-0"
                      title="Predicted Viral Score"
                    >
                      <span
                        className={`font-mono text-sm font-semibold tabular-nums leading-none ${
                          clip.predicted_viral_score >= 90 ? 'text-[#FFE600]' : 'text-[#FAFAFA]'
                        }`}
                      >
                        {clip.predicted_viral_score}
                      </span>
                      <span className="font-mono text-[9px] text-[#71717A] mt-0.5">SCORE</span>
                    </div>

                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-[#FAFAFA] truncate">
                        {clip.yt_title}
                      </p>
                      <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-[#71717A]">
                        <span className="text-[#A1A1AA]">{clip.archetype}</span>
                        <span aria-hidden="true">·</span>
                        <span className="font-mono tabular-nums">{clip.duration_sec}s</span>
                        <span aria-hidden="true">·</span>
                        <span>{clip.ab_variant}</span>
                        <span aria-hidden="true">·</span>
                        <span>{clip.source_streamer}</span>
                        {clip.scheduled_ist_slot && (
                          <>
                            <span aria-hidden="true">·</span>
                            <span className="font-mono text-[#A1A1AA]">
                              {clip.scheduled_ist_slot}
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Right: Status + Minimal Row Actions */}
                  <div className="flex items-center justify-between lg:justify-end gap-4 shrink-0 pl-12 lg:pl-0">
                    <span className="inline-flex items-center gap-1.5 text-xs text-[#A1A1AA] whitespace-nowrap">
                      <span
                        className={`h-1.5 w-1.5 rounded-full ${
                          isRendering ? 'bg-[#F59E0B]' : statusMeta.dot
                        }`}
                        aria-hidden="true"
                      />
                      <span>{isRendering ? 'Rendering' : statusMeta.text}</span>
                    </span>

                    <div className="flex items-center gap-1.5">
                      {clip.status === 'queued' && (
                        <button
                          type="button"
                          disabled={isRendering}
                          onClick={() => handleRender(clip.clip_id)}
                          aria-label={`Render Clip #${clip.clip_number}`}
                          className="inline-flex items-center gap-1.5 rounded-md border border-white/[0.08] bg-[#09090B] px-2.5 py-1.5 text-xs font-medium text-[#FAFAFA] hover:border-white/[0.16] transition-colors whitespace-nowrap cursor-pointer"
                        >
                          <Play className="h-3 w-3 text-[#A1A1AA]" aria-hidden="true" />
                          <span>Render</span>
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => onReviewClip(clip.clip_id)}
                        aria-label={`Review Clip #${clip.clip_number}`}
                        className="inline-flex items-center gap-1.5 rounded-md border border-white/[0.1] bg-white/[0.06] px-3 py-1.5 text-xs font-medium text-[#FAFAFA] hover:bg-white/[0.12] transition-colors whitespace-nowrap cursor-pointer"
                      >
                        <span>Review</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => onSkipClip(clip.clip_id)}
                        aria-label={
                          clip.status === 'skipped'
                            ? `Restore Clip #${clip.clip_number}`
                            : `Skip Clip #${clip.clip_number}`
                        }
                        className="inline-flex items-center gap-1 rounded-md px-2 py-1.5 text-xs text-[#71717A] hover:text-[#FAFAFA] hover:bg-white/[0.04] transition-colors whitespace-nowrap cursor-pointer"
                      >
                        <SkipForward className="h-3.5 w-3.5" aria-hidden="true" />
                        <span>{clip.status === 'skipped' ? 'Restore' : 'Skip'}</span>
                      </button>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </section>
    </div>
  );
}
