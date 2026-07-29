import asyncio
import sys
import os

sys.path.insert(0, r"d:\projects\airport-marketplace\Services\HyperLocal_Services\Supplier_Service")

from infras.primary_db.main import AsyncSupplierLocalSession, init_pg_db
from infras.primary_db.services.supplier_service import SupplierService
from schemas.v1.supplier_schemas.request_schemas import CreateSupplierSchema
from schemas.v1.supplier_schemas.custom_types import SupplierContactInfosType, SupplierLocationInfosType
from sqlalchemy import select
from infras.primary_db.models.supplier_model import Suppliers
from icecream import ic

async def run_test():
    print("=======================================================")
    print("TESTING SUPPLIER CREATION IN POSTGRES PRIMARY DB")
    print("=======================================================")

    await init_pg_db()

    async with AsyncSupplierLocalSession() as session:
        service = SupplierService(session=session)

        # Create supplier schema
        create_payload = CreateSupplierSchema(
            shop_id="050bb7e7-84af-58a4-84e9-dd95572be5d9",
            name="TEST SUPPLIER XYZ",
            contact_infos=SupplierContactInfosType(
                email="testnew123@example.com",
                mobile_number="9998887771"
            ),
            location_infos=SupplierLocationInfosType(
                full_address="123 Test St"
            )
        )

        res = await service.create(data=create_payload)
        ic("Service create result =>", res)

    # Check if supplier exists in DB
    async with AsyncSupplierLocalSession() as session:
        stmt = select(Suppliers).where(Suppliers.contact_infos['email'].astext == "testnew123@example.com")
        sup = (await session.execute(stmt)).scalars().first()
        ic("Db query result after session close =>", sup)
        if sup:
            print("FOUND SUPPLIER IN DB:", sup.id, sup.name, sup.ui_id)
        else:
            print("ERROR: SUPPLIER NOT FOUND IN DB!")

if __name__ == "__main__":
    asyncio.run(run_test())
