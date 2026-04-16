from pydantic import BaseModel
from typing import Optional

class CreateSupplierDbSchema(BaseModel):
    id:str
    shop_id:str
    datas:dict


class UpdateSupplierDbSchema(BaseModel):
    id:str
    shop_id:str
    datas:dict