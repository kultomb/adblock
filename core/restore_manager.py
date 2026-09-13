"""
Quản lý lịch sử gỡ ứng dụng và khôi phục (Restore Hub).
Hỗ trợ:
- App hệ thống: `cmd package install-existing <pkg>`
- App đã backup APK: `adb install -r <backup_path>`
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Optional


class RestoreManager:
    """Quản lý danh sách các app đã gỡ để hỗ trợ hoàn tác/khôi phục."""

    def __init__(self, appdata_dir: str):
        self.appdata_dir = appdata_dir
        self.history_file = os.path.join(appdata_dir, "removed_history.json")
        self.backup_dir = os.path.join(appdata_dir, "apk_backups")
        os.makedirs(self.backup_dir, exist_ok=True)
        self._history: list[dict] = self._load_history()

    def _load_history(self) -> list[dict]:
        if os.path.isfile(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except Exception as exc:
                logging.warning("Không thể đọc removed_history.json: %s", exc)
        return []

    def _save_history(self) -> None:
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self._history, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            logging.error("Lỗi lưu removed_history.json: %s", exc)

    def record_removed(
        self,
        package: str,
        name: str = "",
        is_system: bool = True,
        backup_apk: Optional[str] = None,
    ) -> None:
        """Ghi nhận một package đã gỡ vào lịch sử."""
        # Xóa bản ghi cũ của package này nếu có để đưa lên đầu
        self._history = [item for item in self._history if item.get("package") != package]
        entry = {
            "package": package,
            "name": name or package,
            "is_system": is_system,
            "backup_apk": backup_apk or "",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._history.insert(0, entry)
        # Giới hạn tối đa 200 app gần nhất
        self._history = self._history[:200]
        self._save_history()

    def remove_from_history(self, package: str) -> None:
        """Xóa package khỏi danh sách lịch sử."""
        self._history = [item for item in self._history if item.get("package") != package]
        self._save_history()

    def clear_history(self) -> None:
        """Xóa toàn bộ lịch sử."""
        self._history.clear()
        self._save_history()

    def get_removed_packages(self) -> list[dict]:
        """Lấy danh sách các app đã gỡ trong lịch sử."""
        return list(self._history)

    def restore_package(self, device_manager, package: str) -> tuple[bool, str]:
        """
        Khôi phục package lên thiết bị:
        1. Thử `cmd package install-existing <pkg>` (nhanh nhất với app hệ thống/bloatware).
        2. Thử `pm install-existing <pkg>` (dành cho Android cũ).
        3. Nếu có file backup APK và hai lệnh trên thất bại, nạp lại qua `install -r`.
        """
        if not device_manager.serial:
            return False, "Chưa kết nối thiết bị"

        entry = next((x for x in self._history if x.get("package") == package), None)
        backup_apk = entry.get("backup_apk") if entry else None

        # 1. Thử cmd package install-existing
        out, err, code = device_manager.run(
            ["-s", device_manager.serial, "shell", "cmd", "package", "install-existing", package],
            timeout=15,
        )
        if code == 0 and "installed" in (out or "").lower():
            self.remove_from_history(package)
            return True, f"Khôi phục thành công {package} (từ hệ thống)"

        # 2. Thử pm install-existing (cho Android cũ)
        out2, err2, code2 = device_manager.run(
            ["-s", device_manager.serial, "shell", "pm", "install-existing", package],
            timeout=15,
        )
        combined = f"{out} {out2}".lower()
        if (code2 == 0 and "installed" in combined) or "package " + package.lower() + " installed" in combined:
            self.remove_from_history(package)
            return True, f"Khôi phục thành công {package} (từ hệ thống)"

        # 3. Nếu lệnh trên báo không tìm thấy hoặc thất bại, thử cài từ backup APK
        if backup_apk and os.path.isfile(backup_apk):
            out3, err3, code3 = device_manager.install(backup_apk)
            if code3 == 0 and "success" in (out3 or "").lower():
                self.remove_from_history(package)
                return True, f"Cài lại thành công {package} (từ bản sao lưu APK)"
            return False, f"Không thể khôi phục APK: {err3 or out3 or 'thất bại'}"

        error_msg = err or out or err2 or out2 or "Thiết bị từ chối khôi phục"
        return False, error_msg.strip()
