from models.repo_models.base_repo_model import BaseRepoModel
from ..models.supplier_model import Suppliers,String
from ..main import AsyncSession
from sqlalchemy import select,update,delete,or_,and_,func
from schemas.v1.db_schema.supplier_schema import CreateSupplierDbSchema,UpdateSupplierDbSchema
from typing import Optional
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from core.decorators.error_handler_dec import catch_errors



class SupplierRepo(BaseRepoModel):
    def __init__(self, session:AsyncSession):
        super().__init__(session)
        self.supplier_cols=(
            Suppliers.id,
            Suppliers.datas,
            Suppliers.shop_id
        )


    @start_db_transaction
    async def create(self,data:CreateSupplierDbSchema)->bool:
        self.session.add(Suppliers(**data.model_dump(mode="json")))
        await self.session.commit()
        return True
    

    @start_db_transaction
    async def update(self,data:UpdateSupplierDbSchema)->str|None:
        supplier_toupdate=update(
            Suppliers
        ).where(
            and_(
                Suppliers.id==data.id,
                Suppliers.shop_id==data.shop_id
            )
        ).values(**data.model_dump(mode="json",exclude_none=True,exclude_unset=True)).returning(Suppliers.id)

        is_updated=(await self.session.execute(supplier_toupdate)).scalar_one_or_none()
        return is_updated
    
    @start_db_transaction
    async def delete(self, supplier_id:str,shop_id:str)->str|None:
        supplier_todel=delete(
            Suppliers
        ).where(Suppliers.id==supplier_id,Suppliers.shop_id==shop_id).returning(Suppliers.id)

        is_deleted=(await self.session.execute(supplier_todel)).scalar_one_or_none()

        return is_deleted
    

    async def get(self,timezone:TimeZoneEnum,query:str,limit:int,offset:int):
        search_term=f"%{query}%"
        created_at=func.date(func.timezone(timezone.value,Suppliers.created_at))
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
            ).offset(offset=offset).limit(limit=limit)
            .order_by(created_at)
        )

        suppliers=(await self.session.execute(supplier_stmt)).mappings().all()

        return suppliers

    async def getby_id(self,timezone:TimeZoneEnum,supplier_id:str,shop_id:str):
        created_at=func.date(func.timezone(timezone.value,Suppliers.created_at))
        supplier_stmt=(
            select(
                *self.supplier_cols,
                created_at
            )
            .where(
                Suppliers.id==supplier_id,
                Suppliers.shop_id==shop_id
            )
        )

        supplier=(await self.session.execute(supplier_stmt)).mappings().one_or_none()

        return supplier
    
    async def getby_mobile_number(self,timezone:TimeZoneEnum,mobile_no:str,shop_id:str):
        created_at=func.date(func.timezone(timezone.value,Suppliers.created_at))
        supplier_stmt=(
            select(
                *self.supplier_cols,
                created_at
            )
            .where(
                Suppliers.datas['mobile_number'].astext==mobile_no,
                Suppliers.shop_id==shop_id
            )
        )

        supplier=(await self.session.execute(supplier_stmt)).mappings().one_or_none()

        return supplier
    
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
