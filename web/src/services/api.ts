import {
  INITIAL_HEALTH,
  INITIAL_VIRAL_DNA,
  INITIAL_ONBOARDING,
} from '../data/demoData';
import type {
  BrandKitResult,
  CampaignPreset,
  ClipJob,
  DiscoveredVod,
  HealthStatus,
  LiveUrlItem,
  OnboardingState,
  ViralDnaData,
  WatchedChannel,
} from '../types/studio';
import { rankDiscoveredVods, rankQueueClips } from '../utils/clipLogic';

const BASE_URL = typeof window !== 'undefined' && (window.location.port === '8765' || window.location.origin.includes('8765'))
  ? '/api'
  : 'http://127.0.0.1:8765/api';

const REQUEST_TIMEOUT_MS = 6000;

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers ?? {}),
      },
      signal: controller.signal,
    });
    clearTimeout(timer);
    if (!res.ok) {
      const errText = await res.text().catch(() => res.statusText);
      throw new Error(`API error ${res.status}: ${errText}`);
    }
    return (await res.json()) as T;
  } catch (err) {
    clearTimeout(timer);
    throw err;
  }
}

export function getApiMode(): 'local' {
  return 'local';
}

export function setApiMode(): 'local' {
  return 'local';
}

export async function getHealth(): Promise<HealthStatus> {
  try {
    const data = await request<HealthStatus>('/health');
    return { ...data, mode: 'local', backendReachable: true };
  } catch {
    return {
      ...structuredClone(INITIAL_HEALTH),
      mode: 'local',
      backendReachable: false,
    };
  }
}

export interface PlanJobPayload {
  url: string;
  timestamp_range?: string;
  clip_count: number;
  preset_id: string;
  one_clip_approval: boolean;
}

export async function planJob(payload: PlanJobPayload): Promise<{
  job_id: string;
  new_clips: ClipJob[];
  logs: string[];
}> {
  return await request<{ job_id: string; new_clips: ClipJob[]; logs: string[] }>(
    '/jobs/plan',
    {
      method: 'POST',
      body: JSON.stringify(payload),
    }
  );
}

export async function getJobQueue(): Promise<ClipJob[]> {
  try {
    const data = await request<ClipJob[]>('/jobs/queue');
    return rankQueueClips(data ?? []);
  } catch {
    return [];
  }
}

export async function renderClip(clipId: string): Promise<ClipJob | null> {
  try {
    return await request<ClipJob>(`/jobs/${clipId}/render`, { method: 'POST' });
  } catch {
    return null;
  }
}

export async function skipClip(clipId: string): Promise<ClipJob | null> {
  // Local status toggle on client if offline
  return null;
}

export async function updateClipDraft(updated: ClipJob): Promise<ClipJob> {
  return structuredClone(updated);
}

export async function scheduleClip(
  clipId: string,
  payload: { ist_slot: string; clip: ClipJob }
): Promise<{ clip: ClipJob; live_url_item: LiveUrlItem }> {
  return await request<{ clip: ClipJob; live_url_item: LiveUrlItem }>(
    `/jobs/${clipId}/schedule`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    }
  );
}

export async function getLiveUrls(): Promise<LiveUrlItem[]> {
  try {
    const data = await request<LiveUrlItem[]>('/live-urls');
    return data ?? [];
  } catch {
    return [];
  }
}

export async function markLiveUrlSubmitted(clipId: string): Promise<LiveUrlItem[]> {
  try {
    return await request<LiveUrlItem[]>(`/live-urls/${clipId}/mark-submitted`, {
      method: 'POST',
    });
  } catch {
    return [];
  }
}

export async function getVodStreams(): Promise<{
  channels: WatchedChannel[];
  vods: DiscoveredVod[];
}> {
  try {
    const data = await request<{ channels: WatchedChannel[]; vods: DiscoveredVod[] }>(
      '/vod-watcher/streams'
    );
    return {
      channels: data?.channels ?? [],
      vods: rankDiscoveredVods(data?.vods ?? []),
    };
  } catch {
    return { channels: [], vods: [] };
  }
}

export async function scanVodStreams(
  channels: WatchedChannel[]
): Promise<{ channels: WatchedChannel[]; vods: DiscoveredVod[]; added_count: number }> {
  return await request<{
    channels: WatchedChannel[];
    vods: DiscoveredVod[];
    added_count: number;
  }>('/vod-watcher/scan', {
    method: 'POST',
    body: JSON.stringify({ channels }),
  });
}

export async function getPresets(): Promise<CampaignPreset[]> {
  try {
    const data = await request<CampaignPreset[]>('/presets');
    return data ?? [];
  } catch {
    return [];
  }
}

export async function createPreset(
  preset: Omit<CampaignPreset, 'id' | 'active'>
): Promise<CampaignPreset[]> {
  return await request<CampaignPreset[]>('/presets', {
    method: 'POST',
    body: JSON.stringify(preset),
  });
}

export async function activatePreset(presetId: string): Promise<CampaignPreset[]> {
  return await request<CampaignPreset[]>('/presets/activate', {
    method: 'POST',
    body: JSON.stringify({ preset_id: presetId }),
  });
}

export async function getViralDna(): Promise<ViralDnaData> {
  try {
    const data = await request<ViralDnaData>('/analytics/dna');
    return data ?? structuredClone(INITIAL_VIRAL_DNA);
  } catch {
    return structuredClone(INITIAL_VIRAL_DNA);
  }
}

export async function learnFromAnalytics(): Promise<ViralDnaData> {
  return await request<ViralDnaData>('/analytics/learn', { method: 'POST' });
}

export async function cloneWinners(): Promise<{
  created_clip: ClipJob;
  message: string;
}> {
  return await request<{ created_clip: ClipJob; message: string }>(
    '/analytics/clone-winners',
    { method: 'POST' }
  );
}

export async function getOnboardingState(): Promise<OnboardingState> {
  try {
    const data = await request<OnboardingState>('/onboarding/state');
    return data ?? structuredClone(INITIAL_ONBOARDING);
  } catch {
    return structuredClone(INITIAL_ONBOARDING);
  }
}

export async function saveOnboardingKeys(
  patch: Partial<OnboardingState>
): Promise<OnboardingState> {
  return await request<OnboardingState>('/onboarding/save-keys', {
    method: 'POST',
    body: JSON.stringify(patch),
  });
}

export interface GenerateBrandKitPayload {
  platform: 'instagram' | 'youtube' | 'both';
  brand_name?: string;
  niche?: string;
}

export async function generateBrandKit(
  payload: GenerateBrandKitPayload
): Promise<BrandKitResult> {
  return await request<BrandKitResult>('/onboarding/generate-brand-kit', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
