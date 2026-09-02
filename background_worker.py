import os
from arq.connections import RedisSettings
from infras.primary_db.services.supplier_export_service import process_supplier_export

redis_url = os.getenv("PLATFORM_REDIS_URL") or "redis://localhost:6379"
redis_settings = RedisSettings.from_dsn(redis_url)

async def export_suppliers_task(ctx, payload: dict):
    return await process_supplier_export(payload)

async def startup(ctx):
    pass

async def shutdown(ctx):
    pass

class WorkerSettings:
    queue_name = "supplier_export_queue"
    redis_settings = redis_settings
    functions = [export_suppliers_task]
    on_startup = startup
    on_shutdown = shutdown

