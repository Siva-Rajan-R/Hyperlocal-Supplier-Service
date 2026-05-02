from models.repo_models.base_repo_model import BaseRepoModel
from ..models.supplier_model import Suppliers,String
from sqlalchemy.dialects.postgresql import insert
from ..main import AsyncSession
from sqlalchemy import select,update,delete,or_,and_,func
from schemas.v1.db_schemas.supplier_schema import CreateSupplierDbSchema,UpdateSupplierDbSchema
from schemas.v1.request_schemas.supplier_schema import DeleteSupplierSchema,GetAllSupplierSchema,GetSupplierById,GetSupplierByShopIdSchema,VerifySupplierSchema
from typing import Optional,List
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from core.decorators.error_handler_dec import catch_errors



class SupplierRepo(BaseRepoModel):
    def __init__(self, session:AsyncSession):
        super().__init__(session)
        self.supplier_cols=(
            Suppliers.id,
            Suppliers.datas,
            Suppliers.ui_id,
            Suppliers.shop_id,
            Suppliers.sequence_id,
            Suppliers.name,
            Suppliers.contact_info,
            Suppliers.email,
            Suppliers.mobile_number,
            Suppliers.gst_no,
            Suppliers.created_at,
            Suppliers.updated_at
        )


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
        supplier_toupdate=update(
            Suppliers
        ).where(
            and_(
                Suppliers.id==data.id,
                Suppliers.shop_id==data.shop_id
            )
        ).values(**data.model_dump(mode="json",exclude_none=True,exclude_unset=True)).returning(*self.supplier_cols)

        is_updated=(await self.session.execute(supplier_toupdate)).mappings().one_or_none()
        return is_updated
    
    @start_db_transaction
    async def delete(self, data:DeleteSupplierSchema)->dict|None:
        supplier_todel=delete(
            Suppliers
        ).where(Suppliers.id==data.id,Suppliers.shop_id==data.shop_id).returning(*self.supplier_cols)

        is_deleted=(await self.session.execute(supplier_todel)).mappings().one_or_none()

        return is_deleted
    

    async def get(self,data:GetAllSupplierSchema)-> List[dict] | []:
        search_term=f"%{data.query}%"
        created_at=func.date(func.timezone(data.timezone.value,Suppliers.created_at))
        cursor=(data.offset-1)*data.limit
        supplier_stmt=(
            select(
                *self.supplier_cols,
                created_at
            )
            .where(
                or_(
                    Suppliers.id.ilike(search_term),
                    Suppliers.shop_id.ilike(search_term),
                    func.cast(created_at,String).ilike(search_term)
                )
            ).offset(offset=cursor).limit(limit=data.limit)
        )

        suppliers=(await self.session.execute(supplier_stmt)).mappings().all()

        return suppliers
    

    async def getby_shop_id(self,data:GetSupplierByShopIdSchema)-> List[dict] | []:
        search_term=f"%{data.query}%"
        created_at=func.date(func.timezone(data.timezone.value,Suppliers.created_at))
        cursor=(data.offset-1)*data.limit
        supplier_stmt=(
            select(
                *self.supplier_cols,
                created_at
            )
            .where(
                Suppliers.shop_id==data.shop_id,
                or_(
                    Suppliers.id.ilike(search_term),
                    Suppliers.shop_id.ilike(search_term),
                    func.cast(created_at,String).ilike(search_term)
                )
            ).offset(offset=cursor).limit(limit=data.limit)
        )

        suppliers=(await self.session.execute(supplier_stmt)).mappings().all()

        return suppliers

    async def getby_id(self,data:GetSupplierById)-> dict:
        created_at=func.date(func.timezone(data.timezone.value,Suppliers.created_at))
        supplier_stmt=(
            select(
                *self.supplier_cols,
                created_at
            )
            .where(
                Suppliers.id==data.id,
                Suppliers.shop_id==data.shop_id
            )
        )

        supplier=(await self.session.execute(supplier_stmt)).mappings().one_or_none()

        return supplier
    
    async def verify(self,data:VerifySupplierSchema)-> dict:
        stmt=(
            select(
                Suppliers.id
            ).where(
                Suppliers.shop_id==data.shop_id,
                or_(
                    Suppliers.id==data.email,
                    Suppliers.mobile_number==data.mobile_number
                )
            )
        )

        result=(await self.session.execute(stmt)).scalar_one_or_none()

        if result:
            return {'id':result,'exists':True}
        return {'id':'','exists':False}
    
    async def search(self, query:str, limit:int):
        search_term=f"%{query}%"
        supplier_stmt=(
            select(
                *self.supplier_cols
            )
            .where(
                or_(
                    Suppliers.id.ilike(search_term),
                    Suppliers.shop_id.ilike(search_term)
                )
            ).limit(limit=limit)
        )

        suppliers=(await self.session.execute(supplier_stmt)).mappings().all()

        return suppliers
