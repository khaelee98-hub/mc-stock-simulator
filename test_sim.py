"""
Quick test script for Monte Carlo Investment Simulator V2.
No CLI args needed — runs hardcoded test scenarios.
"""

import numpy as np


def test1_single_ticker():
    """테스트 1: 단일 종목 포트폴리오 (기존 유지)"""
    print("=" * 60)
    print("테스트 1: 단일 종목 시뮬레이션 (005930.KS)")
    print("=" * 60)

    from investment_simulator import (
        fetch_historical_data, compute_portfolio_params,
        run_simulation, compute_total_principal,
    )

    tickers = ["005930.KS"]
    weights = [1.0]
    initial = 10_000_000
    monthly = 500_000
    years = 5
    total_months = years * 12
    num_sims = 1000

    stats, price_data = fetch_historical_data(tickers)
    for t in tickers:
        s = stats[t]
        print(f"  {t}: μ={s['mean']*100:.1f}%  σ={s['vol']*100:.1f}%  "
              f"기간={s['history_start']}~{s['history_end']} ({s['history_years']}년)")

    port_mean, port_vol = compute_portfolio_params(stats, tickers, weights)
    print(f"  포트폴리오: μ={port_mean*100:.1f}%  σ={port_vol*100:.1f}%")

    result = run_simulation(tickers, stats, weights, initial, monthly, total_months, num_sims)
    paths = result["portfolio"]
    total_principal = compute_total_principal(initial, monthly, total_months, "monthly")

    finals = paths[:, -1]
    print(f"  투자 원금: ₩{total_principal:,.0f}")
    print(f"  중앙값: ₩{np.median(finals):,.0f}")
    print(f"  수익 확률: {np.mean(finals > total_principal)*100:.1f}%")
    print(f"  paths shape: {paths.shape}")
    assert paths.shape == (num_sims, total_months + 1), f"shape mismatch: {paths.shape}"
    print("  ✓ 테스트 1 통과\n")


def test2_multi_ticker():
    """테스트 2: 다중 종목 — per_ticker_paths 구조 검증"""
    print("=" * 60)
    print("테스트 2: 다중 종목 시뮬레이션 (005930.KS + 000660.KS)")
    print("=" * 60)

    from investment_simulator import fetch_historical_data, run_simulation

    tickers = ["005930.KS", "000660.KS"]
    weights = [0.6, 0.4]
    initial = 10_000_000
    monthly = 500_000
    total_months = 60
    num_sims = 500

    stats, price_data = fetch_historical_data(tickers)
    result = run_simulation(tickers, stats, weights, initial, monthly, total_months, num_sims)

    # Verify per_ticker_paths
    assert "per_ticker" in result, "per_ticker key missing"
    assert "portfolio" in result, "portfolio key missing"

    for t in tickers:
        assert t in result["per_ticker"], f"{t} not in per_ticker"
        assert result["per_ticker"][t].shape == (num_sims, total_months + 1), \
            f"{t} shape: {result['per_ticker'][t].shape}"
        print(f"  {t} per_ticker shape: {result['per_ticker'][t].shape} ✓")

    # Verify portfolio == sum of per_ticker
    recon = sum(result["per_ticker"].values())
    diff = np.max(np.abs(result["portfolio"] - recon))
    assert diff < 1e-6, f"portfolio != sum(per_ticker), max diff={diff}"
    print(f"  portfolio == sum(per_ticker) ✓ (max diff={diff:.2e})")
    print(f"  portfolio shape: {result['portfolio'].shape} ✓")
    print("  ✓ 테스트 2 통과\n")


def test3_ticker_risk_metrics():
    """테스트 3: compute_ticker_risk_metrics() 반환 구조 검증"""
    print("=" * 60)
    print("테스트 3: 종목별 리스크 메트릭스 (005930.KS)")
    print("=" * 60)

    from investment_simulator import fetch_historical_data, compute_ticker_risk_metrics

    tickers = ["005930.KS"]
    stats, price_data = fetch_historical_data(tickers)
    total_months = 60

    metrics = compute_ticker_risk_metrics("005930.KS", stats, price_data, total_months, num_sims=1000)

    # Verify scalar keys
    for key in ["mu", "sigma", "sharpe_median", "sortino_median", "mdd_median", "var95", "cvar95"]:
        assert key in metrics, f"missing key: {key}"
        print(f"  {key}: {metrics[key]:.4f}")

    # Verify array keys
    for key in ["mu_arr", "sigma_arr", "sharpe_arr", "sortino_arr", "mdd_arr", "var_arr"]:
        assert key in metrics, f"missing key: {key}"
        arr = metrics[key]
        assert isinstance(arr, np.ndarray), f"{key} is not ndarray"
        assert arr.shape == (1000,), f"{key} shape: {arr.shape}, expected (1000,)"
        print(f"  {key}: shape={arr.shape} ✓")

    print("  ✓ 테스트 3 통과\n")


def test4_single_ticker_comparison():
    """테스트 4: 종목 1개 비교 탭 렌더링 무오류 확인"""
    print("=" * 60)
    print("테스트 4: 단일 종목 비교 차트 렌더링")
    print("=" * 60)

    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend

    from investment_simulator import (
        fetch_historical_data, compute_ticker_risk_metrics, plot_ticker_comparison,
    )
    from matplotlib.figure import Figure

    tickers = ["005930.KS"]
    weights = [1.0]
    stats, price_data = fetch_historical_data(tickers)

    ticker_metrics = {}
    for t in tickers:
        ticker_metrics[t] = compute_ticker_risk_metrics(t, stats, price_data, 60, num_sims=500)

    fig = Figure(figsize=(14, 16), dpi=80)
    try:
        plot_ticker_comparison(ticker_metrics, tickers, weights, fig=fig)
        print("  단일 종목 비교 차트 렌더링 성공 ✓")
    except Exception as e:
        print(f"  ✗ 렌더링 오류: {e}")
        raise

    print("  ✓ 테스트 4 통과\n")


if __name__ == "__main__":
    print("\n몬테카를로 투자 시뮬레이터 V2 - 테스트 스크립트\n")

    test1_single_ticker()
    test2_multi_ticker()
    test3_ticker_risk_metrics()
    test4_single_ticker_comparison()

    print("=" * 60)
    print("전체 테스트 통과!")
    print("=" * 60)
