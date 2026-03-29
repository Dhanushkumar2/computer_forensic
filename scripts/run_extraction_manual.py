#!/usr/bin/env python3
"""
Manual extraction runner for Windows (Jean) and Android TAR samples.
"""

import os
import sys

# Ensure project root is on sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.forensic_api.disk_processor import DiskImageProcessor


def main():
    processor = DiskImageProcessor()
    try:
        res_win = processor.process_disk_image(
            case_id='CASE_JEAN_WINDOWS',
            disk_image_path='/home/dhanush/myvenv/forensic_ir_app/data/samples/nps-2008-jean.E01',
            output_format='mongodb'
        )
        print('Windows result:', res_win)

        res_android = processor.process_disk_image(
            case_id='CASE_ANDROID_TAR',
            disk_image_path='/home/dhanush/myvenv/forensic_ir_app/data/samples/adb-data.tar',
            output_format='mongodb'
        )
        print('Android result:', res_android)
    finally:
        processor.close()


if __name__ == "__main__":
    main()
