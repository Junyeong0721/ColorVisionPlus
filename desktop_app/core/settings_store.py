from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from core.color_correction import CorrectionOptions


APP_DATA_DIR = Path(__file__).resolve().parents[1] / "user_data"


DEFAULT_SETTINGS = {
    "ui_language_policy": "ko_only",
    "theme": "light",
    "last_profile_id": "default",
    "default_save_folder": "",
    "preview_max_size": 1600,
    "overlay_enabled": False,
    "overlay_hotkey": "Ctrl+Alt+C",
    "overlay_opacity": 0.35,
    "low_power_mode": False,
}


@dataclass
class CvdProfile:
    profile_id: str
    name: str
    cvd_type: str = "normal"
    correction_strength: int = 0
    contrast_boost: int = 20
    saturation_shift: int = 0
    brightness_shift: int = 0
    gamma: float = 1.0
    created_at: str = ""
    updated_at: str = ""

    def to_options(self) -> CorrectionOptions:
        return CorrectionOptions(
            cvd_type=self.cvd_type,
            correction_strength=self.correction_strength,
            contrast_boost=self.contrast_boost,
            saturation_shift=self.saturation_shift,
            brightness_shift=self.brightness_shift,
            gamma=self.gamma,
        )


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def default_profile() -> CvdProfile:
    now = now_iso()
    return CvdProfile(
        profile_id="default",
        name="내 화면 보정",
        created_at=now,
        updated_at=now,
    )


class SettingsStore:
    def __init__(self, data_dir: Path | None = None):
        self.data_dir = Path(data_dir) if data_dir is not None else APP_DATA_DIR
        self.config_path = self.data_dir / "config.json"
        self.profiles_path = self.data_dir / "profiles.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load_settings(self) -> dict:
        data = self._read_json(self.config_path, DEFAULT_SETTINGS.copy())
        settings = DEFAULT_SETTINGS.copy()
        if isinstance(data, dict):
            settings.update(data)
        else:
            self._backup_invalid_file(self.config_path)
        self.save_settings(settings)
        return settings

    def save_settings(self, settings: dict) -> None:
        merged = DEFAULT_SETTINGS.copy()
        merged.update(settings)
        self._write_json(self.config_path, merged)

    def load_profiles(self) -> list[CvdProfile]:
        data = self._read_json(self.profiles_path, None)
        profiles: list[CvdProfile] = []

        if isinstance(data, list):
            for raw_profile in data:
                profile = self._profile_from_dict(raw_profile)
                if profile is not None:
                    profiles.append(profile)
        elif data is not None:
            self._backup_invalid_file(self.profiles_path)

        if not profiles:
            profiles = [default_profile()]
            self.save_profiles(profiles)

        return profiles

    def save_profiles(self, profiles: list[CvdProfile]) -> None:
        if not profiles:
            profiles = [default_profile()]
        self._write_json(self.profiles_path, [asdict(profile) for profile in profiles])

    def get_last_profile(self) -> CvdProfile:
        settings = self.load_settings()
        profiles = self.load_profiles()
        last_id = settings.get("last_profile_id")

        for profile in profiles:
            if profile.profile_id == last_id:
                return profile

        settings["last_profile_id"] = profiles[0].profile_id
        self.save_settings(settings)
        return profiles[0]

    def set_last_profile(self, profile_id: str) -> None:
        settings = self.load_settings()
        settings["last_profile_id"] = profile_id
        self.save_settings(settings)

    def save_profile_from_options(
        self,
        name: str,
        options: CorrectionOptions,
        profile_id: str | None = None,
    ) -> CvdProfile:
        profiles = self.load_profiles()
        now = now_iso()
        target_id = profile_id or uuid4().hex
        created_at = now

        for index, profile in enumerate(profiles):
            if profile.profile_id == target_id:
                created_at = profile.created_at or now
                profiles[index] = CvdProfile(
                    profile_id=target_id,
                    name=name,
                    cvd_type=options.cvd_type,
                    correction_strength=int(options.correction_strength),
                    contrast_boost=int(options.contrast_boost),
                    saturation_shift=int(options.saturation_shift),
                    brightness_shift=int(options.brightness_shift),
                    gamma=round(float(options.gamma), 2),
                    created_at=created_at,
                    updated_at=now,
                )
                self.save_profiles(profiles)
                self.set_last_profile(target_id)
                return profiles[index]

        new_profile = CvdProfile(
            profile_id=target_id,
            name=name,
            cvd_type=options.cvd_type,
            correction_strength=int(options.correction_strength),
            contrast_boost=int(options.contrast_boost),
            saturation_shift=int(options.saturation_shift),
            brightness_shift=int(options.brightness_shift),
            gamma=round(float(options.gamma), 2),
            created_at=created_at,
            updated_at=now,
        )
        profiles.append(new_profile)
        self.save_profiles(profiles)
        self.set_last_profile(new_profile.profile_id)
        return new_profile

    def delete_profile(self, profile_id: str) -> list[CvdProfile]:
        profiles = [
            profile for profile in self.load_profiles()
            if profile.profile_id != profile_id
        ]
        if not profiles:
            profiles = [default_profile()]
        self.save_profiles(profiles)
        self.set_last_profile(profiles[0].profile_id)
        return profiles

    def export_profile(self, profile_id: str, destination: str | Path) -> CvdProfile:
        profile = self.get_profile(profile_id)
        if profile is None:
            raise ValueError("프로필을 찾을 수 없습니다.")
        self._write_json(Path(destination), asdict(profile))
        return profile

    def import_profile(self, source: str | Path) -> CvdProfile:
        raw_profile = self._read_json(Path(source), None)
        profile = self._profile_from_dict(raw_profile)
        if profile is None:
            raise ValueError("프로필 JSON 형식이 올바르지 않습니다.")

        existing_profiles = self.load_profiles()
        existing_ids = {item.profile_id for item in existing_profiles}
        existing_names = {item.name for item in existing_profiles}

        if profile.profile_id in existing_ids:
            profile.profile_id = uuid4().hex
        if profile.name in existing_names:
            profile.name = f"{profile.name} (가져옴)"

        profile.created_at = profile.created_at or now_iso()
        profile.updated_at = now_iso()
        existing_profiles.append(profile)
        self.save_profiles(existing_profiles)
        self.set_last_profile(profile.profile_id)
        return profile

    def get_profile(self, profile_id: str) -> CvdProfile | None:
        for profile in self.load_profiles():
            if profile.profile_id == profile_id:
                return profile
        return None

    def _profile_from_dict(self, data: object) -> CvdProfile | None:
        if not isinstance(data, dict):
            return None

        profile_id = str(data.get("profile_id") or uuid4().hex)
        name = str(data.get("name") or data.get("display_name") or "내 화면 보정")

        try:
            return CvdProfile(
                profile_id=profile_id,
                name=name,
                cvd_type=str(data.get("cvd_type") or "normal"),
                correction_strength=int(data.get("correction_strength", data.get("severity", 60))),
                contrast_boost=int(data.get("contrast_boost", 20)),
                saturation_shift=int(data.get("saturation_shift", 0)),
                brightness_shift=int(data.get("brightness_shift", 0)),
                gamma=round(float(data.get("gamma", 1.0)), 2),
                created_at=str(data.get("created_at") or now_iso()),
                updated_at=str(data.get("updated_at") or now_iso()),
            )
        except (TypeError, ValueError):
            return None

    def _read_json(self, path: Path, fallback: object) -> object:
        if not path.exists():
            return fallback
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._backup_invalid_file(path)
            return fallback

    def _write_json(self, path: Path, data: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _backup_invalid_file(self, path: Path) -> None:
        if not path.exists():
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = path.with_suffix(f"{path.suffix}.bak_{timestamp}")
        try:
            shutil.copy2(path, backup)
        except OSError:
            pass
