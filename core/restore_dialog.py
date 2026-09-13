"""
Hộp thoại khôi phục ứng dụng đã gỡ (Restore Hub).
Hiển thị danh sách các app đã gỡ để chọn và phục hồi lại thiết bị.
"""

from __future__ import annotations

import customtkinter as ctk
import tkinter as tk
from typing import Callable, Optional

from core.ui_theme import C, UI, RADIUS, SPACE, get_font
from core.window_utils import show_overlay_panel


def show_restore_dialog(
    parent: ctk.Misc,
    removed_items: list[dict],
    on_restore: Callable[[list[str]], None],
    on_remove_history: Optional[Callable[[list[str]], None]] = None,
) -> None:
    """Hiển thị bảng chọn khôi phục app đã gỡ."""
    if not removed_items:
        from core.confirm_dialog import show_notice
        show_notice(parent, "Lịch sử khôi phục", "Chưa có ứng dụng nào trong lịch sử gỡ bỏ.", kind="info")
        return

    selected_pkgs: set[str] = set()
    checkbox_vars: dict[str, tk.BooleanVar] = {}

    def _build(inner: ctk.CTkFrame, close: Callable[[], None]) -> None:
        # Header
        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x", pady=(0, SPACE["3"]))

        UI.label(header, "↺ Khôi phục ứng dụng đã gỡ", variant="heading").pack(anchor="w")
        ctk.CTkLabel(
            header,
            text=f"Có {len(removed_items)} ứng dụng trong lịch sử. Chọn các app bạn muốn đưa trở lại máy.",
            font=get_font("body"),
            text_color=C["text_secondary"],
            anchor="w",
        ).pack(anchor="w", pady=(SPACE["1"], 0))

        # Select all / Deselect bar
        bar = ctk.CTkFrame(inner, fg_color="transparent")
        bar.pack(fill="x", pady=(0, SPACE["2"]))

        def _toggle_all(val: bool) -> None:
            for pkg, var in checkbox_vars.items():
                var.set(val)
                if val:
                    selected_pkgs.add(pkg)
                else:
                    selected_pkgs.discard(pkg)
            _update_status()

        UI.btn(bar, "Chọn tất cả", lambda: _toggle_all(True), variant="ghost", width=80, height=28).pack(side="left", padx=(0, SPACE["2"]))
        UI.btn(bar, "Bỏ chọn", lambda: _toggle_all(False), variant="ghost", width=70, height=28).pack(side="left")

        status_lbl = ctk.CTkLabel(
            bar,
            text="Đã chọn: 0",
            font=get_font("caption"),
            text_color=C["text_secondary"],
        )
        status_lbl.pack(side="right")

        def _update_status() -> None:
            status_lbl.configure(text=f"Đã chọn: {len(selected_pkgs)}")

        # Scrollable list
        scroll = ctk.CTkScrollableFrame(
            inner,
            height=320,
            fg_color=C["card_bg"],
            corner_radius=RADIUS["md"],
        )
        scroll.pack(fill="both", expand=True, pady=(0, SPACE["3"]))

        for item in removed_items:
            pkg = item.get("package", "")
            name = item.get("name", pkg)
            time_str = item.get("timestamp", "")
            is_sys = item.get("is_system", True)
            has_backup = bool(item.get("backup_apk"))

            var = tk.BooleanVar(value=False)
            checkbox_vars[pkg] = var

            def _on_check(p=pkg, v=var) -> None:
                if v.get():
                    selected_pkgs.add(p)
                else:
                    selected_pkgs.discard(p)
                _update_status()

            row = ctk.CTkFrame(scroll, fg_color=C["card_inner_bg"], corner_radius=RADIUS["sm"])
            row.pack(fill="x", pady=2, padx=2)

            cb = ctk.CTkCheckBox(
                row,
                text="",
                variable=var,
                command=_on_check,
                width=24,
                checkbox_width=18,
                checkbox_height=18,
            )
            cb.pack(side="left", padx=(SPACE["2"], SPACE["2"]), pady=SPACE["2"])

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True, pady=SPACE["2"])

            name_lbl = ctk.CTkLabel(
                info,
                text=name,
                font=get_font("body"),
                text_color=C["text_primary"],
                anchor="w",
            )
            name_lbl.pack(anchor="w")

            pkg_lbl = ctk.CTkLabel(
                info,
                text=f"{pkg}  •  Gỡ lúc: {time_str}",
                font=get_font("caption"),
                text_color=C["text_muted"],
                anchor="w",
            )
            pkg_lbl.pack(anchor="w")

            # Tag loại app
            tag_text = "Hệ thống" if is_sys else ("Đã backup APK" if has_backup else "User App")
            tag_color = C["accent"] if is_sys else C["success"]
            tag = ctk.CTkLabel(
                row,
                text=tag_text,
                font=get_font("caption"),
                text_color=tag_color,
                padx=SPACE["2"],
            )
            tag.pack(side="right", padx=SPACE["2"])

        # Bottom actions
        actions = ctk.CTkFrame(inner, fg_color="transparent")
        actions.pack(fill="x", pady=(SPACE["2"], 0))

        def _do_restore() -> None:
            if not selected_pkgs:
                from core.confirm_dialog import show_notice
                show_notice(parent, "Thông báo", "Vui lòng tích chọn ít nhất 1 ứng dụng để khôi phục.", kind="info")
                return
            close()
            on_restore(list(selected_pkgs))

        def _do_remove_history() -> None:
            if not selected_pkgs:
                return
            close()
            if on_remove_history:
                on_remove_history(list(selected_pkgs))

        UI.btn(actions, "Đóng", close, variant="ghost", width=80, height=36).pack(side="right", padx=(SPACE["2"], 0))
        UI.btn(
            actions,
            "↺ Khôi phục đã chọn",
            _do_restore,
            variant="primary",
            width=160,
            height=36,
        ).pack(side="right")

        if on_remove_history:
            UI.btn(
                actions,
                "Xóa khỏi lịch sử",
                _do_remove_history,
                variant="ghost",
                width=120,
                height=36,
            ).pack(side="left")

    show_overlay_panel(parent, _build, max_width=560)
