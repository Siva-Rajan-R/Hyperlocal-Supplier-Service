from icecream import ic
from schemas.v1.supplier_schemas.request_schemas import CreateSupplierSchema,UpdateOutstandingSupplierSchema,UpdateSupplierSchema,DeleteSupplierSchema,GetAllSupplierSchema,GetSupplierById,GetSupplierByShopIdSchema
from schemas.v1.supplier_schemas.db_schemas import CreateSupplierDbSchema,UpdateSupplierDbSchema,DeleteSupplierDbSchema
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
from infras.primary_db.repos.customfield_repo import CustomFieldsRepo,GetFieldByShopIdSchema
from infras.primary_db.services.customfield_service import CustomFieldsService
from schemas.v1.db_schemas.customfield_schema import CreateCustomFieldValueDbSchema
from core.utils.validate_custom_fields import validate_and_filter_custom_fields
from hyperlocal_platform.core.utils.uuid_generator import generate_uuid

class HandleSupplierRequest:
    def __init__(self, session:AsyncSession):
        self.session=session


    async def create(self,data:CreateSupplierSchema):
        if not data.contact_infos or (not data.contact_infos.email and not data.contact_infos.mobile_number):
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error Creating Supplier",
                    description="Please provide a atleast one of the contact info (Email or Mobile number)",
                    success=False
                )
            )

        if data.contact_person_infos and (not data.contact_person_infos.email and not data.contact_person_infos.mobile_number):
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error Creating Supplier",
                    description="Please provide a atleast one of the contact info (Email or Mobile number) for contact person",
                    success=False
                )
            )
        
        # for checking the custome fields
        defined_fields = await CustomFieldsService(session=self.session).get_field_by_shop_id(data=GetFieldByShopIdSchema(shop_id=data.shop_id))
        valid_custom_fields = validate_and_filter_custom_fields(payload_custom_fields=data.custom_fields, defined_custom_fields=defined_fields)
        ic(valid_custom_fields)

        final_data = CreateSupplierSchema(custom_fields=valid_custom_fields,**data.model_dump(exclude=['custom_fields']))
        res=await SupplierService(session=self.session).create(data=final_data)
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
            data=res if res else None
        )


    async def update(self,data:UpdateSupplierSchema):
        if data.contact_infos and (not data.contact_infos.email and not data.contact_infos.mobile_number):
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error Creating Supplier",
                    description="Please provide a atleast one of the contact info (Email or Mobile number)",
                    success=False
                )
            )

        if data.contact_person_infos and (not data.contact_person_infos.email and not data.contact_person_infos.mobile_number):
            raise HTTPException(
                status_code=400,
                detail=ErrorResponseTypDict(
                    status_code=400,
                    msg="Error Creating Supplier",
                    description="Please provide a atleast one of the contact info (Email or Mobile number) for contact person",
                    success=False
                )
            )
        
        defined_fields = await CustomFieldsRepo(session=self.session).get_all_fields(shop_id=data.shop_id)
        valid_custom_fields = validate_and_filter_custom_fields(data.custom_fields, defined_fields)

        final_data = UpdateSupplierSchema(**data.model_dump(exclude=['custom_fields']))
        res=await SupplierService(session=self.session).update(data=final_data)
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
            
        defined_fields_map = {field['field_name']: field['id'] for field in defined_fields}
        for field_name, value in valid_custom_fields.items():
            field_id = defined_fields_map.get(field_name)
            if field_id:
                await CustomFieldsRepo(session=self.session).upsert_field_value(
                    data=CreateCustomFieldValueDbSchema(
                        id=generate_uuid(),
                        shop_id=data.shop_id,
                        supplier_id=res['id'],
                        field_id=field_id,
                        value=str(value)
                    )
                )
        
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Supplier updated successfully",
                status_code=200,
                success=True
            ),
            data=res if res else None
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
            data=res if res else None
        )


    async def get(self,data:GetAllSupplierSchema):
        res=await SupplierService(session=self.session).get(data=data)

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Supplier fetched successfully",
                status_code=200,
                success=True
            ),
            data=res
        )


    async def getby_id(self,data:GetSupplierById):
        res=await SupplierService(session=self.session).getby_id(data=data)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Supplier fetched successfully",
                status_code=200,
                success=True
            ),
            data=res
        )
    
    async def getby_shop_id(self,data:GetSupplierByShopIdSchema):
        res=await SupplierService(session=self.session).getby_shop_id(data=data)

        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Supplier fetched successfully",
                status_code=200,
                success=True
            ),
            data=res
        )
    

    async def update_outstanding(self,data:UpdateOutstandingSupplierSchema):
        res=await SupplierService(session=self.session).update_outstanding(data=data)
        return SuccessResponseTypDict(
            detail=BaseResponseTypDict(
                msg="Supplier outstanding updated successfully",
                status_code=200,
                success=True
            ),
            data=res
        )