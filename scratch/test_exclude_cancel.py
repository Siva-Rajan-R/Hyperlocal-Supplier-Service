import asyncio
import sys
import os
import uuid
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schemas.v1.supplier_schemas.request_schemas import GetSupplierOutstandingHistorySchema
from infras.primary_db.models.supplier_model import SupplierOutstandingHistory

class MockRecord:
    def __init__(self, id, supplier_id, shop_id, cleared_amount, outstanding_amount, payment_method, entity_name, entity_id, invoice_no, notes):
        self.id = id
        self.supplier_id = supplier_id
        self.shop_id = shop_id
        self.cleared_amount = cleared_amount
        self.outstanding_amount = outstanding_amount
        self.payment_method = payment_method
        self.entity_name = entity_name
        self.entity_id = entity_id
        self.invoice_no = invoice_no
        self.notes = notes

def test_filtering_logic():
    records = [
        MockRecord("1", "s1", "sh1", 141.6, 1777936.6, "N/A", "purchase", "p1", "errgetrg", "canceled purchase errgetrg"),
        MockRecord("2", "s1", "sh1", 0, 141.6, "N/A", "purchase", "p1", "errgetrg", "Purchase errgetrg created"),
        MockRecord("3", "s1", "sh1", 123, 46.9, "CASH", "purchase", "p2", "23", "Initial payment of 123.0 for purchase 23"),
        MockRecord("4", "s1", "sh1", 0, 1774046.2, "N/A", "purchase", "p3", "afa", "Purchase afa created"),
    ]

    canceled_ids = set()
    for r in records:
        notes_lower = (r.notes or "").lower()
        if "canceled purchase" in notes_lower or "cancelled purchase" in notes_lower or "cancel purchase" in notes_lower:
            if r.entity_id:
                canceled_ids.add(str(r.entity_id))
            if getattr(r, "invoice_no", None):
                canceled_ids.add(str(r.invoice_no))

    # Mock HTTP response with both canceled and non-canceled purchases
    p_data = [
        {"id": "p1", "invoice_no": "errgetrg", "status": "CANCELED"},
        {"id": "p2", "invoice_no": "23", "status": "COMPLETED"},
        {"id": "p3", "invoice_no": "afa", "status": "PENDING"}
    ]
    for p in p_data:
        if str(p.get("status", "")).upper() in ["CANCELED", "CANCELLED"]:
            if p.get("id"): canceled_ids.add(str(p["id"]))
            if p.get("purchase_id"): canceled_ids.add(str(p["purchase_id"]))
            if p.get("invoice_no"): canceled_ids.add(str(p["invoice_no"]))

    filtered_records = []
    for r in records:
        if r.entity_id and str(r.entity_id) in canceled_ids:
            continue
        if r.invoice_no and str(r.invoice_no) in canceled_ids:
            continue
        notes_lower = (r.notes or "").lower()
        if "canceled purchase" in notes_lower or "cancelled purchase" in notes_lower or "cancel purchase" in notes_lower:
            continue
        filtered_records.append(r)

    print("Filtered records count:", len(filtered_records))
    assert len(filtered_records) == 2, f"Expected 2 records, got {len(filtered_records)}"
    assert [r.id for r in filtered_records] == ["3", "4"], f"Expected records 3 and 4, got {[r.id for r in filtered_records]}"
    print("Filter test PASSED!")

if __name__ == "__main__":
    test_filtering_logic()
