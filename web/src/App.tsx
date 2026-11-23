import { useCallback, useEffect, useRef, useState } from 'react';
import { CommandPalette } from './components/CommandPalette';
import { Sidebar } from './components/Sidebar';
import { TopBar } from './components/TopBar';
import { WhopLiveUrlsDrawer } from './components/WhopLiveUrlsDrawer';
import { CreateView } from './components/views/CreateView';
import { LiveHuntView } from './components/views/LiveHuntView';
import { PresetsView } from './components/views/PresetsView';
import { SetupGuideView } from './components/views/SetupGuideView';
import { StudioView } from './components/views/StudioView';
import { ViralDnaView } from './components/views/ViralDnaView';
import {
  INITIAL_CLIPS,
  INITIAL_DISCOVERED_VODS,
  INITIAL_HEALTH,
  INITIAL_ONBOARDING,
  INITIAL_PRESETS,
  INITIAL_VIRAL_DNA,
  INITIAL_WATCHED_CHANNELS,
  createInitialLiveUrls,
} from './data/demoData';
import * as api from './services/api';
import type {
  ActiveJobProgress,
  AppView,
  CampaignPreset,
  ClipJob,
  DiscoveredVod,
  HealthStatus,
  LiveUrlItem,
  OnboardingState,
  ViralDnaData,
  WatchedChannel,
} from './types/studio';
import { rankQueueClips } from './utils/clipLogic';

export default function App() {
  const [activeView, setActiveView] = useState<AppView>('create');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const [liveUrlsOpen, setLiveUrlsOpen] = useState(false);

  const [health, setHealth] = useState<HealthStatus>(INITIAL_HEALTH);
  const [presets, setPresets] = useState<CampaignPreset[]>(INITIAL_PRESETS);
  const [clips, setClips] = useState<ClipJob[]>(() => rankQueueClips(INITIAL_CLIPS));
  const [selectedClipId, setSelectedClipId] = useState<string>(() => INITIAL_CLIPS[0]?.clip_id ?? '');
  const [liveUrls, setLiveUrls] = useState<LiveUrlItem[]>(() => createInitialLiveUrls());
  const [watchedChannels, setWatchedChannels] = useState<WatchedChannel[]>(INITIAL_WATCHED_CHANNELS);
  const [discoveredVods, setDiscoveredVods] = useState<DiscoveredVod[]>(INITIAL_DISCOVERED_VODS);
  const [viralDna, setViralDna] = useState<ViralDnaData>(INITIAL_VIRAL_DNA);
  const [onboarding, setOnboarding] = useState<OnboardingState>(INITIAL_ONBOARDING);

  // Create form shared state (so Live Hunt "Send to Create" pre-fills seamlessly)
  const [createUrl, setCreateUrl] = useState('');
  const [createRange, setCreateRange] = useState('');
  const [activeJob, setActiveJob] = useState<ActiveJobProgress | null>(null);
  const urlInputRef = useRef<HTMLInputElement | null>(null);

  // Async action states
  const [refreshingUrls, setRefreshingUrls] = useState(false);
  const [scanningStreams, setScanningStreams] = useState(false);
  const [learningAnalytics, setLearningAnalytics] = useState(false);
  const [cloningWinners, setCloningWinners] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const notify = useCallback((message: string) => {
    setToast(message);
  }, []);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3200);
    return () => clearTimeout(t);
  }, [toast]);

  // Global keyboard shortcuts (Ctrl+K / Cmd+K & Escape)
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setCommandOpen((v) => !v);
      } else if (e.key === 'Escape') {
        setCommandOpen(false);
        setLiveUrlsOpen(false);
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  // Hydrate initial state via api.ts
  useEffect(() => {
    let active = true;
    (async () => {
      // First check local engine health
      const h = await api.getHealth();
      if (!active) return;
      setHealth(h);

      // Now fetch data in parallel from local engine
      const [q, urls, streams, ps, dna, ob] = await Promise.all([
        api.getJobQueue(),
        api.getLiveUrls(),
        api.getVodStreams(),
        api.getPresets(),
        api.getViralDna(),
        api.getOnboardingState(),
      ]);
      if (!active) return;
      setClips(q);
      if (q[0]) setSelectedClipId(q[0].clip_id);
      setLiveUrls(urls);
      setWatchedChannels(streams.channels);
      setDiscoveredVods(streams.vods);
      setPresets(ps);
      setViralDna(dna);
      setOnboarding(ob);
    })();
    return () => {
      active = false;
    };
  }, []);

  const activePreset = presets.find((p) => p.active) ?? presets[0];
  const pendingLiveUrlsCount = liveUrls.filter((u) => !u.submitted).length;
  const queuedCount = clips.filter((c) => c.status !== 'skipped' && c.status !== 'scheduled').length;

  const handleRefreshHealth = async () => {
    const h = await api.getHealth();
    setHealth(h);
    if (h.backendReachable) {
      notify('Local FastAPI engine connected (127.0.0.1:8765).');
    } else {
      notify('Local engine offline — run start_web.bat or python server.py.');
    }
  };

  const handleActivatePreset = async (presetId: string) => {
    const updated = await api.activatePreset(presetId);
    setPresets(updated);
    const active = updated.find((p) => p.active);
    if (active) {
      notify(`Active campaign switched to ${active.name}.`);
    }
  };

  const handleCreatePreset = async (preset: Omit<CampaignPreset, 'id' | 'active'>) => {
    const updated = await api.createPreset(preset);
    setPresets(updated);
    notify(`Saved campaign preset "${preset.name}".`);
  };

  const handleStartPlanJob = async (payload: {
    url: string;
    timestamp_range: string;
    clip_count: number;
    preset_id: string;
    one_clip_approval: boolean;
  }) => {
    const jobId = `job-${Date.now().toString().slice(-4)}`;
    setActiveJob({
      job_id: jobId,
      source_url: payload.url,
      current_stage: 'download',
      completed_stages: [],
      progress_pct: 22,
      logs: [`[yt-dlp] Fetching metadata for ${payload.url}`],
      active: true,
    });

    await new Promise((r) => setTimeout(r, 260));
    setActiveJob((prev) =>
      prev
        ? {
            ...prev,
            current_stage: 'transcribe',
            completed_stages: ['download'],
            progress_pct: 58,
            logs: [...prev.logs, '[whisper] Running word-level transcript & Viral DNA scoring...'],
          }
        : null
    );

    const result = await api.planJob(payload);
    const updatedQueue = await api.getJobQueue();
    setClips(updatedQueue);
    if (result.new_clips[0]) {
      setSelectedClipId(result.new_clips[0].clip_id);
    }

    setActiveJob({
      job_id: result.job_id,
      source_url: payload.url,
      current_stage: 'schedule',
      completed_stages: ['download', 'transcribe', 'edit'],
      progress_pct: 100,
      logs: result.logs,
      active: false,
    });
    notify(`Planned ${result.new_clips.length} ranked clips. Top clip ready in Studio.`);
  };

  const handleRenderClip = async (clipId: string) => {
    await api.renderClip(clipId);
    const q = await api.getJobQueue();
    setClips(q);
    notify('Rendered 9:16 vertical clip with captions & campaign logo.');
  };

  const handleSkipClip = async (clipId: string) => {
    await api.skipClip(clipId);
    const q = await api.getJobQueue();
    setClips(q);
  };

  const handleReviewClip = (clipId: string) => {
    setSelectedClipId(clipId);
    setActiveView('studio');
  };

  const handleUpdateClipDraft = (updated: ClipJob) => {
    setClips((prev) => prev.map((c) => (c.clip_id === updated.clip_id ? updated : c)));
    void api.updateClipDraft(updated);
  };

  const handleApproveAndSchedule = async (clip: ClipJob, istSlot: string) => {
    const res = await api.scheduleClip(clip.clip_id, { ist_slot: istSlot, clip });
    const [q, urls] = await Promise.all([api.getJobQueue(), api.getLiveUrls()]);
    setClips(q);
    setLiveUrls(urls);
    notify(`Scheduled Clip #${res.clip.clip_number} to Zernio for ${istSlot}.`);
  };

  const handleRefreshLiveUrls = async () => {
    setRefreshingUrls(true);
    try {
      const urls = await api.getLiveUrls();
      setLiveUrls(urls);
      notify('Synced latest published Instagram Reel & YouTube Short links.');
    } finally {
      setRefreshingUrls(false);
    }
  };

  const handleToggleUrlSubmitted = async (clipId: string) => {
    const updated = await api.markLiveUrlSubmitted(clipId);
    setLiveUrls(updated);
  };

  const handleScanStreams = async () => {
    setScanningStreams(true);
    try {
      const res = await api.scanVodStreams(watchedChannels);
      setWatchedChannels(res.channels);
      setDiscoveredVods(res.vods);
      notify(
        res.added_count > 0
          ? `Found ${res.added_count} fresh unclipped VOD from watched channels.`
          : 'All watched channels are up to date.'
      );
    } finally {
      setScanningStreams(false);
    }
  };

  const handleSendVodToCreate = (vod: DiscoveredVod) => {
    setCreateUrl(vod.url);
    setCreateRange(vod.suggested_range);
    setActiveView('create');
    notify(`Pre-filled ${vod.streamer_name}'s VOD in Create.`);
    setTimeout(() => urlInputRef.current?.focus(), 60);
  };

  const handleLearnAnalytics = async () => {
    setLearningAnalytics(true);
    try {
      const updated = await api.learnFromAnalytics();
      setViralDna(updated);
      notify('Updated Viral DNA scores & learned_rules.md from 24h/48h/72h analytics.');
    } finally {
      setLearningAnalytics(false);
    }
  };

  const handleCloneWinners = async () => {
    setCloningWinners(true);
    try {
      const res = await api.cloneWinners();
      const q = await api.getJobQueue();
      setClips(q);
      setSelectedClipId(res.created_clip.clip_id);
      notify(res.message);
    } finally {
      setCloningWinners(false);
    }
  };

  const handleSaveOnboarding = async (patch: Partial<OnboardingState>) => {
    const updated = await api.saveOnboardingKeys(patch);
    setOnboarding(updated);
  };

  return (
    <div className="flex min-h-screen bg-[#09090B] text-[#FAFAFA]">
      <Sidebar
        activeView={activeView}
        onSelectView={setActiveView}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed((v) => !v)}
        mobileOpen={mobileNavOpen}
        onCloseMobile={() => setMobileNavOpen(false)}
        queuedCount={queuedCount}
        unclippedVodsCount={discoveredVods.length}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar
          activePreset={activePreset}
          presets={presets}
          onSwitchPreset={handleActivatePreset}
          onOpenCommandPalette={() => setCommandOpen(true)}
          onOpenLiveUrlsDrawer={() => setLiveUrlsOpen(true)}
          pendingLiveUrlsCount={pendingLiveUrlsCount}
          backendReachable={health.backendReachable}
          onRefreshHealth={handleRefreshHealth}
          onOpenMobileNav={() => setMobileNavOpen(true)}
        />

        <main className="flex-1 min-w-0">
          {activeView === 'create' && (
            <CreateView
              url={createUrl}
              onUrlChange={setCreateUrl}
              timestampRange={createRange}
              onTimestampRangeChange={setCreateRange}
              presets={presets}
              activePresetId={activePreset?.id ?? ''}
              onSelectPreset={handleActivatePreset}
              clips={clips}
              activeJob={activeJob}
              onStartPlanJob={handleStartPlanJob}
              onRenderClip={handleRenderClip}
              onReviewClip={handleReviewClip}
              onSkipClip={handleSkipClip}
              urlInputRef={urlInputRef}
            />
          )}

          {activeView === 'studio' && activePreset && (
            <StudioView
              clips={clips}
              selectedClipId={selectedClipId}
              onSelectClip={setSelectedClipId}
              activePreset={activePreset}
              onUpdateClip={handleUpdateClipDraft}
              onApproveAndSchedule={handleApproveAndSchedule}
            />
          )}

          {activeView === 'live-hunt' && (
            <LiveHuntView
              channels={watchedChannels}
              vods={discoveredVods}
              scanning={scanningStreams}
              onAddChannel={(ch) => {
                setWatchedChannels((prev) => [ch, ...prev]);
                notify(`Added ${ch.name} (${ch.platform}) to watched channels.`);
              }}
              onRemoveChannel={(id) =>
                setWatchedChannels((prev) => prev.filter((c) => c.id !== id))
              }
              onScanStreams={handleScanStreams}
              onSendToCreate={handleSendVodToCreate}
            />
          )}

          {activeView === 'presets' && (
            <PresetsView
              presets={presets}
              onActivatePreset={handleActivatePreset}
              onCreatePreset={handleCreatePreset}
            />
          )}

          {activeView === 'viral-dna' && (
            <ViralDnaView
              data={viralDna}
              learning={learningAnalytics}
              cloning={cloningWinners}
              onLearnAnalytics={handleLearnAnalytics}
              onCloneWinners={handleCloneWinners}
            />
          )}

          {activeView === 'setup' && (
            <SetupGuideView
              health={health}
              onboarding={onboarding}
              presets={presets}
              onSaveOnboarding={handleSaveOnboarding}
              onRecheckTools={async () => {
                const h = await api.getHealth();
                setHealth(h);
                notify('Verified local toolchain (Python, FFmpeg, yt-dlp, Whisper).');
              }}
              onActivatePreset={handleActivatePreset}
              onNotify={notify}
            />
          )}
        </main>
      </div>

      {/* Quick Command Palette (Ctrl+K) */}
      <CommandPalette
        open={commandOpen}
        onClose={() => setCommandOpen(false)}
        presets={presets}
        onNavigate={setActiveView}
        onFocusPasteUrl={() => {
          setActiveView('create');
          setTimeout(() => urlInputRef.current?.focus(), 60);
        }}
        onCheckNewStreams={() => {
          setActiveView('live-hunt');
          void handleScanStreams();
        }}
        onOpenLiveUrls={() => setLiveUrlsOpen(true)}
        onLearnAnalytics={() => {
          setActiveView('viral-dna');
          void handleLearnAnalytics();
        }}
        onSwitchCampaign={handleActivatePreset}
      />

      {/* Slide-Over Drawer: Live URLs for Whop */}
      <WhopLiveUrlsDrawer
        open={liveUrlsOpen}
        onClose={() => setLiveUrlsOpen(false)}
        items={liveUrls}
        onRefresh={handleRefreshLiveUrls}
        onToggleSubmitted={handleToggleUrlSubmitted}
        refreshing={refreshingUrls}
      />

      {/* Subtle Bottom-Right Toast */}
      {toast && (
        <div
          role="status"
          aria-live="polite"
          className="fixed bottom-5 right-5 z-50 max-w-sm rounded-lg border border-white/[0.12] bg-[#111113]/95 backdrop-blur-md px-4 py-2.5 text-xs font-medium text-[#FAFAFA] shadow-lg"
        >
          {toast}
        </div>
      )}
    </div>
  );
}
