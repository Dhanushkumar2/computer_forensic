import pyewf
import pytsk3
import json
import os

class EWFImgInfo(pytsk3.Img_Info):
    def __init__(self, ewf_handle):
        self._ewf_handle = ewf_handle
        super().__init__(url="", type=pytsk3.TSK_IMG_TYPE_EXTERNAL)

    def close(self):
        self._ewf_handle.close()

    def read(self, offset, size):
        self._ewf_handle.seek(offset)
        return self._ewf_handle.read(size)

    def get_size(self):
        return self._ewf_handle.get_media_size()

def open_ewf_image(image_path):
    """Open a multi-segment EWF image safely."""
    segment_files = pyewf.glob(image_path)
    if not segment_files:
        raise FileNotFoundError(f"No EWF segments found for {image_path}")

    ewf_handle = pyewf.handle()
    ewf_handle.open(segment_files)
    print(f"Found {len(segment_files)} segment(s): {segment_files}")
    return EWFImgInfo(ewf_handle)

def extract_metadata(image_path, output_json="metadata.json"):
    print(f"Opening image: {image_path}")
    img = open_ewf_image(image_path)

    try:
        fs = pytsk3.FS_Info(img)
    except Exception as e:
        print(f"Unable to open filesystem: {e}")
        print("🔍 Trying to read metadata only (no FS parsing)...")
        metadata = {
            "image_path": image_path,
            "image_size": img.get_size(),
            "note": "Filesystem parsing failed, raw metadata extracted."
        }
    else:
        root_dir = fs.open_dir("/")
        file_list = []
        for f in root_dir:
            try:
                name = f.info.name.name.decode("utf-8")
                if name not in [".", ".."]:
                    file_list.append(name)
            except Exception:
                continue

        metadata = {
            "image_path": image_path,
            "image_size": img.get_size(),
            "root_files": file_list[:10]
        }

    with open(output_json, "w") as f:
        json.dump(metadata, f, indent=4)
    print(f"Metadata extracted to {output_json}")
    
def extract_partial_data(image_path, output_file="sample_raw.bin", bytes_to_read=100 * 1024 * 1024):
    """
    Extract a small portion of the EnCase image (default: 100MB).
    """
    print(f"Extracting {bytes_to_read / (1024*1024)} MB from {image_path} ...")

    ewf_handle = pyewf.handle()
    segment_files = pyewf.glob(image_path)
    ewf_handle.open(segment_files)
    img = EWFImgInfo(ewf_handle)

    total_size = img.get_size()
    read_size = min(bytes_to_read, total_size)

    with open(output_file, "wb") as f:
        offset = 0
        chunk_size = 1024 * 1024  # 1MB
        while offset < read_size:
            data = img.read(offset, chunk_size)
            f.write(data)
            offset += len(data)
            if offset % (10 * chunk_size) == 0:
                print(f"   ... {offset / (1024*1024):.1f} MB written")

    print(f"Extracted {read_size / (1024*1024):.2f} MB to {output_file}")


if __name__ == "__main__":
    extract_metadata("forensic_ir_app/data/samples/nps-2008-jean.E01", "sample_metadata.json")
    extract_partial_data("forensic_ir_app/data/samples/nps-2008-jean.E01", "sample_raw.bin", bytes_to_read=50 * 1024 * 1024)
