from fastapi import FastAPI
from api.routers.v1 import supplier_routes
from infras.primary_db.main import init_pg_db
from contextlib import asynccontextmanager
from icecream import ic
from dotenv import load_dotenv
import os,asyncio
from core.configs.settings_config import SETTINGS
from messaging.worker import worker
from hyperlocal_platform.core.enums.environment_enum import EnvironmentEnum
load_dotenv()


@asynccontextmanager
async def supplier_service_lifespan(app:FastAPI):
    try:
        ic("Starting supplier service...")
        await init_pg_db()
        asyncio.create_task(worker())
        yield

    except Exception as e:
        ic(f"Error : Starting supplier service => {e}")

    finally:
        ic("...Stoping supplier Servcie...")

debug=False
openapi_url=None
docs_url=None
redoc_url=None

if SETTINGS.ENVIRONMENT.value==EnvironmentEnum.DEVELOPMENT.value:
    debug=True
    openapi_url="/openapi.json"
    docs_url="/docs"
    redoc_url="/redoc"

app=FastAPI(
    title="Supplier Service",
    description="This service contains all the CRUD operations for supplier service",
    debug=debug,
    openapi_url=openapi_url,
    docs_url=docs_url,
    redoc_url=redoc_url,
    lifespan=supplier_service_lifespan
)



# Routes to include
app.include_router(supplier_routes.router)


