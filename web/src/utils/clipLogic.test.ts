import test from 'node:test';
import assert from 'node:assert/strict';
import {
  validateJobInput,
  validateClipCompliance,
  rankQueueClips,
  rankDiscoveredVods,
  parseWhopBrief,
  formatWhopCountdown,
  convertIstSlotToUtc,
} from './clipLogic';
import type { ClipJob, DiscoveredVod } from '../types/studio';

test('validateJobInput rejects empty or unsupported URLs and accepts Twitch/YouTube/Kick', () => {
  assert.equal(validateJobInput('', '', 5).valid, false);
  assert.equal(validateJobInput('https://example.com/video', '', 5).valid, false);

  const yt = validateJobInput('https://www.youtube.com/watch?v=abc123', '1:10:00-1:40:00', 5);
  assert.equal(yt.valid, true);
  assert.equal(yt.platform, 'YouTube');

  const kick = validateJobInput('https://kick.com/video/9988', '', 10);
  assert.equal(kick.valid, true);
  assert.equal(kick.platform, 'Kick');

  // Invalid range where end <= start
  assert.equal(validateJobInput('https://twitch.tv/videos/123', '1:40:00-1:10:00', 5).valid, false);
  // Out of bounds clip count
  assert.equal(validateJobInput('https://twitch.tv/videos/123', '', 12).valid, false);
});

test('validateClipCompliance enforces required hashtags, IG tag cap, YT 65 char title, and flags', () => {
  const preset = { required_hashtags: ['#gta6', '#Clipup'], max_ig_hashtags: 5 };

  const passing = validateClipCompliance(
    {
      yt_title: 'Vice City Cop AI Just Broke Physics Mid-Chase',
      hashtags: ['#gta6', '#Clipup', '#gtavi', '#gaming'],
      not_made_for_kids: true,
      comments_enabled: true,
      logo_duration_pct: 100,
      logo_aspect_locked: true,
      logo_zero_overlap: true,
    },
    preset
  );
  assert.equal(passing.allPassed, true);

  const failing = validateClipCompliance(
    {
      yt_title: 'This YouTube Shorts Title Is Intentionally Way Too Long Over Sixty Five Characters',
      hashtags: ['#gta6', '#tag2', '#tag3', '#tag4', '#tag5', '#tag6'],
      not_made_for_kids: false,
      comments_enabled: true,
      logo_duration_pct: 100,
      logo_aspect_locked: true,
      logo_zero_overlap: true,
    },
    preset
  );
  assert.equal(failing.allPassed, false);
  assert.equal(failing.checks.find((c) => c.id === 'required-tags')?.passed, false);
  assert.equal(failing.checks.find((c) => c.id === 'ig-tag-cap')?.passed, false);
  assert.equal(failing.checks.find((c) => c.id === 'yt-title')?.passed, false);
  assert.equal(failing.checks.find((c) => c.id === 'not-kids')?.passed, false);
});

test('rankQueueClips sorts strictly descending by predicted_viral_score', () => {
  const clips = [
    { clip_id: 'a', clip_number: 1, predicted_viral_score: 74 },
    { clip_id: 'b', clip_number: 2, predicted_viral_score: 94 },
    { clip_id: 'c', clip_number: 3, predicted_viral_score: 88 },
  ] as ClipJob[];

  const ranked = rankQueueClips(clips);
  assert.deepEqual(
    ranked.map((c) => c.clip_id),
    ['b', 'c', 'a']
  );
});

test('rankDiscoveredVods ranks fresher high-velocity high-score VODs first', () => {
  const vods: DiscoveredVod[] = [
    {
      id: 'old',
      streamer_name: 'OldStream',
      platform: 'Twitch',
      title: 'Old VOD',
      url: 'https://twitch.tv/videos/1',
      duration: '3h',
      published_hours_ago: 22,
      views: 15000,
      views_per_hour: 680,
      learned_streamer_score: 65,
      suggested_range: '0:15:00-0:45:00',
      thumbnail: '',
      clipped: false,
    },
    {
      id: 'hot',
      streamer_name: 'HotStream',
      platform: 'Twitch',
      title: 'Hot VOD',
      url: 'https://twitch.tv/videos/2',
      duration: '2h',
      published_hours_ago: 2,
      views: 6400,
      views_per_hour: 3200,
      learned_streamer_score: 95,
      suggested_range: '1:05:00-1:35:00',
      thumbnail: '',
      clipped: false,
    },
  ];
  const ranked = rankDiscoveredVods(vods);
  assert.equal(ranked[0].id, 'hot');
});

test('parseWhopBrief extracts hashtags, retention days, countries, and CPM from raw text', () => {
  const raw = `
    GTA 6 Launch Clipup Bounty
    Must include #gta6 #Clipup #ViceCity in caption. Max 4 IG tags.
    Keep clips live for 45 days retention. Payout unlocks at 5k views ($2.20 / 1K).
    Tier-1 audience focus: US, UK, Canada, Australia.
  `;
  const parsed = parseWhopBrief(raw);
  assert.equal(parsed.name, 'GTA 6 Launch Clipup Bounty');
  assert.deepEqual(parsed.required_hashtags, ['#gta6', '#Clipup', '#ViceCity']);
  assert.equal(parsed.max_ig_hashtags, 4);
  assert.equal(parsed.retention_days, 45);
  assert.equal(parsed.min_views_unlock, 5000);
  assert.equal(parsed.cpm_rate, '$2.20 / 1K');
  assert.deepEqual(parsed.target_countries, ['US', 'UK', 'CA', 'AU']);
});

test('formatWhopCountdown accurately computes 30-min submission window and urgency', () => {
  const base = Date.UTC(2026, 10, 22, 12, 0, 0);
  const iso = new Date(base).toISOString();

  // 22m 15s elapsed -> 07m 45s remaining -> urgent
  const urgentCheck = formatWhopCountdown(iso, base + (22 * 60 + 15) * 1000);
  assert.equal(urgentCheck.formatted, '07:45');
  assert.equal(urgentCheck.urgent, true);
  assert.equal(urgentCheck.expired, false);

  // 35m elapsed -> 00:00 expired
  const expiredCheck = formatWhopCountdown(iso, base + 35 * 60 * 1000);
  assert.equal(expiredCheck.formatted, '00:00');
  assert.equal(expiredCheck.expired, true);
});

test('convertIstSlotToUtc converts IST (+05:30) slots cleanly to UTC', () => {
  assert.equal(convertIstSlotToUtc('19:30'), '14:00 UTC');
  assert.equal(convertIstSlotToUtc('22:00'), '16:30 UTC');
  assert.equal(convertIstSlotToUtc('01:30'), '20:00 UTC');
});

test('parseTimestampToSec and formatSecToTimestamp accurately offset clip end time', async () => {
  const { parseTimestampToSec, formatSecToTimestamp } = await import('./clipLogic');
  const start = parseTimestampToSec('1:10:00');
  assert.equal(formatSecToTimestamp(start + 23), '1:10:23');
  assert.equal(formatSecToTimestamp(parseTimestampToSec('12:45') + 25), '13:10');
});
