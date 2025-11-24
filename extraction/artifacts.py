#!/usr/bin/env python3
"""
artifacts.py
Robust artifact extractor for NTFS inside an EnCase E01 image.

Outputs: artifacts_output.json

Dependencies:
  pip install pyewf pytsk3 python-registry
"""

import os
import json
import tempfile
import sqlite3
import hashlib

import pyewf
import pytsk3
from Registry import Registry

# ---------- CONFIG ----------
IMAGE_PATH = "/home/dhanush/myvenv/forensic_ir_app/data/samples/nps-2008-jean.E01"
OUTPUT_JSON = "artifacts_output.json"

# ---------- Utilities: EWF wrapper for pytsk3 ----------
class EWFImgInfo(pytsk3.Img_Info):
    def __init__(self, ewf_handle):
        self._ewf_handle = ewf_handle
        super(EWFImgInfo, self).__init__(url="")

    def read(self, offset, size):
        self._ewf_handle.seek(offset)
        return self._ewf_handle.read(size)

    def get_size(self):
        return self._ewf_handle.get_media_size()


def open_ewf(image_path):
    files = pyewf.glob(image_path)
    if not files:
        # fallback to single path
        files = [image_path]
    ewf_handle = pyewf.handle()
    ewf_handle.open(files)
    return ewf_handle


# ---------- Helper: read file content from NTFS path ----------
def read_file_bytes(fs, path):
    """Return file bytes for a given absolute path in the mounted fs, or None."""
    try:
        fobj = fs.open(path)
    except Exception:
        return None
    try:
        size = fobj.info.meta.size
        return fobj.read_random(0, size)
    except Exception:
        return None


def write_temp(data, suffix=""):
    """Write bytes to a temp file and return path."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(data)
    tmp.close()
    return tmp.name


# ---------- Discover users / profile folders ----------
def list_user_profiles(fs):
    candidates = []
    # Common locations for user profiles
    for base in ["/Users", "/Documents and Settings", "/home"]:
        try:
            d = fs.open_dir(base)
        except Exception:
            continue
        try:
            for e in d:
                try:
                    name = e.info.name.name.decode(errors="ignore")
                    if name not in [".", ".."]:
                        candidates.append(os.path.join(base, name))
                except Exception:
                    continue
        except Exception:
            pass
    # deduplicate and return
    return sorted(list(dict.fromkeys(candidates)))


# ---------- Browser history extraction ----------
def extract_chrome_edge_history(fs, user_profile_path):
    # Chrome/Edge DB location patterns (Default profile)
    paths = [
        os.path.join(user_profile_path, "AppData", "Local", "Google", "Chrome", "User Data", "Default", "History"),
        os.path.join(user_profile_path, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default", "History"),
    ]
    results = []
    for p in paths:
        raw = read_file_bytes(fs, p)
        if not raw:
            continue
        tmp = write_temp(raw, suffix=".sqlite")
        try:
            conn = sqlite3.connect(tmp)
            cur = conn.cursor()
            # Chrome stores last_visit_time in Webkit microseconds since 1601-01-01
            cur.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 200")
            for row in cur.fetchall():
                url, title, ts = row
                results.append({"path": p, "url": url, "title": title, "last_visit_time": ts})
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass
            os.remove(tmp)
    return results


def extract_firefox_history(fs, user_profile_path):
    base = os.path.join(user_profile_path, "AppData", "Roaming", "Mozilla", "Firefox", "Profiles")
    results = []
    try:
        d = fs.open_dir(base)
    except Exception:
        return results
    for e in d:
        try:
            name = e.info.name.name.decode(errors="ignore")
            # look for places.sqlite in profile folder
            places = os.path.join(base, name, "places.sqlite")
            raw = read_file_bytes(fs, places)
            if not raw:
                continue
            tmp = write_temp(raw, suffix=".sqlite")
            try:
                conn = sqlite3.connect(tmp)
                cur = conn.cursor()
                cur.execute("SELECT url, title, last_visit_date FROM moz_places ORDER BY last_visit_date DESC LIMIT 200")
                for url, title, ts in cur.fetchall():
                    results.append({"path": places, "url": url, "title": title, "last_visit_date": ts})
            except Exception:
                pass
            finally:
                try:
                    conn.close()
                except:
                    pass
                os.remove(tmp)
        except Exception:
            continue
    return results


# ---------- Registry extraction helpers ----------
def extract_registry_hive(fs, path):
    """Return Registry.Registry object (in memory) or None."""
    raw = read_file_bytes(fs, path)
    if not raw:
        return None
    tmp = write_temp(raw, suffix=".reg")
    try:
        reg = Registry.Registry(tmp)
        os.remove(tmp)
        return reg
    except Exception:
        try:
            os.remove(tmp)
        except Exception:
            pass
        return None


def extract_usb_from_system_hive(reg):
    """Return USBSTOR entries from SYSTEM hive Registry object."""
    out = []
    try:
        key = reg.open("SYSTEM\\CurrentControlSet\\Enum\\USBSTOR")
    except Exception:
        return out
    try:
        for dev in key.subkeys():
            dev_name = dev.name()
            for inst in dev.subkeys():
                inst_name = inst.name()
                friendly = ""
                try:
                    v = inst.value("FriendlyName")
                    friendly = v.value() if v else ""
                except Exception:
                    friendly = ""
                out.append({"device": dev_name, "instance": inst_name, "friendly_name": friendly})
    except Exception:
        pass
    return out


def extract_recentdocs_from_ntuser(reg):
    out = []
    try:
        key = reg.open("Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RecentDocs")
        # RecentDocs contains value entries; we will list value names
        for v in key.values():
            try:
                out.append({"name": v.name(), "value": v.value()})
            except Exception:
                pass
    except Exception:
        pass
    return out


# ---------- Event logs list ----------
def list_event_log_files(fs):
    logs = []
    logs_dir = "/Windows/System32/winevt/Logs"
    try:
        d = fs.open_dir(logs_dir)
    except Exception:
        return logs
    for e in d:
        try:
            name = e.info.name.name.decode(errors="ignore")
            if name.lower().endswith(".evtx"):
                logs.append(os.path.join(logs_dir, name))
        except Exception:
            continue
    return logs


# ---------- Recycle Bin (list files under $Recycle.Bin or Recycler) ----------
def list_recycle_bins(fs):
    paths = []
    # common locations
    candidates = ["/$Recycle.Bin", "/Recycler", "/RECYCLER"]
    for c in candidates:
        try:
            d = fs.open_dir(c)
        except Exception:
            continue
        for e in d:
            try:
                name = e.info.name.name.decode(errors="ignore")
                if name not in [".", ".."]:
                    paths.append(os.path.join(c, name))
            except Exception:
                continue
    return paths


# ---------- Top-level orchestration ----------
def extract_artifacts_from_image(image_path):
    ewf_handle = open_ewf(image_path)
    img = EWFImgInfo(ewf_handle)

    # enumerate partitions and choose NTFS
    try:
        volume = pytsk3.Volume_Info(img)
    except Exception as ex:
        raise RuntimeError("Partition table read failed: " + str(ex))

    ntfs_offset = None
    partitions = []
    for part in volume:
        desc = part.desc
        if isinstance(desc, bytes):
            desc = desc.decode(errors="ignore")
        start = int(part.start)
        length = int(part.len)
        partitions.append({"desc": desc, "start": start, "length": length})
        # simple detection
        if "NTFS" in desc.upper() or "0x07" in desc:
            ntfs_offset = start * 512

    if ntfs_offset is None:
        raise RuntimeError("No NTFS partition detected.")

    # mount filesystem at identified offset
    try:
        fs = pytsk3.FS_Info(img, offset=ntfs_offset)
    except Exception as ex:
        raise RuntimeError("Unable to mount FS at offset {}: {}".format(ntfs_offset, ex))

    # Gather artifacts
    result = {"image_path": image_path, "partitions": partitions, "ntfs_offset_bytes": ntfs_offset, "artifacts": {}}

    # list user profiles
    profiles = list_user_profiles(fs)
    result["profiles"] = profiles

    # browser histories per profile
    browsers = {}
    for profile in profiles:
        try:
            ch = extract_chrome_edge_history(fs, profile)
            ff = extract_firefox_history(fs, profile)
            browsers[profile] = {"chrome_edge": ch, "firefox": ff}
        except Exception:
            browsers[profile] = {"chrome_edge": [], "firefox": []}
    result["artifacts"]["browsers"] = browsers

    # registry hives
    system_reg = extract_registry_hive(fs, "/Windows/System32/config/SYSTEM")
    software_reg = extract_registry_hive(fs, "/Windows/System32/config/SOFTWARE")
    sam_reg = extract_registry_hive(fs, "/Windows/System32/config/SAM")
    result["artifacts"]["registry"] = {"SYSTEM": bool(system_reg), "SOFTWARE": bool(software_reg), "SAM": bool(sam_reg)}

    # usb history from SYSTEM
    usb_entries = extract_usb_from_system_hive(system_reg) if system_reg else []
    result["artifacts"]["usb_history"] = usb_entries

    # NTUSER.DAT per profile -> recent docs
    recent = {}
    for profile in profiles:
        ntuser_path = os.path.join(profile, "NTUSER.DAT")
        reg = extract_registry_hive(fs, ntuser_path)
        if reg:
            recent[profile] = extract_recentdocs_from_ntuser(reg)
        else:
            recent[profile] = []
    result["artifacts"]["recent_docs"] = recent

    # event logs list
    result["artifacts"]["event_logs"] = list_event_log_files(fs)

    # recycle bins
    result["artifacts"]["recycle_bins"] = list_recycle_bins(fs)

    return result


# ---------- CLI ----------
if __name__ == "__main__":
    
    def convert(obj):
        """Recursively convert bytes → utf-8 string or hex if needed."""
        if isinstance(obj, bytes):
            try:
                return obj.decode("utf-8", errors="ignore")
            except Exception:
                return obj.hex()
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(i) for i in obj]
        else:
            return obj

    out_raw = extract_artifacts_from_image(IMAGE_PATH)
    out = convert(out_raw)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)

    print("Artifacts extraction completed →", OUTPUT_JSON)

