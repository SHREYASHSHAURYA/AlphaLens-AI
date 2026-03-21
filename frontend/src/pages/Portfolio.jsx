import { useData } from "../context/DataContext";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
} from "recharts";

const COLORS = ["#38BDF8", "#22C55E", "#F59E0B", "#A78BFA", "#FB7185"];

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

export default function Portfolio() {
  const { data, loading } = useData();

  if (loading)
    return (
      <div className="flex items-center justify-center h-[80vh]">
        <div className="w-12 h-12 border-2 border-[#38BDF8] border-t-transparent rounded-full animate-spin" />
      </div>
    );

  if (!data) return null;

  const portfolio = data.portfolio || {};
  const pvb = portfolio.performance_vs_benchmark || {};
  const positions = portfolio.positions || [];
  const equityCurve = portfolio.equity_curve || [];
  const drawdownCurve = portfolio.drawdown_curve || [];
  const benchmarkEq = portfolio.benchmark?.equity_curve || [];
  const benchmarkDd = portfolio.benchmark?.drawdown_curve || [];

  const equityData = equityCurve.map((v, i) => ({
    i,
    Strategy: v,
    Benchmark: benchmarkEq[i] ?? null,
  }));

  const drawdownData = drawdownCurve.map((v, i) => ({
    i,
    Strategy: v,
    Benchmark: benchmarkDd[i] ?? null,
  }));

  const pieData = positions.map((p, i) => ({
    name: p.symbol.replace(".NS", ""),
    value: p.allocation_pct,
  }));

  return (
    <div className="max-w-7xl mx-auto pt-8 pb-8 px-4 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">
          Portfolio & Strategy Performance
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Capital allocation, equity growth, and benchmark comparison
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
        <StatCard
          label="Initial Capital"
          value={`₹${portfolio.initial_capital?.toLocaleString()}`}
        />
        <StatCard
          label="Final Capital"
          value={`₹${portfolio.final_capital?.toLocaleString()}`}
          color="text-green-400"
        />
        <StatCard
          label="Strategy Return"
          value={`+${pvb.strategy_return_pct}%`}
          color="text-green-400"
        />
        <StatCard
          label="Benchmark Return"
          value={`${pvb.benchmark_return_pct}%`}
        />
        <StatCard
          label="Outperformance"
          value={`+${pvb.outperformance_pct}%`}
          color="text-[#38BDF8]"
        />
        <StatCard
          label="Max Drawdown"
          value={`${pvb.strategy_max_drawdown_pct}%`}
          color="text-red-400"
        />
        <StatCard
          label="Growth"
          value={`${portfolio.compounded_growth}x`}
          color="text-[#38BDF8]"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pie Chart */}
        <div className="bg-[#1E293B] rounded-xl border border-slate-700/50 p-6">
          <h2 className="text-sm font-semibold text-[#E2E8F0] uppercase tracking-widest mb-4">
            Portfolio Allocation
          </h2>
          {pieData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                  >
                    {pieData.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1E293B",
                      border: "1px solid #334155",
                      borderRadius: 8,
                    }}
                    formatter={(v) => [`${v}%`, "Allocation"]}
                  />
                </PieChart>
              </ResponsiveContainer>

              <div className="mt-4 space-y-3">
                {positions.map((p, i) => (
                  <div
                    key={p.symbol}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: COLORS[i % COLORS.length] }}
                      />
                      <span className="text-slate-300 text-sm">
                        {p.symbol.replace(".NS", "")}
                      </span>
                    </div>
                    <div className="text-right">
                      <span className="text-white text-sm font-semibold">
                        {p.allocation_pct}%
                      </span>
                      <span className="text-slate-400 text-xs ml-2">
                        Kelly: {p.kelly_fraction}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-48">
              <p className="text-slate-500 text-sm">No active positions</p>
            </div>
          )}
        </div>

        {/* Positions Table */}
        <div className="lg:col-span-2 bg-[#1E293B] rounded-xl border border-slate-700/50 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-700/50">
            <h2 className="text-sm font-semibold text-[#E2E8F0] uppercase tracking-widest">
              Portfolio Positions
            </h2>
          </div>
          {positions.length > 0 ? (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700/50">
                  {[
                    "Symbol",
                    "Allocation",
                    "Kelly Fraction",
                    "Exp Return",
                    "Profit",
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
                {positions.map((p, i) => (
                  <tr key={p.symbol} className="border-b border-slate-700/30">
                    <td className="px-4 py-4 font-semibold text-white">
                      {p.symbol.replace(".NS", "")}
                    </td>
                    <td className="px-4 py-4 text-slate-300">
                      {p.allocation_pct}%
                    </td>
                    <td className="px-4 py-4 text-slate-300">
                      {p.kelly_fraction}
                    </td>
                    <td className="px-4 py-4 text-green-400">
                      +{p.expected_return_pct}%
                    </td>
                    <td className="px-4 py-4 text-green-400">
                      ₹{p.profit.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="flex items-center justify-center h-48">
              <p className="text-slate-500 text-sm">
                No active BUY positions — system is preserving capital
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Strategy vs Benchmark */}
      <div className="bg-[#1E293B] rounded-xl border border-slate-700/50 p-6">
        <h2 className="text-sm font-semibold text-[#E2E8F0] uppercase tracking-widest mb-6">
          Strategy vs Market
        </h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={equityData}>
            <XAxis
              dataKey="i"
              tick={{ fill: "#94a3b8", fontSize: 11 }}
              label={{
                value: "Trade Periods",
                position: "insideBottom",
                fill: "#64748b",
                fontSize: 11,
              }}
            />
            <YAxis
              tick={{ fill: "#94a3b8", fontSize: 11 }}
              tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1E293B",
                border: "1px solid #334155",
                borderRadius: 8,
              }}
              formatter={(v, name) => [`₹${v?.toLocaleString()}`, name]}
            />
            <Legend wrapperStyle={{ color: "#94a3b8", fontSize: 12 }} />
            <Line
              type="monotone"
              dataKey="Strategy"
              stroke="#38BDF8"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="Benchmark"
              stroke="#F59E0B"
              strokeWidth={2}
              dot={false}
              strokeDasharray="5 5"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Drawdown Chart */}
      <div className="bg-[#1E293B] rounded-xl border border-slate-700/50 p-6">
        <h2 className="text-sm font-semibold text-[#E2E8F0] uppercase tracking-widest mb-6">
          Drawdown Analysis
        </h2>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={drawdownData}>
            <XAxis dataKey="i" tick={{ fill: "#94a3b8", fontSize: 11 }} />
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
            <Legend wrapperStyle={{ color: "#94a3b8", fontSize: 12 }} />
            <Line
              type="monotone"
              dataKey="Strategy"
              stroke="#EF4444"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="Benchmark"
              stroke="#F59E0B"
              strokeWidth={2}
              dot={false}
              strokeDasharray="5 5"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      {/* Strategy vs Market */}
      <div className="bg-[#1E293B] rounded-xl border border-accent/20 p-6">
        <h2 className="text-sm font-semibold text-accent uppercase tracking-widest mb-4">
          Strategy vs Market
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div className="bg-[#0F172A] rounded-lg p-4">
            <p className="text-xs text-slate-400 mb-1">Strategy Growth</p>
            <p className="text-white font-bold text-lg">
              Rs.1,00,000 →{" "}
              <span className="text-green-400">
                Rs.{portfolio.final_capital?.toLocaleString()}
              </span>
            </p>
          </div>
          <div className="bg-[#0F172A] rounded-lg p-4">
            <p className="text-xs text-slate-400 mb-1">Benchmark Growth</p>
            <p className="text-white font-bold text-lg">
              Rs.1,00,000 →{" "}
              <span className="text-yellow-400">
                Rs.{portfolio.benchmark?.final_capital?.toLocaleString()}
              </span>
            </p>
          </div>
        </div>
        <p className="text-slate-400 text-sm">
          Strategy equity growth is compared against a buy-and-hold benchmark to
          demonstrate the advantage of the signal-driven portfolio approach.
        </p>
      </div>
    </div>
  );
}
