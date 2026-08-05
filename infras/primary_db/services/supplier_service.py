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

async def _send_activity_log(shop_id: str, action: str, entity_id: str, description: str, changes: list = None, entity_name: str = ""):
    try:
        from messaging.main import RabbitMQMessagingConfig
        rabbitmq_msg_obj = RabbitMQMessagingConfig()
        await rabbitmq_msg_obj.publish_event(
            routing_key="activity_logs.routing.key",
            exchange_name="activity_logs.exchange",
            payload={
                "shop_id": shop_id,
                "user_name": "Hyperlocal-User",
                "service": "SUPPLIER",
                "action": action,
                "entity_type": "SUPPLIER",
                "entity_id": str(entity_id),
                "entity_name": str(entity_name),
                "description": description,
                "changes": changes or []
            },
            headers={}
        )
    except Exception as e:
        ic(f"Failed to log activity: {e}")



class SupplierService:
    def __init__(self, session:AsyncSession):
        self.session=session
        self.supplier_repo_obj=SupplierRepo(session=session)
        self.supplier_stats_repo_obj=SupplierStatsRepo


    # @start_db_transaction
    async def create(self,data:CreateSupplierSchema)-> dict | None:
        # Check if supplier already exists with the same mobile_number or email in this shop
        from sqlalchemy import select, or_
        from infras.primary_db.models.supplier_model import Suppliers
        
        email = data.contact_infos.email if data.contact_infos else None
        mobile_number = data.contact_infos.mobile_number if data.contact_infos else None
        
        conditions = []
        if email:
            conditions.append(Suppliers.contact_infos['email'].astext == email)
        if mobile_number:
            conditions.append(Suppliers.contact_infos['mobile_number'].astext == mobile_number)
            
        if conditions:
            stmt = select(Suppliers).where(
                Suppliers.shop_id == data.shop_id,
                or_(*conditions)
            )
            existing_sup = (await self.session.execute(stmt)).scalars().first()
            if existing_sup:
                raise HTTPException(
                    status_code=400,
                    detail=ErrorResponseTypDict(
                        msg="Error : Creating Supplier",
                        description="Supplier with this email or mobile number already exists in this shop",
                        success=False,
                        status_code=400
                    )
                )

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

        if data.custom_fields:
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
            try:
                await self.supplier_stats_repo_obj.update_stats(
                    data=SupplierStatsSchema(
                        total_outstanding=0,
                        total_suppliers=1
                    )
                )
            except Exception as e:
                ic(f"Failed to update supplier stats in Read DB: {e}")
            try:
                from messaging.main import RabbitMQMessagingConfig
                rabbitmq_msg_obj = RabbitMQMessagingConfig()
                
                analytics_payload = {
                    "shop_id": data.shop_id,
                    "entity_name": "SUPPLIER",
                    "entity_id": str(supplier_id),
                    "action": "CREATE"
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

            
            try:
                supp_name = getattr(data, 'name', None) or 'Supplier'
                from messaging.main import RabbitMQMessagingConfig
                rabbitmq_msg_obj = RabbitMQMessagingConfig()
                await rabbitmq_msg_obj.publish_event(
                    routing_key="activity_logs.routing.key",
                    exchange_name="activity_logs.exchange",
                    payload={
                        "shop_id": data.shop_id,
                        "user_name": "Hyperlocal-User",
                        "service": "SUPPLIER",
                        "action": "CREATED",
                        "entity_type": "SUPPLIER",
                        "entity_id": str(supplier_id),
                        "entity_name": str(supp_name),
                        "description": f"Created Supplier {supp_name} ({supplier_id})",
                        "changes": []
                    },
                    headers={}
                )
            except Exception as e:
                ic(f"Failed to publish activity log: {e}")

        await self.session.commit()
        return res
    

    async def create_bulk(self, data: List[CreateSupplierSchema]) -> List[dict]:
        results = []
        for item in data:
            try:
                res = await self.create(data=item)
                if res:
                    results.append(res)
            except Exception as e:
                ic(f"Error creating bulk supplier item: {e}")
        return results
    
    # @start_db_transaction
    async def update(self,data:UpdateSupplierSchema)-> dict | None:
        # Fetch old supplier to compare changes
        supplier_get_res = await self.supplier_repo_obj.getby_id(GetSupplierById(id=data.id, shop_id=data.shop_id))
        if not supplier_get_res:
            ic("The give supplier doesn't exists")
            return False

        # Parse existing database objects
        existing_location = supplier_get_res.get("location_infos") or {}
        existing_contact = supplier_get_res.get("contact_infos") or {}
        existing_contact_person = supplier_get_res.get("contact_person_infos") or {}

        # Merge new attributes into database objects
        merged_location = None
        if data.location_infos is not None:
            new_loc_dict = data.location_infos.model_dump(exclude_unset=True, exclude_none=True) if hasattr(data.location_infos, 'model_dump') else data.location_infos
            merged_location = {**existing_location, **new_loc_dict}

        merged_contact = None
        if data.contact_infos is not None:
            new_contact_dict = data.contact_infos.model_dump(exclude_unset=True, exclude_none=True) if hasattr(data.contact_infos, 'model_dump') else data.contact_infos
            merged_contact = {**existing_contact, **new_contact_dict}

        merged_contact_person = None
        if data.contact_person_infos is not None:
            new_contact_p_dict = data.contact_person_infos.model_dump(exclude_unset=True, exclude_none=True) if hasattr(data.contact_person_infos, 'model_dump') else data.contact_person_infos
            merged_contact_person = {**existing_contact_person, **new_contact_p_dict}

        # Build final update schema
        final_data = UpdateSupplierDbSchema(
            id=data.id,
            shop_id=data.shop_id,
            name=data.name if data.name is not None else supplier_get_res.get("name"),
            gst_no=data.gst_no if data.gst_no is not None else supplier_get_res.get("gst_no"),
            additional_infos=data.additional_infos if data.additional_infos is not None else supplier_get_res.get("additional_infos"),
            location_infos=merged_location if merged_location is not None else existing_location,
            contact_infos=merged_contact if merged_contact is not None else existing_contact,
            contact_person_infos=merged_contact_person if merged_contact_person is not None else existing_contact_person
        )

        res=await self.supplier_repo_obj.update(data=final_data) 
        if res:
            if data.custom_fields:
                cust_obj=await CustomFieldsService(session=self.session).upsert_values(
                data=CreateCustomFieldValueSchema(
                        shop_id=data.shop_id,
                        supplier_id=data.id,
                        value_infos=[
                            {'field_id':id,"value":value}
                            for id,value in data.custom_fields.items()
                        ]
                    )
                )
                ic(cust_obj)

            try:
                from messaging.main import RabbitMQMessagingConfig
                rabbitmq_msg_obj = RabbitMQMessagingConfig()
                
                def _is_empty_or_none(val):
                    if val is None: return True
                    if isinstance(val, (dict, list, set, str, tuple)) and len(val) == 0: return True
                    return str(val).strip() in ("None", "{}", "[]", "", "null", "NoneType")

                dumped_updates = data.model_dump(exclude_unset=True, exclude_none=True)
                changes = []
                for key, new_val in dumped_updates.items():
                    if key in ["id", "shop_id", "user_id", "cur_user_id"]:
                        continue
                    prev_val = supplier_get_res.get(key)
                    if _is_empty_or_none(prev_val) and _is_empty_or_none(new_val):
                        continue
                    if prev_val != new_val and str(prev_val).strip() != str(new_val).strip():
                        changes.append({
                            "field": key,
                            "before": str(prev_val) if prev_val is not None else "None",
                            "after": str(new_val) if new_val is not None else "None"
                        })

                supp_name = supplier_get_res.get("name") or getattr(data, "name", None) or "Supplier"

                await rabbitmq_msg_obj.publish_event(
                    routing_key="activity_logs.routing.key",
                    exchange_name="activity_logs.exchange",
                    payload={
                        "shop_id": data.shop_id,
                        "user_name": "Hyperlocal-User",
                        "service": "SUPPLIER",
                        "action": "UPDATED",
                        "entity_type": "SUPPLIER",
                        "entity_id": str(data.id),
                        "entity_name": str(supp_name),
                        "description": f"Updated Supplier {supp_name} ({data.id})",
                        "changes": changes
                    },
                    headers={}
                )

                analytics_payload = {
                    "shop_id": data.shop_id,
                    "entity_name": "SUPPLIER",
                    "entity_id": str(data.id),
                    "action": "UPDATE"
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
                ic(f"Failed to publish activity log/analytics: {e}")

        await self.session.commit()
        return res

    # @start_db_transaction
    async def delete(self,data:DeleteSupplierSchema)-> dict | None:
        supplier_get_res=await self.supplier_repo_obj.getby_id(data=GetSupplierById(shop_id=data.shop_id,id=data.id))
        if not supplier_get_res:
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

            supp_name = supplier_get_res.get("name") or "Supplier"

            try:
                from messaging.main import RabbitMQMessagingConfig
                rabbitmq_msg_obj = RabbitMQMessagingConfig()
                await rabbitmq_msg_obj.publish_event(
                    routing_key="activity_logs.routing.key",
                    exchange_name="activity_logs.exchange",
                    payload={
                        "shop_id": data.shop_id,
                        "user_name": "Hyperlocal-User",
                        "service": "SUPPLIER",
                        "action": "DELETED",
                        "entity_type": "SUPPLIER",
                        "entity_id": str(data.id),
                        "entity_name": str(supp_name),
                        "description": f"Deleted Supplier {supp_name} ({data.id})",
                        "changes": []
                    },
                    headers={}
                )

                analytics_payload = {
                    "shop_id": data.shop_id,
                    "entity_name": "SUPPLIER",
                    "entity_id": str(data.id),
                    "action": "DELETE"
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
                ic(f"Failed to publish events: {e}")

        await self.session.commit()
        return res
    
    # @start_db_transaction
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
            cur_outst_amt=max(0.0, prev_outst_amt - data.outstanding_infos.amount)
        
        original_cleared_amt = data.cleared_amount if data.cleared_amount is not None else data.outstanding_infos.amount
        outst_amt_for_history = data.outstanding_amount if data.outstanding_amount is not None else cur_outst_amt

        updated_outstanding_infos = SupplierOutstandingInfosType(amount=cur_outst_amt)

        final_data=UpdateOutstandingSupplierSchema(
            outstanding_infos=updated_outstanding_infos,
            outstanding_amount=outst_amt_for_history,
            cleared_amount=original_cleared_amt,
            **data.model_dump(exclude=["outstanding_infos", "outstanding_amount", "cleared_amount"])
        )

        res=await self.supplier_repo_obj.update_outstanding(data=final_data)

        ic(res)

        if res:
            total_outst=data.outstanding_infos.amount
            ic(total_outst)
            if data.type==SupplierOutstandingUpdateTypeEnums.DECREMENT:
                total_outst=-total_outst
            

            await self.supplier_stats_repo_obj.update_stats(
                data=SupplierStatsSchema(
                    total_outstanding=total_outst,
                    total_suppliers=0
                )
            )

            try:
                from messaging.main import RabbitMQMessagingConfig
                rabbitmq_msg_obj = RabbitMQMessagingConfig()
                analytics_payload = {
                    "shop_id": data.shop_id,
                    "entity_name": "SUPPLIER",
                    "entity_id": str(data.id),
                    "action": "UPDATE"
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
                ic(f"Failed to publish analytics event on supplier update_outstanding: {e}")

        await self.session.commit()
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

    async def get_outstanding_history(self, supplier_id: str, shop_id: str):
        return await self.supplier_repo_obj.get_outstanding_history(supplier_id=supplier_id, shop_id=shop_id)