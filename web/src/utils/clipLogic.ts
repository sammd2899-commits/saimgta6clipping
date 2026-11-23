import type {
  CampaignPreset,
  ClipJob,
  ComplianceReport,
  DiscoveredVod,
} from '../types/studio';

export interface JobInputValidation {
  valid: boolean;
  error: string | null;
  platform: 'YouTube' | 'Twitch' | 'Kick' | null;
}

const TIMESTAMP_PART = /^(?:\d{1,2}:)?[0-5]?\d:[0-5]\d$/;

export function validateJobInput(
  url: string,
  timestampRange: string,
  clipCount: number
): JobInputValidation {
  const trimmedUrl = url.trim();
  if (!trimmedUrl) {
    return { valid: false, error: 'Paste a YouTube, Twitch, or Kick VOD URL to start.', platform: null };
  }

  let parsed: URL;
  try {
    parsed = new URL(trimmedUrl);
  } catch {
    return { valid: false, error: 'Enter a valid URL starting with https://', platform: null };
  }

  const host = parsed.hostname.toLowerCase();
  let platform: 'YouTube' | 'Twitch' | 'Kick' | null = null;
  if (host.includes('youtube.com') || host.includes('youtu.be')) {
    platform = 'YouTube';
  } else if (host.includes('twitch.tv')) {
    platform = 'Twitch';
  } else if (host.includes('kick.com')) {
    platform = 'Kick';
  }

  if (!platform) {
    return {
      valid: false,
      error: 'Supported sources are YouTube, Twitch, and Kick URLs.',
      platform: null,
    };
  }

  const trimmedRange = timestampRange.trim();
  if (trimmedRange) {
    const parts = trimmedRange.split('-').map((p) => p.trim());
    if (parts.length !== 2 || !TIMESTAMP_PART.test(parts[0]) || !TIMESTAMP_PART.test(parts[1])) {
      return {
        valid: false,
        error: 'Timestamp range must look like 1:10:00-1:40:00 or 12:30-18:45.',
        platform,
      };
    }
    if (parseTimestampToSec(parts[1]) <= parseTimestampToSec(parts[0])) {
      return {
        valid: false,
        error: 'End timestamp must be later than the start timestamp.',
        platform,
      };
    }
  }

  if (!Number.isInteger(clipCount) || clipCount < 1 || clipCount > 10) {
    return {
      valid: false,
      error: 'Clip count must be between 1 and 10.',
      platform,
    };
  }

  return { valid: true, error: null, platform };
}

export function parseTimestampToSec(ts: string): number {
  const segments = ts.split(':').map((n) => Number(n));
  if (segments.some((n) => Number.isNaN(n))) return 0;
  if (segments.length === 3) {
    return segments[0] * 3600 + segments[1] * 60 + segments[2];
  }
  if (segments.length === 2) {
    return segments[0] * 60 + segments[1];
  }
  return segments[0] ?? 0;
}

export function formatSecToTimestamp(totalSec: number): string {
  const safe = Math.max(0, Math.floor(totalSec));
  const h = Math.floor(safe / 3600);
  const m = Math.floor((safe % 3600) / 60);
  const s = safe % 60;
  if (h > 0) {
    return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

export function validateClipCompliance(
  clip: Pick<
    ClipJob,
    | 'yt_title'
    | 'hashtags'
    | 'not_made_for_kids'
    | 'comments_enabled'
    | 'logo_duration_pct'
    | 'logo_aspect_locked'
    | 'logo_zero_overlap'
  >,
  preset: Pick<CampaignPreset, 'required_hashtags' | 'max_ig_hashtags'>
): ComplianceReport {
  const normalizedTags = clip.hashtags.map((t) => t.trim().toLowerCase());
  const missingRequired = preset.required_hashtags.filter(
    (req) => !normalizedTags.includes(req.trim().toLowerCase())
  );

  const requiredTagsPassed = missingRequired.length === 0;
  const igLimitPassed = clip.hashtags.length <= preset.max_ig_hashtags && clip.hashtags.length > 0;
  const ytTitlePassed = clip.yt_title.trim().length > 0 && clip.yt_title.trim().length <= 65;
  const logoPassed =
    clip.logo_duration_pct === 100 && clip.logo_aspect_locked && clip.logo_zero_overlap;

  const checks = [
    {
      id: 'required-tags',
      label: preset.required_hashtags.join(' '),
      passed: requiredTagsPassed,
      detail: requiredTagsPassed
        ? 'Required campaign tags present'
        : `Missing ${missingRequired.join(', ')}`,
    },
    {
      id: 'ig-tag-cap',
      label: `IG ≤ ${preset.max_ig_hashtags} tags`,
      passed: igLimitPassed,
      detail: `${clip.hashtags.length}/${preset.max_ig_hashtags} tags configured`,
    },
    {
      id: 'yt-title',
      label: 'YT Title ≤ 65 chars',
      passed: ytTitlePassed,
      detail: `${clip.yt_title.trim().length}/65 characters`,
    },
    {
      id: 'not-kids',
      label: 'Not Made for Kids',
      passed: clip.not_made_for_kids,
      detail: clip.not_made_for_kids ? 'Adult/general audience flag set' : 'Required for Reels/Shorts discovery',
    },
    {
      id: 'comments-on',
      label: 'Comments ON',
      passed: clip.comments_enabled,
      detail: clip.comments_enabled ? 'Engagement replies enabled' : 'Enable comments before scheduling',
    },
    {
      id: 'logo-integrity',
      label: 'Logo 100% / No Overlap',
      passed: logoPassed,
      detail: logoPassed ? '100% duration · Exact aspect ratio · Zero overlap' : 'Check campaign logo placement',
    },
  ];

  return {
    allPassed: checks.every((c) => c.passed),
    checks,
  };
}

export function rankQueueClips(clips: ClipJob[]): ClipJob[] {
  return [...clips].sort((a, b) => {
    if (b.predicted_viral_score !== a.predicted_viral_score) {
      return b.predicted_viral_score - a.predicted_viral_score;
    }
    return a.clip_number - b.clip_number;
  });
}

export function computeVodCompositeScore(vod: DiscoveredVod): number {
  // Recency favors fresher VODs (< 24h), velocity scales log-wise, streamer score weighs heavily
  const recencyScore = Math.max(0, 100 - vod.published_hours_ago * 3.5);
  const velocityScore = Math.min(100, Math.round((vod.views_per_hour / 2800) * 100));
  return Math.round(
    recencyScore * 0.3 + velocityScore * 0.35 + vod.learned_streamer_score * 0.35
  );
}

export function rankDiscoveredVods(vods: DiscoveredVod[]): DiscoveredVod[] {
  return [...vods].sort(
    (a, b) => computeVodCompositeScore(b) - computeVodCompositeScore(a)
  );
}

export interface ParsedWhopBrief {
  name: string;
  required_hashtags: string[];
  max_ig_hashtags: number;
  retention_days: number;
  target_countries: string[];
  min_views_unlock: number;
  cpm_rate: string;
}

export function parseWhopBrief(rawText: string): ParsedWhopBrief {
  const clean = rawText.trim();

  // Extract campaign title from first non-empty line
  const firstLine = clean.split('\n').map((l) => l.trim()).find(Boolean) ?? 'Untitled Whop Campaign';
  const name = firstLine
    .replace(/^(campaign|brief|whop)\s*[:\-]\s*/i, '')
    .slice(0, 48);

  // Extract hashtags
  const tagMatches = clean.match(/#[a-zA-Z0-9_]+/g) ?? [];
  const uniqueTags = Array.from(new Set(tagMatches));
  const required_hashtags = uniqueTags.length > 0 ? uniqueTags.slice(0, 4) : ['#gta6', '#Clipup'];

  // Max IG hashtags
  const igCapMatch = clean.match(/(?:max|<=|≤|up to)\s*(\d+)\s*(?:ig|instagram)?\s*(?:tags|hashtags)/i);
  const max_ig_hashtags = igCapMatch ? Math.min(10, Math.max(1, Number(igCapMatch[1]))) : 5;

  // Retention days
  const retentionMatch = clean.match(/(\d+)\s*(?:-|\s)?days?\s*(?:retention|live|stay|keep)/i)
    ?? clean.match(/(?:keep|stay live|retain)\s*(?:for\s*)?(\d+)\s*days?/i);
  const retention_days = retentionMatch ? Number(retentionMatch[1]) : 30;

  // Min views payout unlock
  const viewsMatch = clean.match(/(\d+(?:\.\d+)?)\s*k\s*(?:views|min|unlock|minimum)/i);
  const min_views_unlock = viewsMatch ? Math.round(Number(viewsMatch[1]) * 1000) : 3000;

  // CPM rate
  const cpmMatch = clean.match(/\$\d+(?:\.\d+)?\s*(?:\/\s*1k|per\s*1k|cpm)/i);
  const cpm_rate = cpmMatch ? cpmMatch[0].replace(/\s+/g, ' ').trim() : '$1.50 / 1K';

  // Target Tier-1 countries
  const countryCandidates: Array<[RegExp, string]> = [
    [/\b(US|USA|United States)\b/i, 'US'],
    [/\b(UK|United Kingdom)\b/i, 'UK'],
    [/\b(CA|Canada)\b/i, 'CA'],
    [/\b(AU|Australia)\b/i, 'AU'],
    [/\b(DE|Germany)\b/i, 'DE'],
  ];
  const matchedCountries = countryCandidates
    .filter(([rx]) => rx.test(clean))
    .map(([, code]) => code);
  const target_countries = matchedCountries.length > 0 ? matchedCountries : ['US', 'UK', 'CA', 'AU'];

  return {
    name,
    required_hashtags,
    max_ig_hashtags,
    retention_days,
    target_countries,
    min_views_unlock,
    cpm_rate,
  };
}

export interface WhopCountdown {
  remainingSeconds: number;
  formatted: string;
  urgent: boolean;
  expired: boolean;
}

export function formatWhopCountdown(publishedAtIso: string, nowMs: number = Date.now()): WhopCountdown {
  const publishedMs = new Date(publishedAtIso).getTime();
  const windowMs = 30 * 60 * 1000;
  const remainingMs = Math.max(0, publishedMs + windowMs - nowMs);
  const remainingSeconds = Math.floor(remainingMs / 1000);
  const mins = Math.floor(remainingSeconds / 60);
  const secs = remainingSeconds % 60;
  const formatted = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;

  return {
    remainingSeconds,
    formatted,
    urgent: remainingSeconds > 0 && remainingSeconds <= 600,
    expired: remainingSeconds === 0,
  };
}

export function convertIstSlotToUtc(istTime: string): string {
  // Expected format: "HH:MM" in 24h IST (UTC+5:30)
  const match = istTime.trim().match(/^(\d{1,2}):(\d{2})$/);
  if (!match) return '--:-- UTC';
  const hours = Number(match[1]);
  const minutes = Number(match[2]);
  let totalMinutes = hours * 60 + minutes - (5 * 60 + 30);
  if (totalMinutes < 0) totalMinutes += 24 * 60;
  const utcH = Math.floor(totalMinutes / 60) % 24;
  const utcM = totalMinutes % 60;
  return `${String(utcH).padStart(2, '0')}:${String(utcM).padStart(2, '0')} UTC`;
}

export function formatCompactNumber(num: number): string {
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
  return String(num);
}
