import { useData } from "../context/DataContext";
import { useNavigate } from "react-router-dom";

const actionColor = (action) => {
  if (action === "BUY")
    return "text-green-400 bg-green-400/10 border border-green-400/30";
  if (action === "AVOID")
    return "text-red-400 bg-red-400/10 border border-red-400/30";
  return "text-yellow-400 bg-yellow-400/10 border border-yellow-400/30";
};

const signalColor = (pct) => {
  if (pct >= 70) return "#22C55E";
  if (pct >= 40) return "#F59E0B";
  return "#EF4444";
};

function MetricCard({ label, value, sub, color }) {
  return (
    <div className="bg-[#1E293B] rounded-xl p-5 border border-slate-700/50 flex flex-col gap-1 hover:border-slate-500/50 transition-colors">
      <span className="text-xs font-medium text-slate-400 uppercase tracking-widest">
        {label}
      </span>
      <span className={`text-2xl font-bold ${color || "text-[#E2E8F0]"}`}>
        {value}
      </span>
      {sub && <span className="text-xs text-slate-500">{sub}</span>}
    </div>
  );
}

function MarketAwarenessBanner({ opportunities }) {
  if (!opportunities) return null;
  const buyCount = opportunities.filter(
    (o) => o.data.decision.action === "BUY",
  ).length;
  const total = opportunities.length;
  if (buyCount > 0) return null;

  return (
    <div className="mb-6 rounded-xl border border-yellow-400/30 bg-yellow-400/5 px-6 py-4 flex items-start gap-4">
      <span className="text-yellow-400 text-2xl mt-0.5">⚠</span>
      <div>
        <p className="text-yellow-400 font-semibold text-sm">
          Capital Preservation Mode Active
        </p>
        <p className="text-slate-400 text-sm mt-1">
          System has scanned {total} assets and detected no qualifying setups.
          Market conditions are unfavorable — the system is avoiding trades and
          preserving capital until stronger signals emerge.
        </p>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { data, loading, error } = useData();
  const navigate = useNavigate();

  if (loading)
    return (
      <div className="flex items-center justify-center h-[80vh]">
        <div className="text-center">
          <div className="w-12 h-12 border-2 border-[#38BDF8] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-slate-400 text-sm">Scanning markets...</p>
        </div>
      </div>
    );

  if (error)
    return (
      <div className="flex items-center justify-center h-[80vh]">
        <div className="text-center text-red-400">
          <p className="text-lg font-semibold">Connection Error</p>
          <p className="text-sm text-slate-400 mt-2">{error}</p>
        </div>
      </div>
    );

  if (!data) return null;

  const top = data.top_pick;
  const opportunities = data.all_opportunities;
  const portfolio = data.portfolio;
  const pvb = portfolio?.performance_vs_benchmark || {};

  const totalTrades =
    opportunities?.reduce((sum, o) => sum + (o.data.backtest.trades || 0), 0) ||
    0;

  const signalStrengths =
    opportunities?.map((o) => ({
      symbol: o.symbol.replace(".NS", ""),
      strength:
        o.data.signals?.[0]?.type === "No Active Setup"
          ? 0
          : o.data.signals?.[0]?.strength || 0,
      action: o.data.decision.action,
    })) || [];

  const maxBar = Math.max(...signalStrengths.map((s) => s.strength), 0.01);

  return (
    <div className="max-w-7xl mx-auto pt-8 pb-8 px-4">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[#E2E8F0] tracking-tight">
          Market Intelligence Dashboard
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          AI-driven trading opportunity discovery — NSE India
        </p>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        <MetricCard
          label="Top Opportunity"
          value={top?.symbol?.replace(".NS", "") || "—"}
          sub={top?.data?.decision?.action}
          color="text-[#38BDF8]"
        />
        <MetricCard
          label="Strategy Return"
          value={`+${pvb.strategy_return_pct ?? 0}%`}
          color="text-green-400"
        />
        <MetricCard
          label="Benchmark Return"
          value={`${pvb.benchmark_return_pct ?? 0}%`}
          color="text-slate-300"
        />
        <MetricCard
          label="Outperformance"
          value={`+${pvb.outperformance_pct ?? 0}%`}
          color="text-green-400"
        />
        <MetricCard label="Assets Scanned" value={15} sub="NSE symbols" />
        <MetricCard
          label="Trades Tested"
          value={totalTrades}
          sub="historical trades"
        />
      </div>

      {/* Market Awareness Banner */}
      <MarketAwarenessBanner opportunities={opportunities} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Opportunity Table */}
        <div className="lg:col-span-2 bg-[#1E293B] rounded-xl border border-slate-700/50 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-700/50">
            <h2 className="text-sm font-semibold text-[#E2E8F0] uppercase tracking-widest">
              Market Opportunities
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Click a row to view deep analysis
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700/50">
                  {[
                    "Symbol",
                    "Action",
                    "Confidence",
                    "Win Rate",
                    "Exp Return",
                    "ML Prob",
                    "Sharpe",
                  ].map((h) => (
                    <th
                      key={h}
                      className="px-4 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {opportunities?.map((o) => {
                  const d = o.data;
                  const dec = d.decision;
                  const bt = d.backtest;
                  return (
                    <tr
                      key={o.symbol}
                      onClick={() =>
                        navigate(`/opportunity/${encodeURIComponent(o.symbol)}`)
                      }
                      className="border-b border-slate-700/30 hover:bg-slate-700/20 cursor-pointer transition-colors"
                    >
                      <td className="px-4 py-3 font-semibold text-[#E2E8F0]">
                        {o.symbol.replace(".NS", "")}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`text-xs font-bold px-2 py-1 rounded-md ${actionColor(dec.action)}`}
                        >
                          {dec.action}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-300">
                        {Math.round(dec.confidence * 100)}%
                      </td>
                      <td className="px-4 py-3 text-slate-300">
                        {Math.round(bt.win_rate * 100)}%
                      </td>
                      <td className="px-4 py-3 text-slate-300">
                        {(bt.avg_return * 100).toFixed(1)}%
                      </td>
                      <td className="px-4 py-3">
                        {dec.ml_prediction != null ? (
                          <span className="text-[#38BDF8] font-medium">
                            {(dec.ml_prediction * 100).toFixed(1)}%
                          </span>
                        ) : (
                          <span className="text-slate-500">N/A</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-slate-300">{bt.sharpe}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Signal Strength Chart */}
        <div className="bg-[#1E293B] rounded-xl border border-slate-700/50 p-6">
          <h2 className="text-sm font-semibold text-[#E2E8F0] uppercase tracking-widest mb-4">
            Signal Strength
          </h2>
          <div className="flex flex-col gap-4">
            {signalStrengths.map((s) => (
              <div key={s.symbol}>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs font-medium text-slate-300">
                    {s.symbol}
                  </span>
                  <span className="text-xs text-slate-400">
                    {(s.strength * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${(s.strength / maxBar) * 100}%`,
                      backgroundColor: signalColor(s.strength * 100),
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Opportunity Heatmap */}
      <div className="bg-[#1E293B] rounded-xl border border-slate-700/50 p-6 mt-6">
        <h2 className="text-sm font-semibold text-[#E2E8F0] uppercase tracking-widest mb-2">
          Market Signal Heatmap
        </h2>
        <p className="text-slate-500 text-xs mb-6">
          Visual overview of market landscape — color indicates signal strength
          and action
        </p>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          {opportunities?.map((o) => {
            const dec = o.data.decision;
            const bt = o.data.backtest;
            const sig = o.data.signals?.[0];
            const strength =
              sig?.type === "No Active Setup" ? 0 : sig?.strength || 0;
            const bgColor =
              dec.action === "BUY"
                ? `rgba(34,197,94,${0.1 + strength * 0.5})`
                : dec.action === "AVOID"
                  ? `rgba(239,68,68,${0.1 + strength * 0.5})`
                  : `rgba(245,158,11,${0.05 + strength * 0.3})`;
            const borderColor =
              dec.action === "BUY"
                ? "#22C55E"
                : dec.action === "AVOID"
                  ? "#EF4444"
                  : "#F59E0B";
            return (
              <div
                key={o.symbol}
                onClick={() =>
                  navigate(`/opportunity/${encodeURIComponent(o.symbol)}`)
                }
                className="rounded-xl p-4 cursor-pointer hover:scale-105 transition-transform border"
                style={{ backgroundColor: bgColor, borderColor: borderColor }}
              >
                <p className="text-white font-bold text-sm mb-1">
                  {o.symbol.replace(".NS", "")}
                </p>
                <p
                  className="text-xs font-semibold mb-2"
                  style={{ color: borderColor }}
                >
                  {dec.action}
                </p>
                <div className="space-y-1">
                  <p className="text-slate-300 text-xs">
                    Conf: {Math.round(dec.confidence * 100)}%
                  </p>
                  <p className="text-slate-300 text-xs">
                    WR: {Math.round(bt.win_rate * 100)}%
                  </p>
                  <p className="text-slate-300 text-xs">
                    Ret: {(bt.avg_return * 100).toFixed(1)}%
                  </p>
                  {dec.ml_prediction != null && (
                    <p className="text-xs font-semibold text-[#38BDF8]">
                      ML: {(dec.ml_prediction * 100).toFixed(0)}%
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>
        <div className="flex gap-6 mt-4 pt-4 border-t border-slate-700/50">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-green-500/50 border border-green-500" />
            <span className="text-xs text-slate-400">BUY — Strong Signal</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-yellow-500/20 border border-yellow-500" />
            <span className="text-xs text-slate-400">WATCH — Monitoring</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-red-500/50 border border-red-500" />
            <span className="text-xs text-slate-400">AVOID — Weak Signal</span>
          </div>
        </div>
      </div>
    </div>
  );
}
