from ..main import AsyncSession
from ..repos.supplier_repo import SupplierRepo
from schemas.v1.supplier_schemas.request_schemas import CreateSupplierSchema,UpdateOutstandingSupplierSchema,UpdateSupplierSchema,DeleteSupplierSchema,GetAllSupplierSchema,GetSupplierById,GetSupplierByShopIdSchema
from schemas.v1.supplier_schemas.db_schemas import CreateSupplierDbSchema,UpdateSupplierDbSchema,DeleteSupplierDbSchema
from schemas.v1.supplier_schemas.custom_types import SupplierOutstandingInfosType
from models.service_models.base_service_model import BaseServiceModel
from core.data_formats.enums.supplier_enums import SupplierOutstandingUpdateTypeEnums
from hyperlocal_platform.core.models.req_res_models import SuccessResponseTypDict,ErrorResponseTypDict,BaseResponseTypDict
from fastapi.exceptions import HTTPException
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from hyperlocal_platform.core.utils.uuid_generator import generate_uuid
from core.decorators.error_handler_dec import catch_errors
from typing import Optional,List
from icecream import ic
import httpx
from ...read_db.repos.supplier_repo import SupplierStatsRepo
from ...read_db.models.supplier_model import SupplierStatsSchema
from integrations.utility_service import get_ui_id, get_shop_category, get_shop_unit
from .customfield_service import CustomFieldsService,CreateCustomFieldDbSchema,CreateCustomFieldSchema,CreateCustomFieldValueSchema

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



class SupplierService:
    def __init__(self, session:AsyncSession):
        self.session=session
        self.supplier_repo_obj=SupplierRepo(session=session)
        self.supplier_stats_repo_obj=SupplierStatsRepo


    async def create(self,data:CreateSupplierSchema)-> dict | None:
        
        supplier_id:str=generate_uuid()
        ui_id = None
        ui_id_res = await get_ui_id(shop_id=data.shop_id)
        if isinstance(ui_id_res, dict) and "prefix" in ui_id_res:
            ui_id = f"{ui_id_res.get('prefix')}-{ui_id_res.get('current_number')}"
        else:
            return False

        final_data=CreateSupplierDbSchema(
            **data.model_dump(mode="json",exclude_none=True,exclude_unset=True),
            id=supplier_id,
            ui_id=ui_id
        )



        res=await self.supplier_repo_obj.create(data=final_data)
        ic(res)

        cust_obj=await CustomFieldsService(session=self.session).upsert_values(
        data=CreateCustomFieldValueSchema(
                shop_id=data.shop_id,
                supplier_id=supplier_id,
                value_infos=[
                    {'field_id':id,"value":value}
                    for id,value in data.custom_fields.items()
                ]
            )
        )
        ic(cust_obj)
        if res:
            await self.supplier_stats_repo_obj.update_stats(
                data=SupplierStatsSchema(
                    total_outstanding=0,
                    total_suppliers=1
                )
            )
            try:
                from messaging.main import RabbitMQMessagingConfig
                rabbitmq_msg_obj = RabbitMQMessagingConfig()
                
                analytics_payload = {
                    "shop_id": data.shop_id,
                    "datas": [
                        {
                            "supplier_id": supplier_id,
                            "outstanding_amounts": 0,
                            "cleared_amounts": 0
                        }
                    ]
                }
                
                await rabbitmq_msg_obj.publish_event(
                    routing_key="analytics.service.routing.key",
                    exchange_name="analytics.service.exchange",
                    payload=analytics_payload,
                    headers={
                        "entity_name": "supplier_event",
                        "service_name": "ANALYTICS",
                        "saga_id": "none",
                        "reply_key": "none",
                        "reply_exchange": "none",
                        "reply_entity_name": "none",
                        "body": analytics_payload
                    }
                )
            except Exception as e:
                ic(f"Failed to publish analytics event: {e}")

        return res
    
    async def update(self,data:UpdateSupplierSchema)-> dict | None:
        # Fetch old supplier to compare changes
        supplier_get_res = await self.supplier_repo_obj.getby_id(GetSupplierById(id=data.id, shop_id=data.shop_id))
        if not supplier_get_res:
            ic("The give supplier doesn't exists")
            return False
        final_data=UpdateSupplierDbSchema(**data.model_dump(mode="json",exclude_unset=True,exclude_none=True))
        res=await self.supplier_repo_obj.update(data=final_data)
        
        return res

    async def delete(self,data:DeleteSupplierSchema)-> dict | None:
        supplier_get_res=await self.supplier_repo_obj.getby_id(data=GetSupplierById(shop_id=data.shop_id,id=data.id))
        if supplier_get_res:
            ic("The given supplier info doesnt exists")
            return False
        
        final_data=DeleteSupplierDbSchema(**data.model_dump())
        res=await self.supplier_repo_obj.delete(data=final_data)
        if res:
            total_outstanding=supplier_get_res.get("outstanding_infos").get("amount",0) if supplier_get_res.get("outstanding_infos") else 0
            await self.supplier_stats_repo_obj.update_stats(
                data=SupplierStatsSchema(
                    total_outstanding=-total_outstanding,
                    total_suppliers=-1
                )
            )

        return res
    
    async def update_outstanding(self,data:UpdateOutstandingSupplierSchema):
        supplier_get_res=await self.supplier_repo_obj.getby_id(data=GetSupplierById(shop_id=data.shop_id,id=data.id))
        if not supplier_get_res:
            ic("The give supplier doesn't exists")
            return False
        
        prev_outst_amt=supplier_get_res.get('outstanding_infos').get("amount",0) if supplier_get_res.get('outstanding_infos') else 0
        cur_outst_amt=data.outstanding_infos.amount

        if data.type==SupplierOutstandingUpdateTypeEnums.INCREMENT:
            cur_outst_amt=cur_outst_amt+prev_outst_amt
        
        elif data.type==SupplierOutstandingUpdateTypeEnums.DECREMENT:
            cur_outst_amt=abs(cur_outst_amt-prev_outst_amt)
        
        outstanding_infos=SupplierOutstandingInfosType(amount=cur_outst_amt)

        final_data=UpdateOutstandingSupplierSchema(
            outstanding_infos=outstanding_infos,
            **data.model_dump(exclude=["outstanding_infos"])
        )

        res=await self.supplier_repo_obj.update_outstanding(data=final_data)

        ic(res)

        if res:
            total_outst=data.outstanding_infos.amount
            ic(total_outst)
            if data.type==SupplierOutstandingUpdateTypeEnums.DECREMENT:
                total_outst=-total_outst
            
            ic(total_outst,"/////////////////////////////")
            await self.supplier_stats_repo_obj.update_stats(
                data=SupplierStatsSchema(
                    total_outstanding=total_outst,
                    total_suppliers=0
                )
            )

        return res
    



    async def get(self,data:GetAllSupplierSchema)-> dict:
        res=await self.supplier_repo_obj.get(data=data)
        return res


    async def getby_id(self,data:GetSupplierById)-> dict | None:
        res=await self.supplier_repo_obj.getby_id(data=data)
        if res:
            res = dict(res)
        return res
    
    async def getby_shop_id(self,data:GetSupplierByShopIdSchema)-> dict:
        res=await self.supplier_repo_obj.getby_shop_id(data=data)
        return res