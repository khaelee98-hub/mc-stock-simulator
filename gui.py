"""
Monte Carlo Investment Simulator V2 — GUI (CustomTkinter).

Single cream/beige light theme. Two-panel layout:
- Left: fixed-width (440px) input panel with 5 cards
- Right: expandable results panel with CTkTabview (3 tabs)
"""

import threading
from datetime import datetime

import customtkinter as ctk
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from config import (
    load_config, save_config, compute_fonts,
    get_available_font_candidates, get_available_mono_candidates,
    FONT_CANDIDATES, MONO_FONT_CANDIDATES, BASE_FONT_SIZES,
)
from ticker_db import TICKER_DB, search_tickers

# ═══════════════════════════════════════════
#  Theme (Single Light — Cream/Beige)
# ═══════════════════════════════════════════

THEME = {
    "bg":              "#FAF7F2",
    "surface":         "#F5F0E8",
    "card":            "#FFFFFF",
    "border":          "#C8BBA8",
    "accent":          "#6B5230",
    "accent_hover":    "#5A4225",
    "text_primary":    "#0D0905",
    "text_secondary":  "#332810",
    "text_disabled":   "#6B5F4E",
    "input_bg":        "#FFFFFF",
    "input_border":    "#B0A490",
    "input_focus":     "#6B5230",
    "chart_bg":        "#FAF7F2",
    "chart_grid":      "#C8BBA8",
    "chart_text":      "#0D0905",
    "chart_spine":     "#B0A490",
    "table_header_bg": "#EDE5D8",
    "table_row_alt":   "#F8F4EE",
    "success":         "#5A7A5A",
    "error":           "#8B3A3A",
    "warning":         "#8B6F47",
}

ACCENT_COLORS = [
    "#5A7A8B", "#7A8B5A", "#8B5A6F", "#5A6F8B", "#8B7A5A",
    "#6F5A8B", "#5A8B7A", "#8B5A5A", "#6F8B5A", "#8B6F47",
]

# ── Layout Constants ──
WINDOW_WIDTH = 1440
WINDOW_HEIGHT = 920
WINDOW_MIN_W = 1100
WINDOW_MIN_H = 700
LEFT_PANEL_WIDTH = 440
CARD_CORNER_RADIUS = 12
CARD_PADDING = 14
CARD_GAP = 10

MAX_TICKERS = 10

DEFAULT_TICKERS = [
    ("Samsung Electronics",         "005930.KS", "0.25", "삼성전자"),
    ("KODEX 200",                   "069500.KS", "0.25", "KODEX 200"),
    ("SK Hynix",                    "000660.KS", "0.25", "SK하이닉스"),
    ("Korea Aerospace Industries",  "047810.KS", "0.25", "한국항공우주산업"),
]

# ── Font globals ──
FONT_TITLE = FONT_SECTION = FONT_BODY = FONT_INPUT = None
FONT_SMALL = FONT_MONO = FONT_STATUS = None


def _reload_fonts(config=None):
    """Reload global font tuples from config."""
    global FONT_TITLE, FONT_SECTION, FONT_BODY, FONT_INPUT
    global FONT_SMALL, FONT_MONO, FONT_STATUS
    if config is None:
        config = load_config()
    fonts = compute_fonts(config)
    FONT_TITLE = fonts["FONT_TITLE"]
    FONT_SECTION = fonts["FONT_SECTION"]
    FONT_BODY = fonts["FONT_BODY"]
    FONT_INPUT = fonts["FONT_INPUT"]
    FONT_SMALL = fonts["FONT_SMALL"]
    FONT_MONO = fonts["FONT_MONO"]
    FONT_STATUS = fonts["FONT_STATUS"]


# Initialize on import
_reload_fonts()


class InvestmentSimulatorGUI:
    """Main GUI class."""

    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("몬테카를로 투자 시뮬레이터 V2")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(WINDOW_MIN_W, WINDOW_MIN_H)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.ticker_rows = []
        self._autocomplete_window = None
        self._last_result = None
        self._running = False

        self._setup_chart_style()
        self._build_ui()

    # ───────────────────────────────
    #  Chart Style
    # ───────────────────────────────

    def _setup_chart_style(self):
        plt.rcParams["figure.facecolor"] = THEME["chart_bg"]
        plt.rcParams["axes.facecolor"] = THEME["chart_bg"]
        plt.rcParams["axes.edgecolor"] = THEME["chart_spine"]
        plt.rcParams["axes.labelcolor"] = THEME["chart_text"]
        plt.rcParams["text.color"] = THEME["chart_text"]
        plt.rcParams["xtick.color"] = THEME["chart_text"]
        plt.rcParams["ytick.color"] = THEME["chart_text"]
        plt.rcParams["grid.color"] = THEME["chart_grid"]

        # Global font sizes
        plt.rcParams["font.size"] = 16
        plt.rcParams["axes.titlesize"] = 18
        plt.rcParams["axes.labelsize"] = 16
        plt.rcParams["xtick.labelsize"] = 14
        plt.rcParams["ytick.labelsize"] = 14
        plt.rcParams["legend.fontsize"] = 14
        plt.rcParams["figure.titlesize"] = 20

        from investment_simulator import setup_matplotlib_korean_font
        setup_matplotlib_korean_font()

        # Apply font from config
        config = load_config()
        family = config.get("font_family", "Malgun Gothic")
        plt.rcParams["font.family"] = family

    # ───────────────────────────────
    #  Build UI
    # ───────────────────────────────

    def _build_ui(self):
        self.root.configure(fg_color=THEME["bg"])

        # Main container
        self.main_frame = ctk.CTkFrame(self.root, fg_color=THEME["bg"])
        self.main_frame.pack(fill="both", expand=True)

        # Left panel wrapper (fixed width)
        left_wrapper = ctk.CTkFrame(
            self.main_frame, width=LEFT_PANEL_WIDTH, fg_color=THEME["surface"],
            corner_radius=0,
        )
        left_wrapper.pack(side="left", fill="y", padx=0, pady=0)
        left_wrapper.pack_propagate(False)

        # Scrollable inside the fixed wrapper
        self.left_panel = ctk.CTkScrollableFrame(
            left_wrapper, fg_color=THEME["surface"], corner_radius=0,
        )
        self.left_panel.pack(fill="both", expand=True)

        # Right panel (results)
        self.right_panel = ctk.CTkFrame(self.main_frame, fg_color=THEME["bg"])
        self.right_panel.pack(side="left", fill="both", expand=True, padx=0, pady=0)

        self._build_input_panel()
        self._build_results_placeholder()

    def _make_card(self, parent, title=None):
        """Create a card frame with optional title."""
        card = ctk.CTkFrame(
            parent, fg_color=THEME["card"], corner_radius=CARD_CORNER_RADIUS,
            border_width=1, border_color=THEME["border"],
        )
        card.pack(fill="x", padx=CARD_PADDING, pady=(CARD_GAP, 0))

        if title:
            ctk.CTkLabel(
                card, text=title, font=FONT_SECTION,
                text_color=THEME["text_primary"],
            ).pack(anchor="w", padx=CARD_PADDING, pady=(CARD_PADDING, 4))

        return card

    # ───────────────────────────────
    #  Input Panel
    # ───────────────────────────────

    def _build_input_panel(self):
        # Title
        ctk.CTkLabel(
            self.left_panel, text="몬테카를로 투자 시뮬레이터",
            font=FONT_TITLE, text_color=THEME["text_primary"],
        ).pack(padx=CARD_PADDING, pady=(CARD_PADDING, 4))

        self._build_ticker_card()
        self._build_amount_card()
        self._build_period_card()
        self._build_simulation_card()
        self._build_button_card()

    # ── Card 1: Ticker/Weight ──

    def _build_ticker_card(self):
        card = self._make_card(self.left_panel, "종목 / 가중치")
        self.ticker_container = ctk.CTkFrame(card, fg_color="transparent")
        self.ticker_container.pack(fill="x", padx=CARD_PADDING, pady=(0, 4))

        # Header row
        hdr = ctk.CTkFrame(self.ticker_container, fg_color="transparent")
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="회사명 (영문)", font=FONT_SMALL,
                     text_color=THEME["text_secondary"], width=250).pack(side="left")
        ctk.CTkLabel(hdr, text="가중치", font=FONT_SMALL,
                     text_color=THEME["text_secondary"], width=60).pack(side="left", padx=(10, 0))

        self.ticker_rows = []
        for eng_name, ticker_code, weight, ko_name in DEFAULT_TICKERS:
            row = self._add_ticker_row()
            row[1].set(eng_name)
            row[2].set(weight)
            row[3].configure(text=ticker_code)
            row[4].configure(text=ko_name)

        # Add/Remove buttons
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=CARD_PADDING, pady=(4, CARD_PADDING))
        ctk.CTkButton(
            btn_frame, text="+ 종목 추가", width=100, height=28,
            font=FONT_SMALL, fg_color=THEME["accent"], hover_color=THEME["accent_hover"],
            text_color="#FFFFFF",
            command=self._on_add_ticker,
        ).pack(side="left")
        ctk.CTkButton(
            btn_frame, text="- 삭제", width=70, height=28,
            font=FONT_SMALL, fg_color=THEME["error"], hover_color="#6B2A2A",
            text_color="#FFFFFF",
            command=self._on_remove_ticker,
        ).pack(side="left", padx=(8, 0))

        # Weight sum label
        self.weight_sum_label = ctk.CTkLabel(
            btn_frame, text="합계: 1.00", font=FONT_SMALL,
            text_color=THEME["text_secondary"],
        )
        self.weight_sum_label.pack(side="right")

    def _add_ticker_row(self):
        """Add a ticker row. Returns (row_frame, eng_name_var, weight_var, ticker_label, ko_name_label)."""
        row_frame = ctk.CTkFrame(self.ticker_container, fg_color="transparent")
        row_frame.pack(fill="x", pady=2)

        # Top: English name entry + weight entry
        top = ctk.CTkFrame(row_frame, fg_color="transparent")
        top.pack(fill="x")

        eng_name_var = ctk.StringVar()
        eng_entry = ctk.CTkEntry(
            top, textvariable=eng_name_var, width=250, height=30,
            font=FONT_INPUT, fg_color=THEME["input_bg"],
            border_color=THEME["input_border"],
            placeholder_text="영문 회사명 입력...",
        )
        eng_entry.pack(side="left")

        weight_var = ctk.StringVar(value="0.0")
        weight_entry = ctk.CTkEntry(
            top, textvariable=weight_var, width=60, height=30,
            font=FONT_INPUT, fg_color=THEME["input_bg"],
            border_color=THEME["input_border"],
        )
        weight_entry.pack(side="left", padx=(10, 0))

        # Bottom: sub-display (ticker code + Korean name)
        sub = ctk.CTkFrame(row_frame, fg_color="transparent")
        sub.pack(fill="x", padx=(4, 0))

        ticker_label = ctk.CTkLabel(
            sub, text="—", font=FONT_SMALL,
            text_color=THEME["text_disabled"], width=100, anchor="w",
        )
        ticker_label.pack(side="left")

        ko_name_label = ctk.CTkLabel(
            sub, text="—", font=FONT_SMALL,
            text_color=THEME["text_disabled"], anchor="w",
        )
        ko_name_label.pack(side="left", padx=(8, 0))

        # Autocomplete binding
        eng_entry.bind("<KeyRelease>", lambda e, ev=eng_name_var, tl=ticker_label,
                       kl=ko_name_label, entry=eng_entry: self._on_ticker_key(e, ev, tl, kl, entry))
        eng_entry.bind("<FocusOut>", lambda e: self._close_autocomplete())

        # Weight change tracking
        weight_var.trace_add("write", lambda *_: self._update_weight_sum())

        row = (row_frame, eng_name_var, weight_var, ticker_label, ko_name_label)
        self.ticker_rows.append(row)
        return row

    def _on_add_ticker(self):
        if len(self.ticker_rows) < MAX_TICKERS:
            self._add_ticker_row()

    def _on_remove_ticker(self):
        if len(self.ticker_rows) > 1:
            row = self.ticker_rows.pop()
            row[0].destroy()
            self._update_weight_sum()

    def _update_weight_sum(self):
        if not hasattr(self, "weight_sum_label"):
            return
        try:
            self.weight_sum_label.winfo_exists()
        except Exception:
            return
        if not self.weight_sum_label.winfo_exists():
            return
        total = 0.0
        for _, _, wv, _, _ in self.ticker_rows:
            try:
                total += float(wv.get())
            except (ValueError, Exception):
                pass
        color = THEME["success"] if abs(total - 1.0) < 0.01 else THEME["error"]
        self.weight_sum_label.configure(text=f"합계: {total:.2f}", text_color=color)

    # ── Autocomplete ──

    def _on_ticker_key(self, event, eng_var, ticker_label, ko_label, entry):
        if event.keysym in ("Down", "Up", "Return", "Escape"):
            if event.keysym == "Escape":
                self._close_autocomplete()
            return

        query = eng_var.get().strip()
        if len(query) < 1:
            self._close_autocomplete()
            return

        results = search_tickers(query, max_results=8)
        if not results:
            self._close_autocomplete()
            return

        self._show_autocomplete(results, eng_var, ticker_label, ko_label, entry)

    def _show_autocomplete(self, results, eng_var, ticker_label, ko_label, entry):
        self._close_autocomplete()

        self._autocomplete_window = ctk.CTkToplevel(self.root)
        self._autocomplete_window.wm_overrideredirect(True)
        self._autocomplete_window.configure(fg_color=THEME["card"])

        # Position below entry
        x = entry.winfo_rootx()
        y = entry.winfo_rooty() + entry.winfo_height()
        self._autocomplete_window.geometry(f"350x{min(len(results), 8) * 28 + 4}+{x}+{y}")

        for ticker_code, en_name, ko_name in results:
            item = ctk.CTkButton(
                self._autocomplete_window,
                text=f"{en_name:<30s} {ticker_code}",
                font=FONT_MONO, anchor="w", height=26,
                fg_color="transparent", text_color=THEME["text_primary"],
                hover_color=THEME["surface"],
                command=lambda e=en_name, t=ticker_code, k=ko_name: self._select_autocomplete(
                    e, t, k, eng_var, ticker_label, ko_label),
            )
            item.pack(fill="x", padx=2, pady=1)

    def _select_autocomplete(self, en_name, ticker_code, ko_name, eng_var, ticker_label, ko_label):
        eng_var.set(en_name)
        ticker_label.configure(text=ticker_code, text_color=THEME["text_primary"])
        ko_label.configure(text=ko_name, text_color=THEME["text_primary"])
        self._close_autocomplete()

    def _close_autocomplete(self):
        if self._autocomplete_window and self._autocomplete_window.winfo_exists():
            self._autocomplete_window.destroy()
        self._autocomplete_window = None

    # ── Card 2: Investment Amount ──

    def _build_amount_card(self):
        card = self._make_card(self.left_panel, "투자 금액")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=CARD_PADDING, pady=(0, CARD_PADDING))

        # Initial investment
        ctk.CTkLabel(inner, text="초기 투자금", font=FONT_SMALL,
                     text_color=THEME["text_secondary"]).pack(anchor="w")
        row1 = ctk.CTkFrame(inner, fg_color="transparent")
        row1.pack(fill="x", pady=(2, 8))
        self.initial_var = ctk.StringVar(value="10,000,000")
        ctk.CTkEntry(
            row1, textvariable=self.initial_var, width=200, height=30,
            font=FONT_INPUT, fg_color=THEME["input_bg"], border_color=THEME["input_border"],
        ).pack(side="left")
        ctk.CTkLabel(row1, text="원", font=FONT_BODY,
                     text_color=THEME["text_secondary"]).pack(side="left", padx=(8, 0))

        # Regular contribution
        ctk.CTkLabel(inner, text="정기 적립금", font=FONT_SMALL,
                     text_color=THEME["text_secondary"]).pack(anchor="w")
        row2 = ctk.CTkFrame(inner, fg_color="transparent")
        row2.pack(fill="x", pady=(2, 8))
        self.monthly_var = ctk.StringVar(value="500,000")
        ctk.CTkEntry(
            row2, textvariable=self.monthly_var, width=200, height=30,
            font=FONT_INPUT, fg_color=THEME["input_bg"], border_color=THEME["input_border"],
        ).pack(side="left")
        ctk.CTkLabel(row2, text="원", font=FONT_BODY,
                     text_color=THEME["text_secondary"]).pack(side="left", padx=(8, 0))

        # Contribution frequency
        ctk.CTkLabel(inner, text="적립 주기", font=FONT_SMALL,
                     text_color=THEME["text_secondary"]).pack(anchor="w", pady=(4, 2))
        self.freq_var = ctk.StringVar(value="매월")
        ctk.CTkSegmentedButton(
            inner, values=["매주", "매월", "연간"],
            variable=self.freq_var, font=FONT_SMALL,
            fg_color=THEME["surface"], selected_color=THEME["accent"],
            selected_hover_color=THEME["accent_hover"],
            unselected_color=THEME["card"], unselected_hover_color=THEME["surface"],
            text_color=THEME["text_primary"],
        ).pack(fill="x")

    # ── Card 3: Period ──

    def _build_period_card(self):
        card = self._make_card(self.left_panel, "기간 설정")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=CARD_PADDING, pady=(0, CARD_PADDING))

        self.period_mode = ctk.StringVar(value="years")
        ctk.CTkSegmentedButton(
            inner, values=["연수 지정", "날짜 범위"],
            variable=self.period_mode, font=FONT_SMALL,
            fg_color=THEME["surface"], selected_color=THEME["accent"],
            selected_hover_color=THEME["accent_hover"],
            unselected_color=THEME["card"], unselected_hover_color=THEME["surface"],
            text_color=THEME["text_primary"],
            command=self._on_period_mode_change,
        ).pack(fill="x", pady=(0, 8))

        # Years frame
        self.years_frame = ctk.CTkFrame(inner, fg_color="transparent")
        self.years_frame.pack(fill="x")
        ctk.CTkLabel(self.years_frame, text="투자 기간 (년)", font=FONT_SMALL,
                     text_color=THEME["text_secondary"]).pack(anchor="w")
        self.years_var = ctk.StringVar(value="20")
        ctk.CTkEntry(
            self.years_frame, textvariable=self.years_var, width=100, height=30,
            font=FONT_INPUT, fg_color=THEME["input_bg"], border_color=THEME["input_border"],
        ).pack(anchor="w", pady=(2, 0))

        # Date range frame
        self.date_frame = ctk.CTkFrame(inner, fg_color="transparent")
        ctk.CTkLabel(self.date_frame, text="시작 (YYYY-MM)", font=FONT_SMALL,
                     text_color=THEME["text_secondary"]).pack(anchor="w")
        self.start_var = ctk.StringVar(value="2025-01")
        ctk.CTkEntry(
            self.date_frame, textvariable=self.start_var, width=150, height=30,
            font=FONT_INPUT, fg_color=THEME["input_bg"], border_color=THEME["input_border"],
        ).pack(anchor="w", pady=(2, 8))
        ctk.CTkLabel(self.date_frame, text="종료 (YYYY-MM)", font=FONT_SMALL,
                     text_color=THEME["text_secondary"]).pack(anchor="w")
        self.end_var = ctk.StringVar(value="2045-01")
        ctk.CTkEntry(
            self.date_frame, textvariable=self.end_var, width=150, height=30,
            font=FONT_INPUT, fg_color=THEME["input_bg"], border_color=THEME["input_border"],
        ).pack(anchor="w", pady=(2, 0))

    def _on_period_mode_change(self, value):
        if value == "연수 지정":
            self.period_mode.set("years")
            self.date_frame.pack_forget()
            self.years_frame.pack(fill="x")
        else:
            self.period_mode.set("dates")
            self.years_frame.pack_forget()
            self.date_frame.pack(fill="x")

    # ── Card 4: Simulation Settings ──

    def _build_simulation_card(self):
        card = self._make_card(self.left_panel, "시뮬레이션 설정")
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=CARD_PADDING, pady=(0, CARD_PADDING))

        ctk.CTkLabel(inner, text="시뮬레이션 횟수", font=FONT_SMALL,
                     text_color=THEME["text_secondary"]).pack(anchor="w")
        self.sims_var = ctk.StringVar(value="10,000")
        ctk.CTkEntry(
            inner, textvariable=self.sims_var, width=150, height=30,
            font=FONT_INPUT, fg_color=THEME["input_bg"], border_color=THEME["input_border"],
        ).pack(anchor="w", pady=(2, 0))

    # ── Card 5: Buttons ──

    def _build_button_card(self):
        card = self._make_card(self.left_panel)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=CARD_PADDING, pady=CARD_PADDING)

        ctk.CTkButton(
            inner, text="시뮬레이션 실행", font=FONT_BODY, height=40,
            fg_color=THEME["accent"], hover_color=THEME["accent_hover"],
            text_color="#FFFFFF",
            command=self._run_simulation,
        ).pack(fill="x", pady=(0, 8))

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x")

        ctk.CTkButton(
            btn_row, text="초기화", font=FONT_SMALL, width=80, height=30,
            fg_color="transparent", text_color=THEME["text_secondary"],
            border_width=1, border_color=THEME["border"],
            hover_color=THEME["surface"], command=self._reset,
        ).pack(side="left")

        ctk.CTkButton(
            btn_row, text="설정", font=FONT_SMALL, width=80, height=30,
            fg_color="transparent", text_color=THEME["text_secondary"],
            border_width=1, border_color=THEME["border"],
            hover_color=THEME["surface"], command=self._open_settings,
        ).pack(side="left", padx=(8, 0))

        # Status label
        self.status_label = ctk.CTkLabel(
            inner, text="", font=FONT_STATUS, text_color=THEME["text_secondary"],
        )
        self.status_label.pack(anchor="w", pady=(8, 0))

    # ───────────────────────────────
    #  Results Panel
    # ───────────────────────────────

    def _build_results_placeholder(self):
        self.results_placeholder = ctk.CTkLabel(
            self.right_panel, text="시뮬레이션을 실행하면 결과가 여기에 표시됩니다.",
            font=FONT_BODY, text_color=THEME["text_disabled"],
        )
        self.results_placeholder.pack(expand=True)

    def _clear_results(self):
        for w in self.right_panel.winfo_children():
            w.destroy()

    # ───────────────────────────────
    #  Simulation
    # ───────────────────────────────

    def _validate_inputs(self):
        """Validate all inputs. Returns dict or raises ValueError."""
        tickers = []
        weights = []
        for _, eng_var, weight_var, ticker_label, _ in self.ticker_rows:
            ticker_code = ticker_label.cget("text")
            if ticker_code == "—" or not ticker_code.strip():
                raise ValueError(f"종목 '{eng_var.get()}' 의 티커가 선택되지 않았습니다.")
            try:
                w = float(weight_var.get())
            except ValueError:
                raise ValueError(f"종목 '{eng_var.get()}' 의 가중치가 올바르지 않습니다.")
            tickers.append(ticker_code)
            weights.append(w)

        if abs(sum(weights) - 1.0) > 0.01:
            raise ValueError(f"가중치 합이 1.0이어야 합니다 (현재: {sum(weights):.4f})")

        initial = float(self.initial_var.get().replace(",", ""))
        monthly = float(self.monthly_var.get().replace(",", ""))
        sims = int(self.sims_var.get().replace(",", ""))

        # Frequency
        freq_map = {"매주": "weekly", "매월": "monthly", "연간": "yearly"}
        freq = freq_map.get(self.freq_var.get(), "monthly")

        # Period
        if self.period_mode.get() == "years":
            years = float(self.years_var.get())
            start, end = None, None
        else:
            years = None
            start = self.start_var.get()
            end = self.end_var.get()

        return {
            "tickers": tickers, "weights": weights,
            "initial": initial, "monthly": monthly,
            "sims": sims, "freq": freq,
            "start": start, "end": end, "years": years,
        }

    def _run_simulation(self):
        if self._running:
            return

        try:
            params = self._validate_inputs()
        except ValueError as e:
            self.status_label.configure(text=f"오류: {e}", text_color=THEME["error"])
            return

        self._running = True
        self.status_label.configure(text="데이터 수집 중...", text_color=THEME["warning"])

        def worker():
            try:
                from investment_simulator import (
                    fetch_historical_data, compute_portfolio_params,
                    compute_simulation_months, run_simulation,
                    compute_ticker_risk_metrics,
                )

                stats, price_data = fetch_historical_data(params["tickers"])

                total_months = compute_simulation_months(
                    params["start"], params["end"], params["years"])

                self.root.after(0, lambda: self.status_label.configure(
                    text=f"시뮬레이션 실행 중... ({params['sims']:,}회)"))

                result = run_simulation(
                    params["tickers"], stats, params["weights"],
                    params["initial"], params["monthly"],
                    total_months, params["sims"], params["freq"],
                )

                # Per-ticker risk metrics
                self.root.after(0, lambda: self.status_label.configure(
                    text="종목별 리스크 분석 중..."))

                ticker_metrics = {}
                for t in params["tickers"]:
                    ticker_metrics[t] = compute_ticker_risk_metrics(
                        t, stats, price_data, total_months, num_sims=1000)

                port_mean, port_vol = compute_portfolio_params(
                    stats, params["tickers"], params["weights"])

                self._last_result = {
                    "paths": result["portfolio"],
                    "per_ticker_paths": result["per_ticker"],
                    "params": {
                        **params,
                        "total_months": total_months,
                        "port_mean": port_mean,
                        "port_vol": port_vol,
                    },
                    "ticker_metrics": ticker_metrics,
                    "tickers": params["tickers"],
                    "weights": params["weights"],
                    "price_data": price_data,
                    "stats": stats,
                    "run_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }

                self.root.after(0, self._on_simulation_done)

            except Exception as e:
                self.root.after(0, lambda: self._on_simulation_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_simulation_done(self):
        self._running = False
        self.status_label.configure(text="완료!", text_color=THEME["success"])
        self._render_results()

    def _on_simulation_error(self, msg):
        self._running = False
        self.status_label.configure(text=f"오류: {msg}", text_color=THEME["error"])

    # ───────────────────────────────
    #  Render Results (Tab Structure)
    # ───────────────────────────────

    def _render_results(self):
        self._clear_results()
        r = self._last_result
        if not r:
            return

        self.tabview = ctk.CTkTabview(
            self.right_panel, fg_color=THEME["bg"],
            segmented_button_fg_color=THEME["surface"],
            segmented_button_selected_color=THEME["accent"],
            segmented_button_selected_hover_color=THEME["accent_hover"],
            segmented_button_unselected_color=THEME["card"],
            segmented_button_unselected_hover_color=THEME["surface"],
        )
        self.tabview.pack(fill="both", expand=True, padx=8, pady=8)

        self.tabview.add("포트폴리오 결과")
        self.tabview.add("종목별 비교")
        self.tabview.add("Raw Data")

        self._render_portfolio_tab()
        self._render_comparison_tab()
        self._render_raw_data_tab()

    # ── Tab 1: Portfolio Results ──

    def _render_portfolio_tab(self):
        r = self._last_result
        tab = self.tabview.tab("포트폴리오 결과")
        scroll = ctk.CTkScrollableFrame(tab, fg_color=THEME["bg"])
        scroll.pack(fill="both", expand=True)

        p = r["params"]

        from investment_simulator import (
            plot_summary_dashboard, plot_percentile_bar,
            plot_fan_chart, plot_histogram, plot_trend_chart,
        )

        config = load_config()
        font_scale = config.get("font_scale", 100)

        # Summary dashboard
        fig1 = Figure(figsize=(14, 10), dpi=80)
        plot_summary_dashboard(
            r["paths"], r["tickers"], r["weights"], r["stats"],
            p["initial"], p["monthly"], p["total_months"], p["freq"],
            r["per_ticker_paths"], font_scale=font_scale, fig=fig1,
        )
        self._embed_figure(scroll, fig1)

        # Percentile bar
        fig2 = Figure(figsize=(10, 5), dpi=80)
        plot_percentile_bar(
            r["paths"], p["initial"], p["monthly"],
            p["total_months"], p["freq"], font_scale=font_scale, fig=fig2,
        )
        self._embed_figure(scroll, fig2)

        # 2-column grid: trend charts + fan + histogram
        grid = ctk.CTkFrame(scroll, fg_color="transparent")
        grid.pack(fill="x", pady=8)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        col = 0
        row_idx = 0
        for t in r["tickers"]:
            close, daily_ret = r["price_data"][t]
            fig_t = Figure(figsize=(7, 8), dpi=80)
            plot_trend_chart(t, close, daily_ret, r["stats"][t]["mean"],
                           r["stats"][t]["vol"], fig=fig_t)
            frame = ctk.CTkFrame(grid, fg_color="transparent")
            frame.grid(row=row_idx, column=col, padx=4, pady=4, sticky="nsew")
            canvas = FigureCanvasTkAgg(fig_t, master=frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            col += 1
            if col > 1:
                col = 0
                row_idx += 1

        # Fan chart
        fig_fan = Figure(figsize=(7, 5), dpi=80)
        plot_fan_chart(r["paths"], p["total_months"], p["start"], p["end"], fig=fig_fan)
        frame_fan = ctk.CTkFrame(grid, fg_color="transparent")
        frame_fan.grid(row=row_idx, column=col, padx=4, pady=4, sticky="nsew")
        canvas_fan = FigureCanvasTkAgg(fig_fan, master=frame_fan)
        canvas_fan.draw()
        canvas_fan.get_tk_widget().pack(fill="both", expand=True)
        col += 1
        if col > 1:
            col = 0
            row_idx += 1

        # Histogram
        fig_hist = Figure(figsize=(7, 5), dpi=80)
        plot_histogram(r["paths"], fig=fig_hist)
        frame_hist = ctk.CTkFrame(grid, fg_color="transparent")
        frame_hist.grid(row=row_idx, column=col, padx=4, pady=4, sticky="nsew")
        canvas_hist = FigureCanvasTkAgg(fig_hist, master=frame_hist)
        canvas_hist.draw()
        canvas_hist.get_tk_widget().pack(fill="both", expand=True)

    # ── Tab 2: Ticker Comparison ──

    def _render_comparison_tab(self):
        r = self._last_result
        tab = self.tabview.tab("종목별 비교")

        # Help button
        top_bar = ctk.CTkFrame(tab, fg_color="transparent")
        top_bar.pack(fill="x", padx=8, pady=(4, 0))
        ctk.CTkButton(
            top_bar, text="?", width=28, height=28, font=FONT_BODY,
            fg_color=THEME["text_secondary"], text_color="#FFFFFF",
            hover_color=THEME["accent"], corner_radius=14,
            command=self._show_comparison_help_popup,
        ).pack(side="right")

        scroll = ctk.CTkScrollableFrame(tab, fg_color=THEME["bg"])
        scroll.pack(fill="both", expand=True)

        from investment_simulator import plot_ticker_comparison

        N = len(r["tickers"])
        total_height = (N * 1.2 + 0.6) * 6 + 4
        fig = Figure(figsize=(14, total_height), dpi=80)
        plot_ticker_comparison(r["ticker_metrics"], r["tickers"], r["weights"], fig=fig)

        self._embed_figure(scroll, fig)

    def _show_comparison_help_popup(self):
        if hasattr(self, "_help_window") and self._help_window.winfo_exists():
            self._help_window.focus()
            return

        self._help_window = ctk.CTkToplevel(self.root)
        self._help_window.title("지표 설명")
        self._help_window.geometry("500x620")
        self._help_window.transient(self.root)

        scroll = ctk.CTkScrollableFrame(self._help_window, fg_color=THEME["bg"])
        scroll.pack(fill="both", expand=True, padx=8, pady=8)

        help_sections = [
            ("📈 수익률 μ (연환산 기대수익률)",
             "1년 동안 평균적으로 얼마나 올랐는지를 나타냅니다.\n\n"
             "과거 25년치 일간수익률을 1,000회 무작위 추출(부트스트랩)하여\n"
             "분포로 표현합니다. 점 하나의 숫자가 아니라 분포로 보여주는 이유는,\n"
             "같은 종목도 어느 기간을 보느냐에 따라 수익률 추정치가 달라지기 때문입니다.\n\n"
             "📌 읽는 법: 분포가 오른쪽에 있을수록 기대수익률이 높습니다.\n"
             "            분포가 좁을수록 추정이 안정적입니다."),

            ("📉 변동성 σ (연환산 표준편차)",
             "수익률이 얼마나 들쭉날쭉한지를 나타냅니다.\n"
             "변동성이 클수록 오를 때 많이 오르지만, 떨어질 때도 많이 떨어집니다.\n\n"
             "수익률 μ 와 동일한 부트스트랩 방식으로 분포를 만듭니다.\n\n"
             "📌 읽는 법: 분포가 왼쪽에 있을수록 안정적인 종목입니다.\n"
             "            분포가 오른쪽일수록 고위험·고변동 종목입니다."),

            ("⚖️ Sharpe Ratio (샤프 비율)",
             "위험 1단위당 얼마나 수익을 냈는지를 나타냅니다.\n"
             "수익률이 높아도 변동성이 크면 Sharpe가 낮아집니다.\n\n"
             "계산식: (수익률 - 무위험이자율) ÷ 변동성\n"
             "무위험이자율은 연 4%(rf=0.04)를 사용합니다.\n\n"
             "이 분포는 시뮬레이션 1,000개 경로 각각에서 계산한 값입니다.\n\n"
             "📌 읽는 법: 1.0 기준선(점선) 오른쪽이면 양호합니다.\n"
             "            값이 클수록 위험 대비 효율이 좋은 종목입니다."),

            ("🛡️ Sortino Ratio (소르티노 비율)",
             "Sharpe와 비슷하지만, 하락 방향의 변동성만 위험으로 봅니다.\n"
             "오르는 변동성은 좋은 것이므로 불이익을 주지 않습니다.\n\n"
             "일반적으로 Sharpe보다 투자자에게 유리한 지표로 평가됩니다.\n\n"
             "📌 읽는 법: 1.0 기준선(점선) 오른쪽이면 양호합니다.\n"
             "            Sharpe와 함께 보면 종목의 특성을 더 잘 파악할 수 있습니다."),

            ("📊 MDD (최대 낙폭, Maximum Drawdown)",
             "투자 기간 중 고점 대비 가장 많이 떨어진 폭을 나타냅니다.\n"
             "예를 들어 MDD -40%라면, 어느 시점의 최고점에서 40%까지 손실이 난 적이\n"
             "있다는 뜻입니다.\n\n"
             "음수(%) 값으로 표시되며, 시뮬레이션 1,000개 경로 각각의 MDD 분포입니다.\n\n"
             "📌 읽는 법: 분포가 0에 가까울수록(오른쪽) 낙폭이 작아 안전합니다.\n"
             "            분포가 왼쪽으로 치우칠수록 큰 손실 구간이 자주 발생합니다."),

            ("💥 VaR / CVaR (손실 위험 구간)",
             "VaR 95%: 최악의 5% 시나리오에서 원금 대비 얼마나 손실이 나는지입니다.\n"
             "          즉, 100번 중 95번은 이보다 좋은 결과가 나온다는 의미입니다.\n\n"
             "CVaR 95%: 그 최악 5% 시나리오들의 평균 손실입니다.\n"
             "           VaR보다 극단적인 위험을 더 잘 반영합니다.\n\n"
             "원금 대비 수익률(%)로 표시됩니다. x=0 기준선은 원금 보전선입니다.\n\n"
             "📌 읽는 법: 분포가 0(기준선) 오른쪽에 있으면 최악에도 수익입니다.\n"
             "            왼쪽으로 치우칠수록 극단적 손실 위험이 큽니다.\n"
             "            VaR보다 CVaR가 더 보수적인 지표입니다."),
        ]

        for title, body in help_sections:
            section = ctk.CTkFrame(scroll, fg_color=THEME["card"], corner_radius=8,
                                   border_width=1, border_color=THEME["border"])
            section.pack(fill="x", padx=4, pady=4)
            ctk.CTkLabel(section, text=title, font=FONT_SECTION,
                         text_color=THEME["text_primary"]).pack(anchor="w", padx=10, pady=(8, 2))
            ctk.CTkLabel(section, text=body, font=FONT_SMALL,
                         text_color=THEME["text_secondary"],
                         justify="left", wraplength=450).pack(anchor="w", padx=10, pady=(0, 8))

    # ── Tab 3: Raw Data ──

    def _render_raw_data_tab(self):
        r = self._last_result
        tab = self.tabview.tab("Raw Data")
        scroll = ctk.CTkScrollableFrame(tab, fg_color=THEME["bg"])
        scroll.pack(fill="both", expand=True)

        # ── Summary header ──
        header_frame = ctk.CTkFrame(scroll, fg_color=THEME["card"], corner_radius=8,
                                     border_width=1, border_color=THEME["border"])
        header_frame.pack(fill="x", padx=8, pady=8)

        # Find overall date range
        all_starts = [r["stats"][t]["history_start"] for t in r["tickers"]]
        all_ends = [r["stats"][t]["history_end"] for t in r["tickers"]]
        earliest = min(all_starts)
        latest = max(all_ends)

        ticker_names = []
        for t in r["tickers"]:
            if t in TICKER_DB:
                ticker_names.append(TICKER_DB[t]["ko"])
            else:
                ticker_names.append(t)

        ctk.CTkLabel(
            header_frame,
            text=f"데이터 수집 기간: {earliest} ~ {latest}\n"
                 f"수집 종목: {', '.join(ticker_names)}\n"
                 f"시뮬레이션 실행 시각: {r['run_time']}",
            font=FONT_BODY, text_color=THEME["text_primary"], justify="left",
        ).pack(anchor="w", padx=12, pady=10)

        # ── Ticker selection ──
        self._raw_data_scroll = scroll
        self._raw_data_table_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._raw_data_table_frame.pack(fill="x", padx=8)

        if len(r["tickers"]) > 1:
            seg_values = [TICKER_DB[t]["ko"] if t in TICKER_DB else t for t in r["tickers"]]
            self._raw_ticker_map = dict(zip(seg_values, r["tickers"]))
            seg = ctk.CTkSegmentedButton(
                scroll, values=seg_values, font=FONT_SMALL,
                fg_color=THEME["surface"], selected_color=THEME["accent"],
                selected_hover_color=THEME["accent_hover"],
                unselected_color=THEME["card"],
                text_color=THEME["text_primary"],
                command=self._on_raw_ticker_select,
            )
            seg.pack(fill="x", padx=8, pady=(0, 8))
            seg.set(seg_values[0])
            self._render_raw_table(r["tickers"][0])
        else:
            self._render_raw_table(r["tickers"][0])

        # ── Parameter summary table ──
        param_frame = ctk.CTkFrame(scroll, fg_color=THEME["card"], corner_radius=8,
                                    border_width=1, border_color=THEME["border"])
        param_frame.pack(fill="x", padx=8, pady=8)

        ctk.CTkLabel(param_frame, text="파라미터 요약", font=FONT_SECTION,
                     text_color=THEME["text_primary"]).pack(anchor="w", padx=12, pady=(8, 4))

        # Header
        phdr = ctk.CTkFrame(param_frame, fg_color=THEME["table_header_bg"])
        phdr.pack(fill="x", padx=8)
        for text, w in [("종목명", 120), ("티커", 100), ("수집기간(년)", 80),
                        ("μ(연%)", 70), ("σ(연%)", 70)]:
            ctk.CTkLabel(phdr, text=text, font=FONT_SMALL, width=w,
                         text_color=THEME["text_primary"]).pack(side="left", padx=4, pady=4)

        for i, t in enumerate(r["tickers"]):
            s = r["stats"][t]
            row_bg = THEME["table_row_alt"] if i % 2 == 0 else THEME["card"]
            prow = ctk.CTkFrame(param_frame, fg_color=row_bg)
            prow.pack(fill="x", padx=8)

            ko = TICKER_DB[t]["ko"] if t in TICKER_DB else t
            for text, w in [(ko, 120), (t, 100), (f"{s['history_years']}", 80),
                            (f"{s['mean']*100:.1f}%", 70), (f"{s['vol']*100:.1f}%", 70)]:
                ctk.CTkLabel(prow, text=text, font=FONT_SMALL, width=w,
                             text_color=THEME["text_primary"]).pack(side="left", padx=4, pady=2)

    def _on_raw_ticker_select(self, value):
        ticker = self._raw_ticker_map.get(value, value)
        self._render_raw_table(ticker)

    def _render_raw_table(self, ticker, show_all=False):
        """Render historical data table for a single ticker."""
        for w in self._raw_data_table_frame.winfo_children():
            w.destroy()

        r = self._last_result
        close, daily_ret = r["price_data"][ticker]
        rolling_vol = daily_ret.rolling(60).std() * np.sqrt(252) * 100

        # Limit to last 500 rows by default
        n_rows = len(close)
        display_n = n_rows if show_all else min(500, n_rows)
        start_idx = n_rows - display_n

        # Header
        hdr = ctk.CTkFrame(self._raw_data_table_frame, fg_color=THEME["table_header_bg"])
        hdr.pack(fill="x")
        for text, w in [("날짜", 100), ("종가(₩)", 100), ("일간수익률(%)", 100), ("60일변동성(%)", 100)]:
            ctk.CTkLabel(hdr, text=text, font=FONT_SMALL, width=w,
                         text_color=THEME["text_primary"]).pack(side="left", padx=4, pady=4)

        # Data rows (reversed: newest first)
        for i in range(n_rows - 1, start_idx - 1, -1):
            row_bg = THEME["table_row_alt"] if (n_rows - 1 - i) % 2 == 0 else THEME["card"]
            row = ctk.CTkFrame(self._raw_data_table_frame, fg_color=row_bg)
            row.pack(fill="x")

            dt = close.index[i].strftime("%Y-%m-%d")
            price = f"₩{close.iloc[i]:,.0f}"

            if i < len(daily_ret) and i > 0:
                ret_val = daily_ret.iloc[i - 1] * 100 if i - 1 < len(daily_ret) else None
            else:
                ret_val = None

            # Align indices for daily_ret (which starts from index 1 of close)
            ret_idx = close.index[i]
            if ret_idx in daily_ret.index:
                ret_val = daily_ret.loc[ret_idx] * 100
                ret_text = f"{ret_val:+.2f}%"
                ret_color = THEME["success"] if ret_val >= 0 else THEME["error"]
            else:
                ret_text = "—"
                ret_color = THEME["text_disabled"]

            if ret_idx in rolling_vol.index and not np.isnan(rolling_vol.loc[ret_idx]):
                vol_text = f"{rolling_vol.loc[ret_idx]:.1f}%"
            else:
                vol_text = "—"

            ctk.CTkLabel(row, text=dt, font=FONT_SMALL, width=100,
                         text_color=THEME["text_primary"]).pack(side="left", padx=4, pady=1)
            ctk.CTkLabel(row, text=price, font=FONT_SMALL, width=100,
                         text_color=THEME["text_primary"]).pack(side="left", padx=4, pady=1)
            ctk.CTkLabel(row, text=ret_text, font=FONT_SMALL, width=100,
                         text_color=ret_color).pack(side="left", padx=4, pady=1)
            ctk.CTkLabel(row, text=vol_text, font=FONT_SMALL, width=100,
                         text_color=THEME["text_primary"]).pack(side="left", padx=4, pady=1)

        # Show all button
        if not show_all and n_rows > 500:
            ctk.CTkButton(
                self._raw_data_table_frame, text=f"전체 보기 ({n_rows:,}행)",
                font=FONT_SMALL, fg_color=THEME["accent"], hover_color=THEME["accent_hover"],
                command=lambda: self._render_raw_table(ticker, show_all=True),
            ).pack(pady=8)

    # ───────────────────────────────
    #  Helpers
    # ───────────────────────────────

    def _embed_figure(self, parent, fig):
        """Embed matplotlib Figure into a CTk parent."""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=4, pady=4)
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    # ───────────────────────────────
    #  Reset
    # ───────────────────────────────

    def _reset(self):
        # Clear ticker rows
        for row in self.ticker_rows:
            row[0].destroy()
        self.ticker_rows.clear()

        # Re-add defaults
        for eng_name, ticker_code, weight, ko_name in DEFAULT_TICKERS:
            row = self._add_ticker_row()
            row[1].set(eng_name)
            row[2].set(weight)
            row[3].configure(text=ticker_code)
            row[4].configure(text=ko_name)

        self.initial_var.set("10,000,000")
        self.monthly_var.set("500,000")
        self.freq_var.set("매월")
        self.years_var.set("20")
        self.start_var.set("2025-01")
        self.end_var.set("2045-01")
        self.sims_var.set("10,000")
        self.period_mode.set("years")
        self._on_period_mode_change("연수 지정")

        self._clear_results()
        self._build_results_placeholder()
        self.status_label.configure(text="", text_color=THEME["text_secondary"])

    # ───────────────────────────────
    #  Settings Dialog
    # ───────────────────────────────

    def _open_settings(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("설정")
        dialog.geometry("420x400")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center on main window
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 420) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 400) // 2
        dialog.geometry(f"420x400+{x}+{y}")

        config = load_config()

        inner = ctk.CTkFrame(dialog, fg_color=THEME["bg"])
        inner.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(inner, text="글꼴 설정", font=FONT_SECTION,
                     text_color=THEME["text_primary"]).pack(anchor="w", pady=(0, 12))

        # Font family
        ctk.CTkLabel(inner, text="글꼴:", font=FONT_SMALL,
                     text_color=THEME["text_secondary"]).pack(anchor="w")
        font_candidates = get_available_font_candidates()
        font_var = ctk.StringVar(value=config.get("font_family", font_candidates[0]))
        font_combo = ctk.CTkComboBox(
            inner, values=font_candidates, variable=font_var,
            state="readonly", font=FONT_INPUT, width=300,
        )
        font_combo.pack(anchor="w", pady=(2, 8))

        # Mono font
        ctk.CTkLabel(inner, text="고정폭 글꼴:", font=FONT_SMALL,
                     text_color=THEME["text_secondary"]).pack(anchor="w")
        mono_candidates = get_available_mono_candidates()
        mono_var = ctk.StringVar(value=config.get("mono_font", mono_candidates[0]))
        mono_combo = ctk.CTkComboBox(
            inner, values=mono_candidates, variable=mono_var,
            state="readonly", font=FONT_INPUT, width=300,
        )
        mono_combo.pack(anchor="w", pady=(2, 8))

        # Font scale
        ctk.CTkLabel(inner, text="글꼴 크기:", font=FONT_SMALL,
                     text_color=THEME["text_secondary"]).pack(anchor="w")

        scale_frame = ctk.CTkFrame(inner, fg_color="transparent")
        scale_frame.pack(fill="x", pady=(2, 8))

        scale_label = ctk.CTkLabel(scale_frame, text=f"{config.get('font_scale', 100)}%",
                                    font=FONT_BODY, text_color=THEME["text_primary"])
        scale_label.pack(side="right", padx=(8, 0))

        scale_var = ctk.DoubleVar(value=config.get("font_scale", 100))
        scale_slider = ctk.CTkSlider(
            scale_frame, from_=80, to=150, number_of_steps=14,
            variable=scale_var, width=250,
            fg_color=THEME["surface"], progress_color=THEME["accent"],
            button_color=THEME["accent"], button_hover_color=THEME["accent_hover"],
        )
        scale_slider.pack(side="left")

        # Preview
        preview_frame = ctk.CTkFrame(inner, fg_color=THEME["surface"], corner_radius=8,
                                      border_width=1, border_color=THEME["border"])
        preview_frame.pack(fill="x", pady=(0, 16))
        preview_label = ctk.CTkLabel(
            preview_frame, text="미리보기: 가나다 ABC 123",
            font=FONT_BODY, text_color=THEME["text_primary"],
        )
        preview_label.pack(padx=12, pady=12)

        def update_preview(*_):
            scale = int(scale_var.get())
            scale_label.configure(text=f"{scale}%")
            family = font_var.get()
            size = max(8, round(13 * scale / 100))
            preview_label.configure(font=(family, size))

        scale_var.trace_add("write", update_preview)
        font_var.trace_add("write", update_preview)

        # Buttons
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(fill="x")

        def on_apply():
            new_config = {
                "font_family": font_var.get(),
                "mono_font": mono_var.get(),
                "font_scale": int(scale_var.get()),
            }
            save_config(new_config)
            _reload_fonts(new_config)
            self._setup_chart_style()
            dialog.destroy()
            self._rebuild_ui()

        ctk.CTkButton(
            btn_frame, text="적용", font=FONT_BODY, width=80,
            fg_color=THEME["accent"], hover_color=THEME["accent_hover"],
            command=on_apply,
        ).pack(side="right")

        ctk.CTkButton(
            btn_frame, text="취소", font=FONT_BODY, width=80,
            fg_color="transparent", text_color=THEME["text_secondary"],
            border_width=1, border_color=THEME["border"],
            hover_color=THEME["surface"], command=dialog.destroy,
        ).pack(side="right", padx=(0, 8))

    # ───────────────────────────────
    #  UI State Preservation
    # ───────────────────────────────

    def _save_ui_state(self):
        state = {
            "tickers": [
                {
                    "eng_name": row[1].get(),
                    "weight": row[2].get(),
                    "ticker": row[3].cget("text"),
                    "ko_name": row[4].cget("text"),
                }
                for row in self.ticker_rows
            ],
            "initial": self.initial_var.get(),
            "monthly": self.monthly_var.get(),
            "freq": self.freq_var.get(),
            "period_mode": self.period_mode.get(),
            "years": self.years_var.get(),
            "start": self.start_var.get(),
            "end": self.end_var.get(),
            "sims": self.sims_var.get(),
        }
        return state

    def _restore_ui_state(self, state):
        # Clear existing rows
        for row in self.ticker_rows:
            row[0].destroy()
        self.ticker_rows.clear()

        # Restore tickers
        for t in state.get("tickers", []):
            row = self._add_ticker_row()
            row[1].set(t["eng_name"])
            row[2].set(t["weight"])
            row[3].configure(text=t["ticker"])
            row[4].configure(text=t["ko_name"])

        self.initial_var.set(state.get("initial", "10,000,000"))
        self.monthly_var.set(state.get("monthly", "500,000"))
        self.freq_var.set(state.get("freq", "매월"))
        self.years_var.set(state.get("years", "20"))
        self.start_var.set(state.get("start", "2025-01"))
        self.end_var.set(state.get("end", "2045-01"))
        self.sims_var.set(state.get("sims", "10,000"))

        mode = state.get("period_mode", "years")
        self.period_mode.set(mode)
        if mode == "years":
            self._on_period_mode_change("연수 지정")
        else:
            self._on_period_mode_change("날짜 범위")

    def _rebuild_ui(self):
        state = self._save_ui_state()
        for w in self.main_frame.winfo_children():
            w.destroy()

        left_wrapper = ctk.CTkFrame(
            self.main_frame, width=LEFT_PANEL_WIDTH, fg_color=THEME["surface"],
            corner_radius=0,
        )
        left_wrapper.pack(side="left", fill="y", padx=0, pady=0)
        left_wrapper.pack_propagate(False)

        self.left_panel = ctk.CTkScrollableFrame(
            left_wrapper, fg_color=THEME["surface"], corner_radius=0,
        )
        self.left_panel.pack(fill="both", expand=True)

        self.right_panel = ctk.CTkFrame(self.main_frame, fg_color=THEME["bg"])
        self.right_panel.pack(side="left", fill="both", expand=True, padx=0, pady=0)

        self.ticker_rows = []
        self._build_input_panel()
        self._restore_ui_state(state)

        if self._last_result:
            self._render_results()
        else:
            self._build_results_placeholder()

    # ───────────────────────────────
    #  Run
    # ───────────────────────────────

    def run(self):
        self.root.mainloop()
