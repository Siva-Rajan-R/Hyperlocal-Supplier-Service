from fastapi import APIRouter,HTTPException,Query,Depends
from typing import Annotated
from infras.primary_db.main import get_pg_async_session,AsyncSession
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from core.utils.validate_fields import validate_fields
from ...handlers.supplier_handler import HandleSupplierRequest,CreateSupplierSchema,UpdateSupplierSchema
from typing import Optional,List
print(TimeZoneEnum)

router=APIRouter(
    tags=['Supplier CRUD'],
    prefix='/suppliers'
)

PG_ASYNC_SESSION=Annotated[AsyncSession,Depends(get_pg_async_session)]
SHOP_ID="12345567"

# Write methods
@router.post('/')
async def create(data:CreateSupplierSchema,session:PG_ASYNC_SESSION):
    return await HandleSupplierRequest(session=session).create(data=data)

@router.put('/')
async def update(data:UpdateSupplierSchema,session:PG_ASYNC_SESSION):
    return await HandleSupplierRequest(session=session).update(data=data)

@router.delete('/{supplier_id}')
async def delete(supplier_id:str,session:PG_ASYNC_SESSION):
    return await HandleSupplierRequest(session=session).delete(supplier_id=supplier_id,shop_id=SHOP_ID)


# Read methods
@router.get('/search')
async def search(session:PG_ASYNC_SESSION,q:str=Query(...),limit:Optional[int]=Query(5)):
    return await HandleSupplierRequest(session=session).search(query=q,limit=limit)

@router.get('/by/{supplier_id}')
async def get(session:PG_ASYNC_SESSION,supplier_id:str,timezone:Optional[TimeZoneEnum]=Query(TimeZoneEnum.Asia_Kolkata)):
    return await HandleSupplierRequest(session=session).getby_id(supplier_id=supplier_id,shop_id=SHOP_ID,timezone=timezone)

@router.get('/')
async def get(session:PG_ASYNC_SESSION,timezone:Optional[TimeZoneEnum]=Query(TimeZoneEnum.Asia_Kolkata),q:Optional[str]=Query(''),limit:Optional[int]=Query(10),offset:int=Query(1)):
    return await HandleSupplierRequest(session=session).get(
        query=q,
        limit=limit,
        offset=offset,
        timezone=timezone
    )


