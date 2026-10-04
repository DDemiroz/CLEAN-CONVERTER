# SPDX-License-Identifier: GPL-3.0-only
# Copyright © 2026 Demir Demiröz. See LICENSE.md; provided without warranty.
import os
import tkinter as tk

import customtkinter as ctk


def blend_hex(start: str, end: str, amount: float) -> str:
    amount = max(0.0, min(1.0, amount))
    start = start.lstrip("#")
    end = end.lstrip("#")
    sr, sg, sb = int(start[0:2], 16), int(start[2:4], 16), int(start[4:6], 16)
    er, eg, eb = int(end[0:2], 16), int(end[2:4], 16), int(end[4:6], 16)
    r = round(sr + (er - sr) * amount)
    g = round(sg + (eg - sg) * amount)
    b = round(sb + (eb - sb) * amount)
    return f"#{r:02x}{g:02x}{b:02x}"


class StartupSplash:
    TOTAL_MS = 2500
    FADE_IN_MS = 650
    FADE_OUT_MS = 700
    STEP_MS = 35

    def __init__(
        self,
        root: tk.Tk,
        app_name: str,
        studio_name: str,
        logo_path: str,
        bg_color: str,
        panel_color: str,
        text_primary: str,
        text_muted: str,
        border_color: str,
        accent_color: str,
    ):
        self.root = root
        self.app_name = app_name
        self.studio_name = studio_name
        self.logo_path = logo_path
        self.bg_color = bg_color
        self.panel_color = panel_color
        self.text_primary = text_primary
        self.text_muted = text_muted
        self.border_color = border_color
        self.accent_color = accent_color
        self.overlay = None
        self.panel = None
        self.center = None
        self.logo_label = None
        self.title_label = None
        self.studio_label = None
        self.logo_image = None
        self._on_complete = None

    def show(self, on_complete=None):
        self._on_complete = on_complete
        self.root.update_idletasks()
        self.overlay = ctk.CTkFrame(self.root, fg_color=self.bg_color, corner_radius=0)
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.overlay.lift()

        self.panel = ctk.CTkFrame(
            self.overlay,
            width=620,
            height=360,
            corner_radius=32,
            fg_color=self.panel_color,
            border_width=1,
            border_color=self.border_color,
        )
        self.panel.place(relx=0.5, rely=0.5, anchor="center")
        self.panel.pack_propagate(False)

        self.center = ctk.CTkFrame(self.panel, fg_color="transparent")
        self.center.pack(fill="both", expand=True, padx=34, pady=32)
        self.center.grid_columnconfigure(0, weight=1)
        self.center.grid_rowconfigure(0, weight=1)
        self.center.grid_rowconfigure(1, weight=0)

        hero = ctk.CTkFrame(self.center, fg_color="transparent")
        hero.grid(row=0, column=0, sticky="nsew")
        hero.grid_columnconfigure(0, weight=1)

        self.logo_label = self._make_logo_label(hero)
        self.logo_label.pack(pady=(20, 18))

        self.title_label = ctk.CTkLabel(
            hero,
            text=self.app_name,
            text_color=self.text_primary,
            font=("Segoe UI Semibold", 30),
        )
        self.title_label.pack()

        self.studio_label = ctk.CTkLabel(
            self.center,
            text=self.studio_name,
            text_color=self.text_muted,
            font=("Segoe UI", 12),
        )
        self.studio_label.grid(row=1, column=0, sticky="s", pady=(26, 6))

        self._render(progress=0.0, phase="in")
        self._animate(duration_ms=self.TOTAL_MS, on_tick=self._tick, on_done=self._finish)

    def _make_logo_label(self, parent):
        if os.path.exists(self.logo_path):
            try:
                image = tk.PhotoImage(file=self.logo_path)
                self.logo_image = self._scale_photo(image, max_dim=118)
                return tk.Label(parent, image=self.logo_image, bg=self.panel_color, bd=0, highlightthickness=0)
            except tk.TclError:
                pass
        return tk.Label(
            parent,
            text="CC",
            bg=self.panel_color,
            fg=self.text_primary,
            font=("Segoe UI Semibold", 34),
            width=4,
            height=2,
            bd=0,
            highlightthickness=0,
        )

    def _scale_photo(self, image: tk.PhotoImage, max_dim: int) -> tk.PhotoImage:
        width = max(1, image.width())
        height = max(1, image.height())
        factor = max(width / max_dim, height / max_dim, 1)
        subsample = max(1, int(round(factor)))
        return image.subsample(subsample, subsample)

    def _animate(self, duration_ms: int, on_tick, on_done=None):
        steps = max(1, duration_ms // self.STEP_MS)

        def tick(index: int = 0):
            if self.overlay is None or not self.overlay.winfo_exists():
                return
            progress = min(1.0, index / steps)
            on_tick(progress)
            if index >= steps:
                if on_done:
                    on_done()
                return
            self.root.after(self.STEP_MS, lambda: tick(index + 1))

        tick(0)

    def _tick(self, progress: float):
        if progress < self.FADE_IN_MS / self.TOTAL_MS:
            fade_progress = progress / (self.FADE_IN_MS / self.TOTAL_MS)
            self._render(progress=progress, phase="in", phase_progress=fade_progress)
            return

        fade_out_start = 1.0 - (self.FADE_OUT_MS / self.TOTAL_MS)
        if progress >= fade_out_start:
            fade_progress = (progress - fade_out_start) / max(0.001, 1.0 - fade_out_start)
            self._render(progress=1.0, phase="out", phase_progress=fade_progress)
            return

        self._render(progress=progress, phase="hold", phase_progress=1.0)

    def _render(self, progress: float, phase: str, phase_progress: float = 0.0):
        if self.overlay is None or self.panel is None:
            return

        panel_color = self.panel_color
        title_color = self.text_primary
        studio_color = self.text_muted
        border_color = self.border_color
        offset_y = 0
        scale = 1.0
        hero_offset = 0
        if phase == "in":
            eased = phase_progress * phase_progress * (3 - 2 * phase_progress)
            panel_color = blend_hex(self.bg_color, self.panel_color, eased)
            title_color = blend_hex(self.bg_color, self.text_primary, eased)
            studio_color = blend_hex(self.bg_color, self.text_muted, eased)
            border_color = blend_hex(self.bg_color, self.border_color, eased)
            offset_y = round((1.0 - eased) * 18)
            scale = 0.96 + (0.04 * eased)
            hero_offset = round((1.0 - eased) * 8)
        elif phase == "out":
            eased = phase_progress * phase_progress * (3 - 2 * phase_progress)
            panel_color = blend_hex(self.panel_color, self.bg_color, eased * 0.9)
            title_color = blend_hex(self.text_primary, self.bg_color, eased)
            studio_color = blend_hex(self.text_muted, self.bg_color, eased)
            border_color = blend_hex(self.border_color, self.bg_color, eased)
            offset_y = -round(eased * 10)
            scale = 1.0 - (0.02 * eased)
            hero_offset = -round(eased * 6)

        width = round(620 * scale)
        height = round(360 * scale)
        self.panel.configure(fg_color=panel_color, border_color=border_color, width=width, height=height)
        self.panel.place(relx=0.5, rely=0.5, anchor="center", y=offset_y)
        self.title_label.configure(text_color=title_color)
        self.studio_label.configure(text_color=studio_color)

        if isinstance(self.logo_label, tk.Label):
            try:
                self.logo_label.configure(bg=panel_color, fg=title_color)
            except tk.TclError:
                pass
        self.logo_label.pack_configure(pady=(20 + max(0, hero_offset), 18))

    def _finish(self):
        if self.overlay is not None:
            self.overlay.destroy()
        self.overlay = None
        callback = self._on_complete
        self._on_complete = None
        if callback:
            callback()
