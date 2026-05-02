from typing import TypedDict,Optional,List
from pydantic import EmailStr

class SupplierContactInfoTypDict(TypedDict):
    name:str
    mobile_number:str
    email:Optional[EmailStr]=None