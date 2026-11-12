import json
import logging
from pathlib import Path
from src.pipeline import extract_invoice
from src.extractor import UnsupportedFileError, FileTooLargeError, safe_open_pdf
from src.masking import mask_id, mask_invoice_for_viewer

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def test_non_pdf_rejected(tmp_path):
    bad = tmp_path / "x.pdf"
    bad.write_bytes(b"not a pdf")
    try:
        safe_open_pdf(bad)
        assert False, "should have raised"
    except UnsupportedFileError as e:
        assert e.code == "not_a_pdf_magic"


def test_wrong_extension_rejected(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("hi")
    try:
        safe_open_pdf(f)
        assert False
    except UnsupportedFileError as e:
        assert e.code == "unsupported_extension"


def test_oversized_file_rejected(tmp_path, monkeypatch):
    import src.extractor as ex
    monkeypatch.setattr(ex, "MAX_BYTES", 10)
    f = tmp_path / "big.pdf"
    f.write_bytes(b"%PDF-1.4" + b"x" * 100)
    try:
        safe_open_pdf(f)
        assert False
    except FileTooLargeError:
        pass


def test_no_pii_in_logs(caplog):
    caplog.set_level(logging.INFO)
    extract_invoice(SAMPLES / "invoice.pdf")
    joined = " ".join(r.message for r in caplog.records)
    assert "27AABCT1234F1Z5" not in joined     # raw seller tax id
    assert "901-95-4704" not in joined         # raw client tax id
    assert "27AA" in joined or "*" in joined    # masked form is fine


def test_viewer_role_masks_pii():
    raw = {
        "seller": {"name": "TechVision Distributors Pvt Ltd", "tax_id": "27AABCT1234F1Z5"},
        "client": {"name": "Raj Electronics Pvt Ltd", "tax_id": "901-95-4704"},
    }
    masked = mask_invoice_for_viewer(raw)
    assert masked["seller"]["tax_id"] != raw["seller"]["tax_id"]
    assert masked["client"]["tax_id"] != raw["client"]["tax_id"]
    assert "*" in masked["seller"]["tax_id"]


def test_mask_id_shape():
    assert mask_id("27AABCT1234F1Z5") == "27AA*******F1Z5"