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

import csv
import os
import shutil
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .database import db_session
from .models import Service
from .utils import logger
from .constants import MAX_IMPORT_ERRORS


def import_services_from_csv(
    csv_file_path: str,
    clear_existing: bool = False,
    deactivate_existing: bool = False
) -> dict:
    """Import services from CSV file."""
    results = {
        'success': False,
        'imported': 0,
        'skipped': 0,
        'updated': 0,
        'errors': [],
        'cleared': 0,
        'deactivated': 0
    }
    
    # Validate file exists
    if not Path(csv_file_path).exists():
        results['errors'].append(f"File not found: {csv_file_path}")
        return results
    
    try:
        with db_session() as db:
            # Handle clear_existing flag safely
            if clear_existing:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_file = f"backup_services_{timestamp}.csv"
                try:
                    export_services_to_csv(backup_file, active_only=False)
                    logger.warning(f"Backup created before clearing services: {backup_file}")
                except Exception as be:
                    results['errors'].append("Backup failed prior to clearing existing services")
                    logger.error(f"Backup failed: {be}", exc_info=True)
                    return results

                count = db.query(Service).delete()
                db.commit()
                results['cleared'] = count
                logger.warning(f"DELETED {count} existing services - backup at {backup_file}")
            
            if deactivate_existing and not clear_existing:
                count = db.query(Service).update({'active': False})
                results['deactivated'] = count
                logger.info(f"Deactivated {count} existing services.")
            
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                required_cols = {'category', 'service_name', 'display_name', 'price'}
                if not required_cols.issubset(reader.fieldnames or []):
                    missing = required_cols - set(reader.fieldnames or [])
                    results['errors'].append(f"Missing required columns: {missing}")
                    return results
                
                sp = db.begin_nested()
                try:
                    for row_num, row in enumerate(reader, start=2):
                        try:
                            display_name = (row.get('display_name') or '').strip()
                            service_name = (row.get('service_name') or '').strip()
                            category = (row.get('category') or '').strip()
                            variant = (row.get('variant') or '').strip() or None
                            notes = (row.get('notes') or '').strip() or None

                            if not display_name or not service_name:
                                results['errors'].append(
                                    f"Row {row_num}: Missing service_name/display_name"
                                )
                                results['skipped'] += 1
                                continue

                            try:
                                price = Decimal(row['price']) if row['price'] else None
                                if price is not None and price < 0:
                                    raise InvalidOperation("negative price")
                            except (InvalidOperation, ValueError):
                                results['errors'].append(
                                    f"Row {row_num}: Invalid price '{row['price']}'"
                                )
                                results['skipped'] += 1
                                continue
                            
                            existing = db.query(Service).filter(
                                Service.display_name == display_name
                            ).first()
                            
                            if existing:
                                existing.category = category or None
                                existing.name = service_name
                                existing.variant = variant
                                existing.display_name = display_name
                                existing.price = price
                                existing.notes = notes
                                existing.active = True
                                results['updated'] += 1
                            else:
                                service = Service(
                                    category=category or None,
                                    name=service_name,
                                    variant=variant,
                                    display_name=display_name,
                                    price=price,
                                    notes=notes,
                                    active=True
                                )
                                db.add(service)
                                results['imported'] += 1
                        except Exception as e:
                            results['errors'].append(f"Row {row_num}: {str(e)}")
                            results['skipped'] += 1
                            logger.error(f"Error importing row {row_num}: {e}")
                            if len(results['errors']) > MAX_IMPORT_ERRORS:
                                sp.rollback()
                                results['errors'].insert(0, "Import aborted: too many errors")
                                return results
                except Exception as e:
                    sp.rollback()
                    logger.error("Import failed, rolled back to savepoint", exc_info=True)
                    raise
            
        results['success'] = len(results['errors']) == 0
        logger.info(
            f"CSV import completed: {results['imported']} imported, "
            f"{results['updated']} updated, {results['skipped']} skipped, "
            f"{len(results['errors'])} errors"
        )
        
    except Exception as e:
        results['errors'].append(f"Fatal error: {str(e)}")
        logger.error(f"CSV import failed: {e}", exc_info=True)
    
    return results


def export_services_to_csv(csv_file_path: str, active_only: bool = False) -> bool:
    """Export all services to CSV file."""
    try:
        output_path = Path(csv_file_path)
        if output_path.exists():
            logger.warning(f"Overwriting existing file: {csv_file_path}")
        if not output_path.parent.exists():
            output_path.parent.mkdir(parents=True, exist_ok=True)
        if not os.access(output_path.parent, os.W_OK):
            raise PermissionError(f"Cannot write to directory: {output_path.parent}")

        with db_session() as db:
            query = db.query(Service)
            if active_only:
                query = query.filter(Service.active == True)
            
            services = query.order_by(Service.category, Service.name, Service.variant).all()
            
            temp_file = str(output_path) + ".tmp"
            try:
                with open(temp_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'category', 'service_name', 'variant', 'display_name', 'price', 'notes'
                    ])
                    for service in services:
                        writer.writerow([
                            service.category or '',
                            service.name,
                            service.variant or '',
                            service.display_name or service.name,
                            str(service.price) if service.price else '',
                            service.notes or ''
                        ])
                shutil.move(temp_file, output_path)
                logger.info(f"Exported {len(services)} services to {csv_file_path}")
                return True
            finally:
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except Exception:
                        pass
    
    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        return False
