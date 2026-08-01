import asyncio
from infras.primary_db.main import AsyncSupplierLocalSession, init_pg_db
from infras.primary_db.services.supplier_service import SupplierService
from schemas.v1.supplier_schemas.request_schemas import UpdateOutstandingSupplierSchema, SupplierOutstandingInfosType, GetSupplierById
from core.data_formats.enums.supplier_enums import SupplierOutstandingUpdateTypeEnums
from icecream import ic

async def test_update_outstanding():
    await init_pg_db()
    
    async with AsyncSupplierLocalSession() as session:
        service = SupplierService(session=session)
        
        supplier_id = "4d9b3394-0e6c-501e-861e-898a74f6886c"
        shop_id = "3f74a412-68d8-5e16-864e-e2f0bc488150"
        
        data = UpdateOutstandingSupplierSchema(
            id=supplier_id,
            shop_id=shop_id,
            outstanding_infos=SupplierOutstandingInfosType(amount=1000.0),
            type=SupplierOutstandingUpdateTypeEnums.INCREMENT,
            entity_name="purchase",
            entity_id="test-purchase-123",
            payment_method="CASH",
            notes="Test payment increment"
        )
        
        res = await service.update_outstanding(data=data)
        ic("Update outstanding result =>", res)
        
        # Fetch updated record from Postgres
        updated_sup = await service.supplier_repo_obj.getby_id(GetSupplierById(id=supplier_id, shop_id=shop_id))
        ic("Updated Supplier Record =>", updated_sup)

if __name__ == "__main__":
    asyncio.run(test_update_outstanding())
