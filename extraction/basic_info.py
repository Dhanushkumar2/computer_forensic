import hashlib
import json
import os
import tarfile

import pyewf
import pytsk3


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


def analyze_tar(tar_path):
    """Analyze a TAR-based Android data sample."""
    total_members = 0
    total_files = 0
    total_dirs = 0
    total_symlinks = 0
    total_hardlinks = 0
    total_file_size = 0

    top_level = {}
    app_packages = set()

    with tarfile.open(tar_path, "r:*") as tf:
        for member in tf.getmembers():
            total_members += 1

            if member.isdir():
                total_dirs += 1
            elif member.issym():
                total_symlinks += 1
            elif member.islnk():
                total_hardlinks += 1
            else:
                total_files += 1
                total_file_size += member.size

            name = member.name.lstrip("./")
            if not name:
                continue

            top = name.split("/", 1)[0]
            stats = top_level.setdefault(
                top,
                {"members": 0, "files": 0, "dirs": 0, "size": 0},
            )
            stats["members"] += 1
            if member.isdir():
                stats["dirs"] += 1
            else:
                stats["files"] += 1
                stats["size"] += member.size

            if name.startswith("apps/"):
                parts = name.split("/", 2)
                if len(parts) > 1:
                    app_packages.add(parts[1])

    top_level_list = [
        {
            "name": name,
            "members": stats["members"],
            "files": stats["files"],
            "dirs": stats["dirs"],
            "size": stats["size"],
        }
        for name, stats in sorted(top_level.items())
    ]

    return {
        "total_members": total_members,
        "total_files": total_files,
        "total_dirs": total_dirs,
        "total_symlinks": total_symlinks,
        "total_hardlinks": total_hardlinks,
        "total_file_size": total_file_size,
        "top_level": top_level_list,
        "android_app_packages": sorted(app_packages),
        "android_app_count": len(app_packages),
    }


def compute_basic_info(image_path):
    """Compute basic disk or TAR sample information for a given image path."""
    if tarfile.is_tarfile(image_path):
        md5_hash, sha_hash = compute_hashes(image_path)
        tar_stats = analyze_tar(image_path)
        return {
            "image_path": image_path,
            "format": "tar",
            "md5": md5_hash,
            "sha256": sha_hash,
            "tar_stats": tar_stats,
        }

    ewf_handle = open_ewf(image_path)
    total_size = ewf_handle.get_media_size()
    img = EWFImage(ewf_handle)

    allocated, unallocated, partitions = analyze_partitions(img)
    md5_hash, sha_hash = compute_hashes(image_path)

    return {
        "image_path": image_path,
        "format": "ewf",
        "total_disk_space": total_size,
        "allocated_space": allocated,
        "unallocated_space": unallocated,
        "file_systems": partitions,
        "md5": md5_hash,
        "sha256": sha_hash
    }

# ---------- MAIN ----------
if __name__ == "__main__":
    image_path = os.environ.get(
        "FORENSIC_IMAGE_PATH",
        "/home/dhanush/myvenv/forensic_ir_app/data/samples/adb-data.tar"
    )
    output = os.environ.get("FORENSIC_BASIC_INFO_OUTPUT", "disk_basic_info.json")

    print("🧩 Opening E01...")
    result = compute_basic_info(image_path)

    with open(output, "w") as f:
        json.dump(result, f, indent=4)

    print(f"✅ Saved: {output}")
