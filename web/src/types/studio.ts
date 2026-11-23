export type AppView =
  | 'create'
  | 'studio'
  | 'live-hunt'
  | 'presets'
  | 'viral-dna'
  | 'setup';

export type ApiMode = 'demo' | 'local';

export type ClipStatus = 'queued' | 'rendering' | 'ready' | 'scheduled' | 'skipped' | 'error';

export type MomentArchetype =
  | 'NPC AI'
  | 'Crash Physics'
  | 'Police Chase'
  | 'Instant Fail'
  | 'Map Secret';

export type AbVariant = '80% Proven' | '20% Experimental';

export type LayoutMode = 'split-35-65' | 'blurred-fill';

export type CaptionStyle = 'word-yellow' | 'clean-white' | 'bold-outline';

export type JobStageId = 'download' | 'transcribe' | 'edit' | 'schedule';

export interface ToolCheck {
  name: 'Python' | 'FFmpeg' | 'yt-dlp' | 'Whisper' | 'Zernio';
  installed: boolean;
  version: string;
  detail: string;
}

export interface HealthStatus {
  mode: ApiMode;
  backendReachable: boolean;
  activeCampaignId: string;
  activeCampaignName: string;
  tools: ToolCheck[];
}

export interface CaptionWord {
  word: string;
  startSec: number;
  endSec: number;
}

export interface ClipJob {
  clip_id: string;
  clip_number: number;
  source_url: string;
  source_streamer: string;
  timestamp_start: string;
  timestamp_end: string;
  duration_sec: number;
  trim_start_sec: number;
  trim_end_sec: number;
  predicted_viral_score: number;
  archetype: MomentArchetype;
  ab_variant: AbVariant;
  status: ClipStatus;
  yt_title: string;
  ai_title_ideas: string[];
  ig_caption: string;
  dm_share_trigger: string;
  hashtags: string[];
  first_comment: string;
  not_made_for_kids: boolean;
  comments_enabled: boolean;
  hook_banner_text: string;
  hook_banner_y: number; // percentage 8 - 32
  layout_mode: LayoutMode;
  caption_style: CaptionStyle;
  logo_duration_pct: number;
  logo_aspect_locked: boolean;
  logo_zero_overlap: boolean;
  scheduled_ist_slot: string | null;
  transcript_words: CaptionWord[];
  audio_peaks: number[]; // 0..1 normalized waveform peaks
  facecam_image: string;
  gameplay_image: string;
  video_url?: string;
  thumbnail?: string;
}

export interface ActiveJobProgress {
  job_id: string;
  source_url: string;
  current_stage: JobStageId;
  completed_stages: JobStageId[];
  progress_pct: number;
  logs: string[];
  active: boolean;
}

export interface LiveUrlItem {
  clip_id: string;
  title: string;
  campaign_name: string;
  ig_reel_url: string;
  yt_short_url: string;
  published_at: string; // ISO timestamp
  submitted: boolean;
}

export interface WatchedChannel {
  id: string;
  name: string;
  platform: 'YouTube' | 'Twitch' | 'Kick';
  url: string;
  learned_score: number;
}

export interface DiscoveredVod {
  id: string;
  streamer_name: string;
  platform: 'YouTube' | 'Twitch' | 'Kick';
  title: string;
  url: string;
  duration: string;
  published_hours_ago: number;
  views: number;
  views_per_hour: number;
  learned_streamer_score: number;
  suggested_range: string;
  thumbnail: string;
  clipped: boolean;
}

export interface ReferenceStyleProfile {
  pacing?: string;
  hook_style?: string;
  caption_tone?: string;
  layout?: string;
  clip_archetype?: string;
  extracted_keywords?: string[];
  summary?: string;
  reference_count?: number;
}

export interface CampaignPreset {
  id: string;
  name: string;
  whop_handle: string;
  active: boolean;
  required_hashtags: string[];
  max_ig_hashtags: number;
  retention_days: number;
  target_countries: string[];
  min_views_unlock: number;
  cpm_rate: string;
  logo_label: string;
  logo_accent: string;
  logo_data_url?: string;
  raw_brief?: string;
  references?: string[];
  reference_style_profile?: ReferenceStyleProfile;
}

export interface ScoreBarMetric {
  label: string;
  score: number; // 0..100
  detail: string;
  highlight?: boolean;
}

export interface ViralDnaData {
  last_learned_at: string;
  window_label: string;
  kpis: {
    total_views: string;
    total_views_delta: string;
    avg_engagement_pct: string;
    engagement_delta: string;
    payout_unlocks_3k: number;
    payout_delta: string;
    best_ist_slot: string;
    best_slot_region: string;
  };
  archetypes: ScoreBarMetric[];
  duration_sweet_spot: ScoreBarMetric[];
  top_streamers: ScoreBarMetric[];
  ig_retention: ScoreBarMetric[];
  learned_rules: {
    do_rules: string[];
    do_not_rules: string[];
  };
}

export interface ZernioAccount {
  id: string;
  platform: 'Instagram' | 'YouTube';
  handle: string;
  status: 'connected' | 'needs-reauth';
}

export interface BrandKitResult {
  brand_name: string;
  handles: string[];
  bio: string;
  keywords: string[];
  hashtags: string[];
  platform: 'instagram' | 'youtube';
  guide_title: string;
  guide_steps: string[];
  saved_to: string;
}

export interface OnboardingState {
  completed_steps: string[];
  brand_name: string;
  channel_handle: string;
  zernio_api_key: string;
  gemini_api_key?: string;
  discovered_accounts: ZernioAccount[];
  default_ist_slot: string;
  ig_checklist: {
    professional_account: boolean;
    two_factor_enabled: boolean;
    music_rights_cleared: boolean;
  };
  yt_checklist: {
    advanced_features_verified: boolean;
    not_made_for_kids_default: boolean;
    comments_enabled_default: boolean;
  };
  optional_integrations: {
    telegram_bot_token: string;
    telegram_chat_id: string;
    telegram_verified: boolean;
    cloudflare_tunnel_url: string;
    mcp_server_enabled: boolean;
    earshot_sfx_enabled: boolean;
  };
}

export interface IstSlotOption {
  id: string;
  ist: string;
  utc: string;
  regionLabel: string;
  peakScore: number;
}

export interface ComplianceCheckItem {
  id: string;
  label: string;
  passed: boolean;
  detail: string;
}

export interface ComplianceReport {
  allPassed: boolean;
  checks: ComplianceCheckItem[];
}
