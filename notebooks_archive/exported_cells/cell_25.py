# =============================================================================
# 📉 Monte Carlo Analysis (B): Stocks/Bonds + correlation + account allocations
# =============================================================================
# Approach B inputs add:
#   - Stock + bond return distributions (mean/std)
#   - Stock/bond correlation
#   - Account allocation weights (stock %) for IRA/Roth/Taxable
#   - Optional taxable drag (tax friction)
# =============================================================================

print("═" * 80)
print("📉 MONTE CARLO (B): STOCKS/BONDS + CORRELATION + ACCOUNT ALLOCATIONS")
print("═" * 80)

# ----------------------------
# 1) Monte Carlo INPUTS (edit these)
# ----------------------------
MC_N_SIMS = 5_000
MC_HORIZON_YEARS = 25
MC_SEED = 42

# Asset return assumptions (annual, nominal)
MC_STOCK_MEAN = 0.08
MC_STOCK_STD = 0.18
MC_BOND_MEAN = 0.04
MC_BOND_STD = 0.07
MC_STOCK_BOND_CORR = 0.10  # typical low positive / near-zero correlation

# Inflation assumptions
MC_INFL_MEAN = INFLATION_RATE
MC_INFL_STD = 0.01

# Account allocations (stock weight). These match your Chapter 1 comments.
IRA_STOCK_WT = 0.60
ROTH_STOCK_WT = 0.80
TAXABLE_STOCK_WT = 0.70

# Optional tax drag on taxable returns (very simplified).
# Example: 0.50% means subtract 0.005 from the taxable portfolio return each year.
MC_TAXABLE_DRAG = 0.005

# Safety clamps
MC_ASSET_RETURN_MIN = -0.95
MC_ASSET_RETURN_MAX = 1.00
MC_INFL_MIN = -0.02
MC_INFL_MAX = 0.20

# Strategies to run (all 3)
MC_STRATEGIES = [
    dict(name="Conservative (100K x 5, ≤24%)", annual_conversion=100_000, conversion_years=5, allow_32_bracket=False),
    dict(name="Aggressive (175K x 8, allow 32%)", annual_conversion=175_000, conversion_years=8, allow_32_bracket=True),
    dict(name="Very Aggressive (200K x 10, allow 32%)", annual_conversion=200_000, conversion_years=10, allow_32_bracket=True),
 ]

# ----------------------------
# 2) Simulation helpers (apples-to-apples paths)
# ----------------------------
def _simulate_asset_paths_B(*, n_sims: int, horizon_years: int, seed: Optional[int]):
    rng = np.random.default_rng(seed)
    # Correlated normals for stock/bond returns
    corr = float(MC_STOCK_BOND_CORR)
    corr = max(-0.99, min(0.99, corr))
    cov = np.array([[MC_STOCK_STD**2, corr * MC_STOCK_STD * MC_BOND_STD],
                    [corr * MC_STOCK_STD * MC_BOND_STD, MC_BOND_STD**2]], dtype=float)
    L = np.linalg.cholesky(cov)
    z = rng.normal(size=(n_sims, horizon_years, 2))
    shocks = z @ L.T
    stock = MC_STOCK_MEAN + shocks[..., 0]
    bond = MC_BOND_MEAN + shocks[..., 1]
    stock = np.clip(stock, MC_ASSET_RETURN_MIN, MC_ASSET_RETURN_MAX)
    bond = np.clip(bond, MC_ASSET_RETURN_MIN, MC_ASSET_RETURN_MAX)

    infl = rng.normal(loc=MC_INFL_MEAN, scale=MC_INFL_STD, size=(n_sims, horizon_years))
    infl = np.clip(infl, MC_INFL_MIN, MC_INFL_MAX)
    return stock, bond, infl

def _portfolio_return(stock_r: np.ndarray, bond_r: np.ndarray, stock_wt: float) -> np.ndarray:
    w = float(stock_wt)
    w = max(0.0, min(1.0, w))
    return w * stock_r + (1.0 - w) * bond_r

def run_monte_carlo_B(*, strategy: dict, stock: np.ndarray, bond: np.ndarray, infl: np.ndarray, horizon_years: int):
    rows = []
    for sim in range(stock.shape[0]):
        stock_r = stock[sim]
        bond_r = bond[sim]
        infl_r = infl[sim]

        ira_r = _portfolio_return(stock_r, bond_r, IRA_STOCK_WT)
        roth_r = _portfolio_return(stock_r, bond_r, ROTH_STOCK_WT)
        taxable_r = _portfolio_return(stock_r, bond_r, TAXABLE_STOCK_WT) - MC_TAXABLE_DRAG

        out = project_with_tax_tracking(
            annual_conversion=strategy["annual_conversion"],
            conversion_years=strategy["conversion_years"],
            allow_32_bracket=strategy["allow_32_bracket"],
            total_pretax=TOTAL_PRETAX,
            total_roth=TOTAL_ROTH,
            joint_taxable=JOINT_TAXABLE_ACCOUNTS,
            spouse1_age=SPOUSE1_AGE,
            spouse2_age=SPOUSE2_AGE,
            spouse1_ss=SPOUSE1_SS_ANNUAL,
            spouse2_ss=SPOUSE2_SS_ANNUAL,
            years_to_s1_ss=years_to_rajesh_ss,
            years_to_s2_ss=years_to_terri_ss,
            annual_income=ANNUAL_INCOME_NEED,
            min_cash=MINIMUM_CASH_RESERVE,
            # Scalars for compatibility; series override them
            ira_return=IRA_RETURN,
            roth_return=ROTH_RETURN,
            taxable_return=TAXABLE_RETURN,
            inflation=INFLATION_RATE,
            horizon_years=horizon_years,
            ira_returns=ira_r,
            roth_returns=roth_r,
            taxable_returns=taxable_r,
            inflation_rates=infl_r,
        )

        path = out["yearly_data"]
        totals = np.array([d["ira"] + d["roth"] + d["taxable"] for d in path], dtype=float)
        min_total = float(np.min(totals))
        end_total = float(totals[-1])
        success = min_total > 0.0

        rows.append({
            "strategy": strategy["name"],
            "sim": sim,
            "after_tax": out["after_tax"],
            "legacy": out["legacy"],
            "total_lifetime_tax": out["total_lifetime_tax"],
            "end_total_balance": end_total,
            "min_total_balance": min_total,
            "success": success,
        })
    return pd.DataFrame(rows)

# ----------------------------
# 3) Cleaner summaries
# ----------------------------
def _percentile_table(df: pd.DataFrame, metrics: List[str], ps=(0.05, 0.50, 0.95)) -> pd.DataFrame:
    out = {}
    for m in metrics:
        s = df[m].astype(float)
        out[m] = {f"p{int(p*100)}": float(s.quantile(p)) for p in ps}
    tab = pd.DataFrame(out).T
    tab.index.name = "metric"
    return tab

def _fmt_money(x: float) -> str:
    if np.isnan(x):
        return ""
    ax = abs(x)
    if ax >= 1_000_000:
        return f"${x/1_000_000:,.2f}M"
    return f"${x:,.0f}"

def _print_strategy_summary(label: str, df: pd.DataFrame):
    sr = float(df["success"].mean())
    metrics = ["after_tax", "legacy", "end_total_balance", "min_total_balance", "total_lifetime_tax"]
    pt = _percentile_table(df, metrics, ps=(0.05, 0.25, 0.50, 0.75, 0.95))
    pt = pt.applymap(_fmt_money)
    print(f"\n{label}")
    print(f"Success rate (never hit $0 total): {sr:.1%}")
    display(pt)

# ----------------------------
# 4) Run all strategies under the same simulated market paths
# ----------------------------
stock, bond, infl = _simulate_asset_paths_B(
    n_sims=MC_N_SIMS,
    horizon_years=MC_HORIZON_YEARS,
    seed=MC_SEED,
 )

results = []
for strat in MC_STRATEGIES:
    results.append(run_monte_carlo_B(strategy=strat, stock=stock, bond=bond, infl=infl, horizon_years=MC_HORIZON_YEARS))

mc_all = pd.concat(results, ignore_index=True)

print(f"Simulations per strategy: {MC_N_SIMS:,} | Horizon: {MC_HORIZON_YEARS} years")
print(f"Stocks: mean={MC_STOCK_MEAN:.2%}, std={MC_STOCK_STD:.2%} | Bonds: mean={MC_BOND_MEAN:.2%}, std={MC_BOND_STD:.2%} | corr={MC_STOCK_BOND_CORR:.2f}")
print(f"Inflation: mean={MC_INFL_MEAN:.2%}, std={MC_INFL_STD:.2%} | Taxable drag: {MC_TAXABLE_DRAG:.2%}")
print(f"Allocations (stock %): IRA={IRA_STOCK_WT:.0%}, Roth={ROTH_STOCK_WT:.0%}, Taxable={TAXABLE_STOCK_WT:.0%}")

# Compact comparison
comparison_rows = []
for strat in MC_STRATEGIES:
    name = strat["name"]
    df = mc_all[mc_all["strategy"] == name]
    comparison_rows.append({
        "strategy": name,
        "success_rate": float(df["success"].mean()),
        "after_tax_p50": float(df["after_tax"].quantile(0.50)),
        "after_tax_p05": float(df["after_tax"].quantile(0.05)),
        "after_tax_p95": float(df["after_tax"].quantile(0.95)),
        "lifetime_tax_p50": float(df["total_lifetime_tax"].quantile(0.50)),
    })
comparison = pd.DataFrame(comparison_rows)
comparison["success_rate"] = comparison["success_rate"].map(lambda x: f"{x:.1%}")
comparison["after_tax_p05"] = comparison["after_tax_p05"].map(_fmt_money)
comparison["after_tax_p50"] = comparison["after_tax_p50"].map(_fmt_money)
comparison["after_tax_p95"] = comparison["after_tax_p95"].map(_fmt_money)
comparison["lifetime_tax_p50"] = comparison["lifetime_tax_p50"].map(_fmt_money)
display(comparison)

for strat in MC_STRATEGIES:
    name = strat["name"]
    _print_strategy_summary(name, mc_all[mc_all["strategy"] == name])

# ----------------------------
# 5) Plots (2 overlays + 3rd plot: strategy deltas)
# ----------------------------
fig, axes = plt.subplots(1, 3, figsize=(18, 4))

# Overlay outlines for readability
after_tax_bins = np.histogram_bin_edges(mc_all["after_tax"].astype(float), bins=60)
end_bins = np.histogram_bin_edges(mc_all["end_total_balance"].astype(float), bins=60)
colors = plt.cm.tab10.colors

for i, strat in enumerate(MC_STRATEGIES):
    name = strat["name"]
    df = mc_all[mc_all["strategy"] == name]
    c = colors[i % len(colors)]
    axes[0].hist(df["after_tax"], bins=after_tax_bins, histtype="step", linewidth=2.0, color=c, label=name)
    axes[1].hist(df["end_total_balance"], bins=end_bins, histtype="step", linewidth=2.0, color=c, label=name)
    axes[0].axvline(df["after_tax"].quantile(0.50), color=c, linestyle="--", linewidth=1.5)
    axes[1].axvline(df["end_total_balance"].quantile(0.50), color=c, linestyle="--", linewidth=1.5)

axes[0].set_title("After-tax wealth (MC) — dashed = median")
axes[0].set_xlabel("$")
axes[0].set_ylabel("count")
axes[0].legend(fontsize=8)

axes[1].set_title("Ending total balance (MC) — dashed = median")
axes[1].set_xlabel("$")
axes[1].set_ylabel("count")
axes[1].legend(fontsize=8)

# Third plot: distribution of after-tax differences vs Conservative
base_name = MC_STRATEGIES[0]["name"]
pivot = mc_all.pivot(index="sim", columns="strategy", values="after_tax")
deltas = pd.DataFrame({
    f"Aggressive - {base_name}": pivot[MC_STRATEGIES[1]["name"]] - pivot[base_name],
    f"Very Aggressive - {base_name}": pivot[MC_STRATEGIES[2]["name"]] - pivot[base_name],
})
delta_bins = np.histogram_bin_edges(deltas.stack().astype(float), bins=60)
axes[2].hist(deltas.iloc[:, 0], bins=delta_bins, histtype="step", linewidth=2.0, label=deltas.columns[0])
axes[2].hist(deltas.iloc[:, 1], bins=delta_bins, histtype="step", linewidth=2.0, label=deltas.columns[1])
axes[2].axvline(0.0, color="black", linestyle=":", linewidth=1.5)
axes[2].set_title("After-tax advantage vs Conservative")
axes[2].set_xlabel("$ (positive = better than Conservative)")
axes[2].set_ylabel("count")
axes[2].legend(fontsize=8)

plt.tight_layout()
plt.show()