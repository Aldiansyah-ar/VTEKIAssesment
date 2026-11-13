from __future__ import annotations
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class LineItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    no: int
    description: str
    quantity: Decimal
    unit: str
    unit_price: Decimal
    net_worth: Decimal
    vat_rate: Decimal
    gross_worth: Decimal
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class Party(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Optional[str] = None
    tax_id: Optional[str] = None
    gstin: Optional[str] = None


class Invoice(BaseModel):
    model_config = ConfigDict(extra="forbid")
    invoice_number: Optional[str] = None
    issue_date_raw: Optional[str] = None
    issue_date_iso: Optional[str] = None
    date_format_assumed: Optional[str] = None
    currency: Optional[str] = None
    seller: Party = Field(default_factory=Party)
    client: Party = Field(default_factory=Party)
    line_items: List[LineItem] = Field(default_factory=list)
    subtotal: Optional[Decimal] = None
    tax_total: Optional[Decimal] = None
    grand_total: Optional[Decimal] = None

    extraction_method: str = "regex_offline"
    model_version: str = "invoice-extractor/1.0.0"
    field_confidence: dict = Field(default_factory=dict)
    overall_confidence: float = 0.0
    needs_review: bool = False
    review_reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    def to_jsonable(self) -> dict:
        d = self.model_dump()
        for k in ("subtotal", "tax_total", "grand_total"):
            if d.get(k) is not None:
                d[k] = str(d[k])
        for it in d["line_items"]:
            for k in ("quantity", "unit_price", "net_worth", "vat_rate", "gross_worth"):
                it[k] = str(it[k])
        return d