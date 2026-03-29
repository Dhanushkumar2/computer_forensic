#!/usr/bin/env python3
"""
android_tar_extractor.py
Android TAR-based artifact extraction orchestrator.
"""

import json
import os
import tarfile
from datetime import datetime


class AndroidTarExtractor:
    def __init__(self, tar_path):
        self.tar_path = tar_path
        self.tar = None
        self.members = []

    def open(self):
        """Open TAR image and load members."""
        try:
            self.tar = tarfile.open(self.tar_path, "r:*")
            self.members = self.tar.getmembers()
            return True
        except Exception as e:
            print(f"Error opening TAR: {e}")
            return False

    def _normalize(self, name):
        return name.lstrip("./")

    def _member_info(self, member):
        name = self._normalize(member.name)
        if member.isdir():
            mtype = "dir"
        elif member.issym():
            mtype = "symlink"
        elif member.islnk():
            mtype = "hardlink"
        else:
            mtype = "file"

        mtime = None
        try:
            mtime = datetime.fromtimestamp(member.mtime).isoformat()
        except Exception:
            pass

        info = {
            "path": name,
            "size": member.size,
            "mtime": mtime,
            "type": mtype,
        }
        if name.startswith("apps/"):
            parts = name.split("/", 2)
            if len(parts) > 1:
                info["package_name"] = parts[1]
        return info

    def extract_all_artifacts(self, output_file=None):
        """Extract Android artifacts from TAR sample."""
        if not self.open():
            return None

        print(f"Starting Android TAR extraction from: {self.tar_path}")

        packages = set()
        manifests = []
        app_databases = []
        shared_prefs = []
        webview_artifacts = []
        calendar_dbs = []
        sms_backups = []
        other_artifacts = []

        webview_names = {
            "Cookies",
            "Cookies-journal",
            "Web Data",
            "Web Data-journal",
            "History",
            "History-journal",
            "Visited Links",
            "Favicons",
            "Favicons-journal",
            "Top Sites",
            "Top Sites-journal",
            "Login Data",
            "Login Data-journal",
        }

        for member in self.members:
            name = self._normalize(member.name)
            if not name:
                continue

            if name.startswith("apps/"):
                parts = name.split("/", 2)
                if len(parts) > 1:
                    packages.add(parts[1])

            if name.endswith("/_manifest") or name.endswith("_manifest"):
                manifests.append(self._member_info(member))
                continue

            if "/db/" in name and not member.isdir():
                if name.endswith((".db", ".db-journal", ".db-wal", ".db-shm")):
                    app_databases.append(self._member_info(member))
                    if name.endswith("calendar.db"):
                        calendar_dbs.append(self._member_info(member))
                    continue

            if "/sp/" in name and name.endswith(".xml") and not member.isdir():
                shared_prefs.append(self._member_info(member))
                continue

            if "/r/app_webview/" in name and not member.isdir():
                base = os.path.basename(name)
                if base in webview_names or base.endswith((".db", ".sqlite")):
                    webview_artifacts.append(self._member_info(member))
                    continue

            if name.endswith("000000_sms_backup") and not member.isdir():
                sms_backups.append(self._member_info(member))
                continue

            if name.startswith("apps/") and not member.isdir():
                other_artifacts.append(self._member_info(member))

        artifacts = {
            "extraction_info": {
                "image_path": self.tar_path,
                "extraction_time": datetime.now().isoformat(),
                "total_members": len(self.members),
                "format": "android_tar",
            },
            "android_packages": sorted(packages),
            "manifests": manifests,
            "app_databases": app_databases,
            "shared_preferences": shared_prefs,
            "webview_artifacts": webview_artifacts,
            "calendar_databases": calendar_dbs,
            "sms_backups": sms_backups,
            "other_app_artifacts": other_artifacts,
        }

        artifacts["summary"] = self._generate_summary(artifacts)

        if output_file:
            self._save_artifacts(artifacts, output_file)

        print("Android TAR extraction completed!")
        return artifacts

    def _generate_summary(self, artifacts):
        return {
            "total_packages": len(artifacts.get("android_packages", [])),
            "total_manifests": len(artifacts.get("manifests", [])),
            "total_app_databases": len(artifacts.get("app_databases", [])),
            "total_shared_prefs": len(artifacts.get("shared_preferences", [])),
            "total_webview_artifacts": len(artifacts.get("webview_artifacts", [])),
            "total_calendar_databases": len(artifacts.get("calendar_databases", [])),
            "total_sms_backups": len(artifacts.get("sms_backups", [])),
            "total_other_app_artifacts": len(artifacts.get("other_app_artifacts", [])),
            "extraction_timestamp": datetime.now().isoformat(),
        }

    def _save_artifacts(self, artifacts, output_file):
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(artifacts, f, indent=2, ensure_ascii=False)
            print(f"Artifacts saved to: {output_file}")
        except Exception as e:
            print(f"Error saving artifacts: {e}")

    def close(self):
        try:
            if self.tar:
                self.tar.close()
        except Exception as e:
            print(f"Error closing TAR: {e}")


if __name__ == "__main__":
    image_path = os.environ.get(
        "FORENSIC_IMAGE_PATH",
        "/home/dhanush/myvenv/forensic_ir_app/data/samples/adb-data.tar",
    )
    output = os.environ.get(
        "FORENSIC_ANDROID_OUTPUT",
        "android_tar_artifacts.json",
    )

    extractor = AndroidTarExtractor(image_path)
    try:
        artifacts = extractor.extract_all_artifacts(output)

        if artifacts:
            print("\n=== ANDROID EXTRACTION SUMMARY ===")
            summary = artifacts.get("summary", {})
            for key, value in summary.items():
                if key != "extraction_timestamp":
                    print(f"{key.replace('_', ' ').title()}: {value}")
    except KeyboardInterrupt:
        print("\nExtraction interrupted by user")
    except Exception as e:
        print(f"Extraction failed: {e}")
    finally:
        extractor.close()
