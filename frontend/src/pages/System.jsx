export default function System() {
  const architecture = [
    {
      step: "01",
      label: "Market Data",
      desc: "Fetches 2 years of daily OHLCV data for NSE symbols via yfinance",
      color: "#38BDF8",
    },
    {
      step: "02",
      label: "Signal Engine",
      desc: "Detects classical setups: Trend Pullback, Momentum Shift, Volume Breakout, Support Bounce",
      color: "#22C55E",
    },
    {
      step: "03",
      label: "ML Model",
      desc: "GradientBoosting classifier trained on 15 features, validated with AUC gating",
      color: "#A78BFA",
    },
    {
      step: "04",
      label: "Risk Scoring",
      desc: "Kelly criterion sizing, Sharpe weighting, drawdown penalties, reliability adjustment",
      color: "#F59E0B",
    },
    {
      step: "05",
      label: "Portfolio Allocation",
      desc: "Top 3 BUY signals weighted by half-Kelly fractions, compounded simulation",
      color: "#22C55E",
    },
  ];

  const sections = [
    {
      title: "Strategy Philosophy",
      color: "#38BDF8",
      points: [
        "Probability-driven approach — decisions based on statistical edge, not deterministic rules",
        "Signals confirmed using historical success rates, ML probabilities, and multi-factor technical alignment",
        "System avoids trades when market conditions are unfavorable — capital preservation over forced entry",
        "Regime awareness: ADX and MA slope used to detect trending vs choppy markets",
      ],
    },
    {
      title: "Risk Management",
      color: "#22C55E",
      points: [
        "Kelly criterion position sizing — allocates more capital to higher-edge opportunities",
        "Half-Kelly applied (50% of full Kelly) to reduce variance and protect capital",
        "Drawdown penalties in scoring reduce weight of high-return but high-risk signals",
        "Sharpe-weighted scoring rewards consistency over raw return magnitude",
        "Stop loss at 2.5%, take profit at 10% per trade in backtest simulation",
      ],
    },
    {
      title: "Model Transparency",
      color: "#A78BFA",
      points: [
        "Feature importance exposed per symbol — shows which factors drive each ML prediction",
        "AUC threshold of 0.55 required — models below threshold have zero influence on decisions",
        "ML probability and AUC shown explicitly in every recommendation",
        "Human-readable drivers replace raw feature names (atr_pct → rising volatility)",
        "15 features: RSI, MACD, ADX, ATR, MA slopes, volume ratio, momentum, and interaction terms",
      ],
    },
    {
      title: "Performance Interpretation",
      color: "#F59E0B",
      points: [
        "Sharpe ratio measures risk-adjusted returns — higher = more consistent relative to volatility",
        "Max drawdown = largest peak-to-trough loss during the strategy backtest period",
        "Confidence = combined signal strength + historical success rate + ML probability",
        "Outperformance = strategy return minus equal-weight buy-and-hold benchmark return",
        "Compounded growth = final capital / initial capital across all historical trades",
      ],
    },
    {
      title: "System Limitations",
      color: "#EF4444",
      points: [
        "Relies on historical data — cannot guarantee future performance",
        "Market regime shifts or extreme events may cause signals to behave differently",
        "ML probabilities are statistical likelihoods, not guarantees",
        "Backtest results do not account for slippage, brokerage fees, or liquidity constraints",
        "Model retrained per scan — no persistent learning across sessions",
      ],
    },
  ];

  return (
    <div className="max-w-7xl mx-auto pt-8 pb-8 px-4 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">System Overview</h1>
        <p className="text-slate-400 text-sm mt-1">
          Architecture, philosophy, and design principles of AlphaLens AI
        </p>
      </div>

      {/* Identity */}
      <div className="bg-[#1E293B] rounded-xl border border-accent/30 p-6">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-2 h-2 rounded-full bg-accent animate-pulse" />
          <h2 className="text-accent font-semibold text-sm uppercase tracking-widest">
            System Identity
          </h2>
        </div>
        <p className="text-white text-lg font-semibold leading-relaxed">
          AlphaLens AI is an AI-driven trading intelligence system combining
          technical signal detection, machine learning probability modeling, and
          risk-adjusted portfolio construction.
        </p>
        <p className="text-slate-400 text-sm mt-3 leading-relaxed">
          The system analyzes market data, evaluates historical strategy
          performance, and surfaces probabilistic trading opportunities —
          adapting to changing market conditions to optimize capital growth.
        </p>
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: "System", value: "AlphaLens AI" },
            { label: "Version", value: "v1.0" },
            { label: "Model", value: "ML Signal Scorer" },
            { label: "Frequency", value: "Daily / Weekly" },
          ].map((m) => (
            <div key={m.label} className="bg-[#0F172A] rounded-lg p-3">
              <p className="text-xs text-slate-400">{m.label}</p>
              <p className="text-white font-semibold text-sm mt-0.5">
                {m.value}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Architecture */}
      <div className="bg-[#1E293B] rounded-xl border border-slate-700/50 p-6">
        <h2 className="text-sm font-semibold text-[#E2E8F0] uppercase tracking-widest mb-6">
          System Architecture
        </h2>
        <div className="flex flex-col md:flex-row items-start md:items-center gap-2">
          {architecture.map((a, i) => (
            <div key={i} className="flex md:flex-col items-center gap-2 flex-1">
              <div className="flex-1 w-full">
                <div className="bg-[#0F172A] rounded-xl p-4 border border-slate-700/50 hover:border-slate-500/50 transition-colors">
                  <div
                    className="text-xs font-bold mb-1"
                    style={{ color: a.color }}
                  >
                    {a.step}
                  </div>
                  <div className="text-white font-semibold text-sm mb-1">
                    {a.label}
                  </div>
                  <div className="text-slate-400 text-xs leading-relaxed">
                    {a.desc}
                  </div>
                </div>
              </div>
              {i < architecture.length - 1 && (
                <div className="text-slate-600 font-bold text-xl md:rotate-0 rotate-90 px-1">
                  →
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Philosophy sections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {sections.map((s, i) => (
          <div
            key={i}
            className="bg-[#1E293B] rounded-xl border border-slate-700/50 p-6"
          >
            <div className="flex items-center gap-2 mb-4">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: s.color }}
              />
              <h2
                className="text-sm font-semibold uppercase tracking-widest"
                style={{ color: s.color }}
              >
                {s.title}
              </h2>
            </div>
            <ul className="space-y-2">
              {s.points.map((p, j) => (
                <li key={j} className="text-slate-300 text-sm flex gap-2">
                  <span className="text-slate-500 mt-0.5">•</span>
                  <span>{p}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      {/* Research Statement, Model Validation, Statistical Significance */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-[#1E293B] rounded-xl border border-slate-700/50 p-6">
          <h2 className="text-sm font-semibold text-accent uppercase tracking-widest mb-3">
            Research Statement
          </h2>
          <p className="text-slate-300 text-sm leading-relaxed">
            AlphaLens AI is designed as a quantitative research assistant that
            surfaces probabilistic trading opportunities rather than
            deterministic trading signals.
          </p>
        </div>
        <div className="bg-[#1E293B] rounded-xl border border-slate-700/50 p-6">
          <h2 className="text-sm font-semibold text-accent uppercase tracking-widest mb-3">
            Model Validation
          </h2>
          <p className="text-slate-300 text-sm leading-relaxed">
            ML predictions are evaluated using out-of-sample testing and
            AUC-based classification metrics. Model inputs include volatility,
            trend strength, and momentum features derived from market data.
            Backtest results should be interpreted as research evidence rather
            than guaranteed outcomes.
          </p>
        </div>
        <div className="bg-[#1E293B] rounded-xl border border-slate-700/50 p-6">
          <h2 className="text-sm font-semibold text-accent uppercase tracking-widest mb-3">
            Statistical Significance
          </h2>
          <p className="text-slate-300 text-sm leading-relaxed">
            Performance metrics are derived from historical backtests and
            represent empirical observations rather than statistically
            guaranteed results. Trading outcomes may vary due to market regime
            changes, noise, and stochastic price movements.
          </p>
        </div>
      </div>
    </div>
  );
}
