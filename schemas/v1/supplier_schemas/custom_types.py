from pydantic import BaseModel,EmailStr,Field
from core.data_formats.typ_dicts.supplier_typdict import SupplierContactInfoTypDict,SupplierAddressTypDict
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from typing import Optional


class SupplierLocationInfosType(BaseModel):
    zipcode:str
    country:str
    state:str
    full_address:str

class SupplierContactInfosType(BaseModel):
    email:Optional[EmailStr]=None
    mobile_number:Optional[str]=None

class SupplierContactPersonInfosType(BaseModel):
    name:str
    email:Optional[EmailStr]=None
    mobile_number:Optional[str]=None

class SupplierOutstandingInfosType(BaseModel):
    amount:float