from pydantic import BaseModel
from typing import Optional,Dict,Any,List


class SupplierCreateMandatoryFields(BaseModel):
    shop_id:str

    model_config={
        "extra":"allow"
    }


class CreateSupplierSchema(BaseModel):
    datas:SupplierCreateMandatoryFields
    


class SupplierUpdateMandatoryFields(BaseModel):
    id:str
    shop_id:str

    model_config={
        "extra":"allow"
    }

class UpdateSupplierSchema(BaseModel):
    datas:SupplierUpdateMandatoryFields
