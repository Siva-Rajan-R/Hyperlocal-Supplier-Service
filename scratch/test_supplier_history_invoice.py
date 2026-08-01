import asyncio
import sys
import os
import uuid
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infras.primary_db.main import AsyncSupplierLocalSession, init_pg_db, ENGINE
from infras.primary_db.services.supplier_service import SupplierService
from infras.primary_db.models.supplier_model import Suppliers
from schemas.v1.supplier_schemas.request_schemas import UpdateOutstandingSupplierSchema, SupplierOutstandingInfosType
from core.data_formats.enums.supplier_enums import SupplierOutstandingUpdateTypeEnums
from sqlalchemy import text
from icecream import ic

async def test_supplier_history_invoice():
    await init_pg_db()
    
    # Add invoice_no column if not existing
    async with ENGINE.begin() as conn:
        await conn.execute(text("ALTER TABLE supplier_outstanding_history ADD COLUMN IF NOT EXISTS invoice_no VARCHAR;"))
    
    async with AsyncSupplierLocalSession() as session:
        service = SupplierService(session=session)
        shop_id = "test-shop-sup-inv"
        supplier_id = str(uuid.uuid4())
        
        # Seed supplier
        sup = Suppliers(
            id=supplier_id,
            shop_id=shop_id,
            ui_id="SUP-999",
            name="Test Invoice Supplier",
            outstanding_infos={"amount": 10000.0}
        )
        session.add(sup)
        await session.commit()
        ic("Seeded supplier =>", supplier_id)
        
        # Update outstanding with invoice_no
        data = UpdateOutstandingSupplierSchema(
            id=supplier_id,
            shop_id=shop_id,
            outstanding_infos=SupplierOutstandingInfosType(amount=500.0),
            type=SupplierOutstandingUpdateTypeEnums.DECREMENT,
            cleared_amount=500.0,
            outstanding_amount=9500.0,
            entity_name="purchase",
            entity_id=str(uuid.uuid4()),
            invoice_no="INVOICE-TEST-999",
            payment_method="CASH",
            notes="cleared outstanding for the purchase"
        )
        
        res = await service.update_outstanding(data=data)
        ic("Update outstanding result =>", res)
        
        # Fetch cleared history
        history = await service.supplier_repo_obj.get_outstanding_history(supplier_id=supplier_id, shop_id=shop_id)
        ic("Supplier Outstanding History =>", history)
        assert len(history) > 0, "History entry should exist!"
        assert history[0]["invoice_no"] == "INVOICE-TEST-999", f"invoice_no should be INVOICE-TEST-999, got {history[0]['invoice_no']}"
        ic("SUCCESS: Supplier cleared history with invoice_no verified cleanly!")

if __name__ == "__main__":
    asyncio.run(test_supplier_history_invoice())
