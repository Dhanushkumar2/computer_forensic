import pyewf
import pytsk3
import hashlib
import json
import os

IMAGE = "/home/dhanush/myvenv/forensic_ir_app/data/samples/nps-2008-jean.E01"
OUTPUT = "disk_basic_info.json"


# ---------- Open E01 ----------
def open_ewf(path):
    files = pyewf.glob(path)
    handle = pyewf.handle()
    handle.open(files)
    return handle


# ---------- pytsk3 Wrapper ----------
class EWFImage(pytsk3.Img_Info):
    def __init__(self, ewf_handle):
        self._ewf_handle = ewf_handle
        super(EWFImage, self).__init__(url="")

    def read(self, offset, size):
        self._ewf_handle.seek(offset)
        return self._ewf_handle.read(size)

    def get_size(self):
        return self._ewf_handle.get_media_size()


# ---------- Hash Calculation ----------
def compute_hashes(path):
    print("🔐 Computing MD5 & SHA256 (streaming)...")

    md5 = hashlib.md5()
    sha = hashlib.sha256()

    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            md5.update(chunk)
            sha.update(chunk)

    return md5.hexdigest(), sha.hexdigest()


# ---------- Partition Analysis ----------
def analyze_partitions(img):
    volume = pytsk3.Volume_Info(img)

    allocated = 0
    unallocated = 0
    filesystems = []

    for part in volume:
        desc = part.desc
        if isinstance(desc, bytes):
            desc = desc.decode(errors="ignore")

        size = part.len * 512

        if "Unallocated" in desc:
            unallocated += size
        else:
            allocated += size

        filesystems.append({
            "index": part.addr,
            "description": desc,
            "start_offset": part.start * 512,
            "size": size
        })

    return allocated, unallocated, filesystems


# ---------- MAIN ----------
if __name__ == "__main__":
    print("🧩 Opening E01...")
    ewf_handle = open_ewf(IMAGE)

    total_size = ewf_handle.get_media_size()

    img = EWFImage(ewf_handle)

    allocated, unallocated, partitions = analyze_partitions(img)

    md5_hash, sha_hash = compute_hashes(IMAGE)

    result = {
        "total_disk_space": total_size,
        "allocated_space": allocated,
        "unallocated_space": unallocated,
        "file_systems": partitions,
        "md5": md5_hash,
        "sha256": sha_hash
    }

    with open(OUTPUT, "w") as f:
        json.dump(result, f, indent=4)

    print(f"✅ Saved: {OUTPUT}")
