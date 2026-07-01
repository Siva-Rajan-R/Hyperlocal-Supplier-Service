from models.repo_models.base_repo_model import BaseRepoModel
from ..models.supplier_model import Suppliers,String
from sqlalchemy.dialects.postgresql import insert
from ..main import AsyncSession
from sqlalchemy import select,update,delete,or_,and_,func,case
from datetime import datetime, timezone
from schemas.v1.supplier_schemas.db_schemas import CreateSupplierDbSchema,UpdateSupplierDbSchema,DeleteSupplierDbSchema
from schemas.v1.supplier_schemas.request_schemas import CreateSupplierSchema,UpdateSupplierSchema,DeleteSupplierSchema,GetAllSupplierSchema,GetSupplierById,GetSupplierByShopIdSchema,UpdateOutstandingSupplierSchema
from typing import Optional,List
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from core.decorators.error_handler_dec import catch_errors



class SupplierRepo:
    def __init__(self, session:AsyncSession):
        self.session=session
        self.supplier_cols=(
            Suppliers.id,
            Suppliers.ui_id,
            Suppliers.shop_id,
            Suppliers.sequence_id,
            Suppliers.name,
            Suppliers.location_infos,
            Suppliers.contact_infos,
            Suppliers.contact_person_infos,
            Suppliers.outstanding_infos,
            Suppliers.additional_infos,
            Suppliers.gst_no,
            Suppliers.created_at,
            Suppliers.updated_at
        )


    @start_db_transaction
    async def get_next_sequence(self, shop_id: str, start_from: int) -> int:
        from sqlalchemy import text
        seq_name = f"seq_supplier_{shop_id.replace('-', '_').lower()}"
        await self.session.execute(text(f"CREATE SEQUENCE IF NOT EXISTS {seq_name} START WITH {start_from}"))
        res = await self.session.execute(text(f"SELECT nextval('{seq_name}')"))
        return res.scalar_one()

    @start_db_transaction
    async def create(self,data:CreateSupplierDbSchema)->dict | None:
        stmt=(
            insert(
                Suppliers
            )
            .values(**data.model_dump(mode="json",exclude_none=True,exclude_unset=True))
            .returning(*self.supplier_cols)
        )
        res=(await self.session.execute(stmt)).mappings().one_or_none()
        return res
    

    @start_db_transaction
    async def update(self,data:UpdateSupplierDbSchema)->dict|None:
        stmt=update(
            Suppliers
        ).where(
            and_(
                Suppliers.id==data.id,
                Suppliers.shop_id==data.shop_id
            )
        ).values(**data.model_dump(mode="json",exclude_none=True,exclude_unset=True)).returning(*self.supplier_cols)

        res=(await self.session.execute(stmt)).mappings().one_or_none()
        return res
    
    @start_db_transaction
    async def delete(self, data:DeleteSupplierSchema)->dict|None:
        stmt=delete(
            Suppliers
        ).where(Suppliers.id==data.id,Suppliers.shop_id==data.shop_id).returning(*self.supplier_cols)

        res=(await self.session.execute(stmt)).mappings().one_or_none()

        return res
    

    @start_db_transaction
    async def update_outstanding(self,data:UpdateOutstandingSupplierSchema):
        stmt=(
            update(
                Suppliers
            )
            .where(
                Suppliers.id==data.id,
                Suppliers.shop_id==data.shop_id
            )
            .values(
                outstanding_infos=data.outstanding_infos.model_dump(mode='json')
            )
            .returning(*self.supplier_cols)
        )

        res=(await self.session.execute(stmt)).mappings().one_or_none()
        return res
    

    async def get(self,data:GetAllSupplierSchema)-> List[dict] | []:
        search_term=f"%{data.query}%"
        cursor=(data.offset-1)*data.limit
        stmt=(
            select(
                *self.supplier_cols
            )
            .offset(offset=cursor).limit(limit=data.limit)
        )

        res=(await self.session.execute(stmt)).mappings().all()

        return res
    

    async def getby_shop_id(self,data:GetSupplierByShopIdSchema)-> List[dict] | []:
        search_term=f"%{data.query}%"
        cursor=(data.offset-1)*data.limit
        stmt=(
            select(
                *self.supplier_cols
            )
            .where(
                Suppliers.shop_id==data.shop_id
            )
            .offset(offset=cursor).limit(limit=data.limit)
        )

        res=(await self.session.execute(stmt)).mappings().all()

        return res

    async def getby_id(self,data:GetSupplierById)-> dict:
        stmt=(
            select(
                *self.supplier_cols
            )
            .where(
                Suppliers.id==data.id,
                Suppliers.shop_id==data.shop_id
            )
        )

        res=(await self.session.execute(stmt)).mappings().one_or_none()

        return res
    
