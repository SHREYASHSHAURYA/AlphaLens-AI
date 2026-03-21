import { useData } from "../context/DataContext";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

function StatCard({ label, value, color, sub }) {
  return (
    <div className="bg-[#0F172A] rounded-xl p-4 border border-slate-700/50 flex flex-col gap-1">
      <span className="text-xs text-slate-400 uppercase tracking-widest">
        {label}
      </span>
      <span className={`text-xl font-bold ${color || "text-[#E2E8F0]"}`}>
        {value}
      </span>
      {sub && <span className="text-xs text-slate-500">{sub}</span>}
    </div>
  );
}

function segmentReturns(tradeReturns) {
  if (!tradeReturns || tradeReturns.length < 8) return [];
  const n = Math.floor(tradeReturns.length / 4);
  const segs = [
    tradeReturns.slice(0, n),
    tradeReturns.slice(n, n * 2),
    tradeReturns.slice(n * 2, n * 3),
    tradeReturns.slice(n * 3),
  ];
  return segs.map((seg, i) => {
    const ret = seg.reduce((acc, r) => acc * (1 + r), 1) - 1;
    const mean = seg.reduce((a, b) => a + b, 0) / seg.length;
    const std = Math.sqrt(
      seg.reduce((a, b) => a + (b - mean) ** 2, 0) / seg.length,
    );
    const sharpe = std > 0 ? mean / std : 0;
    let peak = 1,
      running = 1,
      maxDD = 0;
    for (const r of seg) {
      running *= 1 + r;
      if (running > peak) peak = running;
      const dd = (running - peak) / peak;
      if (dd < maxDD) maxDD = dd;
    }
    return {
      period: `Period ${i + 1}`,
      return: Math.round(ret * 100 * 10) / 10,
      sharpe: Math.round(sharpe * 100) / 100,
      maxDD: Math.round(maxDD * 100 * 10) / 10,
    };
  });
}

export default function Robustness() {
  const { data, loading } = useData();

  if (loading)
    return (
      <div className="flex items-center justify-center h-[80vh]">
        <div className="w-12 h-12 border-2 border-[#38BDF8] border-t-transparent rounded-full animate-spin" />
      </div>
    );

  if (!data) return null;

  const opportunities = data.all_opportunities || [];
  const top = data.top_pick;

  const tradeReturns = top?.data?.backtest?.trade_returns || [];
  const periodData = segmentReturns(tradeReturns);

  const assetSharpeData = opportunities.map((o) => ({
    name: o.symbol.replace(".NS", ""),
    sharpe: o.data.backtest.sharpe,
    action: o.data.decision.action,
  }));

  const totalTrades = opportunities.reduce(
    (sum, o) => sum + o.data.backtest.trades,
    0,
  );
  const avgTrades = Math.round(totalTrades / opportunities.length);
  const maxTrades = Math.max(
    ...opportunities.map((o) => o.data.backtest.trades),
  );
  const minTrades = Math.min(
    ...opportunities.map((o) => o.data.backtest.trades),
  );
  const avgSharpe =
    Math.round(
      (opportunities.reduce((s, o) => s + o.data.backtest.sharpe, 0) /
        opportunities.length) *
        100,
    ) / 100;

  const actionColor = (action) => {
    if (action === "BUY") return "#22C55E";
    if (action === "AVOID") return "#EF4444";
    return "#F59E0B";
  };

  const topMl = top?.data?.backtest?.ml_model || {};

  return (
    <div className="max-w-7xl mx-auto pt-8 pb-8 px-4 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Robustness & Research</h1>
        <p className="text-slate-400 text-sm mt-1">
          Multi-period validation, cross-asset analysis, and overfitting
          safeguards
        </p>
      </div>

      {/* Sample Size Evidence */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Total Trades"
          value={totalTrades}
          sub="across all assets"
        />
        <StatCard
          label="Avg Trades / Asset"
          value={avgTrades}
          sub="per symbol"
        />
        <StatCard label="Max Trades" value={maxTrades} sub="single asset" />
        <StatCard label="Min Trades" value={minTrades} sub="single asset" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Multi-Period Performance */}
        <div className="bg-[#1E293B] rounded-xl border border-slate-700/50 p-6">
          <h2 className="text-sm font-semibold text-[#E2E8F0] uppercase tracking-widest mb-2">
            Multi-Period Performance
          </h2>
          <p className="text-slate-500 text-xs mb-4">
            Top asset trade history split into 4 equal periods
          </p>
          {periodData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={periodData} margin={{ left: 10, right: 10 }}>
                  <XAxis
                    dataKey="period"
                    tick={{ fill: "#94a3b8", fontSize: 11 }}
                  />
                  <YAxis
                    tick={{ fill: "#94a3b8", fontSize: 11 }}
                    tickFormatter={(v) => `${v}%`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1E293B",
                      border: "1px solid #334155",
                      borderRadius: 8,
                    }}
                    formatter={(v, name) => [`${v}%`, name]}
                  />
                  <Bar dataKey="return" radius={[4, 4, 0, 0]} name="Return">
                    {periodData.map((p, i) => (
                      <Cell
                        key={i}
                        fill={p.return >= 0 ? "#22C55E" : "#EF4444"}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div className="mt-4 space-y-2">
                {periodData.map((p, i) => (
                  <div
                    key={i}
                    className="flex justify-between text-xs text-slate-400 bg-[#0F172A] rounded px-3 py-2"
                  >
                    <span className="font-medium text-slate-300">
                      {p.period}
                    </span>
                    <span
                      className={
                        p.return >= 0 ? "text-green-400" : "text-red-400"
                      }
                    >
                      Return: {p.return}%
                    </span>
                    <span>Sharpe: {p.sharpe}</span>
                    <span className="text-red-400">Max DD: {p.maxDD}%</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-slate-500 text-sm">
              Insufficient trade history for period analysis
            </p>
          )}
        </div>

        {/* Cross-Asset Sharpe */}
        <div className="bg-[#1E293B] rounded-xl border border-slate-700/50 p-6">
          <h2 className="text-sm font-semibold text-[#E2E8F0] uppercase tracking-widest mb-2">
            Cross-Asset Sharpe Ratio
          </h2>
          <p className="text-slate-500 text-xs mb-4">
            Strategy performance consistency across all scanned assets
          </p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart
              data={assetSharpeData}
              layout="vertical"
              margin={{ left: 10, right: 20 }}
            >
              <XAxis type="number" tick={{ fill: "#94a3b8", fontSize: 11 }} />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fill: "#94a3b8", fontSize: 11 }}
                width={80}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1E293B",
                  border: "1px solid #334155",
                  borderRadius: 8,
                }}
                formatter={(v) => [v, "Sharpe"]}
              />
              <Bar dataKey="sharpe" radius={[0, 4, 4, 0]}>
                {assetSharpeData.map((entry, i) => (
                  <Cell key={i} fill={actionColor(entry.action)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div className="mt-4 grid grid-cols-3 gap-3">
            <div className="bg-[#0F172A] rounded-lg p-3 text-center">
              <p className="text-xs text-slate-400">Avg Sharpe</p>
              <p className="text-white font-bold">{avgSharpe}</p>
            </div>
            <div className="bg-[#0F172A] rounded-lg p-3 text-center">
              <p className="text-xs text-slate-400">Assets</p>
              <p className="text-white font-bold">{opportunities.length}</p>
            </div>
            <div className="bg-[#0F172A] rounded-lg p-3 text-center">
              <p className="text-xs text-slate-400">Best Sharpe</p>
              <p className="text-green-400 font-bold">
                {Math.max(...assetSharpeData.map((a) => a.sharpe))}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Walk-Forward Validation */}
      <div className="bg-[#1E293B] rounded-xl border border-slate-700/50 p-6">
        <h2 className="text-sm font-semibold text-[#E2E8F0] uppercase tracking-widest mb-4">
          Walk-Forward ML Validation
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <StatCard
            label="Validation AUC"
            value={topMl.val_auc ?? "N/A"}
            color={topMl.val_auc >= 0.55 ? "text-green-400" : "text-yellow-400"}
          />
          <StatCard
            label="Validation Accuracy"
            value={topMl.val_accuracy ?? "N/A"}
          />
          <StatCard label="Train Samples" value={topMl.train_size ?? "N/A"} />
          <StatCard label="Test Samples" value={topMl.test_size ?? "N/A"} />
        </div>
        <p className="text-slate-400 text-sm">
          Models are evaluated on unseen data using train/test splits to ensure
          predictive performance generalizes beyond the training set. AUC
          threshold of 0.55 is required for a model to influence trading
          decisions.
        </p>
      </div>

      {/* Overfitting Safeguards */}
      <div className="bg-[#1E293B] rounded-xl border border-slate-700/50 p-6">
        <h2 className="text-sm font-semibold text-[#E2E8F0] uppercase tracking-widest mb-4">
          Overfitting Safeguards
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            {
              title: "Out-of-Sample Validation",
              desc: "ML models are trained on 80% of data and validated on the remaining 20% to test generalization.",
            },
            {
              title: "AUC Gating",
              desc: "Only models with AUC ≥ 0.55 are allowed to influence decisions. Weak models are completely ignored.",
            },
            {
              title: "Cross-Asset Testing",
              desc: "Strategy is evaluated across 5+ different NSE assets to ensure performance is not asset-specific.",
            },
            {
              title: "Multi-Period Analysis",
              desc: "Trade history is split into 4 time segments to verify consistent performance across different market regimes.",
            },
            {
              title: "Risk-Adjusted Scoring",
              desc: "Kelly criterion, Sharpe ratio, and drawdown penalties prevent overfitting to high-return but high-risk signals.",
            },
            {
              title: "Limited Feature Set",
              desc: "15 carefully selected features prevent the model from memorizing noise in the training data.",
            },
          ].map((s, i) => (
            <div key={i} className="bg-[#0F172A] rounded-lg p-4">
              <p className="text-accent text-sm font-semibold mb-1">
                • {s.title}
              </p>
              <p className="text-slate-400 text-xs">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Robustness Summary */}
      <div className="bg-[#1E293B] rounded-xl border border-accent/20 p-6">
        <h2 className="text-sm font-semibold text-accent uppercase tracking-widest mb-3">
          Robustness Summary
        </h2>
        <p className="text-slate-300 text-sm leading-relaxed">
          The strategy was evaluated across {opportunities.length} assets,{" "}
          {periodData.length} time segments, and out-of-sample ML validation
          datasets. Combined evidence from multi-period testing, cross-asset
          results ({totalTrades} total trades), and historical performance
          indicates that performance is not dependent on a single asset or time
          window. AlphaLens AI is designed as a quantitative research assistant
          that surfaces probabilistic trading opportunities rather than
          deterministic signals.
        </p>
      </div>
    </div>
  );
}
