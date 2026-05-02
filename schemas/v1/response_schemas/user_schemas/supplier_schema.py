from pydantic import BaseModel,EmailStr
from core.data_formats.typ_dicts.supplier_typdict import SupplierContactInfoTypDict
from typing import Optional
from datetime import date,datetime


class SupplierCreateResponseSchema(BaseModel):
    id:str
    ui_id:int
    name:str
    email:Optional[EmailStr]=None
    mobile_number:str
    contact_info:Optional[SupplierContactInfoTypDict]=None
    gst_no:str
    datas:Optional[dict]
    created_at:datetime
    updated_at:datetime

class SupplierUpdateResponseSchema(BaseModel):
    id:str
    ui_id:int
    name:str
    email:Optional[EmailStr]=None
    mobile_number:str
    contact_info:Optional[SupplierContactInfoTypDict]=None
    gst_no:str
    datas:Optional[dict]
    created_at:datetime
    updated_at:datetime


class SupplierDeleteResponseSchema(BaseModel):
    id:str
    ui_id:int
    name:str
    email:Optional[EmailStr]=None
    mobile_number:str
    contact_info:Optional[SupplierContactInfoTypDict]=None
    gst_no:str
    datas:Optional[dict]
    created_at:datetime
    updated_at:datetime


class SupplierGetResponseSchema(BaseModel):
    id:str
    ui_id:int
    name:str
    email:Optional[EmailStr]=None
    mobile_number:str
    contact_info:Optional[SupplierContactInfoTypDict]=None
    gst_no:str
    datas:Optional[dict]
    created_at:datetime
    updated_at:datetime
