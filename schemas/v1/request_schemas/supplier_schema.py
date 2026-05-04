from pydantic import BaseModel,EmailStr,Field
from core.data_formats.typ_dicts.supplier_typdict import SupplierContactInfoTypDict,SupplierAddressTypDict
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from typing import Optional

# Optional Supplier Schemas
class OptionalSupplierFieldsSchema(BaseModel):
    internal_notes:Optional[str]=None
    address:Optional[SupplierAddressTypDict]=None


# Writable Schemas
class CreateSupplierSchema(BaseModel):
    shop_id:str
    name:str
    email:Optional[EmailStr]=None
    mobile_number:str
    gst_no:str
    contact_info:Optional[SupplierContactInfoTypDict]=None
    datas:Optional[OptionalSupplierFieldsSchema]={}


class UpdateSupplierSchema(BaseModel):
    id:str
    shop_id:str
    name:Optional[str]=None
    email:Optional[EmailStr]=None
    mobile_number:Optional[str]=None
    gst_no:Optional[str]=None
    contact_info:Optional[SupplierContactInfoTypDict]=None
    datas:Optional[OptionalSupplierFieldsSchema]={}


class DeleteSupplierSchema(BaseModel):
    id:str
    shop_id:str



# Fetchable Schemas

class GetAllSupplierSchema(BaseModel):
    query:str=Field(default="",alias='q')
    limit:int=Field(default=10,le=100)
    offset:int=Field(default=1)
    timezone:Optional[TimeZoneEnum]=TimeZoneEnum.Asia_Kolkata

class GetSupplierByShopIdSchema(BaseModel):
    shop_id:str
    query:str=Field(default="",alias='q')
    limit:int=Field(default=10,le=100)
    offset:int=Field(default=1)
    timezone:Optional[TimeZoneEnum]=TimeZoneEnum.Asia_Kolkata

class GetSupplierById(BaseModel):
    shop_id:str
    id:str
    timezone:Optional[TimeZoneEnum]=TimeZoneEnum.Asia_Kolkata

class VerifySupplierSchema(BaseModel):
    shop_id:str
    email:Optional[str]=None
    mobile_number:Optional[str]=None

