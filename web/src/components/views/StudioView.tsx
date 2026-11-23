import { useEffect, useMemo, useRef, useState } from 'react';
import {
  AlertCircle,
  CalendarClock,
  Check,
  Columns2,
  Eye,
  Pause,
  Play,
  Plus,
  Send,
  Sparkles,
  X,
} from 'lucide-react';
import { IST_SLOTS } from '../../data/demoData';
import type {
  CampaignPreset,
  CaptionStyle,
  ClipJob,
  LayoutMode,
} from '../../types/studio';
import { validateClipCompliance } from '../../utils/clipLogic';

interface StudioViewProps {
  clips: ClipJob[];
  selectedClipId: string;
  onSelectClip: (clipId: string) => void;
  activePreset: CampaignPreset;
  onUpdateClip: (clip: ClipJob) => void;
  onApproveAndSchedule: (clip: ClipJob, istSlot: string) => Promise<void>;
}

type InspectorTab = 'text' | 'look' | 'schedule';

export function StudioView({
  clips,
  selectedClipId,
  onSelectClip,
  activePreset,
  onUpdateClip,
  onApproveAndSchedule,
}: StudioViewProps) {
  const clip = useMemo(
    () => clips.find((c) => c.clip_id === selectedClipId) ?? clips[0],
    [clips, selectedClipId]
  );

  const [tab, setTab] = useState<InspectorTab>('text');
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(1.6);
  const [showSafeZone, setShowSafeZone] = useState(false);
  const [newTagInput, setNewTagInput] = useState('');
  const [selectedSlot, setSelectedSlot] = useState(
    clip?.scheduled_ist_slot ?? IST_SLOTS[0].ist
  );
  const [scheduling, setScheduling] = useState(false);
  const [scheduleError, setScheduleError] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    if (videoRef.current) {
      if (playing) {
        videoRef.current.play().catch(() => {});
      } else {
        videoRef.current.pause();
      }
    }
  }, [playing]);

  useEffect(() => {
    if (!clip) return;
    setCurrentTime(Math.min(1.6, clip.trim_end_sec));
    setPlaying(false);
    setSelectedSlot(clip.scheduled_ist_slot ?? IST_SLOTS[0].ist);
    setScheduleError(null);
  }, [clip?.clip_id]);

  useEffect(() => {
    if (!playing || !clip) return;
    const interval = setInterval(() => {
      setCurrentTime((prev) => {
        const next = prev + 0.1;
        if (next >= clip.trim_end_sec) {
          return clip.trim_start_sec;
        }
        return Number(next.toFixed(1));
      });
    }, 100);
    return () => clearInterval(interval);
  }, [playing, clip?.trim_start_sec, clip?.trim_end_sec]);

  if (!clip) {
    return (
      <div className="mx-auto max-w-[720px] px-4 py-24 text-center space-y-4">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl border border-white/[0.08] bg-[#111113]">
          <Play className="h-6 w-6 text-[#FFE600] ml-0.5" />
        </div>
        <div className="space-y-1.5">
          <h2 className="text-base font-semibold text-[#FAFAFA]">No clips queued yet</h2>
          <p className="text-xs text-[#71717A] max-w-[420px] mx-auto">
            Paste a YouTube or Twitch stream URL in the Create tab to discover, rank, and review high-impact moments.
          </p>
        </div>
      </div>
    );
  }

  const compliance = validateClipCompliance(clip, activePreset);

  // Determine active caption chunk (3-word sliding group synced to playback time)
  const words = clip.transcript_words;
  const loopWindow = words.length > 0 ? words[words.length - 1].endSec : 10;
  const effectiveCaptionSec = loopWindow > 0 ? currentTime % loopWindow : 0;
  const activeWordIdx = Math.max(
    0,
    words.findIndex(
      (w) => effectiveCaptionSec >= w.startSec && effectiveCaptionSec <= w.endSec
    )
  );
  const groupStart = Math.floor(activeWordIdx / 3) * 3;
  const visibleCaptionWords = words.slice(groupStart, groupStart + 3);

  const patchClip = (partial: Partial<ClipJob>) => {
    onUpdateClip({ ...clip, ...partial });
    if (scheduleError) setScheduleError(null);
  };

  const handleAddTag = (e: React.FormEvent) => {
    e.preventDefault();
    const raw = newTagInput.trim();
    if (!raw) return;
    const formatted = raw.startsWith('#') ? raw : `#${raw}`;
    if (!clip.hashtags.some((t) => t.toLowerCase() === formatted.toLowerCase())) {
      patchClip({ hashtags: [...clip.hashtags, formatted] });
    }
    setNewTagInput('');
  };

  const handleRemoveTag = (tag: string) => {
    patchClip({ hashtags: clip.hashtags.filter((t) => t !== tag) });
  };

  const handleApproveSchedule = async () => {
    if (!compliance.allPassed) {
      setScheduleError('Fix the highlighted compliance checks before scheduling to Zernio.');
      return;
    }
    setScheduleError(null);
    setScheduling(true);
    try {
      await onApproveAndSchedule(clip, selectedSlot);
    } finally {
      setScheduling(false);
    }
  };

  const showHookBanner = currentTime <= clip.trim_start_sec + 2.5;
  const titleLen = clip.yt_title.length;
  const titleOverLimit = titleLen > 65;

  return (
    <div className="mx-auto w-full max-w-[1280px] px-4 sm:px-6 py-5 sm:py-6">
      {/* Studio Sub-header: Clip selector */}
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <h1 className="text-base font-semibold text-[#FAFAFA] whitespace-nowrap">Studio</h1>
          <span className="text-[#71717A]" aria-hidden="true">
            /
          </span>
          <label htmlFor="studio-clip-select" className="sr-only">
            Select clip to review
          </label>
          <select
            id="studio-clip-select"
            value={clip.clip_id}
            onChange={(e) => onSelectClip(e.target.value)}
            className="max-w-[260px] sm:max-w-[380px] truncate rounded-md border border-white/[0.08] bg-[#111113] px-3 py-1.5 text-xs font-medium text-[#FAFAFA] hover:border-white/[0.16] cursor-pointer"
          >
            {clips.map((c) => (
              <option key={c.clip_id} value={c.clip_id} className="bg-[#111113] text-[#FAFAFA]">
                #{c.clip_number} · Score {c.predicted_viral_score} · {c.yt_title}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-3 text-xs text-[#A1A1AA]">
          <span className="font-mono tabular-nums">
            {clip.timestamp_start} – {clip.timestamp_end}
          </span>
          <span aria-hidden="true">·</span>
          <span>{clip.archetype}</span>
          <span aria-hidden="true">·</span>
          <span className="inline-flex items-center gap-1.5">
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                compliance.allPassed ? 'bg-[#22C55E]' : 'bg-[#EF4444]'
              }`}
              aria-hidden="true"
            />
            <span>{compliance.allPassed ? 'Compliance passed' : 'Compliance warning'}</span>
          </span>
        </div>
      </div>

      {/* Split-Screen 2-Pane Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Pane: 9:16 Vertical Stage */}
        <section
          aria-label="9:16 Vertical Stage Preview"
          className="lg:col-span-5 flex flex-col items-center space-y-4"
        >
          {/* Phone Ratio Stage (1080x1920 -> 9:16) */}
          <div
            data-testid="vertical-stage"
            className="relative w-full max-w-[304px] aspect-[9/16] rounded-2xl border border-white/[0.12] bg-[#09090B] overflow-hidden select-none"
          >
            {clip.video_url ? (
              <div className="relative h-full w-full bg-[#09090B] flex items-center justify-center overflow-hidden">
                <video
                  ref={videoRef}
                  src={clip.video_url}
                  className="h-full w-full object-cover"
                  playsInline
                  loop
                  muted
                  onTimeUpdate={(e) => {
                    const t = (e.target as HTMLVideoElement).currentTime;
                    setCurrentTime(Number(t.toFixed(1)));
                  }}
                  data-testid="rendered-video-player"
                />
              </div>
            ) : clip.layout_mode === 'split-35-65' ? (
              <div className="flex flex-col h-full w-full">
                {/* Top 35% Facecam */}
                <div className="relative h-[35%] w-full overflow-hidden border-b border-black/60 bg-[#141417]">
                  <img
                    src={clip.facecam_image}
                    alt={`${clip.source_streamer} facecam reaction`}
                    referrerPolicy="no-referrer"
                    className="h-full w-full object-cover object-[58%_25%] scale-125"
                  />
                </div>
                {/* Bottom 65% Gameplay */}
                <div className="relative h-[65%] w-full overflow-hidden bg-[#0E0E11]">
                  <img
                    src={clip.gameplay_image}
                    alt={`GTA 6 ${clip.archetype} gameplay`}
                    referrerPolicy="no-referrer"
                    className="h-full w-full object-cover object-center"
                  />
                </div>
              </div>
            ) : (
              /* Blurred Fill Layout */
              <div className="relative h-full w-full bg-[#09090B] flex items-center justify-center overflow-hidden">
                <img
                  src={clip.gameplay_image}
                  alt=""
                  aria-hidden="true"
                  referrerPolicy="no-referrer"
                  className="absolute inset-0 h-full w-full object-cover blur-xl scale-110 opacity-45"
                />
                <img
                  src={clip.gameplay_image}
                  alt={`GTA 6 ${clip.archetype} gameplay`}
                  referrerPolicy="no-referrer"
                  className="relative z-10 w-full aspect-video object-cover shadow-2xl border-y border-white/10"
                />
              </div>
            )}

            {/* Measured contrast scrim for captions */}
            <div className="pointer-events-none absolute inset-x-0 bottom-0 h-44 bg-gradient-to-t from-black/85 via-black/35 to-transparent z-10" />

            {/* Campaign Logo Overlay (Positioned inside safe zone below top 11% UI dead zone) */}
            <div
              className="absolute top-[13%] right-3 z-20 flex items-center gap-1.5 rounded bg-black/75 border border-white/15 px-2 py-1 backdrop-blur-sm"
              title="Campaign Logo (100% duration · Safe Zone)"
            >
              {activePreset.logo_data_url ? (
                <img
                  src={activePreset.logo_data_url}
                  alt={activePreset.name}
                  className="h-4 w-auto object-contain"
                />
              ) : (
                <span className="font-mono text-[10px] font-bold tracking-wider text-[#FAFAFA]">
                  {activePreset.logo_label}
                </span>
              )}
            </div>

            {/* 2.5s Opening Hook Banner */}
            {showHookBanner && clip.hook_banner_text.trim() && (
              <div
                style={{ top: `${clip.hook_banner_y}%` }}
                className="absolute inset-x-4 z-20 flex justify-center transition-all"
              >
                <div className="rounded-md bg-[#09090B]/90 border border-white/15 px-3 py-1.5 text-center shadow-lg">
                  <span className="text-[12px] font-bold tracking-wide text-[#FAFAFA] uppercase">
                    {clip.hook_banner_text}
                  </span>
                </div>
              </div>
            )}

            {/* Live Word-by-Word Captions (#FFE600 active word) */}
            <div className="absolute inset-x-4 bottom-[22%] z-20 flex flex-wrap items-center justify-center gap-x-1.5 gap-y-1 text-center">
              {visibleCaptionWords.map((item, idx) => {
                const globalIndex = groupStart + idx;
                const isActiveWord = globalIndex === activeWordIdx;
                return (
                  <span
                    key={`${item.word}-${globalIndex}`}
                    className={`font-extrabold tracking-tight uppercase drop-shadow-[0_2px_4px_rgba(0,0,0,0.95)] transition-transform duration-100 ${
                      clip.caption_style === 'bold-outline'
                        ? 'text-[20px] px-1 rounded bg-black/60'
                        : 'text-[19px]'
                    } ${
                      isActiveWord
                        ? clip.caption_style === 'clean-white'
                          ? 'text-[#FAFAFA] scale-105'
                          : 'text-[#FFE600] scale-105'
                        : 'text-[#FAFAFA]/90'
                    }`}
                  >
                    {item.word}
                  </span>
                );
              })}
            </div>

            {/* Safe-Zone Overlay Guide (Reels & Shorts dead zones) */}
            {showSafeZone && (
              <div
                data-testid="safe-zone-overlay"
                aria-label="Reels and Shorts safe zone guide"
                className="pointer-events-none absolute inset-0 z-30"
              >
                {/* Top dead zone */}
                <div className="absolute inset-x-0 top-0 h-[11%] bg-[#EF4444]/20 border-b border-dashed border-[#EF4444]/70 flex items-center justify-center">
                  <span className="font-mono text-[9px] text-[#FAFAFA] bg-black/70 px-1.5 py-0.5 rounded">
                    TOP UI DEAD ZONE
                  </span>
                </div>
                {/* Right engagement icons dead zone */}
                <div className="absolute right-0 top-[44%] bottom-[18%] w-[18%] bg-[#F59E0B]/20 border-l border-y border-dashed border-[#F59E0B]/70 flex items-center justify-center">
                  <span className="font-mono text-[8px] text-[#FAFAFA] -rotate-90 whitespace-nowrap bg-black/70 px-1 rounded">
                    REELS / SHORTS ICONS
                  </span>
                </div>
                {/* Bottom caption/description dead zone */}
                <div className="absolute inset-x-0 bottom-0 h-[18%] bg-[#EF4444]/20 border-t border-dashed border-[#EF4444]/70 flex items-center justify-center">
                  <span className="font-mono text-[9px] text-[#FAFAFA] bg-black/70 px-1.5 py-0.5 rounded">
                    CAPTION / AUDIO BAR ZONE
                  </span>
                </div>
              </div>
            )}

            {/* Minimal Bottom Timecode Overlay */}
            <div className="absolute bottom-2.5 left-3 z-20 font-mono text-[10px] text-[#FAFAFA]/80 tabular-nums">
              {currentTime.toFixed(1)}s / {clip.trim_end_sec.toFixed(1)}s
            </div>
          </div>

          {/* Floating Minimal Toolbar */}
          <div className="w-full max-w-[360px] rounded-xl border border-white/[0.08] bg-[#111113] p-3 space-y-3">
            <div className="flex items-center justify-between gap-2">
              <button
                type="button"
                onClick={() => setPlaying((p) => !p)}
                aria-label={playing ? 'Pause preview' : 'Play preview'}
                className="inline-flex items-center gap-1.5 rounded-lg bg-[#FFE600] px-3 py-1.5 text-xs font-semibold text-[#09090B] hover:bg-[#F5DD00] transition-colors whitespace-nowrap cursor-pointer"
              >
                {playing ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
                <span>{playing ? 'Pause' : 'Play'}</span>
              </button>

              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => setShowSafeZone((v) => !v)}
                  aria-pressed={showSafeZone}
                  className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-colors whitespace-nowrap cursor-pointer ${
                    showSafeZone
                      ? 'border-[#FFE600]/60 bg-[#FFE600]/10 text-[#FFE600]'
                      : 'border-white/[0.08] bg-[#09090B] text-[#A1A1AA] hover:text-[#FAFAFA]'
                  }`}
                >
                  <Eye className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>Safe Zone</span>
                </button>

                <button
                  type="button"
                  onClick={() =>
                    patchClip({
                      layout_mode:
                        clip.layout_mode === 'split-35-65' ? 'blurred-fill' : 'split-35-65',
                    })
                  }
                  className="inline-flex items-center gap-1.5 rounded-lg border border-white/[0.08] bg-[#09090B] px-2.5 py-1.5 text-xs font-medium text-[#FAFAFA] hover:border-white/[0.16] transition-colors whitespace-nowrap cursor-pointer"
                >
                  <Columns2 className="h-3.5 w-3.5 text-[#A1A1AA]" aria-hidden="true" />
                  <span>
                    {clip.layout_mode === 'split-35-65' ? '35/65 Split' : 'Blurred Fill'}
                  </span>
                </button>
              </div>
            </div>

            {/* Compact Trim & Audio Peak Waveform Bar */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[11px] font-mono text-[#71717A] tabular-nums">
                <span>In {clip.trim_start_sec}s</span>
                <span>Audio Peaks · {clip.trim_end_sec - clip.trim_start_sec}s</span>
                <span>Out {clip.trim_end_sec}s</span>
              </div>

              <div
                className="relative h-10 rounded-lg border border-white/[0.06] bg-[#09090B] px-1.5 flex items-end gap-[2px] cursor-pointer overflow-hidden"
                onClick={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
                  setCurrentTime(Number((ratio * clip.duration_sec).toFixed(1)));
                }}
              >
                {clip.audio_peaks.map((peak, i) => {
                  const barTime = (i / clip.audio_peaks.length) * clip.duration_sec;
                  const insideTrim =
                    barTime >= clip.trim_start_sec && barTime <= clip.trim_end_sec;
                  const isPast = barTime <= currentTime;
                  return (
                    <span
                      key={i}
                      style={{ height: `${Math.max(16, Math.round(peak * 100))}%` }}
                      className={`flex-1 rounded-t-xs transition-colors ${
                        !insideTrim
                          ? 'bg-white/[0.06]'
                          : isPast
                            ? 'bg-[#FFE600]'
                            : peak > 0.85
                              ? 'bg-[#FAFAFA]/75'
                              : 'bg-white/[0.22]'
                      }`}
                    />
                  );
                })}
              </div>

              <div className="grid grid-cols-2 gap-3 pt-1">
                <label className="flex items-center gap-2 text-[11px] text-[#71717A]">
                  <span className="shrink-0">Trim In</span>
                  <input
                    type="range"
                    min={0}
                    max={Math.max(0, clip.trim_end_sec - 5)}
                    value={clip.trim_start_sec}
                    onChange={(e) => {
                      const val = Number(e.target.value);
                      patchClip({ trim_start_sec: val });
                      if (currentTime < val) setCurrentTime(val);
                    }}
                    className="w-full accent-[#FFE600]"
                  />
                </label>
                <label className="flex items-center gap-2 text-[11px] text-[#71717A]">
                  <span className="shrink-0">Trim Out</span>
                  <input
                    type="range"
                    min={Math.min(clip.duration_sec, clip.trim_start_sec + 5)}
                    max={clip.duration_sec}
                    value={clip.trim_end_sec}
                    onChange={(e) => {
                      const val = Number(e.target.value);
                      patchClip({ trim_end_sec: val });
                      if (currentTime > val) setCurrentTime(val);
                    }}
                    className="w-full accent-[#FFE600]"
                  />
                </label>
              </div>
            </div>
          </div>
        </section>

        {/* Right Pane: Clean Tabbed Inspector */}
        <section
          aria-label="Clip Metadata and Schedule Inspector"
          className="lg:col-span-7 rounded-xl border border-white/[0.08] bg-[#111113] overflow-hidden"
        >
          {/* Inspector Tabs */}
          <div
            role="tablist"
            aria-label="Studio Inspector Sections"
            className="flex items-center border-b border-white/[0.08] px-4"
          >
            {(
              [
                ['text', 'Text & Tags'],
                ['look', 'Look & Logo'],
                ['schedule', 'Schedule'],
              ] as const
            ).map(([key, label]) => (
              <button
                key={key}
                type="button"
                role="tab"
                aria-selected={tab === key}
                onClick={() => setTab(key)}
                className={`relative px-4 py-3.5 text-xs font-medium transition-colors whitespace-nowrap cursor-pointer ${
                  tab === key
                    ? 'text-[#FAFAFA]'
                    : 'text-[#71717A] hover:text-[#A1A1AA]'
                }`}
              >
                {label}
                {tab === key && (
                  <span className="absolute inset-x-2 bottom-0 h-[2px] bg-[#FFE600]" />
                )}
              </button>
            ))}
          </div>

          <div className="p-5 sm:p-6 space-y-6">
            {tab === 'text' && (
              <>
                {/* YouTube Shorts Title */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label
                      htmlFor="yt-shorts-title"
                      className="text-xs font-medium text-[#FAFAFA]"
                    >
                      YouTube Shorts Title
                    </label>
                    <span
                      className={`font-mono text-xs tabular-nums ${
                        titleOverLimit ? 'text-[#EF4444]' : 'text-[#71717A]'
                      }`}
                    >
                      {titleLen}/65 chars
                    </span>
                  </div>
                  <input
                    id="yt-shorts-title"
                    type="text"
                    value={clip.yt_title}
                    onChange={(e) => patchClip({ yt_title: e.target.value })}
                    className={`w-full rounded-lg border bg-[#09090B] px-3.5 py-2.5 text-sm text-[#FAFAFA] focus:outline-none ${
                      titleOverLimit
                        ? 'border-[#EF4444]/60'
                        : 'border-white/[0.08] focus:border-[#FFE600]/60'
                    }`}
                  />

                  {/* 3 One-Click AI Title Ideas */}
                  <div className="space-y-1.5 pt-1">
                    <span className="inline-flex items-center gap-1.5 text-[11px] text-[#71717A]">
                      <Sparkles className="h-3 w-3 text-[#A1A1AA]" aria-hidden="true" />
                      <span>AI Title Ideas</span>
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {clip.ai_title_ideas.map((idea, idx) => (
                        <button
                          key={idx}
                          type="button"
                          onClick={() => patchClip({ yt_title: idea })}
                          className={`rounded-md border px-2.5 py-1 text-xs text-left transition-colors cursor-pointer ${
                            clip.yt_title === idea
                              ? 'border-[#FFE600]/50 bg-[#FFE600]/10 text-[#FAFAFA]'
                              : 'border-white/[0.08] bg-[#09090B] text-[#A1A1AA] hover:border-white/[0.16] hover:text-[#FAFAFA]'
                          }`}
                        >
                          {idea}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Instagram Caption + DM-Share Trigger */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label
                      htmlFor="ig-caption-input"
                      className="text-xs font-medium text-[#FAFAFA]"
                    >
                      Instagram Caption
                    </label>
                    <textarea
                      id="ig-caption-input"
                      rows={3}
                      value={clip.ig_caption}
                      onChange={(e) => patchClip({ ig_caption: e.target.value })}
                      className="w-full rounded-lg border border-white/[0.08] bg-[#09090B] px-3 py-2 text-xs leading-relaxed text-[#FAFAFA] focus:border-[#FFE600]/60 focus:outline-none resize-none"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label
                      htmlFor="dm-share-input"
                      className="text-xs font-medium text-[#FAFAFA]"
                    >
                      DM-Share Trigger
                    </label>
                    <textarea
                      id="dm-share-input"
                      rows={3}
                      value={clip.dm_share_trigger}
                      onChange={(e) => patchClip({ dm_share_trigger: e.target.value })}
                      className="w-full rounded-lg border border-white/[0.08] bg-[#09090B] px-3 py-2 text-xs leading-relaxed text-[#FAFAFA] focus:border-[#FFE600]/60 focus:outline-none resize-none"
                    />
                  </div>
                </div>

                {/* Hashtags + Inline Compliance Gate */}
                <div className="space-y-3 border-t border-white/[0.06] pt-5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-[#FAFAFA]">
                      Hashtags &amp; Compliance Gate
                    </span>
                    <span className="font-mono text-xs text-[#71717A] tabular-nums">
                      {clip.hashtags.length}/{activePreset.max_ig_hashtags} IG tags
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-1.5">
                    {clip.hashtags.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center gap-1 rounded-md border border-white/[0.08] bg-[#09090B] px-2.5 py-1 font-mono text-xs text-[#FAFAFA]"
                      >
                        <span>{tag}</span>
                        <button
                          type="button"
                          onClick={() => handleRemoveTag(tag)}
                          aria-label={`Remove hashtag ${tag}`}
                          className="text-[#71717A] hover:text-[#FAFAFA]"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </span>
                    ))}
                    <form onSubmit={handleAddTag} className="inline-flex items-center gap-1">
                      <input
                        type="text"
                        value={newTagInput}
                        onChange={(e) => setNewTagInput(e.target.value)}
                        placeholder="#addtag"
                        aria-label="Add hashtag"
                        className="w-24 rounded-md border border-white/[0.08] bg-[#09090B] px-2 py-1 font-mono text-xs text-[#FAFAFA] placeholder:text-[#71717A] focus:border-[#FFE600]/60 focus:outline-none"
                      />
                      <button
                        type="submit"
                        aria-label="Add hashtag button"
                        className="flex h-7 w-7 items-center justify-center rounded-md border border-white/[0.08] bg-[#09090B] text-[#A1A1AA] hover:text-[#FAFAFA]"
                      >
                        <Plus className="h-3.5 w-3.5" />
                      </button>
                    </form>
                  </div>

                  {/* Inline Compliance Gate Checkmarks (#gta6 #Clipup, IG <= 5, Not Made for Kids, Comments ON) */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                    {compliance.checks
                      .filter((c) =>
                        ['required-tags', 'ig-tag-cap', 'not-kids', 'comments-on'].includes(c.id)
                      )
                      .map((item) => (
                        <div
                          key={item.id}
                          className="flex items-center justify-between rounded-lg border border-white/[0.06] bg-[#09090B] px-3 py-2 text-xs"
                        >
                          <span className="text-[#A1A1AA] truncate">{item.label}</span>
                          <span
                            className={`inline-flex items-center gap-1 font-mono text-[11px] shrink-0 ${
                              item.passed ? 'text-[#22C55E]' : 'text-[#EF4444]'
                            }`}
                          >
                            {item.passed ? (
                              <Check className="h-3.5 w-3.5" />
                            ) : (
                              <AlertCircle className="h-3.5 w-3.5" />
                            )}
                            <span>{item.passed ? 'Pass' : 'Fix'}</span>
                          </span>
                        </div>
                      ))}
                  </div>

                  {/* Toggles for Not Made for Kids & Comments ON */}
                  <div className="flex flex-wrap items-center gap-4 pt-1 text-xs">
                    <label className="inline-flex items-center gap-2 text-[#A1A1AA] cursor-pointer">
                      <input
                        type="checkbox"
                        checked={clip.not_made_for_kids}
                        onChange={(e) => patchClip({ not_made_for_kids: e.target.checked })}
                        className="accent-[#FFE600]"
                      />
                      <span>Not Made for Kids</span>
                    </label>
                    <label className="inline-flex items-center gap-2 text-[#A1A1AA] cursor-pointer">
                      <input
                        type="checkbox"
                        checked={clip.comments_enabled}
                        onChange={(e) => patchClip({ comments_enabled: e.target.checked })}
                        className="accent-[#FFE600]"
                      />
                      <span>Comments ON</span>
                    </label>
                  </div>
                </div>

                {/* First Comment */}
                <div className="space-y-1.5 border-t border-white/[0.06] pt-5">
                  <label
                    htmlFor="first-comment-input"
                    className="text-xs font-medium text-[#FAFAFA]"
                  >
                    First Comment (auto-pinned on publish)
                  </label>
                  <input
                    id="first-comment-input"
                    type="text"
                    value={clip.first_comment}
                    onChange={(e) => patchClip({ first_comment: e.target.value })}
                    className="w-full rounded-lg border border-white/[0.08] bg-[#09090B] px-3.5 py-2 text-xs text-[#FAFAFA] focus:border-[#FFE600]/60 focus:outline-none"
                  />
                </div>
              </>
            )}

            {tab === 'look' && (
              <div className="space-y-6">
                {/* Caption Style */}
                <div className="space-y-2.5">
                  <span className="text-xs font-medium text-[#FAFAFA]">Caption Style</span>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                    {(
                      [
                        ['word-yellow', 'Electric Word', 'Active word #FFE600'],
                        ['clean-white', 'Clean White', 'Minimal crisp mono'],
                        ['bold-outline', 'Boxed Impact', 'Dark pill backing'],
                      ] as Array<[CaptionStyle, string, string]>
                    ).map(([styleId, label, sub]) => (
                      <button
                        key={styleId}
                        type="button"
                        onClick={() => patchClip({ caption_style: styleId })}
                        className={`rounded-lg border p-3 text-left transition-colors cursor-pointer ${
                          clip.caption_style === styleId
                            ? 'border-[#FFE600]/60 bg-[#09090B]'
                            : 'border-white/[0.08] bg-[#09090B]/60 hover:border-white/[0.16]'
                        }`}
                      >
                        <div className="text-xs font-medium text-[#FAFAFA]">{label}</div>
                        <div className="text-[11px] text-[#71717A] mt-0.5">{sub}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Layout Selection */}
                <div className="space-y-2.5 border-t border-white/[0.06] pt-5">
                  <span className="text-xs font-medium text-[#FAFAFA]">Vertical Framing</span>
                  <div className="grid grid-cols-2 gap-2.5">
                    {(
                      [
                        ['split-35-65', '35/65 Split', 'Top facecam · Bottom gameplay'],
                        ['blurred-fill', 'Blurred Fill', 'Centered 16:9 with ambient blur'],
                      ] as Array<[LayoutMode, string, string]>
                    ).map(([modeId, label, sub]) => (
                      <button
                        key={modeId}
                        type="button"
                        onClick={() => patchClip({ layout_mode: modeId })}
                        className={`rounded-lg border p-3 text-left transition-colors cursor-pointer ${
                          clip.layout_mode === modeId
                            ? 'border-[#FFE600]/60 bg-[#09090B]'
                            : 'border-white/[0.08] bg-[#09090B]/60 hover:border-white/[0.16]'
                        }`}
                      >
                        <div className="text-xs font-medium text-[#FAFAFA]">{label}</div>
                        <div className="text-[11px] text-[#71717A] mt-0.5">{sub}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Hook Banner Text & Y Position */}
                <div className="space-y-4 border-t border-white/[0.06] pt-5">
                  <div className="space-y-1.5">
                    <label
                      htmlFor="hook-banner-input"
                      className="text-xs font-medium text-[#FAFAFA]"
                    >
                      2.5s Opening Hook Banner Text
                    </label>
                    <input
                      id="hook-banner-input"
                      type="text"
                      value={clip.hook_banner_text}
                      onChange={(e) => {
                        patchClip({ hook_banner_text: e.target.value });
                        if (currentTime > clip.trim_start_sec + 2.5) {
                          setCurrentTime(clip.trim_start_sec + 1.0);
                        }
                      }}
                      className="w-full rounded-lg border border-white/[0.08] bg-[#09090B] px-3.5 py-2 text-xs font-medium text-[#FAFAFA] focus:border-[#FFE600]/60 focus:outline-none"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <label htmlFor="hook-y-slider" className="text-[#A1A1AA]">
                        Hook Banner Y-Position
                      </label>
                      <span className="font-mono text-[#FAFAFA] tabular-nums">
                        {clip.hook_banner_y}%
                      </span>
                    </div>
                    <input
                      id="hook-y-slider"
                      type="range"
                      min={12}
                      max={34}
                      value={clip.hook_banner_y}
                      onChange={(e) => {
                        patchClip({ hook_banner_y: Number(e.target.value) });
                        if (currentTime > clip.trim_start_sec + 2.5) {
                          setCurrentTime(clip.trim_start_sec + 1.0);
                        }
                      }}
                      className="w-full accent-[#FFE600]"
                    />
                  </div>
                </div>

                {/* Campaign Logo Integrity Check */}
                <div className="rounded-lg border border-white/[0.08] bg-[#09090B] p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-[#FAFAFA]">
                      Campaign Logo Verification ({activePreset.name})
                    </span>
                    <span className="inline-flex items-center gap-1.5 font-mono text-[11px] text-[#22C55E]">
                      <span className="h-1.5 w-1.5 rounded-full bg-[#22C55E]" />
                      <span>Verified</span>
                    </span>
                  </div>
                  <p className="font-mono text-xs text-[#A1A1AA]">
                    100% duration · Exact aspect ratio · Zero overlap
                  </p>
                </div>
              </div>
            )}

            {tab === 'schedule' && (
              <div className="space-y-6">
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-[#FAFAFA]">
                      Select Tier-1 IST / UTC Slot
                    </span>
                    <span className="font-mono text-[11px] text-[#71717A]">
                      Targets {activePreset.target_countries.join(', ')}
                    </span>
                  </div>

                  <div className="space-y-2">
                    {IST_SLOTS.map((slot) => {
                      const isSelected = selectedSlot === slot.ist;
                      return (
                        <button
                          key={slot.id}
                          type="button"
                          onClick={() => setSelectedSlot(slot.ist)}
                          className={`w-full flex items-center justify-between gap-3 rounded-lg border px-4 py-3 text-left transition-colors cursor-pointer ${
                            isSelected
                              ? 'border-[#FFE600]/70 bg-[#09090B]'
                              : 'border-white/[0.08] bg-[#09090B]/60 hover:border-white/[0.16]'
                          }`}
                        >
                          <div className="flex items-center gap-3 min-w-0">
                            <CalendarClock
                              className={`h-4 w-4 shrink-0 ${
                                isSelected ? 'text-[#FFE600]' : 'text-[#71717A]'
                              }`}
                              aria-hidden="true"
                            />
                            <div className="min-w-0">
                              <div className="flex items-center gap-2 font-mono text-xs text-[#FAFAFA] tabular-nums">
                                <span className="font-semibold">{slot.ist}</span>
                                <span className="text-[#71717A]">/</span>
                                <span className="text-[#A1A1AA]">{slot.utc}</span>
                              </div>
                              <div className="text-xs text-[#71717A] mt-0.5 truncate">
                                {slot.regionLabel}
                              </div>
                            </div>
                          </div>
                          <span className="font-mono text-xs text-[#A1A1AA] tabular-nums shrink-0">
                            {slot.peakScore} peak
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Final Compliance Summary */}
                <div className="rounded-lg border border-white/[0.08] bg-[#09090B] p-4 space-y-2.5">
                  <div className="text-xs font-medium text-[#FAFAFA]">Pre-Flight Checklist</div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 text-xs">
                    {compliance.checks.map((c) => (
                      <div key={c.id} className="flex items-center gap-2">
                        <span
                          className={`h-1.5 w-1.5 rounded-full shrink-0 ${
                            c.passed ? 'bg-[#22C55E]' : 'bg-[#EF4444]'
                          }`}
                          aria-hidden="true"
                        />
                        <span className={c.passed ? 'text-[#A1A1AA]' : 'text-[#EF4444]'}>
                          {c.label}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {scheduleError && (
                  <p role="alert" className="text-xs text-[#EF4444]">
                    {scheduleError}
                  </p>
                )}

                <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-1">
                  <p className="text-xs text-[#71717A]">
                    Publishes to Instagram Reels + YouTube Shorts via Zernio.
                  </p>
                  <button
                    type="button"
                    disabled={scheduling}
                    onClick={handleApproveSchedule}
                    className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#FFE600] px-5 py-2.5 text-sm font-semibold text-[#09090B] hover:bg-[#F5DD00] disabled:opacity-60 transition-colors whitespace-nowrap shrink-0 cursor-pointer"
                  >
                    <Send className="h-4 w-4" aria-hidden="true" />
                    <span>
                      {scheduling
                        ? 'Scheduling...'
                        : clip.status === 'scheduled'
                          ? `Reschedule (${selectedSlot})`
                          : 'Approve & Schedule to Zernio'}
                    </span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
