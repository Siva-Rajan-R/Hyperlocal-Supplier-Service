from infras.primary_db.services.supplier_service import SupplierService
from schemas.v1.request_schemas.supplier_schema import CreateSupplierSchema,UpdateSupplierSchema,DeleteSupplierSchema,GetAllSupplierSchema,GetSupplierById,GetSupplierByShopIdSchema,VerifySupplierSchema
from models.service_models.base_service_model import BaseServiceModel
from schemas.v1.response_schemas.msgqueue_schemas.supplier_schema import SupplierContactInfoTypDict,SupplierCreateResponseSchema,SupplierDeleteResponseSchema,SupplierGetResponseSchema,SupplierUpdateResponseSchema
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict,ErrorResponseTypDict,BaseResponseTypDict
from fastapi.exceptions import HTTPException
from infras.primary_db.main import AsyncSupplierLocalSession
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from hyperlocal_platform.core.utils.uuid_generator import generate_uuid
from core.decorators.error_handler_dec import catch_errors
from typing import Optional,Union
from icecream import ic

class MessagingQueueSupplierService:

    async def verify_supplier(self,data:Union[VerifySupplierSchema,dict]):
        if isinstance(data, dict):
            data = VerifySupplierSchema(**data)
        async with AsyncSupplierLocalSession() as session:
            supplier_service_obj=SupplierService(session=session)
            res=await supplier_service_obj.verify(data=data)

            return res
        

    async def get_suppliers(self,data:Union[GetAllSupplierSchema,dict]):
        if isinstance(data, dict):
            data = GetAllSupplierSchema(**data)
        async with AsyncSupplierLocalSession() as session:
            supplier_service_obj=SupplierService(session=session)
            res=await supplier_service_obj.get(data=data)

            if not res:
                return res

            return [SupplierGetResponseSchema(**r).model_dump(mode="json") for r in res]
    
    async def get_supplier_by_id(self,data:Union[GetSupplierById,dict]):
        if isinstance(data, dict):
            data = GetSupplierById(**data)
        async with AsyncSupplierLocalSession() as session:
            supplier_service_obj=SupplierService(session=session)
            res=await supplier_service_obj.getby_id(data=data)

            if not res:
                return res
            
            return SupplierGetResponseSchema(**res).model_dump(mode="json")
    
    async def get_supplier_by_shop_id(self,data:Union[GetSupplierByShopIdSchema,dict]):
        if isinstance(data, dict):
            data = GetSupplierByShopIdSchema(**data)
        async with AsyncSupplierLocalSession() as session:
            supplier_service_obj=SupplierService(session=session)
            res=await supplier_service_obj.getby_shopid(data=data)

            if not res:
                return res
            
            return [SupplierGetResponseSchema(**r).model_dump(mode="json") for r in res]