import { useState } from "react";
import { useData } from "../context/DataContext";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  AreaChart,
  Area,
} from "recharts";

function StatCard({ label, value, color, sub }) {
  return (
    <div className="bg-[#0F172A] rounded-xl p-5 border border-slate-700/50 flex flex-col gap-1">
      <span className="text-xs text-slate-400 uppercase tracking-widest">
        {label}
      </span>
      <span className={`text-2xl font-bold ${color || "text-[#E2E8F0]"}`}>
        {value}
      </span>
      {sub && <span className="text-xs text-slate-500">{sub}</span>}
    </div>
  );
}

export default function Simulator() {
  const { data, loading } = useData();
  const [amount, setAmount] = useState(100000);
  const [simulated, setSimulated] = useState(null);

  if (loading)
    return (
      <div className="flex items-center justify-center h-[80vh]">
        <div className="w-12 h-12 border-2 border-[#38BDF8] border-t-transparent rounded-full animate-spin" />
      </div>
    );

  if (!data) return null;

  const portfolio = data.portfolio || {};
  const positions = portfolio.positions || [];
  const expectedReturn = (portfolio.returns_pct || 0) / 100;

  const simulate = () => {
    const worst = Math.round(amount * (1 + expectedReturn * 0.5));
    const expected = Math.round(amount * (1 + expectedReturn));
    const best = Math.round(amount * (1 + expectedReturn * 1.5));

    const allocations = positions.map((p) => ({
      symbol: p.symbol.replace(".NS", ""),
      amount: Math.round(amount * (p.allocation_pct / 100)),
      pct: p.allocation_pct,
    }));

    const distributionData = [
      { label: "Worst Case", value: worst, color: "#EF4444" },
      { label: "Expected", value: expected, color: "#38BDF8" },
      { label: "Best Case", value: best, color: "#22C55E" },
    ];

    setSimulated({ worst, expected, best, allocations, distributionData });
  };

  return (
    <div className="max-w-7xl mx-auto pt-8 pb-8 px-4 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Investment Simulator</h1>
        <p className="text-slate-400 text-sm mt-1">
          Simulate portfolio outcomes based on historical strategy performance
        </p>
      </div>

      {/* Input */}
      <div className="bg-[#1E293B] rounded-xl border border-slate-700/50 p-6">
        <h2 className="text-sm font-semibold text-[#E2E8F0] uppercase tracking-widest mb-4">
          Simulate Your Investment
        </h2>
        <div className="flex flex-col md:flex-row gap-4 items-end">
          <div className="flex-1">
            <label className="text-xs text-slate-400 uppercase tracking-wider block mb-2">
              Investment Amount (₹)
            </label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(Number(e.target.value))}
              className="w-full bg-[#0F172A] border border-slate-600 rounded-lg px-4 py-3 text-white text-lg focus:outline-none focus:border-accent"
              min={1000}
              step={10000}
            />
          </div>
          <button
            onClick={simulate}
            className="bg-accent text-bg font-bold px-8 py-3 rounded-lg hover:opacity-90 transition-opacity text-sm uppercase tracking-wider"
          >
            Simulate Portfolio
          </button>
        </div>

        {positions.length > 0 && (
          <div className="mt-4 p-4 bg-[#0F172A] rounded-lg">
            <p className="text-xs text-slate-400 uppercase tracking-wider mb-2">
              Based on strategy return of {portfolio.returns_pct}%
            </p>
            <div className="flex gap-6 flex-wrap">
              {positions.map((p) => (
                <div key={p.symbol} className="text-sm">
                  <span className="text-slate-400">
                    {p.symbol.replace(".NS", "")}:
                  </span>
                  <span className="text-white ml-1 font-semibold">
                    {p.allocation_pct}%
                  </span>
                  <span className="text-slate-500 ml-1 text-xs">
                    (Kelly {p.kelly_fraction})
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Results */}
      {simulated && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <StatCard
              label="Worst Case"
              value={`₹${simulated.worst.toLocaleString()}`}
              color="text-red-400"
              sub={`+${Math.round(expectedReturn * 0.5 * 100)}% return`}
            />
            <StatCard
              label="Expected Case"
              value={`₹${simulated.expected.toLocaleString()}`}
              color="text-[#38BDF8]"
              sub={`+${portfolio.returns_pct}% return`}
            />
            <StatCard
              label="Best Case"
              value={`₹${simulated.best.toLocaleString()}`}
              color="text-green-400"
              sub={`+${Math.round(expectedReturn * 1.5 * 100)}% return`}
            />
          </div>

          {/* Allocation Breakdown */}
          <div className="bg-[#1E293B] rounded-xl border border-slate-700/50 p-6">
            <h2 className="text-sm font-semibold text-[#E2E8F0] uppercase tracking-widest mb-4">
              Recommended Allocation
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {simulated.allocations.map((a, i) => (
                <div
                  key={a.symbol}
                  className="bg-[#0F172A] rounded-lg p-4 flex justify-between items-center"
                >
                  <div>
                    <p className="text-white font-semibold">{a.symbol}</p>
                    <p className="text-slate-400 text-xs mt-0.5">
                      {a.pct}% of portfolio
                    </p>
                  </div>
                  <p className="text-accent font-bold text-lg">
                    ₹{a.amount.toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Distribution Chart */}
          <div className="bg-[#1E293B] rounded-xl border border-slate-700/50 p-6">
            <h2 className="text-sm font-semibold text-[#E2E8F0] uppercase tracking-widest mb-6">
              Outcome Distribution
            </h2>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart
                data={simulated.distributionData}
                margin={{ top: 10, right: 20, left: 20, bottom: 10 }}
              >
                <XAxis
                  dataKey="label"
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                />
                <YAxis
                  tick={{ fill: "#94a3b8", fontSize: 12 }}
                  tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1E293B",
                    border: "1px solid #334155",
                    borderRadius: 8,
                  }}
                  formatter={(v) => [
                    `₹${v.toLocaleString()}`,
                    "Portfolio Value",
                  ]}
                />
                <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                  {simulated.distributionData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>

            <div className="mt-4 p-4 bg-[#0F172A] rounded-lg">
              <p className="text-slate-400 text-xs">
                Outcomes are estimated based on historical strategy performance
                of {portfolio.returns_pct}%. Worst case assumes 50% of expected
                return. Best case assumes 150% of expected return. Past
                performance does not guarantee future results.
              </p>
            </div>
          </div>
        </>
      )}

      {!simulated && (
        <div className="bg-[#1E293B] rounded-xl border border-slate-700/50 p-12 flex items-center justify-center">
          <div className="text-center">
            <p className="text-slate-400 text-lg">
              Enter an amount and click Simulate Portfolio
            </p>
            <p className="text-slate-500 text-sm mt-2">
              See worst, expected, and best case outcomes
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
