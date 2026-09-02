from fastapi import APIRouter,HTTPException,Query,Depends
from typing import Annotated
from infras.primary_db.main import get_pg_async_session,AsyncSession
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from core.utils.validate_fields import validate_fields
from ...handlers.supplier_handler import HandleSupplierRequest
from schemas.v1.supplier_schemas.request_schemas import CreateSupplierSchema,UpdateOutstandingSupplierSchema,UpdateSupplierSchema,DeleteSupplierSchema,GetAllSupplierSchema,GetSupplierById,GetSupplierByShopIdSchema
from typing import Optional,List
print(TimeZoneEnum)

router=APIRouter(
    tags=['Supplier CRUD'],
    prefix='/suppliers'
)

PG_ASYNC_SESSION=Annotated[AsyncSession,Depends(get_pg_async_session)]
SHOP_ID="TEST-SHOP"

# Write methods
@router.post('')
async def create(data:CreateSupplierSchema,session:PG_ASYNC_SESSION):
    return await HandleSupplierRequest(session=session).create(data=data)


@router.post('/bulk')
async def create_bulk(data:List[CreateSupplierSchema],session:PG_ASYNC_SESSION):
    return await HandleSupplierRequest(session=session).create_bulk(data=data)

@router.put('')
async def update(data:UpdateSupplierSchema,session:PG_ASYNC_SESSION):
    return await HandleSupplierRequest(session=session).update(data=data)

@router.delete('/{shop_id}/{id}')
async def delete(session:PG_ASYNC_SESSION,data:DeleteSupplierSchema=Depends()):
    return await HandleSupplierRequest(session=session).delete(data=data)

@router.put('/outstanding')
async def update_outstanding(session:PG_ASYNC_SESSION,data:UpdateOutstandingSupplierSchema):
    return await HandleSupplierRequest(session=session).update_outstanding(data=data)


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

@router.get('/cleared-history/{shop_id}/{supplier_id}')
async def get_outstanding_history(shop_id: str, supplier_id: str, session: PG_ASYNC_SESSION):
    return await HandleSupplierRequest(session=session).get_outstanding_history(supplier_id=supplier_id, shop_id=shop_id)


# --- Export Routes ---
from schemas.v1.export_schemas import ExportDataRequestSchema
from arq import create_pool
from arq.connections import RedisSettings
import json, os, uuid
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict, BaseResponseTypDict
import redis.asyncio as aioredis

REDIS_URL = os.getenv("PLATFORM_REDIS_URL") or "redis://localhost:6379"

@router.post('/export')
async def export_suppliers(data: ExportDataRequestSchema):
    job_id = str(uuid.uuid4())
    payload = data.model_dump()
    payload["job_id"] = job_id
    
    redis = await create_pool(RedisSettings.from_dsn(REDIS_URL))
    await redis.enqueue_job("export_suppliers_task", payload, _job_id=job_id, _queue_name="supplier_export_queue")
    await redis.close()

    
    # Store initial state in Redis
    redis_client = aioredis.Redis.from_url(REDIS_URL, decode_responses=True)
    await redis_client.set(
        f"EXPORT_JOB:{job_id}",
        json.dumps({
            "job_id": job_id,
            "entity": "SUPPLIER",
            "status": "QUEUED",
            "params": payload
        }),
        ex=86400
    )
    await redis_client.aclose()
    
    return SuccessResponseTypDict(
        detail=BaseResponseTypDict(
            msg="Supplier export job scheduled successfully in the background",
            status_code=202,
            success=True
        ),
        data={
            "job_id": job_id,
            "entity": "SUPPLIER",
            "status": "QUEUED"
        }
    )

@router.get('/export/status/{job_id}')
async def get_supplier_export_status(job_id: str):
    redis_client = aioredis.Redis.from_url(REDIS_URL, decode_responses=True)
    raw = await redis_client.get(f"EXPORT_JOB:{job_id}")
    await redis_client.aclose()
    
    if not raw:
        raise HTTPException(status_code=404, detail="Export job not found")
        
    return SuccessResponseTypDict(
        detail=BaseResponseTypDict(
            msg="Export status fetched successfully",
            status_code=200,
            success=True
        ),
        data=json.loads(raw)
    )


