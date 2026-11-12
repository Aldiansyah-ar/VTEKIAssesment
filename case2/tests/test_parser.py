from src.parser import parse_line_items, parse_header, parse_totals

SAMPLE_TEXT = """
Invoice no: 51109301
Date of issue: 03/07/2023
Seller:
TechVision Distributors Pvt Ltd
Tax Id: 27AABCT1234F1Z5
GSTIN: 27AABCT1234F1Z5
Client:
Raj Electronics Pvt Ltd
Tax Id: 901-95-4704
1. Garmin Fenix 7 Solar Multisport GPS 9.00 pcs 74,120.00 667,080.00 10% 733,788.00
2. Apple Watch Series 9 GPS 45mm Midnight 8.00 pcs 52,083.00 416,664.00 10% 458,330.40
3. Xiaomi 14 Pro 512GB White 8.00 pcs
74,154.00 593,232.00 10% 652,555.20
Total | INR 1,676,976.00 | INR 167,697.60 | INR 1,844,673.60
"""


def test_header_fields():
    h = parse_header(SAMPLE_TEXT)
    assert h["invoice_number"] == "51109301"
    assert h["issue_date_raw"] == "03/07/2023"
    assert h["currency"] == "INR"
    assert h["seller_name"] == "TechVision Distributors Pvt Ltd"
    assert h["client_name"] == "Raj Electronics Pvt Ltd"
    assert h["seller_tax_id"] == "27AABCT1234F1Z5"
    assert h["client_tax_id"] == "901-95-4704"


def test_line_items_with_malformed_row():
    items, review = parse_line_items(SAMPLE_TEXT)
    assert len(items) == 3
    assert review == []
    assert items[2]["description"] == "Xiaomi 14 Pro 512GB White"
    assert str(items[2]["net_worth"]) == "593232.00"
    assert str(items[2]["gross_worth"]) == "652555.20"


def test_totals_text_fallback():
    out = parse_totals(SAMPLE_TEXT, tables=[])
    assert str(out["subtotal"]) == "1676976.00"
    assert str(out["tax_total"]) == "167697.60"
    assert str(out["grand_total"]) == "1844673.60"