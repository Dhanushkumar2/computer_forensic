import binascii
import os

# File to read
RAW_FILE = "sample_raw.bin"

# Known file signatures (magic numbers)
SIGNATURES = {
    b"\xFF\xD8\xFF": "JPEG image",
    b"\x89PNG": "PNG image",
    b"%PDF": "PDF document",
    b"PK\x03\x04": "ZIP / DOCX / JAR",
    b"GIF89a": "GIF image",
    b"BM": "Bitmap image",
    b"\x7FELF": "Linux Executable",
}

def detect_file_signature(data):
    for sig, desc in SIGNATURES.items():
        if data.startswith(sig):
            return desc
    return "Unknown"

def hex_preview(file_path, num_bytes=1024):
    """Prints a human-readable hex + ASCII preview"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, "rb") as f:
        data = f.read(num_bytes)

    print(f"\nPreviewing first {num_bytes} bytes of {file_path}\n")
    print(f"🔍 Detected file type: {detect_file_signature(data)}\n")

    # Print hex + ascii view
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        print(f"{i:08X}  {hex_part:<48}  {ascii_part}")

if __name__ == "__main__":
    hex_preview(RAW_FILE, num_bytes=512)  # view first 512 bytes
