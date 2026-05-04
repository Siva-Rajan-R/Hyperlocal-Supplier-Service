from icecream import ic
from schemas.v1.request_schemas.supplier_schema import CreateSupplierSchema,UpdateSupplierSchema,DeleteSupplierSchema,GetSupplierByShopIdSchema,GetAllSupplierSchema,GetSupplierById
from schemas.v1.response_schemas.user_schemas.supplier_schema import SupplierContactInfoTypDict,SupplierCreateResponseSchema,SupplierDeleteResponseSchema,SupplierGetResponseSchema,SupplierUpdateResponseSchema
from models.service_models.base_service_model import BaseServiceModel
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict,ErrorResponseTypDict,BaseResponseTypDict
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from core.decorators.error_handler_dec import catch_errors
from infras.primary_db.services.supplier_service import SupplierService
from sqlalchemy.ext.asyncio import AsyncSession
from core.utils.validate_fields import validate_fields
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from typing import Optional,List

class HandleSupplierRequest(BaseServiceModel):
    def __init__(self, session:AsyncSession):
        self.session=session


    async def create(self,data:CreateSupplierSchema):
        res=await SupplierService(session=self.session).create(data=data)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    msg="Error : Creating supplier",
                    description="Invalid datas for creating suppliers",
                    status_code=400,
                    success=False
                )
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Supplier created successfully",
                status_code=201,
                success=True
            ),
            data=SupplierCreateResponseSchema(**res) if res else None
        )


    async def update(self,data:UpdateSupplierSchema):
        res=await SupplierService(session=self.session).update(data=data)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    msg="Error : Updating supplier",
                    description="Invalid supplier id or shop_id for updating suppliers",
                    status_code=400,
                    success=False
                )
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Supplier updated successfully",
                status_code=200,
                success=True
            ),
            data=SupplierUpdateResponseSchema(**res) if res else None
        )


    async def delete(self,data:DeleteSupplierSchema):
        res=await SupplierService(session=self.session).delete(data=data)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    msg="Error : Deleting supplier",
                    description="Invalid supplier id for deleting supplier",
                    status_code=400,
                    success=False
                )
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Supplier deleted successfully",
                status_code=200,
                success=True
            ),
            data=SupplierDeleteResponseSchema(**res) if res else None
        )


    async def get(self,data:GetAllSupplierSchema):
        res=await SupplierService(session=self.session).get(data=data)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Supplier fetched successfully",
                status_code=200,
                success=True
            ),
            data=[SupplierGetResponseSchema(**r) for r in res] if res else None
        )


    async def getby_id(self,data:GetSupplierById):
        res=await SupplierService(session=self.session).getby_id(data=data)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Supplier fetched successfully",
                status_code=200,
                success=True
            ),
            data=SupplierGetResponseSchema(**res) if res else None
        )
    
    async def getby_shop_id(self,data:GetSupplierByShopIdSchema):
        res=await SupplierService(session=self.session).getby_shop_id(data=data)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Supplier fetched successfully",
                status_code=200,
                success=True
            ),
            data=[SupplierGetResponseSchema(**r) for r in res] if res else None
        )
    

    async def search(self, query:str, limit:Optional[int]=5):
        res=await SupplierService(session=self.session).search(query=query,limit=limit)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Supplier fetched successfully",
                status_code=200,
                success=True
            ),
            data=res
        )