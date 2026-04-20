from schemas.v1.request_schema.supplier_schema import CreateSupplierSchema,UpdateSupplierSchema
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
        # await validate_fields(service_name="SUPPLIER",shop_id="",incoming_fields=data.datas)

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
            )
        )


    async def update(self,data:UpdateSupplierSchema):
        # await validate_fields(service_name="SUPPLIER",shop_id="",incoming_fields=data.datas)
        res=await SupplierService(session=self.session).update(data=data)
        if not res:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    msg="Error : Updating supplier",
                    description="Invalid supplier id or barcode for updating suppliers",
                    status_code=400,
                    success=False
                )
            )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Supplier updated successfully",
                status_code=200,
                success=True
            )
        )


    async def delete(self,supplier_id:str,shop_id:str):
        res=await SupplierService(session=self.session).delete(supplier_id=supplier_id,shop_id=shop_id)
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
            )
        )


    async def get(self,timezone:TimeZoneEnum,query:Optional[str]="",limit:Optional[int]=10,offset:int=1):
        res=await SupplierService(session=self.session).get(query=query,limit=limit,offset=offset,timezone=timezone)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Supplier fetched successfully",
                status_code=200,
                success=True
            ),
            data=res
        )


    async def getby_id(self,timezone:TimeZoneEnum,supplier_id:str,shop_id:str):
        res=await SupplierService(session=self.session).getby_id(timezone=timezone,supplier_id=supplier_id,shop_id=shop_id)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Supplier fetched successfully",
                status_code=200,
                success=True
            ),
            data=res
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