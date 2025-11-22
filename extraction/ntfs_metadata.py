import pyewf
import pytsk3
import json

EWF_PATH = "forensic_ir_app/data/samples/nps-2008-jean.E01"
OUTPUT_JSON = "ntfs_metadata.json"

# ---------------------------
# Custom Img_Info wrapper
# ---------------------------
class EwfImgInfo(pytsk3.Img_Info):
    def __init__(self, ewf_handle):
        self._ewf_handle = ewf_handle
        super(EwfImgInfo, self).__init__()

    def close(self):
        self._ewf_handle.close()

    def read(self, offset, size):
        self._ewf_handle.seek(offset)
        return self._ewf_handle.read(size)

    def get_size(self):
        return self._ewf_handle.get_media_size()

# ---------------------------
# Helpers
# ---------------------------
def open_image(ewf_path):
    files = pyewf.glob(ewf_path)
    ewf_handle = pyewf.handle()
    ewf_handle.open(files)
    return ewf_handle

def list_partitions(img):
    try:
        volume = pytsk3.Volume_Info(img)
        print("🧱 Found partitions:")
        for part in volume:
            desc = part.desc.decode("utf-8")
            print(f" - {part.addr}: {desc} ({part.start * 512} bytes offset, {part.len * 512} bytes length)")
        return volume
    except Exception as e:
        print(f"⚠️ No partition table found: {e}")
        return None

def extract_ntfs_metadata(fs, output_path):
    print("🔍 Extracting NTFS metadata...")
    metadata = []

    try:
        root_dir = fs.open_dir("/")
        for entry in root_dir:
            if entry.info.name and entry.info.name.name.decode("utf-8") not in [".", ".."]:
                name = entry.info.name.name.decode("utf-8")
                meta = entry.info.meta
                if meta:
                    metadata.append({
                        "name": name,
                        "size": meta.size,
                        "created": str(meta.crtime),
                        "modified": str(meta.mtime),
                        "type": str(meta.type)
                    })
    except Exception as e:
        print(f"⚠️ Metadata extraction failed: {e}")
        return

    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=4)
    print(f"✅ Extracted metadata for {len(metadata)} files to {output_path}")

def extract_image_metadata(img_info, output_path):
    print("🔍 Extracting image-level metadata...")
    metadata = {
        "image_size": img_info.get_size(),
        "note": "Raw image metadata extracted."
    }
    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=4)
    print(f"✅ Saved basic image metadata to {output_path}")

# ---------------------------
# Main logic
# ---------------------------
if __name__ == "__main__":
    print("🧩 Opening EnCase image...")
    ewf_handle = open_image(EWF_PATH)
    img = EwfImgInfo(ewf_handle)

    volume = list_partitions(img)
    found_fs = False

    if volume:
        for part in volume:
            desc = part.desc.decode("utf-8")
            if "NTFS" in desc or "Basic data partition" in desc:
                offset = part.start * 512
                print(f"🧩 Trying NTFS partition at offset {offset}")
                try:
                    fs = pytsk3.FS_Info(img, offset=offset)
                    extract_ntfs_metadata(fs, OUTPUT_JSON)
                    found_fs = True
                    break
                except Exception as e:
                    print(f"⚠️ Unable to open filesystem: {e}")
    if not found_fs:
        extract_image_metadata(img, OUTPUT_JSON)
