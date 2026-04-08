#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
from typing import Optional


class WabiSabiPalette:
    # Base
    LINEN = "#F9F7F2"
    RICE_GRAY = "#EEEBE5"
    WASHI_YELLOW = "#FAF3E0"

    # Accent
    INDIGO = "#4A5C6A"
    MOSS = "#6B8C6B"
    LEAF = "#D4A574"

    # Text
    CHARCOAL = "#333333"
    DEEP_GRAY = "#666666"

    # Lines
    LINE = "#E5E1D6"


def _pick_font_family(root: tk.Misc, preferred: list[str], fallback: str) -> str:
    try:
        families = set(tkfont.families(root))
        for f in preferred:
            if f in families:
                return f
    except Exception:
        pass
    return fallback


def apply_wabi_sabi_theme(root: tk.Misc) -> None:
    p = WabiSabiPalette

    ui_font = _pick_font_family(root, ["Noto Sans JP", "Source Han Sans SC", "思源黑体", "Microsoft YaHei UI", "微软雅黑"], "Segoe UI")
    mono_font = _pick_font_family(root, ["Noto Sans Mono", "Consolas", "Cascadia Mono"], "Consolas")

    # Global backgrounds
    try:
        root.configure(bg=p.LINEN)
    except Exception:
        pass

    style = ttk.Style(root)

    # Prefer a native-like theme then override.
    try:
        if "vista" in style.theme_names():
            style.theme_use("vista")
        elif "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass

    # Defaults
    style.configure(".",
                    background=p.LINEN,
                    foreground=p.CHARCOAL,
                    bordercolor=p.LINE,
                    lightcolor=p.LINE,
                    darkcolor=p.LINE,
                    font=(ui_font, 10))

    style.configure("TFrame", background=p.LINEN)

    style.configure("Card.TFrame", background=p.WASHI_YELLOW, borderwidth=1, relief="solid")

    style.configure("TLabel", background=p.LINEN, foreground=p.CHARCOAL)
    style.configure("Secondary.TLabel", background=p.LINEN, foreground=p.DEEP_GRAY)
    style.configure("Title.TLabel", background=p.LINEN, foreground=p.CHARCOAL, font=(ui_font, 18, "bold"))

    style.configure("TLabelFrame", background=p.LINEN, foreground=p.CHARCOAL)
    style.configure("TLabelFrame.Label", background=p.LINEN, foreground=p.DEEP_GRAY, font=(ui_font, 10, "bold"))

    style.configure("TButton",
                    padding=(14, 8),
                    background=p.RICE_GRAY,
                    foreground=p.CHARCOAL,
                    borderwidth=1,
                    focusthickness=0)
    style.map("TButton",
              background=[("pressed", p.LINE), ("active", p.WASHI_YELLOW), ("disabled", p.RICE_GRAY)],
              foreground=[("disabled", p.DEEP_GRAY)])

    style.configure("Accent.TButton",
                    padding=(14, 8),
                    background=p.INDIGO,
                    foreground=p.LINEN,
                    borderwidth=1)
    style.map("Accent.TButton",
              background=[("pressed", p.INDIGO), ("active", "#3f5260"), ("disabled", p.RICE_GRAY)],
              foreground=[("disabled", p.DEEP_GRAY)])

    style.configure("TEntry",
                    padding=(10, 8),
                    fieldbackground=p.WASHI_YELLOW,
                    foreground=p.CHARCOAL,
                    borderwidth=1,
                    relief="solid")
    style.map("TEntry",
              fieldbackground=[("disabled", p.RICE_GRAY)],
              foreground=[("disabled", p.DEEP_GRAY)])

    style.configure("TCombobox",
                    padding=(10, 8))

    style.configure("TCheckbutton", background=p.LINEN, foreground=p.CHARCOAL)

    style.configure("TNotebook", background=p.LINEN, borderwidth=0)
    style.configure("TNotebook.Tab", padding=(14, 8), background=p.RICE_GRAY)
    style.map("TNotebook.Tab",
              background=[("selected", p.WASHI_YELLOW), ("active", p.WASHI_YELLOW)],
              foreground=[("selected", p.CHARCOAL), ("active", p.CHARCOAL)])

    style.configure("WabiSabi.Treeview",
                    background=p.WASHI_YELLOW,
                    fieldbackground=p.WASHI_YELLOW,
                    foreground=p.CHARCOAL,
                    rowheight=28,
                    bordercolor=p.LINE,
                    lightcolor=p.LINE,
                    darkcolor=p.LINE,
                    font=(ui_font, 10))
    style.configure("WabiSabi.Treeview.Heading",
                    background=p.RICE_GRAY,
                    foreground=p.DEEP_GRAY,
                    font=(ui_font, 10, "bold"))

    # For path / logs
    style.configure("Mono.TLabel", background=p.LINEN, foreground=p.DEEP_GRAY, font=(mono_font, 9))


def fade_in_window(win: tk.Toplevel, duration_ms: int = 240, steps: int = 12) -> None:
    try:
        win.attributes("-alpha", 0.0)
    except Exception:
        return

    step = max(1, int(duration_ms / max(1, steps)))

    def _tick(i: int = 0):
        try:
            alpha = min(1.0, (i + 1) / steps)
            win.attributes("-alpha", alpha)
            if alpha < 1.0:
                win.after(step, lambda: _tick(i + 1))
        except Exception:
            pass

    _tick(0)


class DotsLoader:
    def __init__(self, label: tk.Label | ttk.Label, base_text: str = "整理中"):
        self.label = label
        self.base_text = base_text
        self._job: Optional[str] = None
        self._n = 0

    def start(self, interval_ms: int = 220) -> None:
        self.stop()

        def _loop():
            self._n = (self._n + 1) % 4
            dots = "·" * self._n
            try:
                if isinstance(self.label, (tk.Label, ttk.Label)):
                    self.label.configure(text=f"{self.base_text}{dots}")
            except Exception:
                pass
            self._job = self.label.after(interval_ms, _loop)

        _loop()

    def stop(self) -> None:
        if self._job:
            try:
                self.label.after_cancel(self._job)
            except Exception:
                pass
            self._job = None
            try:
                self.label.configure(text=self.base_text)
            except Exception:
                pass


def create_scrollable_container(parent: tk.Misc, padding: str | int = 10) -> tuple[ttk.Frame, tk.Canvas, ttk.Frame]:
    outer = ttk.Frame(parent)
    outer.grid_rowconfigure(0, weight=1)
    outer.grid_columnconfigure(0, weight=1)

    canvas = tk.Canvas(outer, highlightthickness=0)
    v_scroll = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=canvas.yview)
    canvas.configure(yscrollcommand=v_scroll.set)

    canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    v_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))

    content = ttk.Frame(canvas, padding=str(padding))
    window_id = canvas.create_window((0, 0), window=content, anchor="nw")

    def _on_content_configure(_event=None):
        try:
            canvas.configure(scrollregion=canvas.bbox("all"))
        except Exception:
            pass

    def _on_canvas_configure(event=None):
        try:
            if event is not None:
                canvas.itemconfigure(window_id, width=event.width)
        except Exception:
            pass

    content.bind("<Configure>", _on_content_configure)
    canvas.bind("<Configure>", _on_canvas_configure)

    def _widget_wants_own_scroll(w: tk.Misc) -> bool:
        try:
            cls = w.winfo_class()
            if cls in {"Text", "Treeview", "Listbox", "Canvas"}:
                return True
        except Exception:
            return False
        return False

    def _on_mousewheel(event):
        try:
            if getattr(event, "widget", None) is not None and _widget_wants_own_scroll(event.widget):
                return
            if hasattr(event, 'delta') and event.delta:
                delta = int(-1 * (event.delta / 120))
            else:
                delta = 0
            if delta:
                canvas.yview_scroll(delta, "units")
        except Exception:
            pass

    def _bind_mousewheel(_event=None):
        try:
            outer.winfo_toplevel().bind_all("<MouseWheel>", _on_mousewheel)
        except Exception:
            pass

    def _unbind_mousewheel(_event=None):
        try:
            outer.winfo_toplevel().unbind_all("<MouseWheel>")
        except Exception:
            pass

    content.bind("<Enter>", _bind_mousewheel)
    content.bind("<Leave>", _unbind_mousewheel)

    return outer, canvas, content
