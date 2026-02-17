"""
Test script for CSV service import functionality.

This script:
1. Runs the database migration
2. Imports services from the CSV file
3. Verifies the import was successful
"""

import sys
from pathlib import Path

import pytest
from sqlalchemy import func

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.migrate_service_schema import migrate_service_table
from app.csv_service_importer import import_services_from_csv
from app.infrastructure.database import db_session, init_db
from app.models import Service
from app.repositories.service_repository import ServiceRepository


def test_import():
    """Test the CSV import process."""
    print("=" * 60)
    print("Step 1: Running database migration...")
    print("=" * 60)

    try:
        init_db()
        migrate_service_table()
        print("? Migration completed successfully!\n")
    except Exception as e:
        print(f"? Migration failed: {e}\n")
        pytest.fail(f"Migration failed: {e}")

    print("=" * 60)
    print("Step 2: Importing services from CSV...")
    print("=" * 60)

    # Locate the CSV file - try multiple common locations
    possible_paths = [
        Path(__file__).parent.parent / "services_full_seed.csv",
        Path("services_full_seed.csv"),
        Path.home() / "Downloads" / "services_full_seed.csv",
        Path(__file__).parent / "services_full_seed.csv",
    ]

    csv_path = None
    for path in possible_paths:
        if path.exists():
            csv_path = path
            break

    if not csv_path:
        print(f"? CSV file not found in any of these locations:")
        for path in possible_paths:
            print(f"  - {path}")
        print("\nPlease copy services_full_seed.csv to one of the above locations.")
        pytest.skip("CSV seed file not available for import test.")

    print(f"Using CSV file: {csv_path}\n")

    try:
        service_repo = ServiceRepository(db_session)
        results = import_services_from_csv(
            str(csv_path),
            service_repo=service_repo,
            deactivate_existing=False,
        )

        print("\nImport Results:")
        print("-" * 60)
        print(f"? Success: {results['success']}")
        print(f"? Imported: {results['imported']} new services")
        print(f"? Updated: {results['updated']} existing services")
        print(f"? Skipped: {results['skipped']} rows with errors")
        print(f"? Deactivated: {results['deactivated']} old services")

        if results['errors']:
            print(f"\n? Errors ({len(results['errors'])}):")
            for error in results['errors'][:10]:
                print(f"  - {error}")
            if len(results['errors']) > 10:
                print(f"  ... and {len(results['errors']) - 10} more errors")

        print()

    except Exception as e:
        print(f"? Import failed: {e}\n")
        import traceback

        traceback.print_exc()
        pytest.fail(f"Import failed: {e}")

    print("=" * 60)
    print("Step 3: Verifying imported data...")
    print("=" * 60)

    try:
        with db_session() as db:
            # Count total services
            total = db.query(Service).count()
            active = db.query(Service).filter(Service.active == True).count()

            print(f"Total services in database: {total}")
            print(f"Active services: {active}")

            # Count by category
            categories = db.query(Service.category, func.count(Service.id)).group_by(
                Service.category
            ).all()

            print("\nServices by category:")
            print("-" * 60)
            for category, count in sorted(categories, key=lambda x: x[1], reverse=True):
                category_name = category or "(No category)"
                print(f"  {category_name}: {count}")

            # Show sample services
            print("\nSample services:")
            print("-" * 60)
            samples = db.query(Service).filter(Service.active == True).limit(10).all()
            for s in samples:
                variant = f" ({s.variant})" if s.variant else ""
                price = f"?{s.price}" if s.price else "No price"
                print(f"  [{s.category}] {s.name}{variant} - {price}")

        print("\n? Verification completed successfully!")

    except Exception as e:
        print(f"? Verification failed: {e}")
        import traceback

        traceback.print_exc()
        pytest.fail(f"Verification failed: {e}")

    assert results["success"]
