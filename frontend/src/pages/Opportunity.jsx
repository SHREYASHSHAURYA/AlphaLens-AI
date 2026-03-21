import { useParams, useNavigate } from "react-router-dom";
import { useData } from "../context/DataContext";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  RadialBarChart,
  RadialBar,
} from "recharts";

const actionColor = (action) => {
  if (action === "BUY")
    return "text-green-400 bg-green-400/10 border border-green-400/30";
  if (action === "AVOID")
    return "text-red-400 bg-red-400/10 border border-red-400/30";
  return "text-yellow-400 bg-yellow-400/10 border border-yellow-400/30";
};

function StatCard({ label, value, color }) {
  return (
    <div className="bg-[#0F172A] rounded-xl p-4 border border-slate-700/50 flex flex-col gap-1">
      <span className="text-xs text-slate-400 uppercase tracking-widest">
        {label}
      </span>
      <span className={`text-xl font-bold ${color || "text-[#E2E8F0]"}`}>
        {value}
      </span>
    </div>
  );
}

function GaugeBar({ label, value, max, color }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-xs text-slate-400">{label}</span>
        <span className="text-xs font-semibold" style={{ color }}>
          {value}
        </span>
      </div>
      <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

export default function Opportunity() {
  const { symbol } = useParams();
  const { data } = useData();
  const navigate = useNavigate();

  if (!data)
    return (
      <div className="flex items-center justify-center h-[80vh]">
        <p className="text-slate-400">No data loaded. Go back to Dashboard.</p>
      </div>
    );

  const decoded = decodeURIComponent(symbol);
  const record = data.all_opportunities?.find((o) => o.symbol === decoded);

  if (!record)
    return (
      <div className="flex items-center justify-center h-[80vh]">
        <div className="text-center">
          <p className="text-slate-400 mb-4">Symbol not found: {decoded}</p>
          <button
            onClick={() => navigate("/")}
            className="text-accent underline text-sm"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );

  const d = record.data;
  const dec = d.decision;
  const bt = d.backtest;
  const ml = bt.ml_model || {};
  const mlExp = d.ml_explanation;
  const why = d.why || [];

  const topFeatures = ml.top_features || [];
  const maxImportance = Math.max(...topFeatures.map((f) => f[1]), 0.01);
  const featureData = topFeatures.map((f) => ({
    name: f[0]
      .replace(/_/g, " ")
      .replace("norm", "")
      .replace("pct", "%")
      .trim(),
    value: Math.round(f[1] * 100),
  }));

  const featureColors = ["#38BDF8", "#22C55E", "#F59E0B", "#A78BFA", "#FB7185"];

  return (
    <div className="max-w-7xl mx-auto pt-8 pb-8 px-4 space-y-6">
      {/* Back + Symbol Selector */}
      <div className="sticky top-16 z-40 bg-[#0F172A]/95 backdrop-blur-sm pb-2 pt-1 flex items-center justify-between">
        <button
          onClick={() => navigate("/")}
          className="text-slate-400 hover:text-accent text-sm flex items-center gap-2 transition-colors"
        >
          ← Back to Dashboard
        </button>
        <select
          value={decoded}
          onChange={(e) =>
            navigate(`/opportunity/${encodeURIComponent(e.target.value)}`)
          }
          className="bg-[#1E293B] border border-slate-600 text-slate-300 text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-accent"
        >
          {data.all_opportunities?.map((o) => (
            <option key={o.symbol} value={o.symbol}>
              {o.symbol.replace(".NS", "")} — {o.data.decision.action}
            </option>
          ))}
        </select>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">
            {decoded.replace(".NS", "")}
          </h1>
          <p className="text-slate-400 text-sm mt-1">{decoded} — NSE India</p>
        </div>
        <span
          className={`text-sm font-bold px-4 py-2 rounded-lg border ${actionColor(dec.action)}`}
        >
          {dec.action}
        </span>
      </div>

      {/* Signal Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <StatCard
          label="Action"
          value={dec.action}
          color={
            dec.action === "BUY"
              ? "text-green-400"
              : dec.action === "AVOID"
                ? "text-red-400"
                : "text-yellow-400"
          }
        />
        <StatCard
          label="Confidence"
          value={`${Math.round(dec.confidence * 100)}%`}
          color="text-[#38BDF8]"
        />
        <StatCard label="Risk Level" value={dec.risk} />
        <StatCard label="Signal Type" value={d.signals?.[0]?.type || "N/A"} />
        <StatCard
          label="ML AUC"
          value={dec.ml_auc ?? "N/A"}
          color={dec.ml_auc >= 0.55 ? "text-green-400" : "text-yellow-400"}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AI Analyst Brief */}
        <div className="bg-[#1E293B] rounded-xl border border-[#38BDF8]/30 p-6">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-2 h-2 rounded-full bg-accent animate-pulse" />
            <h2 className="text-accent font-semibold text-sm uppercase tracking-widest">
              AI Analyst Brief
            </h2>
          </div>

          <p className="text-white font-semibold mb-1">
            {decoded.replace(".NS", "")} — {dec.action}
          </p>
          <p className="text-slate-400 text-sm mb-4">
            Confidence: {Math.round(dec.confidence * 100)}%
          </p>

          <div className="space-y-4">
            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wider mb-2">
                Why this opportunity exists
              </p>
              {why.length > 0 ? (
                why.map((w, i) => (
                  <p key={i} className="text-slate-300 text-sm">
                    • {w}
                  </p>
                ))
              ) : (
                <p className="text-slate-300 text-sm">• {d.reasoning}</p>
              )}
            </div>

            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wider mb-2">
                Historical Evidence
              </p>
              <p className="text-slate-300 text-sm">
                • Win Rate: {Math.round(bt.win_rate * 100)}%
              </p>
              <p className="text-slate-300 text-sm">
                • Average Return: {(bt.avg_return * 100).toFixed(2)}%
              </p>
              <p className="text-slate-300 text-sm">
                • Sharpe Ratio: {bt.sharpe}
              </p>
            </div>

            <div>
              <p className="text-xs text-slate-400 uppercase tracking-wider mb-2">
                Risk Factors
              </p>
              <p className="text-slate-300 text-sm">
                • Maximum drawdown: {(bt.max_drawdown * 100).toFixed(2)}%
              </p>
              <p className="text-slate-300 text-sm">
                • Volatility (Std Dev): {(bt.std_dev * 100).toFixed(2)}%
              </p>
            </div>
          </div>
        </div>

        {/* ML Explainability */}
        <div className="bg-[#1E293B] rounded-xl border border-slate-700/50 p-6">
          <h2 className="text-sm font-semibold text-[#E2E8F0] uppercase tracking-widest mb-4">
            ML Explainability
          </h2>

          {mlExp ? (
            <div className="mb-4 p-3 bg-[#0F172A] rounded-lg border border-accent/20">
              <p className="text-accent text-sm font-medium">
                ML predicts {mlExp.probability}% win probability driven by:
              </p>
              {mlExp.drivers?.map((d, i) => (
                <p key={i} className="text-slate-300 text-sm mt-1">
                  • {d}
                </p>
              ))}
            </div>
          ) : (
            <div className="mb-4 p-3 bg-[#0F172A] rounded-lg border border-yellow-400/20">
              <p className="text-yellow-400 text-sm">
                ML model not reliable for this asset (AUC &lt; 0.55)
              </p>
            </div>
          )}

          {featureData.length > 0 && (
            <>
              <p className="text-xs text-slate-400 uppercase tracking-wider mb-3">
                Feature Importance
              </p>
              <ResponsiveContainer width="100%" height={150}>
                <BarChart
                  data={featureData}
                  layout="vertical"
                  margin={{ left: 10, right: 20 }}
                >
                  <XAxis
                    type="number"
                    tick={{ fill: "#94a3b8", fontSize: 11 }}
                  />
                  <YAxis
                    type="category"
                    dataKey="name"
                    tick={{ fill: "#94a3b8", fontSize: 11 }}
                    width={100}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1E293B",
                      border: "1px solid #334155",
                      borderRadius: 8,
                    }}
                    formatter={(v) => [`${v}%`, "Importance"]}
                  />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {featureData.map((_, i) => (
                      <Cell
                        key={i}
                        fill={featureColors[i % featureColors.length]}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </>
          )}

          <div className="grid grid-cols-2 gap-3 mt-4">
            <div className="bg-[#0F172A] rounded-lg p-3">
              <p className="text-xs text-slate-400">Validation AUC</p>
              <p className="text-white font-semibold">{ml.val_auc ?? "N/A"}</p>
            </div>
            <div className="bg-[#0F172A] rounded-lg p-3">
              <p className="text-xs text-slate-400">Accuracy</p>
              <p className="text-white font-semibold">
                {ml.val_accuracy ?? "N/A"}
              </p>
            </div>
            <div className="bg-[#0F172A] rounded-lg p-3">
              <p className="text-xs text-slate-400">Train Samples</p>
              <p className="text-white font-semibold">
                {ml.train_size ?? "N/A"}
              </p>
            </div>
            <div className="bg-[#0F172A] rounded-lg p-3">
              <p className="text-xs text-slate-400">Test Samples</p>
              <p className="text-white font-semibold">
                {ml.test_size ?? "N/A"}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Historical Performance Gauges */}
      <div className="bg-[#1E293B] rounded-xl border border-slate-700/50 p-6">
        <h2 className="text-sm font-semibold text-[#E2E8F0] uppercase tracking-widest mb-6">
          Historical Strategy Metrics
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {[
            {
              label: "Win Rate",
              value: Math.round(bt.win_rate * 100),
              max: 100,
              unit: "%",
              color: "#22C55E",
            },
            {
              label: "Avg Return",
              value: parseFloat((bt.avg_return * 100).toFixed(2)),
              max: 15,
              unit: "%",
              color: "#38BDF8",
            },
            {
              label: "Sharpe Ratio",
              value: parseFloat(bt.sharpe),
              max: 2,
              unit: "",
              color: "#A78BFA",
            },
            {
              label: "Max Drawdown",
              value: Math.abs(parseFloat((bt.max_drawdown * 100).toFixed(1))),
              max: 50,
              unit: "%",
              color: "#EF4444",
            },
          ].map((g, i) => (
            <div key={i} className="flex flex-col items-center">
              <ResponsiveContainer width="100%" height={120}>
                <RadialBarChart
                  cx="50%"
                  cy="80%"
                  innerRadius="60%"
                  outerRadius="90%"
                  startAngle={180}
                  endAngle={0}
                  data={[
                    {
                      value: Math.min((g.value / g.max) * 100, 100),
                      fill: g.color,
                    },
                  ]}
                >
                  <RadialBar
                    dataKey="value"
                    cornerRadius={4}
                    background={{ fill: "#0F172A" }}
                  />
                </RadialBarChart>
              </ResponsiveContainer>
              <p className="text-lg font-bold -mt-6" style={{ color: g.color }}>
                {g.value}
                {g.unit}
              </p>
              <p className="text-xs text-slate-400 mt-1">{g.label}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-3 gap-4 mt-6">
          <StatCard label="Total Trades" value={bt.trades} />
          <StatCard
            label="Std Deviation"
            value={`${(bt.std_dev * 100).toFixed(2)}%`}
          />
          <StatCard
            label="ML Prediction"
            value={
              dec.ml_prediction != null
                ? `${(dec.ml_prediction * 100).toFixed(1)}%`
                : "N/A"
            }
            color="text-[#38BDF8]"
          />
        </div>
      </div>
    </div>
  );
}
