"""
CSV Service Import Utility

Imports services from CSV file with columns:
- category
- service_name
- variant
- display_name
- price
- notes

Usage:
    from app.csv_service_importer import import_services_from_csv
    import_services_from_csv('path/to/services.csv')
"""

from __future__ import annotations

import csv
import os
import shutil
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .constants import BACKUP_DIR, MAX_IMPORT_ERRORS
from .infrastructure.logging import logger
from .repositories.service_repository import ServiceRepository


def import_services_from_csv(
    csv_file_path: str,
    service_repo: ServiceRepository,
    clear_existing: bool = False,
    deactivate_existing: bool = False,
) -> dict:
    """Import services from CSV file."""
    results = {
        "success": False,
        "imported": 0,
        "skipped": 0,
        "updated": 0,
        "errors": [],
        "cleared": 0,
        "deactivated": 0,
    }

    # Validate file exists
    if not Path(csv_file_path).exists():
        results["errors"].append(f"File not found: {csv_file_path}")
        return results

    try:
        if clear_existing:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = str(BACKUP_DIR / f"backup_services_{timestamp}.csv")
            try:
                export_services_to_csv(backup_file, service_repo, active_only=False)
                logger.warning("Backup created before clearing services: %s", backup_file)
            except Exception as exc:
                results["errors"].append("Backup failed prior to clearing existing services")
                logger.error("Backup failed: %s", exc, exc_info=True)
                return results

            results["cleared"] = service_repo.delete_all()
            logger.warning("DELETED %s existing services - backup at %s", results["cleared"], backup_file)

        if deactivate_existing and not clear_existing:
            results["deactivated"] = service_repo.deactivate_all()
            logger.info("Deactivated %s existing services.", results["deactivated"])

        with open(csv_file_path, "r", encoding="utf-8") as file_handle:
            reader = csv.DictReader(file_handle)

            required_cols = {"category", "service_name", "display_name", "price"}
            if not required_cols.issubset(reader.fieldnames or []):
                missing = required_cols - set(reader.fieldnames or [])
                results["errors"].append(f"Missing required columns: {missing}")
                return results

            for row_num, row in enumerate(reader, start=2):
                try:
                    display_name = (row.get("display_name") or "").strip()
                    service_name = (row.get("service_name") or "").strip()
                    category = (row.get("category") or "").strip() or None
                    variant = (row.get("variant") or "").strip() or None
                    notes = (row.get("notes") or "").strip() or None

                    if not display_name or not service_name:
                        results["errors"].append(
                            f"Row {row_num}: Missing service_name/display_name"
                        )
                        results["skipped"] += 1
                        continue

                    try:
                        price = Decimal(row["price"]) if row["price"] else None
                        if price is not None and price < 0:
                            raise InvalidOperation("negative price")
                    except (InvalidOperation, ValueError):
                        results["errors"].append(
                            f"Row {row_num}: Invalid price '{row['price']}'"
                        )
                        results["skipped"] += 1
                        continue

                    updated = service_repo.upsert_from_import(
                        display_name=display_name,
                        name=service_name,
                        category=category,
                        variant=variant,
                        price=price,
                        notes=notes,
                        active=True,
                    )
                    if updated:
                        results["updated"] += 1
                    else:
                        results["imported"] += 1
                except Exception as exc:
                    results["errors"].append(f"Row {row_num}: {str(exc)}")
                    results["skipped"] += 1
                    logger.error("Error importing row %s: %s", row_num, exc)
                    if len(results["errors"]) > MAX_IMPORT_ERRORS:
                        results["errors"].insert(0, "Import aborted: too many errors")
                        return results

        results["success"] = len(results["errors"]) == 0
        logger.info(
            "CSV import completed: %s imported, %s updated, %s skipped, %s errors",
            results["imported"],
            results["updated"],
            results["skipped"],
            len(results["errors"]),
        )
    except Exception as exc:
        results["errors"].append(f"Fatal error: {str(exc)}")
        logger.error("CSV import failed: %s", exc, exc_info=True)

    return results


def export_services_to_csv(
    csv_file_path: str,
    service_repo: ServiceRepository,
    active_only: bool = False,
) -> bool:
    """Export all services to CSV file."""
    try:
        output_path = Path(csv_file_path)
        if output_path.exists():
            logger.warning("Overwriting existing file: %s", csv_file_path)
        if not output_path.parent.exists():
            output_path.parent.mkdir(parents=True, exist_ok=True)
        if not os.access(output_path.parent, os.W_OK):
            raise PermissionError(f"Cannot write to directory: {output_path.parent}")

        services = service_repo.list_for_export(active_only=active_only)
        service_count = len(services)

        temp_file = str(output_path) + ".tmp"
        try:
            with open(temp_file, "w", newline="", encoding="utf-8") as file_handle:
                writer = csv.writer(file_handle)
                writer.writerow(
                    ["category", "service_name", "variant", "display_name", "price", "notes"]
                )
                for service in services:
                    writer.writerow(
                        [
                            service.category or "",
                            service.name,
                            service.variant or "",
                            service.display_name or service.name,
                            str(service.price) if service.price else "",
                            service.notes or "",
                        ]
                    )
            shutil.move(temp_file, output_path)
            logger.info("Exported %s services to %s", service_count, csv_file_path)
            return True
        finally:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass

    except Exception as exc:
        logger.error("Export failed: %s", exc, exc_info=True)
        return False
