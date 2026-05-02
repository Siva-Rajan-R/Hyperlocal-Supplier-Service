from pydantic import BaseModel,EmailStr
from core.data_formats.typ_dicts.supplier_typdict import SupplierContactInfoTypDict
from typing import Optional

class CreateSupplierDbSchema(BaseModel):
    id:str
    shop_id:str
    name:str
    email:Optional[EmailStr]=None
    mobile_number:str
    gst_no:str
    contact_info:Optional[SupplierContactInfoTypDict]=None
    datas:Optional[dict]={}


class UpdateSupplierDbSchema(BaseModel):
    id:str
    shop_id:str
    name:Optional[str]=None
    email:Optional[EmailStr]=None
    mobile_number:Optional[str]=None
    gst_no:Optional[str]=None
    contact_info:Optional[SupplierContactInfoTypDict]=None
    datas:Optional[dict]={}