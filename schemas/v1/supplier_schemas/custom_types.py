from pydantic import BaseModel,EmailStr,Field
from core.data_formats.typ_dicts.supplier_typdict import SupplierContactInfoTypDict,SupplierAddressTypDict
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from typing import Optional


class SupplierLocationInfosType(BaseModel):
    zipcode:Optional[str]=None
    country:Optional[str]=None
    state:Optional[str]=None
    full_address:Optional[str]=None

class SupplierContactInfosType(BaseModel):
    email:Optional[EmailStr]=None
    mobile_number:Optional[str]=None

class SupplierContactPersonInfosType(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile_number: Optional[str] = None

class SupplierOutstandingInfosType(BaseModel):
    amount:float