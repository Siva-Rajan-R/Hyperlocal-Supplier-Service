from typing import TypedDict,Optional,List
from pydantic import EmailStr

class SupplierContactInfoTypDict(TypedDict):
    name:str
    mobile_number:str
    email:Optional[EmailStr]=None

class SupplierAddressTypDict(TypedDict):
    full_address:str
    zipcode:str
    city:str