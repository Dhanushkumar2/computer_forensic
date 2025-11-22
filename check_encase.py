import os
import pyewf
import pytsk3
from tqdm import tqdm

SAMPLE_PATH = "forensic_ir_app/data/samples/"
IMAGE_BASENAME = "nps-2008-jean.E01"

def open_ewf_image(image_path):
    base = os.path.splitext(image_path)[0]
    segment_files = sorted([os.path.join(SAMPLE_PATH, f)
                            for f in os.listdir(SAMPLE_PATH)
                            if f.startswith(os.path.basename(base).split('.')[0])])

    if not segment_files:
        raise FileNotFoundError("❌ No EWF segment files found in the sample directory.")

    print(f"🧩 Found {len(segment_files)} EWF segment(s): {segment_files}")

    ewf_handle = pyewf.handle()
    ewf_handle.open(segment_files)

    class EWFImgInfo(pytsk3.Img_Info):
        def __init__(self, ewf_handle):
            self._ewf_handle = ewf_handle
            super(EWFImgInfo, self).__init__(url="", type=pytsk3.TSK_IMG_TYPE_EXTERNAL)

        def read(self, offset, size):
            self._ewf_handle.seek(offset)
            return self._ewf_handle.read(size)

        def get_size(self):
            return self._ewf_handle.get_media_size()

    return EWFImgInfo(ewf_handle)

def get_partition_offsets(img):
    """
    Detects partitions and returns list of offsets.
    """
    print("🔍 Scanning for partitions...")
    partition_table = pytsk3.Volume_Info(img)
    offsets = []
    for part in partition_table:
        desc = part.desc.decode("utf-8", errors="ignore")
        start = part.start * 512  # sector to byte offset
        print(f"📦 Partition: {desc} | Start sector: {part.start} | Offset: {start} bytes")
        offsets.append(start)
    return offsets

def extract_sample_metadata(img, offset):
    """
    Extracts metadata from the filesystem at given offset.
    """
    print(f"🧠 Attempting to open filesystem at offset {offset}...")
    fs = pytsk3.FS_Info(img, offset=offset)
    root_dir = fs.open_dir(path="/")

    metadata = []
    count = 0
    print("📂 Extracting sample metadata from filesystem...")
    for entry in tqdm(root_dir, desc="Reading files"):
        if not hasattr(entry, "info") or not hasattr(entry.info, "name"):
            continue

        name = entry.info.name.name.decode("utf-8", errors="ignore")
        if name in [".", ".."]:
            continue

        try:
            size = entry.info.meta.size if entry.info.meta else 0
            created = entry.info.meta.crtime if entry.info.meta else 0
            modified = entry.info.meta.mtime if entry.info.meta else 0
            accessed = entry.info.meta.atime if entry.info.meta else 0

            metadata.append({
                "file_name": name,
                "size": size,
                "created": created,
                "modified": modified,
                "accessed": accessed
            })
        except Exception:
            continue

        count += 1
        if count >= 50:  # Only read 50 files for testing
            break

    print(f"✅ Extracted {len(metadata)} entries successfully.")
    return metadata

def main():
    print("🚀 Checking EnCase image...")
    img = open_ewf_image(os.path.join(SAMPLE_PATH, IMAGE_BASENAME))

    # Step 1: Find all partitions
    offsets = get_partition_offsets(img)
    if not offsets:
        raise RuntimeError("❌ No partitions found in the image!")

    # Step 2: Try to extract from first valid partition
    for offset in offsets:
        try:
            metadata = extract_sample_metadata(img, offset)
            if metadata:
                print("\n🧾 Sample Extracted Files:")
                for i, m in enumerate(metadata[:5]):
                    print(f"{i+1}. {m['file_name']} — {m['size']} bytes")
                break
        except Exception as e:
            print(f"⚠️ Failed to open partition at {offset}: {e}")

if __name__ == "__main__":
    main()
