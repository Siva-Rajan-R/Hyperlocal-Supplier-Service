from pydantic import BaseModel,EmailStr,Field
from core.data_formats.typ_dicts.supplier_typdict import SupplierContactInfoTypDict,SupplierAddressTypDict
from core.data_formats.enums.supplier_enums import SupplierOutstandingUpdateTypeEnums
from .custom_types import SupplierOutstandingInfosType,SupplierContactInfosType,SupplierContactPersonInfosType,SupplierLocationInfosType
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from typing import Optional



# Writable Schemas
class CreateSupplierSchema(BaseModel):
    shop_id:str
    name:str
    contact_infos:SupplierContactInfosType
    location_infos:SupplierLocationInfosType
    contact_person_infos:Optional[SupplierContactPersonInfosType]=None
    gst_no:Optional[str]=None
    additional_infos:Optional[dict]={}
    custom_fields:Optional[dict]={}

class UpdateSupplierSchema(BaseModel):
    id:str
    shop_id:str
    name:Optional[str]=None
    contact_infos:Optional[SupplierContactInfosType]=None
    location_infos:Optional[SupplierLocationInfosType]=None
    contact_person_infos:Optional[SupplierContactPersonInfosType]=None
    gst_no:Optional[str]=None
    additional_infos:Optional[dict]={}
    custom_fields:Optional[dict]={}


class DeleteSupplierSchema(BaseModel):
    id:str
    shop_id:str

class UpdateOutstandingSupplierSchema(BaseModel):
    id:str
    shop_id:str
    outstanding_infos:SupplierOutstandingInfosType
    type:SupplierOutstandingUpdateTypeEnums
    entity_name: Optional[str] = None
    entity_id: Optional[str] = None
    invoice_no: Optional[str] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    outstanding_amount: Optional[float] = None
    cleared_amount: Optional[float] = None




# Fetchable Schemas

class GetAllSupplierSchema(BaseModel):
    query:str=Field(default="",alias='q')
    limit:int=Field(default=10,le=100)
    offset:int=Field(default=1)
    from_date:Optional[str]=None
    to_date:Optional[str]=None
    has_outstanding:Optional[bool]=None

class GetSupplierByShopIdSchema(BaseModel):
    shop_id:str
    query:str=Field(default="",alias='q')
    limit:int=Field(default=10,le=100)
    offset:int=Field(default=1)
    from_date:Optional[str]=None
    to_date:Optional[str]=None
    has_outstanding:Optional[bool]=None

class GetSupplierById(BaseModel):
    shop_id:str
    id:str

class VerifySupplierSchema(BaseModel):
    shop_id:str
    email:Optional[str]=None
    mobile_number:Optional[str]=None

class GetSupplierOutstandingHistorySchema(BaseModel):
    supplier_id: str
    shop_id: str

