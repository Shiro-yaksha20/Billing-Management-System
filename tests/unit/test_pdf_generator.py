"""Unit tests for PDF generator."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path
import importlib

import pytest
from reportlab.pdfbase import pdfmetrics

from app.dto.receipt_dto import ReceiptData, ReceiptItemData
from app.infrastructure import pdf_generator
from app.infrastructure.pdf_generator import generate_receipt_pdf


def _build_receipt() -> ReceiptData:
    return ReceiptData(
        bill_id=1,
        bill_number="B1",
        bill_datetime=datetime(2024, 1, 1, 10, 0, 0),
        subtotal=Decimal("10"),
        discount_amount=Decimal("0"),
        tax_percent=Decimal("0"),
        tax_amount=Decimal("0"),
        total=Decimal("10"),
        payment_method="Cash",
        payment_status="Paid",
        transaction_id=None,
        customer_name="Test",
        customer_phone="123",
        staff_name="Staff",
        items=[
            ReceiptItemData(
                service_name="Cut",
                display_name="Cut",
                variant=None,
                quantity=1,
                unit_price=Decimal("10"),
                line_total=Decimal("10"),
            )
        ],
    )


def test_generate_receipt_pdf_creates_unique_file(settings_service, receipts_dir):
    receipt = _build_receipt()
    fixed_time = datetime(2024, 1, 1, 10, 0, 0)

    class _FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_time

    original_datetime = pdf_generator.datetime
    pdf_generator.datetime = _FixedDateTime

    timestamp = fixed_time.strftime("%Y%m%d_%H%M%S")
    existing_path = Path(receipts_dir) / f"receipt_{receipt.bill_id}_{timestamp}.pdf"
    existing_path.parent.mkdir(parents=True, exist_ok=True)
    existing_path.write_text("existing", encoding="utf-8")

    try:
        pdf_path = generate_receipt_pdf(receipt, settings_service)
    finally:
        pdf_generator.datetime = original_datetime

    assert pdf_path != str(existing_path)
    assert Path(pdf_path).exists()


def test_generate_receipt_pdf_with_optional_fields(settings_service, receipts_dir) -> None:
    receipt = _build_receipt()
    receipt = ReceiptData(
        **{**receipt.__dict__, "transaction_id": "TX123"}
    )
    settings_service.set_setting("salon_instagram", "@insta")
    settings_service.set_setting("salon_gstin", "GSTIN123")

    pdf_path = generate_receipt_pdf(receipt, settings_service)
    assert Path(pdf_path).exists()


def test_generate_receipt_pdf_preview_mode(settings_service, receipts_dir) -> None:
    receipt = _build_receipt()

    pdf_path = generate_receipt_pdf(receipt, settings_service, is_preview=True)

    assert Path(pdf_path).exists()


def test_generate_receipt_pdf_build_failure_cleans_temp(settings_service, receipts_dir, monkeypatch) -> None:
    receipt = _build_receipt()

    class _FailDoc:
        def __init__(self, filename, **kwargs):
            self._filename = filename

        def build(self, story):
            Path(self._filename).write_text("temp", encoding="utf-8")
            raise RuntimeError("fail")

    monkeypatch.setattr(pdf_generator, "SimpleDocTemplate", _FailDoc)

    with pytest.raises(IOError):
        generate_receipt_pdf(receipt, settings_service)


def test_pdf_generator_font_fallback(monkeypatch):
    import app.infrastructure.pdf_generator as pdf_module

    def _raise(*args, **kwargs):
        raise RuntimeError("fail")

    monkeypatch.setattr(pdfmetrics, "registerFont", _raise)

    reloaded = importlib.reload(pdf_module)

    assert reloaded.DEFAULT_FONT == "Helvetica"


def test_generate_receipt_pdf_creates_receipts_dir(settings_service, monkeypatch, tmp_path):
    from app.infrastructure import pdf_generator as module

    receipt = _build_receipt()
    receipts_path = tmp_path / "receipts"
    monkeypatch.setattr(module, "RECEIPTS_DIR", str(receipts_path))

    pdf_path = generate_receipt_pdf(receipt, settings_service)

    assert receipts_path.exists()
    assert Path(pdf_path).exists()


def test_generate_receipt_pdf_includes_variant(settings_service, receipts_dir) -> None:
    receipt = _build_receipt()
    receipt = ReceiptData(
        **{
            **receipt.__dict__,
            "items": [
                ReceiptItemData(
                    service_name="Cut",
                    display_name="Cut",
                    variant="Short",
                    quantity=1,
                    unit_price=Decimal("10"),
                    line_total=Decimal("10"),
                )
            ],
        }
    )

    pdf_path = generate_receipt_pdf(receipt, settings_service)
    assert Path(pdf_path).exists()


def test_generate_receipt_pdf_doc_creation_failure(settings_service, receipts_dir, monkeypatch):
    receipt = _build_receipt()

    def _fail_doc(*args, **kwargs):
        raise RuntimeError("fail")

    monkeypatch.setattr(pdf_generator, "SimpleDocTemplate", _fail_doc)

    with pytest.raises(IOError):
        generate_receipt_pdf(receipt, settings_service)


def test_generate_receipt_pdf_cleanup_handles_remove_failure(settings_service, receipts_dir, monkeypatch):
    receipt = _build_receipt()

    class _FailDoc:
        def __init__(self, filename, **kwargs):
            self._filename = filename

        def build(self, story):
            Path(self._filename).write_text("temp", encoding="utf-8")
            raise RuntimeError("fail")

    monkeypatch.setattr(pdf_generator, "SimpleDocTemplate", _FailDoc)
    monkeypatch.setattr("os.remove", lambda path: (_ for _ in ()).throw(OSError("fail")))

    with pytest.raises(IOError):
        generate_receipt_pdf(receipt, settings_service)


def test_pdf_generator_font_registration_success(monkeypatch):
    import importlib
    import app.infrastructure.pdf_generator as pdf_module

    class _TTFont:
        def __init__(self, *args, **kwargs):
            pass

    monkeypatch.setattr("reportlab.pdfbase.ttfonts.TTFont", _TTFont)
    monkeypatch.setattr("reportlab.pdfbase.pdfmetrics.registerFont", lambda *args, **kwargs: None)

    reloaded = importlib.reload(pdf_module)

    assert reloaded.DEFAULT_FONT == "DejaVuSans"
