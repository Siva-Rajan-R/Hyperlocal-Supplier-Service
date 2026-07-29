from .. import main
from motor.motor_asyncio import AsyncIOMotorClient


def supplier_collection():
    if main.READ_DATABASE is None:
        main.CLIENT = AsyncIOMotorClient(main.READ_DB_URL)
        main.READ_DATABASE = main.CLIENT['SupplierServiceReadDb']
    return main.READ_DATABASE['SupplierCollections']