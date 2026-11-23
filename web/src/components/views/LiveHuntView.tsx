import { useState } from 'react';
import { ArrowUpRight, Plus, RefreshCw, X } from 'lucide-react';
import type { DiscoveredVod, WatchedChannel } from '../../types/studio';
import { computeVodCompositeScore, formatCompactNumber } from '../../utils/clipLogic';

interface LiveHuntViewProps {
  channels: WatchedChannel[];
  vods: DiscoveredVod[];
  scanning: boolean;
  onAddChannel: (channel: WatchedChannel) => void;
  onRemoveChannel: (channelId: string) => void;
  onScanStreams: () => Promise<void>;
  onSendToCreate: (vod: DiscoveredVod) => void;
}

function parseStreamerUrl(
  rawUrl: string
): { name: string; platform: 'YouTube' | 'Twitch' | 'Kick'; url: string } | null {
  try {
    const u = new URL(rawUrl.trim());
    const host = u.hostname.toLowerCase();
    const segment = u.pathname
      .split('/')
      .filter(Boolean)
      .pop()
      ?.replace(/^@/, '');
    if (!segment) return null;

    if (host.includes('youtube.com') || host.includes('youtu.be')) {
      return { name: segment, platform: 'YouTube', url: u.toString() };
    }
    if (host.includes('twitch.tv')) {
      return { name: segment, platform: 'Twitch', url: u.toString() };
    }
    if (host.includes('kick.com')) {
      return { name: segment, platform: 'Kick', url: u.toString() };
    }
    return null;
  } catch {
    return null;
  }
}

export function LiveHuntView({
  channels,
  vods,
  scanning,
  onAddChannel,
  onRemoveChannel,
  onScanStreams,
  onSendToCreate,
}: LiveHuntViewProps) {
  const [channelUrl, setChannelUrl] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault();
    const parsed = parseStreamerUrl(channelUrl);
    if (!parsed) {
      setError('Enter a valid YouTube, Twitch, or Kick channel URL (e.g. https://twitch.tv/kaicenat).');
      return;
    }
    if (channels.some((c) => c.url.toLowerCase() === parsed.url.toLowerCase())) {
      setError('That channel is already in your watched list.');
      return;
    }
    setError(null);
    onAddChannel({
      id: `ch-${Date.now().toString().slice(-4)}`,
      name: parsed.name,
      platform: parsed.platform,
      url: parsed.url,
      learned_score: 82,
    });
    setChannelUrl('');
  };

  return (
    <div className="mx-auto w-full max-w-[1040px] px-4 sm:px-8 py-8 space-y-8">
      {/* Header Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-[#FAFAFA]">Live Hunt</h1>
          <p className="text-xs text-[#A1A1AA] mt-1">
            Auto-VOD watcher ranking fresh unclipped streams by recency, view velocity, and Viral DNA score.
          </p>
        </div>

        <button
          type="button"
          disabled={scanning}
          onClick={onScanStreams}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#FFE600] px-4 py-2 text-xs font-semibold text-[#09090B] hover:bg-[#F5DD00] disabled:opacity-60 transition-colors whitespace-nowrap shrink-0 cursor-pointer"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${scanning ? 'animate-spin' : ''}`} />
          <span>{scanning ? 'Scanning streams...' : 'Check New Streams'}</span>
        </button>
      </div>

      {/* Watched Channels Bar */}
      <section
        aria-label="Watched Streamer Channels"
        className="rounded-xl border border-white/[0.08] bg-[#111113] p-4 space-y-3.5"
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <span className="text-xs font-medium text-[#FAFAFA]">
            Watched Channels ({channels.length})
          </span>
          <form onSubmit={handleAdd} className="flex items-center gap-2 w-full sm:w-auto">
            <label htmlFor="add-streamer-url" className="sr-only">
              Add streamer channel URL
            </label>
            <input
              id="add-streamer-url"
              type="url"
              value={channelUrl}
              onChange={(e) => {
                setChannelUrl(e.target.value);
                if (error) setError(null);
              }}
              placeholder="https://twitch.tv/streamer or kick.com/..."
              className="w-full sm:w-[290px] rounded-lg border border-white/[0.08] bg-[#09090B] px-3 py-1.5 text-xs text-[#FAFAFA] placeholder:text-[#71717A] focus:border-[#FFE600]/60 focus:outline-none"
            />
            <button
              type="submit"
              className="inline-flex items-center gap-1.5 rounded-lg border border-white/[0.1] bg-white/[0.06] px-3 py-1.5 text-xs font-medium text-[#FAFAFA] hover:bg-white/[0.12] transition-colors whitespace-nowrap shrink-0 cursor-pointer"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Watch</span>
            </button>
          </form>
        </div>

        {error && (
          <p role="alert" className="text-xs text-[#EF4444]">
            {error}
          </p>
        )}

        <div className="flex flex-wrap items-center gap-2">
          {channels.map((ch) => (
            <div
              key={ch.id}
              className="inline-flex items-center gap-2 rounded-lg border border-white/[0.08] bg-[#09090B] px-3 py-1.5 text-xs"
            >
              <span className="font-medium text-[#FAFAFA]">{ch.name}</span>
              <span className="text-[#71717A]">{ch.platform}</span>
              <span className="font-mono text-[11px] text-[#A1A1AA] tabular-nums">
                {ch.learned_score}
              </span>
              <button
                type="button"
                onClick={() => onRemoveChannel(ch.id)}
                aria-label={`Remove watched channel ${ch.name}`}
                className="text-[#71717A] hover:text-[#FAFAFA] transition-colors ml-0.5"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Discovered Unclipped VODs */}
      <section aria-label="Discovered unclipped VODs" className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-[#FAFAFA]">
            Unclipped VODs ({vods.length})
          </h2>
          <span className="text-xs text-[#71717A]">
            Ranked by recency · velocity · streamer score
          </span>
        </div>

        <div className="space-y-3">
          {vods.length === 0 ? (
            <div className="rounded-xl border border-dashed border-white/[0.08] bg-[#111113]/50 p-10 text-center space-y-1.5">
              <p className="text-sm font-medium text-[#FAFAFA]">No streams scanned yet</p>
              <p className="text-xs text-[#71717A] max-w-[420px] mx-auto">
                Add an approved streamer channel above and click &quot;Check New Streams&quot; to discover fresh unclipped VODs.
              </p>
            </div>
          ) : (
            vods.map((vod) => {
            const composite = computeVodCompositeScore(vod);
            return (
              <article
                key={vod.id}
                className="group flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 rounded-xl border border-white/[0.08] bg-[#111113] p-4 hover:border-white/[0.14] transition-colors"
              >
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 min-w-0 flex-1">
                  <div className="relative h-24 sm:h-20 w-full sm:w-36 rounded-lg overflow-hidden bg-[#09090B] border border-white/[0.06] shrink-0">
                    <img
                      src={vod.thumbnail}
                      alt={vod.title}
                      referrerPolicy="no-referrer"
                      className="h-full w-full object-cover"
                    />
                    <span className="absolute bottom-1.5 right-1.5 rounded bg-black/80 px-1.5 py-0.5 font-mono text-[10px] text-[#FAFAFA] tabular-nums">
                      {vod.duration}
                    </span>
                  </div>

                  <div className="min-w-0 flex-1 space-y-1.5">
                    <h3 className="text-sm font-medium text-[#FAFAFA] leading-snug line-clamp-2">
                      {vod.title}
                    </h3>
                    <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1 text-xs text-[#71717A]">
                      <span className="text-[#FAFAFA] font-medium">{vod.streamer_name}</span>
                      <span aria-hidden="true">·</span>
                      <span>{vod.platform}</span>
                      <span aria-hidden="true">·</span>
                      <span className="font-mono tabular-nums">{vod.published_hours_ago}h ago</span>
                      <span aria-hidden="true">·</span>
                      <span className="font-mono tabular-nums">
                        {formatCompactNumber(vod.views_per_hour)} views/hr
                      </span>
                      <span aria-hidden="true">·</span>
                      <span className="font-mono text-[#A1A1AA] tabular-nums">
                        Hot window {vod.suggested_range}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between md:justify-end gap-4 shrink-0 pt-2 md:pt-0 border-t md:border-t-0 border-white/[0.06]">
                  <div className="text-left md:text-right">
                    <div className="font-mono text-sm font-semibold text-[#FAFAFA] tabular-nums">
                      {composite}
                    </div>
                    <div className="text-[11px] text-[#71717A]">Hunt Score</div>
                  </div>

                  <button
                    type="button"
                    onClick={() => onSendToCreate(vod)}
                    className="inline-flex items-center gap-1.5 rounded-lg border border-white/[0.1] bg-white/[0.06] px-3.5 py-2 text-xs font-medium text-[#FAFAFA] hover:bg-[#FFE600] hover:text-[#09090B] hover:border-[#FFE600] transition-colors whitespace-nowrap cursor-pointer"
                  >
                    <span>Send to Create</span>
                    <ArrowUpRight className="h-3.5 w-3.5" aria-hidden="true" />
                  </button>
                </div>
              </article>
            );
          })
        )}
      </div>
      </section>
    </div>
  );
}
