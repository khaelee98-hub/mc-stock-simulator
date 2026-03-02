"""
Monte Carlo Investment Simulator V2 — Core Engine & Entry Point.

Fetches historical stock/ETF data from Yahoo Finance, computes portfolio
parameters, runs per-ticker GBM simulations, and renders charts.
Supports CLI and GUI modes. All monetary values in KRW (₩).
"""

import argparse
import platform
import sys
from datetime import date, datetime

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import yfinance as yf
from dateutil.relativedelta import relativedelta
from matplotlib.figure import Figure
from scipy import stats as scipy_stats

# ── Constants ──
FREQ_LABELS = {"weekly": "매주", "monthly": "매월", "yearly": "연간"}
FREQ_CONTRIB_LABELS = {"weekly": "주간 적립", "monthly": "월간 적립", "yearly": "연간 적립"}


# ═══════════════════════════════════════════
#  Data Functions
# ═══════════════════════════════════════════

def fetch_historical_data(tickers, start_date=None, end_date=None, history_years=25):
    """Download price data via yfinance and compute per-ticker stats.

    Default range: today - history_years ~ today.

    Returns:
        (stats_dict, price_data_dict)
        stats_dict[ticker] = {"mean", "vol", "history_start", "history_end", "history_years"}
        price_data_dict[ticker] = (close_series, daily_returns_series)
    """
    today = date.today()
    if end_date is None:
        end_date = today.strftime("%Y-%m-%d")
    if start_date is None:
        start_date = (today - relativedelta(years=history_years)).strftime("%Y-%m-%d")

    stats = {}
    price_data = {}

    for ticker in tickers:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=True)
        if df.empty:
            raise ValueError(f"'{ticker}' 데이터를 가져올 수 없습니다. 티커를 확인해주세요.")

        # Handle multi-level columns from yf.download
        if isinstance(df.columns, pd.MultiIndex):
            close = df["Close"].iloc[:, 0].dropna()
        else:
            close = df["Close"].dropna()

        daily_returns = close.pct_change().dropna()

        if len(daily_returns) < 20:
            raise ValueError(f"'{ticker}' 데이터가 부족합니다 (거래일 {len(daily_returns)}일).")

        ann_mean = daily_returns.mean() * 252
        ann_vol = daily_returns.std() * np.sqrt(252)

        hist_start = close.index[0]
        hist_end = close.index[-1]
        hist_years = (hist_end - hist_start).days / 365.25

        stats[ticker] = {
            "mean": ann_mean,
            "vol": ann_vol,
            "history_start": hist_start.strftime("%Y-%m-%d"),
            "history_end": hist_end.strftime("%Y-%m-%d"),
            "history_years": round(hist_years, 1),
        }
        price_data[ticker] = (close, daily_returns)

    return stats, price_data


def compute_portfolio_params(stats, tickers, weights):
    """Blend per-asset stats into portfolio expected return and volatility.

    Assumes uncorrelated assets: σ_p = √(Σ wᵢ² σᵢ²).
    Used for display only — simulation uses per-ticker params directly.
    """
    port_mean = sum(w * stats[t]["mean"] for t, w in zip(tickers, weights))
    port_vol = np.sqrt(sum((w * stats[t]["vol"]) ** 2 for t, w in zip(tickers, weights)))
    return port_mean, port_vol


def compute_simulation_months(start=None, end=None, years=None):
    """Convert period arguments to total months."""
    if years is not None:
        return int(years * 12)
    if start and end:
        s = pd.Timestamp(start)
        e = pd.Timestamp(end)
        return max(1, (e.year - s.year) * 12 + (e.month - s.month))
    return 120  # default 10 years


def compute_total_principal(initial, contribution, total_months, contribution_freq):
    """Calculate total invested capital based on frequency."""
    if contribution_freq == "weekly":
        total_contributions = contribution * (52 / 12) * total_months
    elif contribution_freq == "yearly":
        total_contributions = contribution * (total_months // 12)
    else:  # monthly
        total_contributions = contribution * total_months
    return initial + total_contributions


# ═══════════════════════════════════════════
#  Risk Analytics
# ═══════════════════════════════════════════

def compute_mdd_stats(paths):
    """Per-path MDD and recovery period.

    Args:
        paths: np.ndarray shape (num_sims, total_months+1)

    Returns:
        dict with median/mean/p90/worst MDD and median/mean recovery months.
    """
    running_max = np.maximum.accumulate(paths, axis=1)
    # Avoid division by zero
    running_max = np.where(running_max == 0, 1, running_max)
    drawdowns = (paths - running_max) / running_max
    mdd_per_path = drawdowns.min(axis=1)

    # Recovery: months from MDD point back to previous peak
    recovery_months = []
    for i in range(paths.shape[0]):
        mdd_idx = np.argmin(drawdowns[i])
        peak_val = running_max[i, mdd_idx]
        recovered = np.where(paths[i, mdd_idx:] >= peak_val)[0]
        if len(recovered) > 0:
            recovery_months.append(recovered[0])
        else:
            recovery_months.append(paths.shape[1] - mdd_idx)
    recovery_months = np.array(recovery_months)

    return {
        "median_mdd": np.median(mdd_per_path),
        "mean_mdd": np.mean(mdd_per_path),
        "p90_mdd": np.percentile(mdd_per_path, 10),  # 10th percentile = worst 90%
        "worst_mdd": np.min(mdd_per_path),
        "median_recovery": np.median(recovery_months),
        "mean_recovery": np.mean(recovery_months),
    }


def compute_sortino_ratio(port_mean, paths, risk_free_rate=0.04):
    """Downside-deviation-based Sortino ratio from log monthly returns.

    Args:
        port_mean: annualized expected return (scalar or per-path)
        paths: np.ndarray shape (num_sims, total_months+1)
        risk_free_rate: annualized risk-free rate

    Returns:
        float: median Sortino ratio across paths
    """
    # Monthly log returns
    with np.errstate(divide="ignore", invalid="ignore"):
        monthly_returns = np.log(paths[:, 1:] / np.where(paths[:, :-1] == 0, 1, paths[:, :-1]))
    monthly_returns = np.nan_to_num(monthly_returns, nan=0.0, posinf=0.0, neginf=0.0)

    rf_monthly = risk_free_rate / 12
    excess = monthly_returns - rf_monthly
    downside = np.minimum(excess, 0)
    downside_std = np.sqrt(np.mean(downside ** 2, axis=1))

    mean_monthly = np.mean(monthly_returns, axis=1)
    sortino = np.where(
        downside_std > 1e-10,
        (mean_monthly - rf_monthly) / downside_std * np.sqrt(12),
        0.0,
    )
    return float(np.median(sortino))


# ═══════════════════════════════════════════
#  Per-Ticker Risk Metrics (NEW V2)
# ═══════════════════════════════════════════

def compute_ticker_risk_metrics(ticker, stats, price_data, total_months, num_sims=1000):
    """Run bootstrap sampling + standalone single-ticker MC simulation.

    Args:
        ticker: ticker code string
        stats: stats_dict from fetch_historical_data
        price_data: price_data_dict from fetch_historical_data
        total_months: simulation period in months
        num_sims: number of simulation paths (default 1000)

    Returns:
        dict with scalar metrics and array distributions.
    """
    mu = stats[ticker]["mean"]
    sigma = stats[ticker]["vol"]
    rf = 0.04
    initial = 10_000_000  # ₩10M fixed for normalization

    rng = np.random.default_rng()

    # ── Bootstrap μ/σ ──
    daily_returns = price_data[ticker][1].dropna().values
    n_bootstrap = 1000
    sample_size = min(252, len(daily_returns))
    mu_boot = np.zeros(n_bootstrap)
    sigma_boot = np.zeros(n_bootstrap)
    for i in range(n_bootstrap):
        sample = rng.choice(daily_returns, size=sample_size, replace=True)
        mu_boot[i] = sample.mean() * 252
        sigma_boot[i] = sample.std() * np.sqrt(252)

    # ── Single-ticker GBM simulation (no contributions) ──
    drift = (mu - 0.5 * sigma ** 2) / 12
    dt_sqrt = sigma * np.sqrt(1 / 12)
    Z = rng.standard_normal((num_sims, total_months))

    sim_paths = np.zeros((num_sims, total_months + 1))
    sim_paths[:, 0] = initial
    for t in range(1, total_months + 1):
        sim_paths[:, t] = sim_paths[:, t - 1] * np.exp(drift + dt_sqrt * Z[:, t - 1])

    # ── Per-path metrics ──
    # Monthly log returns
    with np.errstate(divide="ignore", invalid="ignore"):
        monthly_log = np.log(sim_paths[:, 1:] / np.where(sim_paths[:, :-1] == 0, 1, sim_paths[:, :-1]))
    monthly_log = np.nan_to_num(monthly_log, nan=0.0, posinf=0.0, neginf=0.0)

    rf_monthly = rf / 12

    # Sharpe per path
    mean_m = np.mean(monthly_log, axis=1)
    std_m = np.std(monthly_log, axis=1)
    sharpe_arr = np.where(std_m > 1e-10, (mean_m - rf_monthly) / std_m * np.sqrt(12), 0.0)

    # Sortino per path
    excess_m = monthly_log - rf_monthly
    downside_m = np.minimum(excess_m, 0)
    downside_std_m = np.sqrt(np.mean(downside_m ** 2, axis=1))
    sortino_arr = np.where(downside_std_m > 1e-10, (mean_m - rf_monthly) / downside_std_m * np.sqrt(12), 0.0)

    # MDD per path
    running_max = np.maximum.accumulate(sim_paths, axis=1)
    running_max = np.where(running_max == 0, 1, running_max)
    dd = (sim_paths - running_max) / running_max
    mdd_arr = dd.min(axis=1) * 100  # percentage

    # VaR: final value as % change from initial
    finals = sim_paths[:, -1]
    var_arr = (finals - initial) / initial * 100

    # VaR/CVaR 95%
    var95 = np.percentile(var_arr, 5)
    cvar95 = float(np.mean(var_arr[var_arr <= var95])) if np.any(var_arr <= var95) else var95

    return {
        "mu": mu,
        "sigma": sigma,
        "sharpe_median": float(np.median(sharpe_arr)),
        "sortino_median": float(np.median(sortino_arr)),
        "mdd_median": float(np.median(mdd_arr)),
        "var95": float(var95),
        "cvar95": float(cvar95),
        "mu_arr": mu_boot,
        "sigma_arr": sigma_boot,
        "sharpe_arr": sharpe_arr,
        "sortino_arr": sortino_arr,
        "mdd_arr": mdd_arr,
        "var_arr": var_arr,
    }


# ═══════════════════════════════════════════
#  Simulation
# ═══════════════════════════════════════════

def _get_contribution(t, contribution, contribution_freq):
    """Calculate contribution for step t."""
    if contribution_freq == "weekly":
        return contribution * 52 / 12
    elif contribution_freq == "yearly":
        return contribution if (t % 12 == 0) else 0.0
    else:  # monthly
        return contribution


def run_simulation(tickers, stats, weights, initial, contribution,
                   total_months, num_sims, contribution_freq="monthly"):
    """Per-ticker independent GBM paths, then sum for portfolio.

    Returns:
        {"portfolio": np.ndarray, "per_ticker": {ticker: np.ndarray}}
    """
    rng = np.random.default_rng()
    per_ticker_paths = {}

    for ticker, w in zip(tickers, weights):
        mu_i = stats[ticker]["mean"]
        vol_i = stats[ticker]["vol"]
        drift_i = (mu_i - 0.5 * vol_i ** 2) / 12
        dt_sqrt = vol_i * np.sqrt(1 / 12)
        Z = rng.standard_normal((num_sims, total_months))

        paths_i = np.zeros((num_sims, total_months + 1))
        # t=0: 0
        # t=1: initial allocation + first contribution, then apply return
        contrib_t1 = _get_contribution(1, contribution, contribution_freq)
        paths_i[:, 1] = (w * initial + contrib_t1 * w) * np.exp(drift_i + dt_sqrt * Z[:, 0])

        for t in range(2, total_months + 1):
            contrib_t = _get_contribution(t, contribution, contribution_freq)
            paths_i[:, t] = (paths_i[:, t - 1] + contrib_t * w) * np.exp(drift_i + dt_sqrt * Z[:, t - 1])

        per_ticker_paths[ticker] = paths_i

    portfolio_paths = sum(per_ticker_paths.values())

    return {"portfolio": portfolio_paths, "per_ticker": per_ticker_paths}


# ═══════════════════════════════════════════
#  Plotting — Portfolio
# ═══════════════════════════════════════════

def _format_krw(value, _=None):
    """Format value as ₩ with commas."""
    if abs(value) >= 1e8:
        return f"₩{value / 1e8:.1f}억"
    elif abs(value) >= 1e4:
        return f"₩{value / 1e4:.0f}만"
    return f"₩{value:,.0f}"


def plot_fan_chart(paths, total_months, start=None, end=None, fig=None):
    """Confidence bands (10-90th, 25-75th) + median + 20 sample paths."""
    if fig is None:
        fig = plt.figure(figsize=(12, 6))
    ax = fig.add_subplot(111)

    months = np.arange(total_months + 1)

    # Percentile bands
    p10 = np.percentile(paths, 10, axis=0)
    p25 = np.percentile(paths, 25, axis=0)
    p50 = np.median(paths, axis=0)
    p75 = np.percentile(paths, 75, axis=0)
    p90 = np.percentile(paths, 90, axis=0)

    ax.fill_between(months, p10, p90, alpha=0.15, color="#5A7A8B", label="10-90th 백분위")
    ax.fill_between(months, p25, p75, alpha=0.3, color="#5A7A8B", label="25-75th 백분위")
    ax.plot(months, p50, color="#8B6F47", linewidth=2, label="중앙값 (50th)")

    # Sample paths
    n_samples = min(20, paths.shape[0])
    for i in range(n_samples):
        ax.plot(months, paths[i], alpha=0.1, color="#6B5B45", linewidth=0.5)

    ax.set_xlabel("개월")
    ax.set_ylabel("포트폴리오 가치")
    ax.set_title("몬테카를로 시뮬레이션 팬 차트")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(_format_krw))
    ax.legend(loc="upper left", fontsize=14)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if fig is None:
        plt.show()
    return fig


def plot_histogram(paths, fig=None):
    """Final portfolio value distribution with percentile markers."""
    finals = paths[:, -1]

    if fig is None:
        fig = plt.figure(figsize=(10, 6))
    ax = fig.add_subplot(111)

    ax.hist(finals, bins=80, alpha=0.7, color="#5A7A8B", edgecolor="white", linewidth=0.3)

    p10 = np.percentile(finals, 10)
    p50 = np.median(finals)
    p90 = np.percentile(finals, 90)

    for val, label, color in [
        (p10, f"10th: {_format_krw(p10)}", "#8B3A3A"),
        (p50, f"중앙값: {_format_krw(p50)}", "#8B6F47"),
        (p90, f"90th: {_format_krw(p90)}", "#5A7A5A"),
    ]:
        ax.axvline(val, color=color, linestyle="--", linewidth=1.5, label=label)

    ax.set_xlabel("최종 포트폴리오 가치")
    ax.set_ylabel("빈도")
    ax.set_title("최종 가치 분포")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_format_krw))
    ax.legend(fontsize=14)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if fig is None:
        plt.show()
    return fig


def plot_trend_chart(ticker, close, daily_returns, mean, vol, fig=None):
    """3-panel: price with MAs, daily returns, rolling volatility."""
    if fig is None:
        fig = plt.figure(figsize=(12, 10))

    # Panel 1: Price with 50/200 MA
    ax1 = fig.add_subplot(3, 1, 1)
    ax1.plot(close.index, close.values, linewidth=1, color="#5A7A8B", label="종가")
    if len(close) >= 50:
        ma50 = close.rolling(50).mean()
        ax1.plot(close.index, ma50.values, linewidth=1, color="#8B6F47", alpha=0.8, label="50일 MA")
    if len(close) >= 200:
        ma200 = close.rolling(200).mean()
        ax1.plot(close.index, ma200.values, linewidth=1, color="#7A8B5A", alpha=0.8, label="200일 MA")
    ax1.set_title(f"{ticker} 주가")
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(_format_krw))
    ax1.legend(fontsize=14)
    ax1.grid(True, alpha=0.3)

    # Panel 2: Daily returns
    ax2 = fig.add_subplot(3, 1, 2)
    colors = ["#5A7A5A" if r >= 0 else "#8B3A3A" for r in daily_returns.values]
    ax2.bar(daily_returns.index, daily_returns.values * 100, width=1, color=colors, alpha=0.6)
    ax2.set_title("일간 수익률 (%)")
    ax2.set_ylabel("%")
    ax2.grid(True, alpha=0.3)

    # Panel 3: Rolling 60-day volatility
    ax3 = fig.add_subplot(3, 1, 3)
    rolling_vol = daily_returns.rolling(60).std() * np.sqrt(252) * 100
    ax3.plot(rolling_vol.index, rolling_vol.values, linewidth=1, color="#8B5A6F")
    ax3.set_title("60일 롤링 변동성 (연환산 %)")
    ax3.set_ylabel("%")
    ax3.grid(True, alpha=0.3)

    fig.suptitle(f"{ticker}  μ={mean * 100:.1f}%  σ={vol * 100:.1f}%", fontsize=16, fontweight="bold")
    fig.tight_layout()

    if fig is None:
        plt.show()
    return fig


def plot_summary_dashboard(paths, tickers, weights, stats, initial, contribution,
                           total_months, contribution_freq, per_ticker_paths,
                           font_scale=100, fig=None):
    """2×2 dashboard with donut charts (V2: pie→donut)."""
    if fig is None:
        fig = plt.figure(figsize=(14, 10))

    finals = paths[:, -1]
    p50 = np.median(finals)
    total_principal = compute_total_principal(initial, contribution, total_months, contribution_freq)
    port_mean, port_vol = compute_portfolio_params(stats, tickers, weights)

    from ticker_db import TICKER_DB
    labels = []
    for t in tickers:
        if t in TICKER_DB:
            labels.append(TICKER_DB[t]["ko"])
        else:
            labels.append(t)

    colors = [
        "#5A7A8B", "#7A8B5A", "#8B5A6F", "#5A6F8B", "#8B7A5A",
        "#6F5A8B", "#5A8B7A", "#8B5A5A", "#6F8B5A", "#8B6F47",
    ]
    pie_colors = colors[: len(tickers)]

    # ── Top-left: Initial allocation donut ──
    ax1 = fig.add_subplot(2, 2, 1)
    wedges1, texts1, autotexts1 = ax1.pie(
        weights, labels=labels, autopct="%1.1f%%", colors=pie_colors,
        wedgeprops={"width": 0.5}, pctdistance=0.75,
        textprops={"fontsize": 16},
    )
    for t in autotexts1:
        t.set_fontsize(15)
    ax1.set_title("초기 비중")
    # Center text
    ax1.text(0, 0, f"₩{initial:,.0f}", ha="center", va="center", fontsize=17, fontweight="bold")

    # ── Top-right: Projected end allocation donut (drift-adjusted median) ──
    ax2 = fig.add_subplot(2, 2, 2)
    end_weights = []
    for t in tickers:
        median_final = np.median(per_ticker_paths[t][:, -1])
        end_weights.append(max(0, median_final))
    total_end = sum(end_weights)
    if total_end > 0:
        end_weights = [w / total_end for w in end_weights]
    else:
        end_weights = weights

    wedges2, texts2, autotexts2 = ax2.pie(
        end_weights, labels=labels, autopct="%1.1f%%", colors=pie_colors,
        wedgeprops={"width": 0.5}, pctdistance=0.75,
        textprops={"fontsize": 16},
    )
    for t in autotexts2:
        t.set_fontsize(15)
    ax2.set_title("예상 최종 비중 (중앙값)")
    ax2.text(0, 0, _format_krw(p50), ha="center", va="center", fontsize=17, fontweight="bold")

    # ── Bottom-left: Key statistics ──
    ax3 = fig.add_subplot(2, 2, 3)
    ax3.axis("off")

    mdd = compute_mdd_stats(paths)
    sortino = compute_sortino_ratio(port_mean, paths)
    sharpe_val = (port_mean - 0.04) / port_vol if port_vol > 0 else 0

    p10 = np.percentile(finals, 10)
    p90 = np.percentile(finals, 90)
    var95 = np.percentile(finals, 5)
    profit_prob = np.mean(finals > total_principal) * 100
    double_prob = np.mean(finals > total_principal * 2) * 100

    text_lines = [
        f"투자 원금: {_format_krw(total_principal)}",
        f"중앙값 결과: {_format_krw(p50)}",
        f"수익/원금: {p50 / total_principal:.2f}x",
        f"",
        f"10th 백분위: {_format_krw(p10)}",
        f"90th 백분위: {_format_krw(p90)}",
        f"",
        f"포트폴리오 μ: {port_mean * 100:.1f}%",
        f"포트폴리오 σ: {port_vol * 100:.1f}%",
        f"Sharpe: {sharpe_val:.2f}",
        f"Sortino: {sortino:.2f}",
        f"",
        f"중앙값 MDD: {mdd['median_mdd'] * 100:.1f}%",
        f"VaR 95%: {_format_krw(var95)}",
        f"",
        f"수익 확률: {profit_prob:.1f}%",
        f"2배 달성 확률: {double_prob:.1f}%",
    ]
    ax3.text(0.05, 0.95, "\n".join(text_lines), transform=ax3.transAxes,
             fontsize=14, verticalalignment="top")
    ax3.set_title("주요 통계")

    # ── Bottom-right: Investment info ──
    ax4 = fig.add_subplot(2, 2, 4)
    ax4.axis("off")

    freq_label = FREQ_LABELS.get(contribution_freq, contribution_freq)
    info_lines = [
        f"초기 투자금: ₩{initial:,.0f}",
        f"정기 적립금: ₩{contribution:,.0f} ({freq_label})",
        f"투자 기간: {total_months}개월 ({total_months / 12:.1f}년)",
        f"총 투자 원금: {_format_krw(total_principal)}",
        f"시뮬레이션 수: {paths.shape[0]:,}",
        f"",
        "─" * 30,
        f"종목 구성:",
    ]
    for t, w, lbl in zip(tickers, weights, labels):
        mu_i = stats[t]["mean"]
        vol_i = stats[t]["vol"]
        info_lines.append(f"  {lbl} ({t}): {w * 100:.1f}%  μ={mu_i * 100:.1f}%  σ={vol_i * 100:.1f}%")

    ax4.text(0.05, 0.95, "\n".join(info_lines), transform=ax4.transAxes,
             fontsize=14, verticalalignment="top")
    ax4.set_title("투자 설정")

    fig.tight_layout()

    if fig is None:
        plt.show()
    return fig


def plot_percentile_bar(paths, initial, contribution, total_months, contribution_freq,
                        font_scale=100, fig=None):
    """Percentile bar chart."""
    finals = paths[:, -1]
    total_principal = compute_total_principal(initial, contribution, total_months, contribution_freq)

    if fig is None:
        fig = plt.figure(figsize=(10, 5))
    ax = fig.add_subplot(111)

    percentiles = [5, 10, 25, 50, 75, 90, 95]
    values = [np.percentile(finals, p) for p in percentiles]
    labels = [f"{p}th" for p in percentiles]

    bar_colors = []
    for v in values:
        if v >= total_principal:
            bar_colors.append("#5A7A5A")
        else:
            bar_colors.append("#8B3A3A")

    bars = ax.barh(labels, values, color=bar_colors, alpha=0.8, height=0.6)

    # Principal line
    ax.axvline(total_principal, color="#8B6F47", linestyle="--", linewidth=1.5,
               label=f"투자 원금: {_format_krw(total_principal)}")

    for bar, val in zip(bars, values):
        ax.text(val, bar.get_y() + bar.get_height() / 2,
                f" {_format_krw(val)}", va="center", fontsize=14)

    ax.set_xlabel("최종 가치")
    ax.set_title("백분위별 최종 포트폴리오 가치")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(_format_krw))
    ax.legend(fontsize=14)
    ax.grid(True, alpha=0.3, axis="x")
    fig.tight_layout()

    if fig is None:
        plt.show()
    return fig


# ═══════════════════════════════════════════
#  Plotting — Per-Ticker Comparison (NEW V2)
# ═══════════════════════════════════════════

ACCENT_COLORS = [
    "#5A7A8B", "#7A8B5A", "#8B5A6F", "#5A6F8B", "#8B7A5A",
    "#6F5A8B", "#5A8B7A", "#8B5A5A", "#6F8B5A", "#8B6F47",
]


def _plot_hist_panel(axes, ticker_metrics, tickers, colors, key, title, ref_line=None):
    """Generic histogram panel: one subplot per ticker, shared X-axis."""
    all_values = np.concatenate([ticker_metrics[t][key] for t in tickers])
    xlim = (np.percentile(all_values, 1), np.percentile(all_values, 99))

    for j, t in enumerate(tickers):
        ax = axes[j] if len(tickers) > 1 else axes
        data = ticker_metrics[t][key]
        ax.hist(data, bins=40, color=colors[j % len(colors)], alpha=1.0, edgecolor="white", linewidth=0.3)
        median_val = np.median(data)
        ax.axvline(median_val, color=colors[j % len(colors)], linestyle="--", linewidth=1.5)
        ax.text(median_val, ax.get_ylim()[1] * 0.85 if ax.get_ylim()[1] > 0 else 1,
                f" {median_val:.2f}", fontsize=14, color=colors[j % len(colors)])

        if ref_line is not None:
            ax.axvline(ref_line, color="#B8A898", linestyle=":", linewidth=1)

        ax.set_xlim(xlim)

        from ticker_db import TICKER_DB
        en_name = TICKER_DB[t]["en"] if t in TICKER_DB else t
        ax.set_title(f"{en_name} ({t})", fontsize=14, loc="left")
        ax.tick_params(labelsize=8)

        if j == 0:
            ax.text(0.5, 1.15, title, transform=ax.transAxes,
                    fontsize=16, fontweight="bold", ha="center", va="bottom")

    return axes


def _plot_hist_mu(axes, ticker_metrics, tickers, colors):
    return _plot_hist_panel(axes, ticker_metrics, tickers, colors, "mu_arr", "수익률 μ (연환산 %)")


def _plot_hist_sigma(axes, ticker_metrics, tickers, colors):
    return _plot_hist_panel(axes, ticker_metrics, tickers, colors, "sigma_arr", "변동성 σ (연환산 %)")


def _plot_hist_sharpe(axes, ticker_metrics, tickers, colors):
    return _plot_hist_panel(axes, ticker_metrics, tickers, colors, "sharpe_arr", "Sharpe Ratio", ref_line=1.0)


def _plot_hist_sortino(axes, ticker_metrics, tickers, colors):
    return _plot_hist_panel(axes, ticker_metrics, tickers, colors, "sortino_arr", "Sortino Ratio", ref_line=1.0)


def _plot_hist_mdd(axes, ticker_metrics, tickers, colors):
    return _plot_hist_panel(axes, ticker_metrics, tickers, colors, "mdd_arr", "MDD (%)")


def _plot_hist_var(axes, ticker_metrics, tickers, colors):
    return _plot_hist_panel(axes, ticker_metrics, tickers, colors, "var_arr", "VaR / CVaR (원금 대비 %)", ref_line=0)


def _plot_scatter_risk_return(ax, ticker_metrics, tickers, weights, colors):
    """Risk-return scatter, bubble size = weight."""
    from ticker_db import TICKER_DB

    for j, (t, w) in enumerate(zip(tickers, weights)):
        sigma_val = ticker_metrics[t]["sigma"] * 100
        mu_val = ticker_metrics[t]["mu"] * 100
        ax.scatter(sigma_val, mu_val, s=w * 3000, color=colors[j % len(colors)],
                   alpha=0.7, edgecolors="white", linewidth=1.5, zorder=3)
        en_name = TICKER_DB[t]["en"] if t in TICKER_DB else t
        ax.annotate(en_name, (sigma_val, mu_val), fontsize=14,
                    xytext=(8, 8), textcoords="offset points")

    all_sigma = [ticker_metrics[t]["sigma"] * 100 for t in tickers]
    all_mu = [ticker_metrics[t]["mu"] * 100 for t in tickers]
    ax.axhline(np.mean(all_mu), color="#B8A898", linestyle=":", linewidth=1)
    ax.axvline(np.mean(all_sigma), color="#B8A898", linestyle=":", linewidth=1)
    ax.set_xlabel("변동성 σ (%)")
    ax.set_ylabel("수익률 μ (%)")
    ax.set_title("리스크-수익 산점도")
    ax.grid(True, alpha=0.3)


def plot_ticker_comparison(ticker_metrics, tickers, weights, fig=None):
    """Master comparison function rendering all panels."""
    N = len(tickers)
    colors = ACCENT_COLORS

    if fig is None:
        total_height = (N * 1.2 + 0.6) * 6 + 4
        fig = Figure(figsize=(14, total_height), dpi=80)

    gs = fig.add_gridspec(
        nrows=7, ncols=2,
        height_ratios=[N, N, N, N, N, N, 3],
        hspace=0.5, wspace=0.35,
    )

    panel_funcs = [
        _plot_hist_mu, _plot_hist_sigma,
        _plot_hist_sharpe, _plot_hist_sortino,
        _plot_hist_mdd, _plot_hist_var,
    ]

    for i, func in enumerate(panel_funcs):
        col = i % 2
        row = i // 2
        sub_gs = gs[row, col].subgridspec(N, 1, hspace=0.4)
        axes = [fig.add_subplot(sub_gs[j]) for j in range(N)]
        if N == 1:
            axes = axes[0]
        func(axes, ticker_metrics, tickers, colors)

    # Scatter at bottom
    ax_scatter = fig.add_subplot(gs[6, :])
    _plot_scatter_risk_return(ax_scatter, ticker_metrics, tickers, weights, colors)

    return fig


# ═══════════════════════════════════════════
#  Font Setup
# ═══════════════════════════════════════════

def setup_matplotlib_korean_font():
    """Auto-detect and configure Korean font for matplotlib."""
    system = platform.system()
    if system == "Windows":
        candidates = ["Malgun Gothic", "맑은 고딕"]
    elif system == "Darwin":
        candidates = ["Apple SD Gothic Neo", "AppleGothic"]
    else:
        candidates = ["Noto Sans KR", "NanumGothic", "UnDotum"]

    from matplotlib import font_manager
    available = {f.name for f in font_manager.fontManager.ttflist}

    for font in candidates:
        if font in available:
            plt.rcParams["font.family"] = font
            break

    plt.rcParams["axes.unicode_minus"] = False


# ═══════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="몬테카를로 투자 시뮬레이터 V2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--gui", action="store_true", help="GUI 모드 실행")
    parser.add_argument("--tickers", nargs="+", help="티커 코드 목록")
    parser.add_argument("--weights", nargs="+", type=float, help="가중치 목록")
    parser.add_argument("--initial", type=float, default=10_000_000, help="초기 투자금 (₩)")
    parser.add_argument("--monthly", type=float, default=500_000, help="정기 적립금 (₩)")
    parser.add_argument("--start", type=str, help="시뮬레이션 시작 (YYYY-MM)")
    parser.add_argument("--end", type=str, help="시뮬레이션 종료 (YYYY-MM)")
    parser.add_argument("--years", type=float, help="투자 기간 (년)")
    parser.add_argument("--simulations", type=int, default=10000, help="시뮬레이션 횟수")
    parser.add_argument("--contribution-freq", choices=["weekly", "monthly", "yearly"],
                        default="monthly", help="적립 주기")
    parser.add_argument("--history-years", type=int, default=25,
                        choices=[15, 20, 25, 30], help="과거 데이터 수집 기간 (년)")
    parser.add_argument("--start-date", type=str, default=None,
                        help="히스토리 데이터 시작일 (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default=None,
                        help="히스토리 데이터 종료일 (YYYY-MM-DD)")
    return parser.parse_args()


def validate_period_args(args, gui_mode=False):
    """Validate and return (start, end, years) from args."""
    if gui_mode:
        return args.get("start"), args.get("end"), args.get("years")

    if args.years is None and args.start is None:
        args.years = 10  # default
    if args.start and not args.end:
        raise ValueError("--start 지정 시 --end 도 필요합니다.")
    if args.end and not args.start:
        raise ValueError("--end 지정 시 --start 도 필요합니다.")
    return args.start, args.end, args.years


def main():
    """Entry point."""
    args = parse_args()

    if args.gui:
        from gui import InvestmentSimulatorGUI
        InvestmentSimulatorGUI().run()
        return

    # CLI mode
    if not args.tickers:
        print("오류: --tickers 를 지정해주세요.")
        sys.exit(1)
    if not args.weights:
        print("오류: --weights 를 지정해주세요.")
        sys.exit(1)
    if len(args.tickers) != len(args.weights):
        print("오류: --tickers 와 --weights 의 개수가 일치해야 합니다.")
        sys.exit(1)
    if abs(sum(args.weights) - 1.0) > 0.01:
        print(f"오류: 가중치 합이 1.0이어야 합니다 (현재: {sum(args.weights):.4f}).")
        sys.exit(1)

    setup_matplotlib_korean_font()

    start, end, years = validate_period_args(args)
    total_months = compute_simulation_months(start, end, years)

    print(f"데이터 수집 중... (과거 {args.history_years}년)")
    stats, price_data = fetch_historical_data(
        args.tickers, args.start_date, args.end_date,
        history_years=args.history_years)

    for t in args.tickers:
        s = stats[t]
        print(f"  {t}: μ={s['mean'] * 100:.1f}%  σ={s['vol'] * 100:.1f}%  "
              f"기간={s['history_start']}~{s['history_end']} ({s['history_years']}년)")

    port_mean, port_vol = compute_portfolio_params(stats, args.tickers, args.weights)
    print(f"\n포트폴리오: μ={port_mean * 100:.1f}%  σ={port_vol * 100:.1f}%")

    print(f"\n시뮬레이션 실행 중... ({args.simulations:,}회, {total_months}개월)")
    result = run_simulation(
        args.tickers, stats, args.weights, args.initial, args.monthly,
        total_months, args.simulations, args.contribution_freq,
    )
    paths = result["portfolio"]

    finals = paths[:, -1]
    total_principal = compute_total_principal(
        args.initial, args.monthly, total_months, args.contribution_freq)

    print(f"\n{'═' * 50}")
    print(f"투자 원금: ₩{total_principal:,.0f}")
    print(f"중앙값 결과: {_format_krw(np.median(finals))}")
    print(f"10th 백분위: {_format_krw(np.percentile(finals, 10))}")
    print(f"90th 백분위: {_format_krw(np.percentile(finals, 90))}")
    print(f"수익 확률: {np.mean(finals > total_principal) * 100:.1f}%")
    print(f"{'═' * 50}")

    # Show plots
    plot_summary_dashboard(
        paths, args.tickers, args.weights, stats, args.initial, args.monthly,
        total_months, args.contribution_freq, result["per_ticker"],
    )
    plot_fan_chart(paths, total_months, start, end)
    plot_histogram(paths)

    for t in args.tickers:
        close, daily_ret = price_data[t]
        plot_trend_chart(t, close, daily_ret, stats[t]["mean"], stats[t]["vol"])

    plot_percentile_bar(paths, args.initial, args.monthly, total_months, args.contribution_freq)
    plt.show()


if __name__ == "__main__":
    main()
