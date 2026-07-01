from pydantic import BaseModel,EmailStr,Field
from core.data_formats.typ_dicts.supplier_typdict import SupplierContactInfoTypDict,SupplierAddressTypDict
from .custom_types import SupplierOutstandingInfosType,SupplierContactInfosType,SupplierContactPersonInfosType,SupplierLocationInfosType
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from typing import Optional



# Writable Schemas
class CreateSupplierDbSchema(BaseModel):
    id:str
    ui_id:str
    shop_id:str
    name:str
    contact_infos:SupplierContactInfosType
    location_infos:SupplierLocationInfosType
    contact_person_infos:Optional[SupplierContactPersonInfosType]=None
    gst_no:Optional[str]=None
    additional_infos:Optional[dict]={}


class UpdateSupplierDbSchema(BaseModel):
    id:str
    shop_id:str
    name:Optional[str]=None
    contact_infos:Optional[SupplierContactInfosType]=None
    location_infos:Optional[SupplierLocationInfosType]=None
    contact_person_infos:Optional[SupplierContactPersonInfosType]=None
    gst_no:Optional[str]=None
    additional_infos:Optional[dict]={}


class DeleteSupplierDbSchema(BaseModel):
    id:str
    shop_id:str

