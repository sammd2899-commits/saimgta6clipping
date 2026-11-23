import { CopyPlus, RefreshCw } from 'lucide-react';
import type { ScoreBarMetric, ViralDnaData } from '../../types/studio';

interface ViralDnaViewProps {
  data: ViralDnaData;
  learning: boolean;
  cloning: boolean;
  onLearnAnalytics: () => Promise<void>;
  onCloneWinners: () => Promise<void>;
}

function ScoreBarCard({
  title,
  subtitle,
  items,
}: {
  title: string;
  subtitle: string;
  items: ScoreBarMetric[];
}) {
  return (
    <section className="rounded-xl border border-white/[0.08] bg-[#111113] p-5 space-y-4">
      <div>
        <h2 className="text-sm font-semibold text-[#FAFAFA]">{title}</h2>
        <p className="text-xs text-[#71717A] mt-0.5">{subtitle}</p>
      </div>

      {items.length === 0 ? (
        <p className="text-xs text-[#71717A] py-3 italic">
          No metrics recorded yet — publish clips and click "Learn from Analytics" to train this model.
        </p>
      ) : (
        <div className="space-y-3.5">
          {items.map((item) => (
            <div key={item.label} className="space-y-1.5">
              <div className="flex items-baseline justify-between gap-2 text-xs">
                <span className="font-medium text-[#FAFAFA] truncate">{item.label}</span>
                <div className="flex items-center gap-2.5 shrink-0">
                  <span className="text-[#71717A] hidden sm:inline">{item.detail}</span>
                  <span className="font-mono font-semibold text-[#FAFAFA] tabular-nums w-7 text-right">
                    {item.score}
                  </span>
                </div>
              </div>
              <div className="h-1.5 w-full rounded-full bg-white/[0.06] overflow-hidden">
                <div
                  style={{ width: `${Math.min(100, Math.max(4, item.score))}%` }}
                  className={`h-full rounded-full transition-all duration-300 ${
                    item.highlight ? 'bg-[#FFE600]' : 'bg-[#FAFAFA]/45'
                  }`}
                />
              </div>
              <p className="text-[11px] text-[#71717A] sm:hidden">{item.detail}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

export function ViralDnaView({
  data,
  learning,
  cloning,
  onLearnAnalytics,
  onCloneWinners,
}: ViralDnaViewProps) {
  return (
    <div className="mx-auto w-full max-w-[1120px] px-4 sm:px-8 py-8 space-y-8">
      {/* Top Action Row */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-[#FAFAFA]">Viral DNA</h1>
          <p className="text-xs text-[#A1A1AA] mt-1">
            Self-learning ranking memory · Last synced{' '}
            <span className="font-mono text-[#FAFAFA]">{data.last_learned_at}</span>
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            type="button"
            disabled={cloning}
            onClick={onCloneWinners}
            className="inline-flex items-center gap-2 rounded-lg border border-white/[0.1] bg-[#111113] px-3.5 py-2 text-xs font-medium text-[#FAFAFA] hover:border-white/[0.18] disabled:opacity-60 transition-colors whitespace-nowrap cursor-pointer"
          >
            <CopyPlus className="h-3.5 w-3.5 text-[#A1A1AA]" />
            <span>{cloning ? 'Cloning...' : 'Clone Winners'}</span>
          </button>

          <button
            type="button"
            disabled={learning}
            onClick={onLearnAnalytics}
            className="inline-flex items-center gap-2 rounded-lg bg-[#FFE600] px-4 py-2 text-xs font-semibold text-[#09090B] hover:bg-[#F5DD00] disabled:opacity-60 transition-colors whitespace-nowrap cursor-pointer"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${learning ? 'animate-spin' : ''}`} />
            <span>
              {learning ? 'Learning...' : `Learn from Analytics (${data.window_label})`}
            </span>
          </button>
        </div>
      </div>

      {/* 4 Quiet High-Contrast KPI Tiles */}
      <section aria-label="Performance KPIs" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        <div className="rounded-xl border border-white/[0.08] bg-[#111113] p-4 space-y-1">
          <span className="text-xs text-[#71717A]">Total Views</span>
          <div className="font-mono text-2xl font-semibold text-[#FAFAFA] tabular-nums">
            {data.kpis.total_views}
          </div>
          <span className="block font-mono text-[11px] text-[#A1A1AA]">
            {data.kpis.total_views_delta}
          </span>
        </div>

        <div className="rounded-xl border border-white/[0.08] bg-[#111113] p-4 space-y-1">
          <span className="text-xs text-[#71717A]">Avg Engagement %</span>
          <div className="font-mono text-2xl font-semibold text-[#FAFAFA] tabular-nums">
            {data.kpis.avg_engagement_pct}
          </div>
          <span className="block font-mono text-[11px] text-[#A1A1AA]">
            {data.kpis.engagement_delta}
          </span>
        </div>

        <div className="rounded-xl border border-white/[0.08] bg-[#111113] p-4 space-y-1">
          <span className="text-xs text-[#71717A]">3K Payout Unlocks</span>
          <div className="font-mono text-2xl font-semibold text-[#FAFAFA] tabular-nums">
            {data.kpis.payout_unlocks_3k}
          </div>
          <span className="block font-mono text-[11px] text-[#A1A1AA]">
            {data.kpis.payout_delta}
          </span>
        </div>

        <div className="rounded-xl border border-white/[0.08] bg-[#111113] p-4 space-y-1">
          <span className="text-xs text-[#71717A]">Best IST Slot</span>
          <div className="font-mono text-2xl font-semibold text-[#FAFAFA] tabular-nums">
            {data.kpis.best_ist_slot}
          </div>
          <span className="block text-[11px] text-[#A1A1AA] truncate">
            {data.kpis.best_slot_region}
          </span>
        </div>
      </section>

      {/* Monochrome + Yellow Horizontal Score Bars (2x2 Grid) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ScoreBarCard
          title="Winning Moment Archetypes"
          subtitle="Composite score from 24h–72h Reels & Shorts performance"
          items={data.archetypes}
        />
        <ScoreBarCard
          title="Duration Sweet Spot"
          subtitle="Completion rate by final trimmed clip duration"
          items={data.duration_sweet_spot}
        />
        <ScoreBarCard
          title="Top Streamer Sources"
          subtitle="Learned source weight feeding Live Hunt & Queue Ranker"
          items={data.top_streamers}
        />
        <ScoreBarCard
          title="IG Retention & Skip Rate"
          subtitle="Hook retention and DM-share velocity benchmarks"
          items={data.ig_retention}
        />
      </div>

      {/* Compact Learned Rules Card (memory/learned_rules.md) */}
      <section
        aria-labelledby="learned-rules-heading"
        className="rounded-xl border border-white/[0.08] bg-[#111113] p-5 space-y-4"
      >
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/[0.06] pb-3">
          <div>
            <h2 id="learned-rules-heading" className="text-sm font-semibold text-[#FAFAFA]">
              Learned Rules
            </h2>
            <p className="text-xs text-[#71717A] mt-0.5">
              Injected into ranking &amp; title prompts from{' '}
              <span className="font-mono">memory/learned_rules.md</span>
            </p>
          </div>
          <span className="font-mono text-[11px] text-[#71717A]">
            {data.learned_rules.do_rules.length} DO · {data.learned_rules.do_not_rules.length} DO-NOT
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2.5">
            <h3 className="flex items-center gap-2 text-xs font-semibold text-[#FAFAFA]">
              <span className="h-1.5 w-1.5 rounded-full bg-[#22C55E]" aria-hidden="true" />
              <span>DO</span>
            </h3>
            {data.learned_rules.do_rules.length === 0 ? (
              <p className="text-xs text-[#71717A] italic py-1">No learned DO rules recorded yet.</p>
            ) : (
              <ul className="space-y-2 text-xs leading-relaxed text-[#A1A1AA]">
                {data.learned_rules.do_rules.map((rule, idx) => (
                  <li key={idx} className="flex items-start gap-2.5">
                    <span className="font-mono text-[11px] text-[#71717A] mt-0.5 shrink-0">
                      {String(idx + 1).padStart(2, '0')}
                    </span>
                    <span>{rule}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="space-y-2.5">
            <h3 className="flex items-center gap-2 text-xs font-semibold text-[#FAFAFA]">
              <span className="h-1.5 w-1.5 rounded-full bg-[#EF4444]" aria-hidden="true" />
              <span>DO-NOT</span>
            </h3>
            {data.learned_rules.do_not_rules.length === 0 ? (
              <p className="text-xs text-[#71717A] italic py-1">No learned DO-NOT rules recorded yet.</p>
            ) : (
              <ul className="space-y-2 text-xs leading-relaxed text-[#A1A1AA]">
                {data.learned_rules.do_not_rules.map((rule, idx) => (
                  <li key={idx} className="flex items-start gap-2.5">
                    <span className="font-mono text-[11px] text-[#71717A] mt-0.5 shrink-0">
                      {String(idx + 1).padStart(2, '0')}
                    </span>
                    <span>{rule}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
