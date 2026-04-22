from ..main import AsyncSession
from ..repos.supplier_repo import SupplierRepo,CreateSupplierDbSchema,UpdateSupplierDbSchema
from schemas.v1.request_schema.supplier_schema import CreateSupplierSchema,UpdateSupplierSchema
from models.service_models.base_service_model import BaseServiceModel
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict,ErrorResponseTypDict,BaseResponseTypDict
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from hyperlocal_platform.core.utils.uuid_generator import generate_uuid
from core.decorators.error_handler_dec import catch_errors
from typing import Optional
from icecream import ic

class SupplierService(BaseServiceModel):
    def __init__(self, session:AsyncSession):
        super().__init__(session)
        self.supplier_repo_obj=SupplierRepo(session=session)

    async def create(self,data:CreateSupplierSchema):
        
        supplier_id:str=generate_uuid()
        ic(data.datas)
        data=CreateSupplierDbSchema(
            datas=data.datas.model_dump(mode="json"),
            shop_id=data.datas.shop_id,
            id=supplier_id
        )

        res=await self.supplier_repo_obj.create(data=data)
        if not res:
            return False
        
        return data
    
    async def update(self,data:UpdateSupplierSchema):
        data=UpdateSupplierDbSchema(
            datas=data.datas.model_dump(mode="json"),
            shop_id=data.datas.shop_id,
            id=data.datas.id
        )
        res=await self.supplier_repo_obj.update(data=data)
        if not res:
            return False
        
        return True

    async def delete(self,supplier_id:str,shop_id:str):
        res=await self.supplier_repo_obj.delete(supplier_id=supplier_id,shop_id=shop_id)
        if not res:
            return False
        
        return True


    async def get(self,timezone:TimeZoneEnum,query:Optional[str]="",limit:Optional[int]=10,offset:int=1):
        offset=offset-1
        res=await self.supplier_repo_obj.get(query=query,limit=limit,offset=offset,timezone=timezone)
        return res


    async def getby_id(self,timezone:TimeZoneEnum,supplier_id:str,shop_id:str):
        res=await self.supplier_repo_obj.getby_id(timezone=timezone,supplier_id=supplier_id,shop_id=shop_id)
        return res
    
    async def getby_mobile_no(self,mobile_no:str,shop_id:str,timezone:TimeZoneEnum=TimeZoneEnum.Asia_Kolkata):
        res=await self.supplier_repo_obj.getby_mobile_number(timezone=timezone,mobile_no=mobile_no,shop_id=shop_id)
        return res
    

    async def search(self, query:str, limit:Optional[int]=5):
        res=await self.supplier_repo_obj.search(query=query,limit=limit)
        return res