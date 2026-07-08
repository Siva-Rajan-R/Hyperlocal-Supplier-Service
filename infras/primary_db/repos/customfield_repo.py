from sqlalchemy import select, update, delete,or_,and_,bindparam
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from icecream import ic
from sqlalchemy.dialects.postgresql import insert
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from ..models.customfield_model import SupplierCustomFields,SupplierCustomFieldsValues
from schemas.v1.db_schemas.customfield_schema import CreateCustomFieldDbSchema, CreateCustomFieldValueDbSchema,UpdateCustomFieldDbSchema,DeleteCustomFieldDbSchema
from schemas.v1.request_schemas.customfield_schema import GetFieldById,GetFieldByShopIdSchema,GetFieldByName,GetValueByIdName,GetvaluesByCustomerId

class CustomFieldsRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    # --- Custom Fields (Definitions) ---
    
    @start_db_transaction
    async def create_all_field(self, data: List[CreateCustomFieldDbSchema]) -> bool:
        field_toadd=[SupplierCustomFields(**field.model_dump()) for field in data]
        self.session.add_all(field_toadd)
        return True
    

    @start_db_transaction
    async def update_field(self, data:UpdateCustomFieldDbSchema) -> Optional[str]:
        stmt = (
            update(SupplierCustomFields)
            .where(SupplierCustomFields.id == data.id, SupplierCustomFields.shop_id == data.shop_id)
            .values(**data.model_dump(exclude=['field_id','shop_id'],exclude_none=True,exclude_unset=True))
            .returning(SupplierCustomFields.id)
        )
        res = (await self.session.execute(stmt)).scalar_one_or_none()
        return res

    @start_db_transaction
    async def delete_field(self,data:DeleteCustomFieldDbSchema) -> bool:
        stmt = delete(SupplierCustomFields).where(
            SupplierCustomFields.id == data.id,
            SupplierCustomFields.shop_id == data.shop_id
        )
        res = await self.session.execute(stmt)
        return res.rowcount > 0


    async def get_field_by_id(self,data:GetFieldById) -> Optional[dict]:
        stmt = select(SupplierCustomFields).where(
            SupplierCustomFields.id == data.id, 
            SupplierCustomFields.shop_id == data.shop_id
        )
        res = (await self.session.execute(stmt)).scalars().first()
        if res:
            return {c.name: getattr(res, c.name) for c in res.__table__.columns}
        return None
    

    async def get_bulk_fields(self,shop_id: str,ids: List[str]=[],names:List[str]=[]) -> Optional[dict]:
        if not ids and not names:
            return []
        
        stmt = select(SupplierCustomFields).where(
            or_(SupplierCustomFields.id.in_(ids),SupplierCustomFields.field_name.in_(names)), 
            SupplierCustomFields.shop_id == shop_id
        )
        res = (await self.session.execute(stmt)).mappings().all()
        if res:
            return [{c.name: getattr(row, c.name) for c in row.__table__.columns} for row in res]
        return []
    

    async def get_field_by_name(self, data:GetFieldByName) -> Optional[dict]:
        stmt = select(SupplierCustomFields).where(
            SupplierCustomFields.field_name == data.name, 
            SupplierCustomFields.shop_id == data.shop_id
        )
        res = (await self.session.execute(stmt)).scalars().first()
        if res:
            return {c.name: getattr(res, c.name) for c in res.__table__.columns}
        return None

    async def get_fields_by_shop_id(self, data:GetFieldByShopIdSchema) -> List[dict]:
        stmt = select(SupplierCustomFields).where(SupplierCustomFields.shop_id == data.shop_id)
        res = (await self.session.execute(stmt)).scalars().all()
        return [{c.name: getattr(row, c.name) for c in row.__table__.columns} for row in res]
    

    async def get_fields(self) -> List[dict]:
        stmt = select(SupplierCustomFields)
        res = (await self.session.execute(stmt)).scalars().all()
        return [{c.name: getattr(row, c.name) for c in row.__table__.columns} for row in res]


    @start_db_transaction
    async def upsert_field_value(self, data: List[CreateCustomFieldValueDbSchema]) -> bool:
        if not data:
            return True

        # 1. Convert the pydantic schemas to a list of raw dictionaries
        insert_mappings = [d.model_dump() for d in data]

        # 2. Build the native PostgreSQL INSERT statement
        stmt = insert(SupplierCustomFieldsValues)
        
        # 3. Construct the UPSERT (ON CONFLICT) logic
        # Resolves on the unique combination of customer and field
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["supplier_id", "field_id"],  
            set_={
                "value": stmt.excluded.value,   # Update the actual text/data value
                "shop_id": stmt.excluded.shop_id  # Keeps the shop relation intact/valid
            }
        )

        # 4. Execute the batch operation efficiently in one database round-trip
        conn = await self.session.connection()
        res = await conn.execute(upsert_stmt, insert_mappings)
        
        ic("Total rows handled (Inserted + Updated) => ", res.rowcount)
        return True

        
    async def get_values_by_supplier_id(self, data:GetvaluesByCustomerId) -> List[dict]:
        stmt = select(SupplierCustomFieldsValues).where(
            SupplierCustomFieldsValues.supplier_id == data.id,
            SupplierCustomFieldsValues.shop_id == data.shop_id
        )
        res = (await self.session.execute(stmt)).scalars().all()
        return [{c.name: getattr(row, c.name) for c in row.__table__.columns} for row in res]

    async def get_values(self):
        stmt = select(SupplierCustomFieldsValues)
        res = (await self.session.execute(stmt)).scalars().all()
        return [{c.name: getattr(row, c.name) for c in row.__table__.columns} for row in res]
    
    async def get_values_by_id(self,id:str,shop_id:str):
        stmt = select(SupplierCustomFieldsValues).where(
            SupplierCustomFieldsValues.id == id,
            SupplierCustomFieldsValues.shop_id == shop_id
        )
        res = (await self.session.execute(stmt)).mappings().all()
        return [{c.name: getattr(row, c.name) for c in row.__table__.columns} for row in res]

