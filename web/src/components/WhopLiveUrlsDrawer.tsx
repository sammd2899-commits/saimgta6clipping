import { useEffect, useState } from 'react';
import { Check, CheckSquare, Copy, RefreshCw, Square, X } from 'lucide-react';
import type { LiveUrlItem } from '../types/studio';
import { formatWhopCountdown } from '../utils/clipLogic';

interface WhopLiveUrlsDrawerProps {
  open: boolean;
  onClose: () => void;
  items: LiveUrlItem[];
  onRefresh: () => void;
  onToggleSubmitted: (clipId: string) => void;
  refreshing: boolean;
}

export function WhopLiveUrlsDrawer({
  open,
  onClose,
  items,
  onRefresh,
  onToggleSubmitted,
  refreshing,
}: WhopLiveUrlsDrawerProps) {
  const [nowMs, setNowMs] = useState(() => Date.now());
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [showSubmitted, setShowSubmitted] = useState(false);

  useEffect(() => {
    if (!open) return;
    setNowMs(Date.now());
    const id = setInterval(() => setNowMs(Date.now()), 1000);
    return () => clearInterval(id);
  }, [open]);

  if (!open) return null;

  const pendingItems = items.filter((i) => !i.submitted);
  const submittedItems = items.filter((i) => i.submitted);
  const visibleItems = showSubmitted ? items : pendingItems;

  const copyText = async (key: string, url: string) => {
    try {
      await navigator.clipboard.writeText(url);
    } catch {
      // Clipboard API may be blocked in headless/sandbox environments; still show feedback
    }
    setCopiedKey(key);
    setTimeout(() => setCopiedKey((curr) => (curr === key ? null : curr)), 1600);
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Live URLs for Whop"
      className="fixed inset-0 z-50 flex justify-end"
    >
      <button
        type="button"
        aria-label="Close Live URLs drawer"
        onClick={onClose}
        className="fixed inset-0 bg-black/70 backdrop-blur-sm"
      />
      <aside className="relative z-10 flex h-full w-full max-w-[440px] flex-col border-l border-white/[0.08] bg-[#09090B]/95 backdrop-blur-md">
        <div className="flex items-center justify-between border-b border-white/[0.08] px-5 py-4">
          <div>
            <h2 className="text-[15px] font-semibold text-[#FAFAFA]">Live URLs for Whop</h2>
            <p className="text-xs text-[#71717A] mt-0.5">
              Submit manually on Whop within 30 minutes of publish.
            </p>
          </div>
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={onRefresh}
              aria-label="Refresh live URLs"
              className="flex h-8 w-8 items-center justify-center rounded-md border border-white/[0.08] bg-[#111113] text-[#A1A1AA] hover:text-[#FAFAFA] hover:border-white/[0.14] transition-colors"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            </button>
            <button
              type="button"
              onClick={onClose}
              aria-label="Close drawer"
              className="flex h-8 w-8 items-center justify-center rounded-md text-[#A1A1AA] hover:text-[#FAFAFA] hover:bg-white/[0.06] transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-2.5 text-xs">
          <span className="text-[#A1A1AA] font-mono tabular-nums">
            {pendingItems.length} pending · {submittedItems.length} submitted
          </span>
          {submittedItems.length > 0 && (
            <button
              type="button"
              onClick={() => setShowSubmitted((v) => !v)}
              className="text-[#A1A1AA] hover:text-[#FAFAFA] underline underline-offset-4 transition-colors"
            >
              {showSubmitted ? 'Hide submitted' : 'Show submitted'}
            </button>
          )}
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
          {items.length === 0 ? (
            <div className="rounded-xl border border-white/[0.08] bg-[#111113] p-8 text-center">
              <p className="text-sm font-medium text-[#FAFAFA]">No live URLs recorded yet</p>
              <p className="mt-1 text-xs text-[#71717A]">
                Published clips from Zernio will appear here with 30-minute Whop submission countdowns.
              </p>
            </div>
          ) : visibleItems.length === 0 ? (
            <div className="rounded-xl border border-white/[0.08] bg-[#111113] p-8 text-center">
              <p className="text-sm font-medium text-[#FAFAFA]">All caught up</p>
              <p className="mt-1 text-xs text-[#71717A]">
                Every published Reel and Short has been marked submitted on Whop.
              </p>
            </div>
          ) : (
            visibleItems.map((item) => {
              const countdown = formatWhopCountdown(item.published_at, nowMs);
              const igKey = `${item.clip_id}-ig`;
              const ytKey = `${item.clip_id}-yt`;

              return (
                <div
                  key={item.clip_id}
                  className={`rounded-xl border p-4 transition-colors ${
                    item.submitted
                      ? 'border-white/[0.05] bg-[#111113]/50 opacity-60'
                      : 'border-white/[0.08] bg-[#111113] hover:border-white/[0.14]'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-[#FAFAFA] leading-snug">
                        {item.title}
                      </p>
                      <p className="mt-1 text-xs text-[#71717A]">{item.campaign_name}</p>
                    </div>
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 font-mono text-[11px] tabular-nums shrink-0 ${
                        item.submitted
                          ? 'border-white/[0.08] text-[#22C55E]'
                          : countdown.expired
                            ? 'border-[#EF4444]/30 text-[#EF4444]'
                            : countdown.urgent
                              ? 'border-[#F59E0B]/40 text-[#F59E0B]'
                              : 'border-white/[0.08] text-[#A1A1AA]'
                      }`}
                    >
                      <span
                        className={`h-1.5 w-1.5 rounded-full ${
                          item.submitted
                            ? 'bg-[#22C55E]'
                            : countdown.expired
                              ? 'bg-[#EF4444]'
                              : 'bg-[#F59E0B]'
                        }`}
                        aria-hidden="true"
                      />
                      {item.submitted
                        ? 'Submitted'
                        : countdown.expired
                          ? 'Window closed'
                          : `${countdown.formatted} left`}
                    </span>
                  </div>

                  <div className="mt-3.5 space-y-2">
                    {/* Instagram Reel URL */}
                    <div className="flex items-center justify-between gap-2 rounded-lg border border-white/[0.06] bg-[#09090B] px-3 py-2">
                      <div className="min-w-0">
                        <span className="block text-[11px] text-[#71717A]">Instagram Reel</span>
                        <span className="block font-mono text-xs text-[#A1A1AA] truncate">
                          {item.ig_reel_url}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => copyText(igKey, item.ig_reel_url)}
                        aria-label={`Copy Instagram Reel URL for ${item.title}`}
                        className="flex items-center gap-1.5 rounded-md border border-white/[0.08] bg-[#111113] px-2.5 py-1 text-xs font-medium text-[#FAFAFA] hover:border-white/[0.16] transition-colors shrink-0 whitespace-nowrap"
                      >
                        {copiedKey === igKey ? (
                          <>
                            <Check className="h-3.5 w-3.5 text-[#22C55E]" />
                            <span>Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="h-3.5 w-3.5 text-[#A1A1AA]" />
                            <span>Copy URL</span>
                          </>
                        )}
                      </button>
                    </div>

                    {/* YouTube Short URL */}
                    <div className="flex items-center justify-between gap-2 rounded-lg border border-white/[0.06] bg-[#09090B] px-3 py-2">
                      <div className="min-w-0">
                        <span className="block text-[11px] text-[#71717A]">YouTube Short</span>
                        <span className="block font-mono text-xs text-[#A1A1AA] truncate">
                          {item.yt_short_url}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => copyText(ytKey, item.yt_short_url)}
                        aria-label={`Copy YouTube Short URL for ${item.title}`}
                        className="flex items-center gap-1.5 rounded-md border border-white/[0.08] bg-[#111113] px-2.5 py-1 text-xs font-medium text-[#FAFAFA] hover:border-white/[0.16] transition-colors shrink-0 whitespace-nowrap"
                      >
                        {copiedKey === ytKey ? (
                          <>
                            <Check className="h-3.5 w-3.5 text-[#22C55E]" />
                            <span>Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="h-3.5 w-3.5 text-[#A1A1AA]" />
                            <span>Copy URL</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>

                  <div className="mt-3 pt-3 border-t border-white/[0.06] flex items-center justify-between">
                    <button
                      type="button"
                      onClick={() => onToggleSubmitted(item.clip_id)}
                      className="flex items-center gap-2 text-xs font-medium text-[#A1A1AA] hover:text-[#FAFAFA] transition-colors"
                    >
                      {item.submitted ? (
                        <CheckSquare className="h-4 w-4 text-[#22C55E]" />
                      ) : (
                        <Square className="h-4 w-4 text-[#71717A]" />
                      )}
                      <span>{item.submitted ? 'Submitted on Whop' : 'Mark Submitted'}</span>
                    </button>
                    <span className="font-mono text-[11px] text-[#71717A]">{item.clip_id}</span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </aside>
    </div>
  );
}
