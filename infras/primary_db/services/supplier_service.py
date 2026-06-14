from ..main import AsyncSession
from ..repos.supplier_repo import SupplierRepo
from schemas.v1.db_schemas.supplier_schema import CreateSupplierDbSchema,UpdateSupplierDbSchema
from schemas.v1.request_schemas.supplier_schema import CreateSupplierSchema,UpdateSupplierSchema,DeleteSupplierSchema,GetAllSupplierSchema,GetSupplierById,GetSupplierByShopIdSchema,VerifySupplierSchema
from models.service_models.base_service_model import BaseServiceModel
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict,ErrorResponseTypDict,BaseResponseTypDict
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from hyperlocal_platform.core.utils.uuid_generator import generate_uuid
from core.decorators.error_handler_dec import catch_errors
from typing import Optional,List
from icecream import ic
import httpx

ACTIVITY_LOG_URL = "http://127.0.0.1:8001/activity-logs"

async def _send_activity_log(shop_id: str, action: str, entity_id: str, description: str, changes: list = None):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(ACTIVITY_LOG_URL, json={
                "shop_id": shop_id,
                "user_name": "siva",
                "service": "Supplier",
                "action": action,
                "entity_type": "Supplier",
                "entity_id": entity_id,
                "description": description,
                "changes": changes or []
            })
    except Exception as e:
        ic(f"Failed to log activity: {e}")



class SupplierService(BaseServiceModel):
    def __init__(self, session:AsyncSession):
        super().__init__(session)
        self.supplier_repo_obj=SupplierRepo(session=session)

    async def create(self,data:CreateSupplierSchema)-> dict | None:
        
        supplier_id:str=generate_uuid()
        shop_id = data.shop_id
        supplier_name = data.name
        ic(data.datas)
        from infras.read_db.repos.shopidconfig_repo import ShopIdConfigReadDbRepo
        from core.utils.id_formatter import format_ui_id
        
        shop_config = await ShopIdConfigReadDbRepo.get_config(shop_id)
        sup_config = shop_config.get("supplier", {})
        prefix = sup_config.get("prefix", "SUP")
        start_from = sup_config.get("start_from", 1)
        
        raw_sequence = await self.supplier_repo_obj.get_next_sequence(shop_id, start_from)
        ui_id_str = format_ui_id(prefix, start_from, raw_sequence)

        data=CreateSupplierDbSchema(
            **data.model_dump(mode="json",exclude_none=True,exclude_unset=True),
            id=supplier_id,
            ui_id=ui_id_str
        )

        res=await self.supplier_repo_obj.create(data=data)
        if res:
            res = dict(res)
            await _send_activity_log(
                shop_id=shop_id,
                action="CREATE",
                entity_id=supplier_id,
                description=f"Created new supplier: {supplier_name}",
                changes=[{"field": "name", "before": "", "after": str(supplier_name)}]
            )
        return res
    
    async def update(self,data:UpdateSupplierSchema)-> dict | None:
        # Fetch old supplier to compare changes
        old_supplier = await self.supplier_repo_obj.getby_id(GetSupplierById(id=data.id, shop_id=data.shop_id))
        data_db=UpdateSupplierDbSchema(**data.model_dump(mode="json",exclude_unset=True,exclude_none=True))
        res=await self.supplier_repo_obj.update(data=data_db)
        if res and old_supplier:
            res = dict(res)
            changes_list = []
            desc_changes = []
            for k, v in data.model_dump(exclude_none=True, exclude_unset=True).items():
                if k not in ["id", "shop_id"] and k in old_supplier and str(old_supplier[k]) != str(v):
                    desc_changes.append(f"{k} prv({old_supplier[k]}) after ({v})")
                    changes_list.append({"field": k, "before": str(old_supplier[k]), "after": str(v)})
            if desc_changes:
                await _send_activity_log(
                    shop_id=data.shop_id,
                    action="UPDATE",
                    entity_id=data.id,
                    description=f"Updated supplier: {', '.join(desc_changes)}",
                    changes=changes_list
                )
        return res

    async def delete(self,data:DeleteSupplierSchema)-> dict | None:
        old_supplier = await self.supplier_repo_obj.getby_id(GetSupplierById(id=data.id, shop_id=data.shop_id))
        res=await self.supplier_repo_obj.delete(data=data)
        if res:
            res = dict(res)
            supplier_name = old_supplier.get('name', 'Unknown') if old_supplier else 'Unknown'
            await _send_activity_log(
                shop_id=data.shop_id,
                action="DELETE",
                entity_id=data.id,
                description=f"Deleted supplier: {supplier_name}",
                changes=[{"field": "name", "before": str(supplier_name), "after": "DELETED"}]
            )
        return res


    async def get(self,data:GetAllSupplierSchema)-> dict:
        res=await self.supplier_repo_obj.get(data=data)
        if data.offset in (0, 1):
            overall_values = await self.supplier_repo_obj.get_overall_values(data=data)
            return {
                "overall_datas": overall_values,
                "datas": res
            }
        return {"datas": res}


    async def getby_id(self,data:GetSupplierById)-> dict | None:
        res=await self.supplier_repo_obj.getby_id(data=data)
        if res:
            res = dict(res)
        return res
    
    async def getby_shop_id(self,data:GetSupplierByShopIdSchema)-> dict:
        res=await self.supplier_repo_obj.getby_shop_id(data=data)
        if data.offset in (0, 1):
            overall_values = await self.supplier_repo_obj.get_overall_values(data=data)
            return {
                "overall_datas": overall_values,
                "datas": res
            }
        return {"datas": res}
    
    async def verify(self,data:VerifySupplierSchema)-> dict:
        res=await self.supplier_repo_obj.verify(data=data)
        return res

    

    async def search(self, shop_id: str, query:str, limit:Optional[int]=5):
        res=await self.supplier_repo_obj.search(shop_id=shop_id, query=query,limit=limit)
        return res