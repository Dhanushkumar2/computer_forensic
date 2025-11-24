import json
import pyewf
import pytsk3
import sys

IMAGE = "/home/dhanush/myvenv/forensic_ir_app/data/samples/nps-2008-jean.E01"


# -----------------------------
# 1. OPEN EWF / E01 IMAGE
# -----------------------------
def open_ewf(image_path):
    try:
        ewf_files = pyewf.glob(image_path)
        handle = pyewf.handle()
        handle.open(ewf_files)
        print("🧩 Opening E01 image...")
        return handle
    except Exception as e:
        print(f"❌ Failed to open E01 image: {e}")
        sys.exit(1)


# -----------------------------
# 2. EXTRACT SAFE METADATA
# -----------------------------
def extract_basic_metadata(handle):
    """Extract metadata supported by latest pyewf."""
    print("🔍 Extracting basic metadata...")

    metadata = {}

    # Unique segment count
    try:
        metadata["segment_count"] = handle.get_number_of_segments()
    except:
        metadata["segment_count"] = None

    # Total size
    try:
        metadata["media_size"] = handle.get_media_size()
    except:
        metadata["media_size"] = None

    # Sector size
    try:
        metadata["bytes_per_sector"] = handle.get_bytes_per_sector()
    except:
        metadata["bytes_per_sector"] = None

    # Chunk size (EWF internal)
    try:
        metadata["chunk_size"] = handle.get_chunk_size()
    except:
        metadata["chunk_size"] = None

    metadata["compression"] = "Not available in this pyewf version"
    return metadata


# -----------------------------
# 3. OPEN PARTITION USING pytsk3
# -----------------------------
def open_partition(handle):
    # Create a virtual file system interface for pytsk3
    class EWFImgInfo(pytsk3.Img_Info):
        def __init__(self, ewf_handle):
            self._ewf_handle = ewf_handle
            super().__init__(url="", type=pytsk3.TSK_IMG_TYPE_EXTERNAL)

        def read(self, offset, size):
            self._ewf_handle.seek(offset)
            return self._ewf_handle.read(size)

        def get_size(self):
            return self._ewf_handle.get_media_size()

    img = EWFImgInfo(handle)

    try:
        partition_table = pytsk3.Volume_Info(img)
        print("🧱 Found partitions:")
        for part in partition_table:
            print(f" - {part.addr}: {part.desc} ({part.start * 512} bytes offset, {part.len * 512} bytes length)")
        return img, partition_table

    except Exception as e:
        print(f"❌ Unable to read partition table: {e}")
        sys.exit(1)


# -----------------------------
# 4. Extract NTFS Root Directory
# -----------------------------
def extract_ntfs_file_list(img, partition):
    print(f"🧩 Trying NTFS partition at offset {partition.start * 512}")

    try:
        fs = pytsk3.FS_Info(img, offset=partition.start * 512)
    except Exception as e:
        print(f"❌ Unable to open NTFS filesystem: {e}")
        return []

    directory = fs.open_dir(path="/")

    results = []
    print("📁 Extracting NTFS root directory...")

    for entry in directory:
        if not hasattr(entry, "info") or not hasattr(entry.info, "name"):
            continue

        name = entry.info.name.name.decode("utf-8", errors="ignore")

        # skip NTFS system entries
        if name in [".", ".."]:
            continue

        try:
            type_flag = entry.info.meta.type if entry.info.meta else None
            size = entry.info.meta.size if entry.info.meta else 0
            created = entry.info.meta.crtime if entry.info.meta else 0
            modified = entry.info.meta.mtime if entry.info.meta else 0
        except:
            type_flag, size, created, modified = None, None, None, None

        results.append({
            "name": name,
            "size": size,
            "created": str(created),
            "modified": str(modified),
            "type": str(type_flag)
        })

    return results


# -----------------------------
# MAIN EXECUTION
# -----------------------------
if __name__ == "__main__":
    import os
    print(os.path.abspath("data/samples/nps-2008-jean.E01"))

    # 1. Open Image
    handle = open_ewf(IMAGE)

    # 2. Metadata
    metadata = extract_basic_metadata(handle)
    with open("image_metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)
    print("✅ Saved: image_metadata.json")

    # 3. Partition Table
    img, partitions = open_partition(handle)

    # 4. Extract data only from NTFS partition (0x07)
    for part in partitions:
        if part.desc.startswith("NTFS") or "0x07" in part.desc:
            files = extract_ntfs_file_list(img, part)
            with open("ntfs_root_files.json", "w") as f:
                json.dump(files, f, indent=4)
            print("✅ Saved: ntfs_root_files.json")
            break

    print("🎉 Extraction complete!")
