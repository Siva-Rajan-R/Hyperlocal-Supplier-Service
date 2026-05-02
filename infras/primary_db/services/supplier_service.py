from ..main import AsyncSession
from ..repos.supplier_repo import SupplierRepo
from schemas.v1.db_schemas.supplier_schema import CreateSupplierDbSchema,UpdateSupplierDbSchema
from schemas.v1.request_schemas.supplier_schema import CreateSupplierSchema,UpdateSupplierSchema,DeleteSupplierSchema,GetAllSupplierSchema,GetSupplierById,GetSupplierByShopIdSchema,VerifySupplierSchema
from models.service_models.base_service_model import BaseServiceModel
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict,ErrorResponseTypDict,BaseResponseTypDict
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from hyperlocal_platform.core.utils.uuid_generator import generate_uuid
from core.decorators.error_handler_dec import catch_errors
from typing import Optional,List
from icecream import ic

class SupplierService(BaseServiceModel):
    def __init__(self, session:AsyncSession):
        super().__init__(session)
        self.supplier_repo_obj=SupplierRepo(session=session)

    async def create(self,data:CreateSupplierSchema)-> dict | None:
        
        supplier_id:str=generate_uuid()
        ic(data.datas)
        data=CreateSupplierDbSchema(
            **data.model_dump(mode="json",exclude_none=True,exclude_unset=True),
            id=supplier_id
        )

        res=await self.supplier_repo_obj.create(data=data)
        return res
    
    async def update(self,data:UpdateSupplierSchema)-> dict | None:
        data=UpdateSupplierDbSchema(**data.model_dump(mode="json",exclude_unset=True,exclude_none=True))
        res=await self.supplier_repo_obj.update(data=data)
        return res

    async def delete(self,data:DeleteSupplierSchema)-> dict | None:
        res=await self.supplier_repo_obj.delete(data=data)
        return res


    async def get(self,data:GetAllSupplierSchema)-> List[dict] | list:
        res=await self.supplier_repo_obj.get(data=data)
        return res


    async def getby_id(self,data:GetSupplierById)-> dict | None:
        res=await self.supplier_repo_obj.getby_id(data=data)
        return res
    
    async def getby_shop_id(self,data:GetSupplierByShopIdSchema)-> List[dict] | list:
        res=await self.supplier_repo_obj.getby_shop_id(data=data)
        return res
    
    async def verify(self,data:VerifySupplierSchema)-> dict:
        res=await self.supplier_repo_obj.verify(data=data)
        return res

    

    async def search(self, query:str, limit:Optional[int]=5):
        res=await self.supplier_repo_obj.search(query=query,limit=limit)
        return res