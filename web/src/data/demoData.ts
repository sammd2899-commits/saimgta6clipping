import type {
  CampaignPreset,
  ClipJob,
  DiscoveredVod,
  HealthStatus,
  IstSlotOption,
  LiveUrlItem,
  OnboardingState,
  ViralDnaData,
  WatchedChannel,
} from '../types/studio';

export const ASSETS = {
  facecam: '/src/assets/images/studio_facecam_streamer_1795398567151.jpg',
  gameplayVertical: '/src/assets/images/studio_gameplay_vice_1795398558600.jpg',
  vodChase: '/src/assets/images/vod_thumb_chase_1795398562021.jpg',
  vodNpc: '/src/assets/images/vod_thumb_npc_1795398559170.jpg',
};

export const IST_SLOTS: IstSlotOption[] = [
  {
    id: 'slot-1930',
    ist: '19:30 IST',
    utc: '14:00 UTC',
    regionLabel: 'UK Afternoon · US Morning',
    peakScore: 96,
  },
  {
    id: 'slot-2130',
    ist: '21:30 IST',
    utc: '16:00 UTC',
    regionLabel: 'US East Lunch · UK Prime',
    peakScore: 93,
  },
  {
    id: 'slot-2330',
    ist: '23:30 IST',
    utc: '18:00 UTC',
    regionLabel: 'US Afternoon Peak',
    peakScore: 89,
  },
  {
    id: 'slot-0130',
    ist: '01:30 IST',
    utc: '20:00 UTC',
    regionLabel: 'US Evening · CA Prime',
    peakScore: 91,
  },
  {
    id: 'slot-0430',
    ist: '04:30 IST',
    utc: '23:00 UTC',
    regionLabel: 'US West Night · AU Morning',
    peakScore: 82,
  },
];

export const INITIAL_PRESETS: CampaignPreset[] = [];

export const INITIAL_HEALTH: HealthStatus = {
  mode: 'local',
  backendReachable: false,
  activeCampaignId: '',
  activeCampaignName: 'Connecting...',
  tools: [],
};

export const INITIAL_CLIPS: ClipJob[] = [];

export function createInitialLiveUrls(): LiveUrlItem[] {
  return [];
}

export const INITIAL_WATCHED_CHANNELS: WatchedChannel[] = [];

export const INITIAL_DISCOVERED_VODS: DiscoveredVod[] = [];

export const INITIAL_VIRAL_DNA: ViralDnaData = {
  last_learned_at: 'No analytics synced yet',
  window_label: 'Pending Sync',
  kpis: {
    total_views: '0',
    total_views_delta: '0%',
    avg_engagement_pct: '0%',
    engagement_delta: '0 pts',
    payout_unlocks_3k: 0,
    payout_delta: '0',
    best_ist_slot: '18:00 IST',
    best_slot_region: 'Peak slot (UK/US)',
  },
  archetypes: [],
  duration_sweet_spot: [],
  top_streamers: [],
  ig_retention: [],
  learned_rules: {
    do_rules: [],
    do_not_rules: [],
  },
};

export const INITIAL_ONBOARDING: OnboardingState = {
  completed_steps: [],
  brand_name: '',
  channel_handle: '',
  zernio_api_key: '',
  gemini_api_key: '',
  discovered_accounts: [],
  default_ist_slot: '18:00 IST',
  ig_checklist: {
    professional_account: false,
    two_factor_enabled: false,
    music_rights_cleared: false,
  },
  yt_checklist: {
    advanced_features_verified: false,
    not_made_for_kids_default: false,
    comments_enabled_default: false,
  },
  optional_integrations: {
    telegram_bot_token: '',
    telegram_chat_id: '',
    telegram_verified: false,
    cloudflare_tunnel_url: '',
    mcp_server_enabled: false,
    earshot_sfx_enabled: false,
  },
};
