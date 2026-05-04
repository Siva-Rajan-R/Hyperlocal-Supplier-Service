from fastapi import APIRouter,HTTPException,Query,Depends
from typing import Annotated
from infras.primary_db.main import get_pg_async_session,AsyncSession
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from core.utils.validate_fields import validate_fields
from ...handlers.supplier_handler import HandleSupplierRequest
from schemas.v1.request_schemas.supplier_schema import CreateSupplierSchema,UpdateSupplierSchema,DeleteSupplierSchema,GetAllSupplierSchema,GetSupplierById,GetSupplierByShopIdSchema,VerifySupplierSchema
from typing import Optional,List
print(TimeZoneEnum)

router=APIRouter(
    tags=['Supplier CRUD'],
    prefix='/suppliers'
)

PG_ASYNC_SESSION=Annotated[AsyncSession,Depends(get_pg_async_session)]
SHOP_ID="37d5519b-51a1-5854-982b-4d6524171017"

# Write methods
@router.post('')
async def create(data:CreateSupplierSchema,session:PG_ASYNC_SESSION):
    return await HandleSupplierRequest(session=session).create(data=data)

@router.put('')
async def update(data:UpdateSupplierSchema,session:PG_ASYNC_SESSION):
    return await HandleSupplierRequest(session=session).update(data=data)

@router.delete('/{shop_id}/{id}')
async def delete(session:PG_ASYNC_SESSION,data:DeleteSupplierSchema=Depends()):
    return await HandleSupplierRequest(session=session).delete(data=data)


# Read methods

@router.get('/by/shop/{shop_id}')
async def getby_shop_id(session:PG_ASYNC_SESSION,data:GetSupplierByShopIdSchema=Depends()):
    return await HandleSupplierRequest(session=session).getby_shop_id(data=data)

@router.get('/by/{shop_id}/{id}')
async def get(session:PG_ASYNC_SESSION,data:GetSupplierById=Depends()):
    return await HandleSupplierRequest(session=session).getby_id(data=data)

@router.get('')
async def get(session:PG_ASYNC_SESSION,data:GetAllSupplierSchema=Depends()):
    return await HandleSupplierRequest(session=session).get(data=data)



