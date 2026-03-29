#!/usr/bin/env python3
"""
Check MongoDB connectivity and auto-load a summary of stored data.
"""

import os
import sys
from datetime import datetime

# Add project root to path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from database.mongodb_retrieval import ForensicMongoRetrieval


def main():
    print("🔎 Checking MongoDB connectivity...")
    retrieval = ForensicMongoRetrieval()

    try:
        # Ping server
        retrieval.client.admin.command("ping")
        print("✅ MongoDB ping OK")

        # List collections
        collections = retrieval.db.list_collection_names()
        print(f"📚 Collections: {len(collections)}")
        for name in sorted(collections):
            print(f"  - {name}")

        # Load cases
        cases = retrieval.get_all_cases()
        print(f"\n🧩 Cases found: {len(cases)}")
        for c in cases[:5]:
            print(f"  - {c.get('case_id')} | {c.get('image_path')} | {c.get('extraction_time')}")

        # Auto-load latest case summary if available
        if cases:
            latest = max(
                cases,
                key=lambda c: c.get("extraction_time") or ""
            )
            case_id = latest.get("case_id")
            print(f"\n📈 Loading summary for latest case: {case_id}")
            summary = retrieval.get_case_summary(case_id)
            counts = summary.get("counts", {}) if summary else {}
            total = sum(v for v in counts.values() if isinstance(v, int))
            print(f"  Total artifacts: {total}")
            print("  Counts:")
            for k, v in counts.items():
                print(f"    {k}: {v}")
        else:
            print("\n⚠️  No cases found in MongoDB.")

        print("\n✅ MongoDB connectivity check complete.")

    except Exception as e:
        print(f"❌ MongoDB check failed: {e}")
    finally:
        retrieval.close()


if __name__ == "__main__":
    main()
