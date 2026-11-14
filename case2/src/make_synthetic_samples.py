from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

SAMPLES = Path(__file__).resolve().parents[1] / "samples"
SAMPLES.mkdir(exist_ok=True)


def _draw_invoice(path: Path, include_total: bool = True, image_only: bool = False):
    c = canvas.Canvas(str(path), pagesize=A4)
    if image_only:
        c.rect(100, 400, 300, 200, fill=1)
        c.showPage(); c.save(); return
    y = 800
    lines = [
        "Invoice no: INV-2024-0001",
        "Date of issue: 15/02/2024",
        "Seller:",
        "Acme Distribution Pvt Ltd",
        "1 Demo Street, Mumbai 400001",
        "Tax Id: 27AAACR1234F1Z9",
        "GSTIN: 27AAACR1234F1Z9",
        "Client:",
        "Beta Retail Pvt Ltd",
        "9 Sample Road, Bengaluru 560001",
        "Tax Id: 111-22-3333",
    ]
    for ln in lines:
        c.drawString(60, y, ln); y -= 16
    y -= 8
    c.drawString(60, y, "1. Widget A 4.00 pcs 1,000.00 4,000.00 10% 4,400.00"); y -= 16
    c.drawString(60, y, "2. Widget B 2.00 pcs 2,500.00 5,000.00 10% 5,500.00"); y -= 24
    if include_total:
        c.drawString(60, y, "Total | INR 9,000.00 | INR 900.00 | INR 9,900.00"); y -= 16
    c.showPage(); c.save()


if __name__ == "__main__":
    _draw_invoice(SAMPLES / "invoice_clean.pdf", include_total=True)
    _draw_invoice(SAMPLES / "invoice_missing_total.pdf", include_total=False)
    _draw_invoice(SAMPLES / "invoice_no_text.pdf", image_only=True)
    (SAMPLES / "bad_upload.txt").write_text("not a pdf")
    print("synthetic samples written to", SAMPLES)