from ..models.supplier_model import SupplierStatsSchema
from ..collections.supplier_collection import supplier_collection


class SupplierStatsRepo:
    @staticmethod
    async def update_stats(data:SupplierStatsSchema):
        final_data=data.model_dump(mode="json",exclude_none=True)
        supplier_db=supplier_collection()
        await supplier_db.update_one(
            {"_id":"supplier_collections"},
            {
                "$inc":final_data
            },
            upsert=True
        )

        return True