from pydantic import BaseModel
from typing import Optional

class CreateSupplierSchema(BaseModel):
    datas:dict
    shop_id:str


class UpdateSupplierSchema(BaseModel):
    id:str
    shop_id:str
    datas:dict
