# CLAUDE.md — Monte Carlo Investment Simulator V2

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Monte Carlo investment simulator that fetches historical stock/ETF data from Yahoo Finance, computes portfolio parameters, and runs GBM (Geometric Brownian Motion) simulations to project portfolio outcomes. Supports both CLI and GUI modes. UI is entirely in Korean (한국어).

**V2 Changes from V1:**
1. 테마 단일화 — 라이트(크림/베이지) 단일 테마, 다크 테마 제거
2. 티커 입력 UX 개편 — 영문 회사명 입력 → 자동완성 → 티커코드·한국어명 읽기전용 표시
3. 통화 단위 전환 — 전 UI·차트·테이블 달러($) → 원(₩)
4. 기본 종목 변경 — 4종목 25% 균등 비중 (삼성전자·KODEX200·SK하이닉스·한국항공우주산업)
5. 파이차트 → 도넛차트 (중앙에 총액 텍스트 삽입)
6. 결과창 탭 구조 추가 — 탭1 포트폴리오 결과 / 탭2 종목별 비교 / 탭3 Raw Data
7. 적립 주기 분기(quarterly) 제거 — 매주·매월·연간 3가지만 지원
8. GBM 구조 변경 — 포트폴리오 단일 경로 → 종목별 독립 경로 후 합산

---

## Commands

```bash
# CLI: date range mode (금액 단위: 원)
python investment_simulator.py --tickers 005930.KS 000660.KS --weights 0.6 0.4 \
  --initial 10000000 --monthly 500000 --start 2025-01 --end 2026-01 --simulations 10000

# CLI: years mode
python investment_simulator.py --tickers 005930.KS 000660.KS --weights 0.6 0.4 \
  --initial 10000000 --monthly 500000 --years 20 --simulations 10000

# CLI: with contribution frequency (weekly/monthly/yearly)
python investment_simulator.py --tickers 005930.KS --weights 1.0 \
  --initial 10000000 --monthly 300000 --years 5 --contribution-freq weekly --simulations 1000

# CLI: custom historical data range for parameter estimation
python investment_simulator.py --tickers 005930.KS --weights 1.0 \
  --initial 10000000 --years 10 --start-date 2015-01-01 --end-date 2023-12-31

# GUI mode
python investment_simulator.py --gui

# Quick test script (no CLI args needed)
python test_sim.py

# Install dependencies
pip install -r requirements.txt
```

---

## File Structure

```
├── investment_simulator.py   # Entry point, simulation engine, CLI, plotting
├── gui.py                    # CustomTkinter GUI
├── ticker_db.py              # Ticker database + autocomplete search
├── config.py                 # Font/display config persistence
├── config.json               # User font preferences (persisted, not code)
├── test_sim.py               # Quick test script with hardcoded params
├── requirements.txt          # Python dependencies
└── CLAUDE.md                 # This file
```

---

## Architecture

### `investment_simulator.py` — Core Engine & Entry Point

Entry point (`main()`), core simulation logic, CLI parsing, and all chart rendering.

**Data Functions:**
- `fetch_historical_data(tickers, start_date, end_date)` — Downloads price data via `yf.download()`, computes annualized mean return and volatility per ticker (252 trading days). Returns `(stats_dict, price_data_dict)` where `price_data[ticker] = (close_series, daily_returns_series)`.

  **[V2] 히스토리 데이터 기간 정책:**
  - 기본 수집 범위: 오늘 기준 **25년 전** (`today - 25 years`) ~ 오늘
  - CLI `--start-date` / `--end-date` 미입력 시 자동 적용
  - 종목별 상장일이 25년보다 짧은 경우: `yf.download()` 가 반환하는 **실제 첫 거래일부터 전량 수집** (최장치 fallback)
  - fallback 감지 방법: 반환된 데이터의 `index[0]` 가 요청한 `start_date` 보다 늦으면 자동으로 최장치로 처리 (별도 예외처리 불필요 — yfinance 자체 동작)
  - GUI 모드에서도 동일 정책 적용 (사용자가 `--start-date` 를 별도 지정하지 않는 한)
  - 수집된 실제 기간은 `stats_dict[ticker]["history_start"]` / `"history_end"` / `"history_years"` 에 저장하여 UI 및 대시보드 테이블에 표시 가능하게 함
- `compute_portfolio_params(stats, tickers, weights)` — Blends per-asset stats into portfolio expected return and volatility. **Assumes uncorrelated assets** for portfolio vol: `σ_p = √(Σ wᵢ² σᵢ²)`.
- `compute_simulation_months(start, end, years)` — Converts period args to total months.
- `compute_total_principal(initial, contribution, total_months, contribution_freq)` — Calculates total invested capital based on frequency.

**Risk Analytics:**
- `compute_mdd_stats(paths)` — Per-path MDD and recovery period calculation. Returns dict with median/mean/p90/worst MDD and median/mean recovery months.
- `compute_sortino_ratio(port_mean, paths, risk_free_rate)` — Downside-deviation-based Sortino ratio from log monthly returns.

**[NEW V2] Per-Ticker Risk Function:**
- `compute_ticker_risk_metrics(ticker, stats, price_data, total_months, num_sims=1000)` — Runs bootstrap sampling + standalone single-ticker Monte Carlo simulation (1,000 paths, contribution=0, initial=₩10,000,000 고정) and returns a dict:
  ```python
  {
    # 스칼라 (산점도 및 요약용)
    "mu": float,              # stats_dict[ticker]["mean"] — 연환산 수익률 포인트 추정치
    "sigma": float,           # stats_dict[ticker]["vol"]  — 연환산 변동성 포인트 추정치
    "sharpe_median": float,   # np.median(sharpe_arr)
    "sortino_median": float,  # np.median(sortino_arr)
    "mdd_median": float,      # np.median(mdd_arr) — 음수 %
    "var95": float,           # 전체 경로 최종값의 5th percentile (% 정규화)
    "cvar95": float,          # 전체 경로 최종값 중 ≤var95 의 평균 (% 정규화)
    # 배열 (히스토그램용)
    "mu_arr": np.ndarray,       # shape (1000,) — 부트스트랩 연환산 μ 분포
    "sigma_arr": np.ndarray,    # shape (1000,) — 부트스트랩 연환산 σ 분포
    "sharpe_arr": np.ndarray,   # shape (1000,) — 경로별 Sharpe
    "sortino_arr": np.ndarray,  # shape (1000,) — 경로별 Sortino
    "mdd_arr": np.ndarray,      # shape (1000,) — 경로별 MDD (음수 %)
    "var_arr": np.ndarray,      # shape (1000,) — 경로별 최종값 % 변화율
  }
  ```

  **경로별 지표 계산 방법 (구현 명세):**
  - `mu_arr` / `sigma_arr`: `price_data[ticker][1]`(일간수익률) 배열을 1,000회 복원추출(252일) → 연환산 평균/표준편차. **`price_data`를 인자로 받아야 하므로 시그니처에 포함**
  - `sharpe_arr`: 각 경로의 월간 로그수익률 시계열 → `(mean_monthly - rf/12) / std_monthly × sqrt(12)`
  - `sortino_arr`: 각 경로의 월간 로그수익률 시계열 → `compute_sortino_ratio(ticker_mu, single_path_reshaped, rf=0.04)` 호출. **주의: `port_mean` 자리에 반드시 해당 종목의 `ticker_mu`를 전달** (포트폴리오 mu 아님)
  - `mdd_arr`: 각 경로에 `compute_mdd_stats()` 적용 → path별 mdd 값 추출
  - `var_arr`: 각 경로 최종값을 초기값(₩10,000,000) 대비 수익률 %로 정규화 → `(final - 10_000_000) / 10_000_000 × 100`

**Simulation:**
- `run_simulation(tickers, stats, weights, initial, contribution, total_months, num_sims, contribution_freq)` — 종목별 독립 GBM 경로를 생성하고 합산해 포트폴리오 경로를 반환.
  - **V2 변경**: 기존 단일 `(portfolio_mean, portfolio_vol)` 인자 → 종목별 `stats`, `weights` 로 교체
  - Returns:
    ```python
    {
      "portfolio": np.ndarray,  # shape (num_sims, total_months+1) — V_portfolio 합산 경로
      "per_ticker": dict,       # {ticker: np.ndarray shape (num_sims, total_months+1)} — 종목별 경로
    }
    ```
  - 내부 구조:
    ```python
    rng = np.random.default_rng()
    per_ticker_paths = {}
    for ticker, w in zip(tickers, weights):
        mu_i, vol_i = stats[ticker]["mean"], stats[ticker]["vol"]
        drift_i = (mu_i - 0.5 * vol_i**2) / 12
        Z = rng.standard_normal((num_sims, total_months))   # 종목별 독립 샘플
        paths_i = np.zeros((num_sims, total_months + 1))
        # t=1: initial + 첫 스텝 적립금 기초 투입 후 수익률 적용
        contrib_t1 = _get_contribution(1, contribution, contribution_freq)
        paths_i[:, 1] = (w * initial + contrib_t1 * w) \
                        * np.exp(drift_i + vol_i * np.sqrt(1/12) * Z[:, 0])
        # initial, contribution 단위: 원(₩)
        for t in range(2, total_months + 1):
            contrib_t = _get_contribution(t, contribution, contribution_freq)
            paths_i[:, t] = (paths_i[:, t-1] + contrib_t * w) \
                            * np.exp(drift_i + vol_i * np.sqrt(1/12) * Z[:, t-1])
        per_ticker_paths[ticker] = paths_i
    portfolio_paths = sum(per_ticker_paths.values())
    return {"portfolio": portfolio_paths, "per_ticker": per_ticker_paths}
    ```
  - `compute_portfolio_params()` 는 시뮬레이션에 더 이상 사용되지 않음 — 파라미터 참고 표시용으로만 유지

**Plotting:**
- `plot_fan_chart(paths, total_months, start, end, fig)` — Confidence bands (10-90th, 25-75th percentile) + median + 20 sample paths.
- `plot_histogram(paths, fig)` — Final portfolio value distribution with 10th/Median/90th percentile markers.
- `plot_trend_chart(ticker, close, daily_returns, mean, vol, fig)` — 3-panel: price with 50/200-day MA, daily returns bar chart, rolling 60-day annualized volatility.
- `plot_summary_dashboard(paths, ..., font_scale, fig)` — 2×2 grid dashboard. **파이차트 대신 도넛차트** 사용:
  - `ax.pie(..., wedgeprops={"width": 0.5})` — 중앙 구멍 비율 50%
  - 도넛 중앙에 포트폴리오 총액(₩ 포맷) 텍스트 삽입
  - 좌상단: 초기 비중 도넛차트, 우상단: 시뮬레이션 종료 시점 예상 비중 도넛차트 (drift 반영 중앙값 기준)
- `plot_percentile_bar(paths, initial, contribution, total_months, contribution_freq, font_scale, fig)` — Percentile bar chart.

**[NEW V2] Per-Ticker Comparison Plots:**
- `plot_ticker_comparison(ticker_metrics_dict, tickers, weights, fig)` — Master function that renders all panels into a provided `fig`. Called by GUI in the comparison tab.
  - Internally calls the following sub-functions, each drawing into a subplot axis:
  - `_plot_hist_mu(ax, ticker_metrics, tickers, colors)` — 연환산 수익률 μ **부트스트랩 히스토그램** (일간 수익률 배열을 1,000회 리샘플링 → 각 샘플의 연환산 평균 분포)
  - `_plot_hist_sigma(ax, ticker_metrics, tickers, colors)` — 연환산 변동성 σ **부트스트랩 히스토그램** (동일 방식 — 각 샘플의 연환산 표준편차 분포)
  - `_plot_hist_sharpe(ax, ticker_metrics, tickers, colors)` — Sharpe ratio **분포 히스토그램** (시뮬레이션 경로별 계산값 배열)
  - `_plot_hist_sortino(ax, ticker_metrics, tickers, colors)` — Sortino ratio **분포 히스토그램** (경로별 계산값 배열)
  - `_plot_hist_mdd(ax, ticker_metrics, tickers, colors)` — MDD **분포 히스토그램** (경로별 음수값 배열)
  - `_plot_hist_var(ax, ticker_metrics, tickers, colors)` — VaR 95% / CVaR 95% **분포 히스토그램** (경로별 값 배열)
  - `_plot_scatter_risk_return(ax, ticker_metrics, tickers, weights, colors)` — Risk-return scatter, bubble size = weight

  **데이터 타입 구분 (구현 시 핵심):**

  | 함수 | 데이터 타입 | 소스 |
  |---|---|---|
  | `_plot_hist_mu` | np.ndarray (1000,) | 부트스트랩: 일간수익률 배열을 1,000회 복원추출(252일) → 연환산 평균 |
  | `_plot_hist_sigma` | np.ndarray (1000,) | 부트스트랩: 일간수익률 배열을 1,000회 복원추출(252일) → 연환산 표준편차 |
  | `_plot_hist_sharpe` | np.ndarray (1000,) | 경로별 `(월수익률평균 - rf/12) / 월수익률std × sqrt(12)` |
  | `_plot_hist_sortino` | np.ndarray (1000,) | 경로별 downside deviation 기반 |
  | `_plot_hist_mdd` | np.ndarray (1000,) | 경로별 최대 낙폭 % |
  | `_plot_hist_var` | np.ndarray (1000,) | 경로별 최종값 초기값 대비 수익률 % |

  **부트스트랩 μ/σ 계산 명세:**
  ```python
  # fetch_historical_data()에서 반환된 daily_returns 배열 사용
  # price_data[ticker] = (close_series, daily_returns_series)
  daily_returns = price_data[ticker][1].dropna().values  # shape: (거래일수,)
  n_bootstrap = 1000
  sample_size = 252  # 1년치 거래일 — 분포의 연간 불확실성 표현
  rng = np.random.default_rng()
  mu_boot = np.zeros(n_bootstrap)
  sigma_boot = np.zeros(n_bootstrap)
  for i in range(n_bootstrap):
      sample = rng.choice(daily_returns, size=sample_size, replace=True)
      mu_boot[i]    = sample.mean() * 252        # 연환산 평균
      sigma_boot[i] = sample.std() * np.sqrt(252) # 연환산 변동성
  # → mu_boot, sigma_boot 를 ticker_metrics["mu_arr"], ["sigma_arr"] 에 저장
  ```
  부트스트랩은 `compute_ticker_risk_metrics()` 내에서 시뮬레이션과 함께 수행.
  `price_data` 딕셔너리를 인자로 추가로 전달해야 함 → 함수 시그니처:
  `compute_ticker_risk_metrics(ticker, stats, price_data, total_months, num_sims=1000)`

**CLI:**
- `parse_args()` — argparse setup. `--start-date` / `--end-date` 기본값 변경: **기본값 = (today - 25년) ~ today**. `dateutil.relativedelta` 사용. 상장일이 25년보다 짧은 종목은 yfinance 반환 실제 첫 거래일 자동 사용 (최장치 fallback).
- `validate_period_args(args, gui_mode)` — Period validation (unchanged).
- `setup_matplotlib_korean_font()` — Auto-detects Korean font by OS.

**Constants:**
- `FREQ_LABELS` — Korean labels for contribution frequencies (`{"weekly": "매주", "monthly": "매월", "yearly": "연간"}`). 분기(quarterly) 제외.
- `FREQ_CONTRIB_LABELS` — Korean contribution type labels. 분기(quarterly) 제외.

---

### `gui.py` — GUI (CustomTkinter)

`InvestmentSimulatorGUI` class using **CustomTkinter**. Two-panel layout: fixed-width left input panel (440px), expandable right results panel.

---

#### [V2] Theme System — Single Light Theme

Dark theme is **fully removed**. A single `THEME` dict replaces `THEME_DARK` / `THEME_LIGHT`. Theme toggle button is removed from UI.

```python
THEME = {
    # Backgrounds
    "bg":              "#FAF7F2",   # 따뜻한 크림 (메인 배경)
    "surface":         "#F5F0E8",   # 베이지 (서브 배경)
    "card":            "#FFFFFF",   # 카드 배경
    "border":          "#E8E0D0",   # 연한 베이지 보더

    # Accent
    "accent":          "#8B6F47",   # 따뜻한 브라운 (버튼, 강조)
    "accent_hover":    "#7A5F3A",   # 버튼 hover

    # Text
    "text_primary":    "#2C2416",   # 다크 브라운 (메인 텍스트)
    "text_secondary":  "#6B5B45",   # 미디엄 브라운 (서브 텍스트)
    "text_disabled":   "#B8A898",   # 비활성 텍스트

    # Input
    "input_bg":        "#FFFFFF",
    "input_border":    "#D4C9B8",
    "input_focus":     "#8B6F47",

    # Chart
    "chart_bg":        "#FAF7F2",
    "chart_grid":      "#E8E0D0",
    "chart_text":      "#2C2416",
    "chart_spine":     "#D4C9B8",

    # Table
    "table_header_bg": "#EDE5D8",
    "table_row_alt":   "#F8F4EE",

    # Status
    "success":         "#5A7A5A",
    "error":           "#8B3A3A",
    "warning":         "#8B6F47",
}

ACCENT_COLORS = [
    "#5A7A8B",  # 0: 첫 종목 — THEME["accent"]와 구별되는 블루그레이 계열로 변경
    "#7A8B5A", "#8B5A6F", "#5A6F8B", "#8B7A5A",
    "#6F5A8B", "#5A8B7A", "#8B5A5A", "#6F8B5A", "#8B6F47",
]
# ※ THEME["accent"] = "#8B6F47" (브라운) 는 UI 버튼/강조용
# ※ ACCENT_COLORS 는 차트 종목 구분용 — 첫 번째 색을 다르게 하여 UI 요소와 혼동 방지
```

`_setup_chart_style()` applies `THEME` to `plt.rcParams`:
```python
plt.rcParams["figure.facecolor"]  = THEME["chart_bg"]
plt.rcParams["axes.facecolor"]    = THEME["chart_bg"]
plt.rcParams["axes.edgecolor"]    = THEME["chart_spine"]
plt.rcParams["axes.labelcolor"]   = THEME["chart_text"]
plt.rcParams["text.color"]        = THEME["chart_text"]
plt.rcParams["xtick.color"]       = THEME["chart_text"]
plt.rcParams["ytick.color"]       = THEME["chart_text"]
plt.rcParams["grid.color"]        = THEME["chart_grid"]
```

**Removed from V1:**
- `THEME_DARK`, `THEME_LIGHT` dicts
- `_toggle_theme()` function
- Theme toggle button in input panel
- **`_style_figure(fig)` 함수 제거** — 단일 라이트 테마에서는 `_setup_chart_style()` 의 `plt.rcParams` 전역 설정으로 충분. 개별 Figure 후처리 불필요.

---

#### [V2] Ticker Input UX — English-First with Sub-display

**V1 구조 (3컬럼 행):**
```
[회사명(한/영 혼용)] | [티커] | [가중치]
```

**V2 구조 (2컬럼 행 + 서브 표시 영역):**
```
┌─────────────────────────────────┬──────────┐
│  English company name (입력창)   │  가중치   │
├─────────────────────────────────┴──────────┤
│  005930.KS  │  삼성전자           [읽기전용] │  ← sub-display (선택 후 표시)
└────────────────────────────────────────────┘
```

**ticker_rows 튜플 구조 변경:**
```python
# V1
(row_frame, name_var, ticker_var, weight_var)

# V2
(row_frame, eng_name_var, weight_var, ticker_label, korean_name_label)
# ticker_label, korean_name_label: CTkLabel (읽기전용, sub-display 영역)
```

**자동완성 드롭다운 항목 형식:**
```
Samsung Electronics      005930.KS
Apple                    AAPL
SK Hynix                 000660.KS
```
- 영문명 왼쪽 정렬, 티커 오른쪽 정렬 (공백 패딩 또는 grid)
- 선택 시: `eng_name_var` ← 영문명, `ticker_label` ← 티커코드, `korean_name_label` ← 한국어명

**Sub-display 미선택 상태:**
```
티커: —    │    회사명(한): —
```
(회색 비활성 텍스트로 표시)

**Autocomplete 탐색 (변경사항):**
- `search_tickers(query)` 쿼리 대상: 영문명만 (한글 검색 제거)
- `_syncing` 플래그 제거 (단방향이므로 불필요)
- `<Down>` 키 드롭다운 이동, `<Escape>` 닫기 유지

---

#### Spacing Constants (unchanged)

```python
WINDOW_WIDTH=1440, WINDOW_HEIGHT=920
WINDOW_MIN_W=1100, WINDOW_MIN_H=700
LEFT_PANEL_WIDTH=440
CARD_CORNER_RADIUS=12, CARD_PADDING=14, CARD_GAP=10
```

#### Typography (unchanged)

7 font tuples from config: `FONT_TITLE`, `FONT_SECTION`, `FONT_BODY`, `FONT_INPUT`, `FONT_SMALL`, `FONT_MONO`, `FONT_STATUS`

#### Class Constants

```python
MAX_TICKERS = 10

# DEFAULT_TICKERS: 초기 UI 로드용 데이터 튜플 (eng_name, ticker_code, weight, ko_name)
# row_frame은 _add_ticker_row() 호출 시 동적 생성되므로 여기에 포함하지 않음
DEFAULT_TICKERS = [
    ("Samsung Electronics",         "005930.KS", "0.25", "삼성전자"),
    ("KODEX 200",                   "069500.KS", "0.25", "KODEX 200"),
    ("SK Hynix",                    "000660.KS", "0.25", "SK하이닉스"),
    ("Korea Aerospace Industries",  "047810.KS", "0.25", "한국항공우주산업"),
]
```

**`DEFAULT_TICKERS` → `ticker_rows` 로드 흐름 (구현 명세):**
```python
# _reset() 또는 초기화 시:
for eng_name, ticker_code, weight, ko_name in DEFAULT_TICKERS:
    row = _add_ticker_row()          # (row_frame, eng_name_var, weight_var,
                                     #  ticker_label, korean_name_label) 생성
    row[1].set(eng_name)             # eng_name_var
    row[2].set(weight)               # weight_var
    row[3].configure(text=ticker_code)   # ticker_label (CTkLabel)
    row[4].configure(text=ko_name)       # korean_name_label (CTkLabel)
```

---

#### Input Panel (left, 5 cards — unchanged except ticker card)

1. **티커/가중치 카드** — V2 UX 적용 (상세 위 참조)
2. **투자 금액 카드** — 단위: **원(₩)** (달러 사용 금지)
   - 초기 투자금 입력창 우측 레이블: `원`
   - 정기 적립금 입력창 우측 레이블: `원`
   - 기본값: 초기 투자금 `10,000,000` 원, 정기 적립금 `500,000` 원
3. **기간 설정 카드** — 변경 없음
4. **시뮬레이션 설정 카드** — 변경 없음
5. **버튼 카드** — 테마 토글 버튼 제거, 나머지 동일

---

#### [V2] Results Panel — Tab Structure

시뮬레이션 완료 후 오른쪽 패널에 **CTkTabview** 추가:

```
[ 포트폴리오 결과 ]  |  [ 종목별 비교 ]  |  [ Raw Data ]
```

**탭 1: 포트폴리오 결과** (V1 기존 결과 — 파이차트→도넛차트 변경 외 동일)
- Summary dashboard (full width) — **도넛차트** 2개 (초기 비중 / 예상 최종 비중)
- Percentile bar chart (full width)
- 2-column grid: trend charts per ticker, fan chart, histogram

**탭 2: 종목별 비교** (신규)
- `_render_comparison_tab()` 함수로 렌더링
- Figure 크기: 종목 수 N에 따라 동적 결정 — `Figure(figsize=(14, (N×1.2+0.6)×6+4), dpi=80)` (상세는 Comparison Tab Layout 참조)
- `plot_ticker_comparison()` 호출 → `FigureCanvasTkAgg` 임베드
- **[예외처리] 종목 수 == 1이면**: 단독 히스토그램 모드로 렌더링. 범례 없이 해당 종목 분포만 각 패널에 표시. 탭 비활성화 없이 정상 렌더링.

**탭 3: Raw Data** (신규)
- `_render_raw_data_tab()` 함수로 렌더링
- 시뮬레이션에 실제 사용된 과거 주가 데이터를 표 형태로 표시
- 목적: 시뮬레이션 수행 근거 데이터 열람 및 검증

---

#### [V2] Raw Data Tab Layout

**구성 — 종목별 서브섹션 세로 나열:**

```
┌────────────────────────────────────────────────────────────┐
│  [요약 정보 헤더]                                           │
│  데이터 수집 기간: 2000-01-03 ~ 2025-03-02  (25.2년)       │
│  수집 종목: 삼성전자, KODEX200, SK하이닉스, 한국항공우주    │
│  시뮬레이션 실행 시각: 2026-03-02 14:35:22                 │
├────────────────────────────────────────────────────────────┤
│  [종목 탭 or 섹션 선택]                                     │
│  [ 삼성전자 ] [ KODEX200 ] [ SK하이닉스 ] [ 한국항공우주 ] │
├────────────────────────────────────────────────────────────┤
│  선택된 종목 테이블 (스크롤 가능)                           │
│  날짜       │ 종가(₩)  │ 일간수익률(%) │ 60일변동성(%) │   │
│  2000-01-03 │  50,000  │     —         │     —         │   │
│  2000-01-04 │  48,500  │    -3.00%     │     —         │   │
│  ...        │  ...     │    ...        │    ...        │   │
│  2025-03-02 │ 62,100   │    +1.25%     │    28.4%      │   │
├────────────────────────────────────────────────────────────┤
│  [파라미터 요약 테이블]  (전 종목 한 눈에 보기)             │
│  종목명     │ 티커      │ 수집기간  │ μ(연%) │ σ(연%) │    │
│  삼성전자   │005930.KS  │ 25.2년    │ 12.3%  │ 32.1%  │    │
│  KODEX200   │069500.KS  │ 22.1년    │  8.7%  │ 18.4%  │    │
│  SK하이닉스 │000660.KS  │ 25.2년    │ 18.5%  │ 42.3%  │    │
│  한국항공우주│047810.KS │ 15.3년    │ 22.1%  │ 38.7%  │    │
└────────────────────────────────────────────────────────────┘
```

**구현 명세:**

- **전체 컨테이너**: `CTkScrollableFrame` — 내용이 길어도 스크롤 가능
- **요약 헤더**: `CTkLabel` 3줄 — 수집 기간, 종목 목록, 실행 시각
  - 실행 시각: `datetime.now().strftime("%Y-%m-%d %H:%M:%S")` — 시뮬레이션 완료 시점 기록
- **종목 선택**: `CTkSegmentedButton` — 종목 버튼 클릭 시 해당 종목 테이블로 전환
- **종목별 데이터 테이블**: `CTkScrollableFrame` + `CTkLabel` grid 방식
  - 표시 컬럼: `날짜` / `종가(₩)` / `일간수익률(%)` / `60일 롤링 변동성(%)`
  - 날짜 포맷: `YYYY-MM-DD`
  - 종가: `₩{value:,.0f}`
  - 일간수익률: `+X.XX%` / `-X.XX%` — 양수 녹색(`THEME["success"]`), 음수 적색(`THEME["error"]`)
  - 60일 변동성: 처음 59일은 `—` 표시
  - 행 교차 배경색: `THEME["table_row_alt"]` (짝수 행)
  - 헤더 행 배경: `THEME["table_header_bg"]`
  - **성능 주의**: 25년치 일간 데이터 ≈ 6,300행. 전체를 한 번에 렌더링하면 느림. 최신 500행만 기본 표시 후 `[전체 보기]` 버튼으로 확장하는 방식 사용.
- **파라미터 요약 테이블**: 전 종목을 한 행씩 정리
  - 컬럼: `종목명` / `티커` / `수집 기간(년)` / `연환산 수익률 μ(%)` / `연환산 변동성 σ(%)`
  - 데이터 소스: `stats_dict[ticker]` — `history_years`, `mean`, `vol`
  - μ, σ 값은 소수점 1자리 % 포맷: `f"{mean*100:.1f}%"`

**데이터 소스 매핑:**

| 테이블 컬럼 | 소스 |
|---|---|
| 날짜 | `price_data[ticker][0].index` (close_series.index) |
| 종가(₩) | `price_data[ticker][0].values` (close_series) |
| 일간수익률(%) | `price_data[ticker][1].values` (daily_returns_series) |
| 60일 변동성(%) | `price_data[ticker][1].rolling(60).std() × √252` |
| μ | `stats_dict[ticker]["mean"]` |
| σ | `stats_dict[ticker]["vol"]` |
| 수집 기간 | `stats_dict[ticker]["history_years"]` |

> `_last_result` 캐시 전체 구조는 Simulation Flow 섹션을 참조.

---

#### [V2] Comparison Tab Layout

**레이아웃 구조 — 지표별 패널 × 종목별 세로 나열:**

각 지표(6개)마다 하나의 패널 그룹을 구성하고, 그 안에서 종목별 히스토그램을 **위→아래로 나란히 배치**합니다. 전 종목이 **동일한 X축 범위**를 공유하므로 분포 위치를 직접 비교할 수 있습니다.

```
┌────────────────────────────────────────────────────┐
│  지표 A: 수익률 μ              지표 B: 변동성 σ    │
│  ┌──────────────────────┐  ┌──────────────────────┐│
│  │ VOO  ████░░░░░       │  │ VOO  ░░███░░░        ││
│  │ AAPL ░░░░██████░     │  │ AAPL ░░░░░████░      ││
│  │ MSFT ░░████░░░       │  │ MSFT ░░███░░░        ││
│  └──────────────────────┘  └──────────────────────┘│
│       ↑ 공유 X축                   ↑ 공유 X축       │
├────────────────────────────────────────────────────┤
│  지표 C: Sharpe             지표 D: Sortino         │
│  (동일 구조)                 (동일 구조)             │
├────────────────────────────────────────────────────┤
│  지표 E: MDD                지표 F: VaR/CVaR        │
│  (동일 구조)                 (동일 구조)             │
├────────────────────────────────────────────────────┤
│         리스크-수익 산점도 (전체 너비)               │
└────────────────────────────────────────────────────┘
```

**Figure 크기 계산:**
- 종목 수(N)에 따라 Figure 높이 동적 결정
- 각 지표 패널 높이 = `N × 1.2인치 + 0.6인치(제목)` 기준
- `Figure(figsize=(14, (N×1.2+0.6) × 6 + 4), dpi=80)`
  - 예) N=3: `Figure(figsize=(14, 30), dpi=80)`
  - 예) N=1: `Figure(figsize=(14, 16), dpi=80)` (단독 모드)

**Subplot 구조 (matplotlib):**
```python
# 종목 N개, 지표 6개, 산점도 1개
# gridspec: 7행(지표6 + 산점도1) × 2열
# 각 지표 행 높이 = N (종목 수만큼 subplot 세분화)
# 산점도 행 높이 = 3 (고정)

fig = Figure(figsize=(14, total_height), dpi=80)
gs = fig.add_gridspec(
    nrows=7, ncols=2,
    height_ratios=[N, N, N, N, N, N, 3],
    hspace=0.5, wspace=0.35
)
# 각 지표(i)의 종목(j) subplot: gs[i, col].subgridspec(N, 1)
# 산점도: gs[6, :] (두 열 병합)
```

**히스토그램 공통 스펙:**

| 항목 | 값 |
|---|---|
| bins | 40 |
| 방향 | **세로 히스토그램** (가로 X축, 세로 빈도 Y축) — `orientation='vertical'` |
| X축 | **전 종목 동일 범위 고정** (`xlim = (전체 min, 전체 max)`) |
| Y축 | 빈도(count) — 종목별 독립 |
| 색상 | `ACCENT_COLORS[j]` (j = 종목 인덱스) |
| 알파 | 1.0 (불투명 — 종목별 분리 배치이므로 오버레이 없음) |
| 중앙값 선 | 수직 점선, 종목 컬러, 값 라벨 (상단) |
| 종목 라벨 | 각 서브플롯 제목(title) = 영문 회사명 + 티커 |
| 패널 제목 | 각 지표 그룹 최상단에 지표명 표시 |

> **부트스트랩 vs 시뮬레이션 샘플 수 구분:**
> - `n_bootstrap = 1000` — μ/σ 패널용. 일간수익률 배열을 1,000회 복원추출하여 연환산 분포 생성
> - `num_sims = 1000` — Sharpe/Sortino/MDD/VaR 패널용. 종목별 단독 GBM 경로 1,000개
> - 두 값이 우연히 같지만 **별개의 파라미터**이며 독립적으로 변경 가능

**패널별 X축 범위 계산 방법:**
```python
# 해당 지표의 전 종목 배열을 합쳐서 전체 min/max 계산
all_values = np.concatenate([ticker_metrics[t]["mu_arr"] for t in tickers])
xlim = (np.percentile(all_values, 1), np.percentile(all_values, 99))
# 양 극단 1% 제외하여 이상치 영향 차단
# → 모든 종목 서브플롯에 동일 xlim 적용
```

**패널별 상세:**

| 패널 | X축 | 기준선 |
|---|---|---|
| 수익률 μ | 연환산 % (부트스트랩) | — |
| 변동성 σ | 연환산 % (부트스트랩) | — |
| Sharpe | ratio (경로별) | 점선 x=1.0 |
| Sortino | ratio (경로별) | 점선 x=1.0 |
| MDD | % 음수 (경로별) | — |
| VaR / CVaR | % 원금 대비 (경로별) | 점선 x=0 (원금선) |

> **단위 통일 원칙**: 모든 패널 % 기준. VaR/CVaR = `(final - initial) / initial × 100`. $ 절대값 사용 금지.

**산점도 스펙:**
- X축: σ (연환산 변동성 %), Y축: μ (연환산 수익률 %)
- 버블 크기: 포트폴리오 가중치에 비례 (`weight × 3000`)
- 라벨: 영문 회사명 (버블 오른쪽 상단)
- 색상: `ACCENT_COLORS` 순서대로
- 참조선: x=평균σ, y=평균μ 점선 그리드

**종목 1개 예외처리:**
- 오버레이 없이 동일 레이아웃 유지 (세로 나열 종목이 1개뿐)
- 각 패널에 해당 종목 단독 히스토그램 표시
- 산점도는 점 1개 + 라벨만 표시

---

#### [V2] 종목별 비교 탭 — 초보자 도움말

비교 탭 우측 상단에 **`?` 도움말 버튼**을 배치합니다. 클릭하면 `CTkToplevel` 팝업 창이 열리고, 6개 지표 패널의 의미를 초보자도 이해할 수 있는 언어로 설명합니다.

**도움말 버튼 위치:**
```
[ 종목별 비교 탭 상단 ]
┌──────────────────────────────────────────── [?] ┐
│  수익률 μ  │  변동성 σ  │ ...                    │
```
- `CTkButton(text="?", width=28, height=28)` — 작은 원형 버튼
- 색상: `THEME["text_secondary"]` 배경, 흰 글자
- 탭이 렌더링될 때 함께 배치

**도움말 팝업 창 명세:**
- 크기: `500 × 620px`, 창 제목: `"지표 설명"`
- `CTkScrollableFrame` 내부에 지표별 섹션 카드 세로 나열
- 각 카드: 제목(굵게) + 한 줄 요약 + 본문 + 읽는 법

**도움말 텍스트 (전문 — 구현 시 이 텍스트 그대로 사용):**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 수익률 μ (연환산 기대수익률)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1년 동안 평균적으로 얼마나 올랐는지를 나타냅니다.

과거 25년치 일간수익률을 1,000회 무작위 추출(부트스트랩)하여
분포로 표현합니다. 점 하나의 숫자가 아니라 분포로 보여주는 이유는,
같은 종목도 어느 기간을 보느냐에 따라 수익률 추정치가 달라지기 때문입니다.

📌 읽는 법: 분포가 오른쪽에 있을수록 기대수익률이 높습니다.
            분포가 좁을수록 추정이 안정적입니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📉 변동성 σ (연환산 표준편차)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
수익률이 얼마나 들쭉날쭉한지를 나타냅니다.
변동성이 클수록 오를 때 많이 오르지만, 떨어질 때도 많이 떨어집니다.

수익률 μ 와 동일한 부트스트랩 방식으로 분포를 만듭니다.

📌 읽는 법: 분포가 왼쪽에 있을수록 안정적인 종목입니다.
            분포가 오른쪽일수록 고위험·고변동 종목입니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚖️  Sharpe Ratio (샤프 비율)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
위험 1단위당 얼마나 수익을 냈는지를 나타냅니다.
수익률이 높아도 변동성이 크면 Sharpe가 낮아집니다.

계산식: (수익률 - 무위험이자율) ÷ 변동성
무위험이자율은 연 4%(rf=0.04)를 사용합니다.

이 분포는 시뮬레이션 1,000개 경로 각각에서 계산한 값입니다.

📌 읽는 법: 1.0 기준선(점선) 오른쪽이면 양호합니다.
            값이 클수록 위험 대비 효율이 좋은 종목입니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛡️  Sortino Ratio (소르티노 비율)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sharpe와 비슷하지만, 하락 방향의 변동성만 위험으로 봅니다.
오르는 변동성은 좋은 것이므로 불이익을 주지 않습니다.

일반적으로 Sharpe보다 투자자에게 유리한 지표로 평가됩니다.

📌 읽는 법: 1.0 기준선(점선) 오른쪽이면 양호합니다.
            Sharpe와 함께 보면 종목의 특성을 더 잘 파악할 수 있습니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 MDD (최대 낙폭, Maximum Drawdown)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
투자 기간 중 고점 대비 가장 많이 떨어진 폭을 나타냅니다.
예를 들어 MDD -40%라면, 어느 시점의 최고점에서 40%까지 손실이 난 적이
있다는 뜻입니다.

음수(%) 값으로 표시되며, 시뮬레이션 1,000개 경로 각각의 MDD 분포입니다.

📌 읽는 법: 분포가 0에 가까울수록(오른쪽) 낙폭이 작아 안전합니다.
            분포가 왼쪽으로 치우칠수록 큰 손실 구간이 자주 발생합니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💥 VaR / CVaR (손실 위험 구간)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VaR 95%: 최악의 5% 시나리오에서 원금 대비 얼마나 손실이 나는지입니다.
          즉, 100번 중 95번은 이보다 좋은 결과가 나온다는 의미입니다.

CVaR 95%: 그 최악 5% 시나리오들의 평균 손실입니다.
           VaR보다 극단적인 위험을 더 잘 반영합니다.

원금 대비 수익률(%)로 표시됩니다. x=0 기준선은 원금 보전선입니다.

📌 읽는 법: 분포가 0(기준선) 오른쪽에 있으면 최악에도 수익입니다.
            왼쪽으로 치우칠수록 극단적 손실 위험이 큽니다.
            VaR보다 CVaR가 더 보수적인 지표입니다.
```

**구현 함수명:** `_show_comparison_help_popup()`
- 버튼 `command=self._show_comparison_help_popup`
- 창이 이미 열려있으면 `focus()`만 호출 (중복 팝업 방지)
  ```python
  if hasattr(self, "_help_window") and self._help_window.winfo_exists():
      self._help_window.focus()
      return
  self._help_window = CTkToplevel(self.root)
  ```

---

#### Simulation Flow (V2)

```
_run_simulation()
  → _validate_inputs()
  → 백그라운드 스레드
      → fetch_historical_data()            # 종목별 stats, price_data 수집
      → compute_ticker_risk_metrics(       # [NEW] 종목별 개별 리스크 계산
            ticker, stats, price_data,     #   price_data 전달 필수 (부트스트랩용)
            total_months, num_sims=1000    
        )  — 각 종목마다 반복 호출
      → compute_portfolio_params()
      → run_simulation()                   # 포트폴리오 전체 시뮬레이션
  → root.after(0, _on_simulation_done)
  → _render_results()                      # 탭1 렌더링
  → _render_comparison_tab()              # [NEW] 탭2 렌더링
  → _render_raw_data_tab()               # [NEW] 탭3 렌더링
```

**`_last_result` 캐시 구조 (V2):**
```python
_last_result = {
    "paths": np.ndarray,         # shape (num_sims, total_months+1) — 포트폴리오 합산 경로
    "per_ticker_paths": dict,    # [NEW] {ticker: np.ndarray} — 종목별 경로 (비교 탭용)
    "params": dict,
    "ticker_metrics": dict,      # [NEW] {ticker: {mu, sigma, ..., mu_arr, sigma_arr, ...}}
    "tickers": list,
    "weights": list,
    "price_data": dict,          # [NEW] {ticker: (close_series, daily_returns_series)} — Raw Data 탭용
    "stats": dict,               # [NEW] stats_dict 전체 — Raw Data 파라미터 요약 테이블용
    "run_time": str,             # [NEW] 실행 시각 "YYYY-MM-DD HH:MM:SS" — Raw Data 헤더용
}
```

---

#### Settings Dialog (unchanged)

- Font family, mono font, scale(80-150%) 조정
- `config.json` 영속화

#### UI State Preservation ([V2] 수정 필요)

- `_save_ui_state()` / `_restore_ui_state(state)` — font 설정 적용 시 입력값 보존
- **[V2 수정]** `ticker_rows` 튜플 구조가 V1 4-tuple → V2 5-tuple 로 변경됨에 따라 두 함수 모두 수정 필요
  ```python
  # V1: (row_frame, name_var, ticker_var, weight_var)
  # V2: (row_frame, eng_name_var, weight_var, ticker_label, korean_name_label)

  # _save_ui_state() 저장 대상 (V2)
  state["tickers"] = [
      {
          "eng_name": row[1].get(),               # eng_name_var
          "weight":   row[2].get(),               # weight_var
          "ticker":   row[3].cget("text"),        # ticker_label (CTkLabel)
          "ko_name":  row[4].cget("text"),        # korean_name_label (CTkLabel)
      }
      for row in self.ticker_rows
  ]

  # _restore_ui_state() 복원 대상 (V2)
  # _add_ticker_row() 로 행 생성 후 각 필드에 저장값 설정
  ```

---

### `ticker_db.py` — Ticker Database (V2)

**[V2] DB 구조 변경:**

```python
# V1
TICKER_DB = {
    "005930.KS": "삼성전자 Samsung Electronics",
}

# V2
TICKER_DB = {
    "005930.KS": {"en": "Samsung Electronics",        "ko": "삼성전자"},           # DEFAULT
    "069500.KS": {"en": "KODEX 200",                  "ko": "KODEX 200"},          # DEFAULT
    "000660.KS": {"en": "SK Hynix",                   "ko": "SK하이닉스"},         # DEFAULT
    "047810.KS": {"en": "Korea Aerospace Industries", "ko": "한국항공우주산업"},   # DEFAULT
    "AAPL":      {"en": "Apple",                      "ko": "애플"},
    ...
}
```

**[V2] `search_tickers(query, max_results=15)`:**
- 쿼리 대상: 영문명(`en`) 만 검색 (한글 검색 제거)
- 반환 형식: `List[(ticker_code, en_name, ko_name)]`
- 정렬: 정확한 티커 매치 → 영문명 접두어 → 영문명 포함 (case-insensitive)

**[V2] `resolve_ticker(query)`:**
- 반환: `(ticker_code, en_name, ko_name)` 또는 `None`

---

### `config.py` — Font Configuration (unchanged)

- OS별 기본 폰트 자동 선택
- 7가지 폰트 튜플 관리
- `load_config()`, `save_config()`, `compute_fonts()` 동일

---

### `test_sim.py` — Quick Test ([V2] 확장 필요)

Standalone test with hardcoded params. No CLI args needed.

**[V2] 추가 테스트 항목 (기존 VOO 단일 테스트 유지 + 아래 추가):**

```python
# 테스트 1 (기존 유지): 단일 종목 포트폴리오 (금액 단위: 원)
tickers=["005930.KS"], weights=[1.0], initial=10_000_000, monthly=500_000, years=5, sims=1000

# 테스트 2 (신규): 다중 종목 — run_simulation() 종목별 분리 구조 검증
tickers=["005930.KS", "000660.KS"], weights=[0.6, 0.4], initial=10_000_000, monthly=500_000, years=5, sims=500
# 검증: per_ticker_paths 키 존재, 각 shape == (500, 61), portfolio == sum(per_ticker)

# 테스트 3 (신규): compute_ticker_risk_metrics() 반환 구조 검증
# 검증: mu_arr.shape==(1000,), sigma_arr.shape==(500,), sharpe_arr, sortino_arr, mdd_arr, var_arr 존재
# ※ 부트스트랩 n_bootstrap=1000, 시뮬레이션 num_sims=1000 — 같은 숫자지만 별개 파라미터

# 테스트 4 (신규): 종목 1개일 때 비교 탭 단독 히스토그램 렌더링 무오류 확인
# plot_ticker_comparison() 에 ticker 1개짜리 dict 전달 → 오류 없이 Figure 반환 확인
```

---

## Investment Policy Definitions

시뮬레이션에서 적용되는 투자 방식의 명확한 정의입니다. CLI/GUI 모드 공통 적용.

### 초기 투자금 집행 방식
- **첫 스텝(t=1) 일괄 투입**: `initial` 금액은 종목별로 `w_i × initial` 로 분배되어 t=1에 투입
- `V_i(0) = 0` 으로 시작, t=1 스텝에서 `w_i × initial + contribution × w_i` 가 동시 반영됨

### 적립금 투자 방식
- **가중치 기준 종목별 분산 투자**: 매 스텝 `contribution` 을 `w_i` 비율로 각 종목에 분배
- `contribution_i(t) = contribution_t × w_i`
- 리밸런싱은 없으므로 가중치는 초기 분배 비율로만 사용되며 이후 drift 허용

### 상관관계 처리
- **독립 샘플**: 종목별 Z_i ~ N(0,1) 을 독립적으로 생성 (무상관 가정 유지)
- 구현 단순성 확보, 기존 파라미터 추정 방식(`σ_p = √(Σ wᵢ²σᵢ²)`)과 일관성 유지

### 리밸런싱 정책
- **없음**: 가중치 drift 허용
- 초기 분배 이후 종목별 비중은 각 종목의 수익률에 따라 자연스럽게 변화
- `plot_summary_dashboard()` 의 "Projected portfolio 도넛차트" 는 이 drift 추정치로 표시

### 포트폴리오 합산 방식
- **단순 합산**: `V_portfolio(t) = Σ V_i(t)`
- 종목별 경로를 합산해 포트폴리오 총 경로 생성
- MDD, VaR, Sortino 등 모든 포트폴리오 레벨 지표는 `V_portfolio` 기준으로 계산

### 투자 파라미터 확정 정책 (Input Lock)

시뮬레이션 실행 시점에 입력된 값이 **시뮬레이션 전 기간에 걸쳐 고정**됩니다. 실행 중 변경 불가.

| 파라미터 | 입력 위치 | 고정 기준 | 비고 |
|---|---|---|---|
| 종목별 가중치 (w_i) | 티커/가중치 카드 — 가중치 입력창 | 입력값 고정, 리밸런싱 없음 | 합계 = 1.0 실시간 검증 |
| 초기 투자금 (initial) | 투자 금액 카드 | t=1에 `w_i × initial` 로 종목별 분배 후 고정 | 추가 납입 없음 |
| 정기 적립금 (contribution) | 투자 금액 카드 | 매 스텝 `contribution × w_i` 로 종목별 동일 비율 분배 | 금액 변경 없음 |
| 적립 주기 | 투자 금액 카드 — 세그먼트 버튼 | 선택 주기 고정 | 매주/매월/연간 (분기 제외) |

**정책 의미:**
- 가중치는 최초 입력 시 결정되며, 초기 투자금과 매 스텝 적립금 모두 **동일한 비율**로 종목별 분배
- 예: `삼성전자 25% / SK하이닉스 25% / KODEX200 25% / 한국항공우주 25%`, initial=10,000,000원, monthly=500,000원 이면
  - t=1: 각 종목에 2,500,000 + 125,000 원씩 투입
  - t≥2: 매월 각 종목에 125,000 원씩 투입
- 시뮬레이션 도중 가중치 drift가 발생해도 적립금 분배 비율은 초기 w_i 고정값 사용

| 정책 | 선택 | 비고 |
|---|---|---|
| 초기 투자금 | t=1, `w_i × initial` 분배 | 적립금 분배 방식과 통일 |
| 적립금 | `contribution × w_i` 종목별 분산 | 가중치 의미 명확화 |
| 상관관계 | 독립 샘플 (무상관) | 기존 σ_p 수식과 일치 ✓ |
| 리밸런싱 | 없음 (drift 허용) | 단순성 유지 |
| 포트폴리오 합산 | `Σ V_i(t)` 단순 합산 | MDD/VaR 계산 기준 명확 |

---

## Simulation Mathematics

**GBM (월간, 종목별 분리 구조 — V2):**
```
dt = 1/12
drift_i    = (μ_i - 0.5σ_i²) × dt
Z_i(t)    ~ N(0,1)  독립 샘플 (종목 간 무상관 가정)

V_i(0) = 0                                                       ← 전 종목 t=0은 0
V_i(1) = (w_i × initial + contribution_t1 × w_i)
         × exp(drift_i + σ_i × √dt × Z_i(1))                    ← t=1: initial + 적립금 동시 투입
V_i(t) = (V_i(t-1) + contribution_t × w_i)
         × exp(drift_i + σ_i × √dt × Z_i(t))    (t ≥ 2)        ← 적립금 먼저 투입 후 수익률 적용

V_portfolio(t) = Σ_i V_i(t)                                     ← 포트폴리오 합산 경로
```

> **적립금 투입 순서:** 각 스텝에서 `contribution × w_i` 를 먼저 더한 뒤 수익률을 곱함
> (기말 투입이 아닌 기초 투입 방식 — 적립금도 해당 월 수익률에 노출됨)

**파라미터 추정:**
- 일간 수익률 → 연환산: mean×252, vol×√252
- 포트폴리오 합성 σ: `σ_p = √(Σ wᵢ²σᵢ²)` — **V2에서는 시뮬레이션 입력값으로 사용하지 않음, 대시보드 표시용 참고값으로만 유지**
- 시뮬레이션은 종목별 μ_i, σ_i 를 직접 사용 (blended 값 불필요)
- **[V2] 기본 히스토리 범위: 25년 (상장일 < 25년이면 최장치 자동 fallback)**

**리스크 지표 (포트폴리오 레벨 — 변경 없음):**
- Sharpe, Sortino, MDD, Calmar, VaR 95/99%, CVaR, 수익/원금 비율, 2배달성확률, 손실확률

**[NEW] 종목별 리스크 지표 (비교 탭용):**
- 각 종목 단독 시뮬레이션 1,000회 실행
- 무적립금(contribution=0), 초기투자금 ₩10,000,000 고정으로 정규화
- 동일 기간(total_months) 적용하여 포트폴리오와 비교 가능하게 유지

---

## Contribution Frequency Logic

| Frequency | Korean Label | Per Monthly Step |
|---|---|---|
| weekly | 매주 | `amount × 52/12` every step |
| monthly | 매월 | `amount` every step |
| yearly | 연간 | `amount` every 12th step (m%12==0) |

> **분기(quarterly) 제거**: t=1 초기 투자금 투입 시점과 적립 주기 간 불일치 문제를 방지하기 위해 지원 주기에서 제외. 매주/매월/연간 3가지만 지원.

---

## GUI–Core Interface Pattern

Plot functions accept optional `fig` parameter:
- CLI: `fig=None` → 내부에서 Figure 생성 → `plt.show()`
- GUI: `fig=Figure(...)` → 외부 Figure에 그리기 → `FigureCanvasTkAgg`

---

## Dependencies

numpy, pandas, matplotlib, scipy, yfinance, customtkinter, python-dateutil (see requirements.txt)

> **[V2 추가]** `python-dateutil` — 25년 기간 계산 `relativedelta(years=25)` 사용. `pandas` 내부 의존성으로 대부분 환경에 설치되어 있으나 `requirements.txt` 에 명시적으로 추가 필요.

---

## Conventions

- UI 텍스트/레이블: 한국어
- 티커 DB: 영문명/한국명 분리 (`en`/`ko`)
- 한국 티커: `.KS` (KOSPI), `.KQ` (KOSDAQ)
- 통화: `₩` prefix + 쉼표 포맷 (`₩{value:,.0f}`) — 달러($) 사용 금지, 전 UI/차트/테이블 원화 통일
- GUI: 카드 기반 레이아웃, 크림/베이지 라이트 단일 테마
- 스레드 안전: `root.after(0, callback)` 경유
- 폰트 설정: `config.json` 영속화

---

## V2 수정 파일 요약

| 파일 | 주요 변경 내용 |
|---|---|
| `gui.py` | 테마 단일화(크림/베이지), 티커 입력 UX 개편, CTkTabview 탭 구조 추가(탭1~3), 비교 탭·Raw Data 탭 렌더링 함수 추가, **투자 금액 단위 원(₩) 변경**, **파이차트→도넛차트** |
| `ticker_db.py` | DB 구조 `{en, ko}` 분리, `search_tickers()` 영문 기준으로 수정, **DEFAULT 4종목 추가** |
| `investment_simulator.py` | `compute_ticker_risk_metrics()` 추가, `plot_ticker_comparison()` 및 히스토그램 서브함수 6개 추가, **통화 단위 원화 전환**, **도넛차트 구현** |
| `config.py` | 테마 관련 설정 정리 (최소 변경) |
