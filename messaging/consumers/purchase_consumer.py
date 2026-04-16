from models.messaging_models.consumer_model import BaseConsumerModel
from hyperlocal_platform.core.typed_dicts.messaging_typdict import SuccessMessagingTypDict,EventPublishingTypDict
from hyperlocal_platform.core.enums.routingkey_enum import RoutingkeyActions,RoutingkeyState,RoutingkeyVersions
from core.errors.messaging_errors import ErrorTypeSEnum,BussinessError,FatalError,RetryableError,SagaStateErrorTypDict
from infras.primary_db.main import AsyncSupplierLocalSession
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from hyperlocal_platform.core.utils.routingkey_builder import generate_routingkey
from infras.primary_db.services.supplier_service import SupplierService
from hyperlocal_platform.core.utils.exception_serializer import serialize_exception
from schemas.v1.request_schema.supplier_schema import CreateSupplierSchema,UpdateSupplierSchema
from hyperlocal_platform.core.typed_dicts.saga_status_typ_dict import SagaStateErrorTypDict
from hyperlocal_platform.core.typed_dicts.messaging_typdict import EventPublishingTypDict,SuccessMessagingTypDict
from icecream import ic

class PurchaseConsumer(BaseConsumerModel):
    async def create(self)->SuccessMessagingTypDict:
        compensation_payload=EventPublishingTypDict(
            exchange_name="suppliers.purchase.products.exchange",
            routing_key=generate_routingkey(
                domain="suppliers",
                work_for="purchase",
                action=RoutingkeyActions.CREATE,
                state=RoutingkeyState.FAILED,
                version=RoutingkeyVersions.V1
            ),
            headers=self.headers,
            payload={}
        )

        emit_copensation=False

        try:
            event_data:dict=self.payload.get('data',{})
            supplier_data=event_data['data']['datas']['supplier']
            additional_data=event_data['additional_data']
            emit_copensation=True if event_data.get('products',{}).get('created_barcodes',None) else False
            res={}
            async with AsyncSupplierLocalSession() as session:
                is_exists=await SupplierService(session=session).getby_mobile_no(mobile_no=supplier_data['mobile_number'],shop_id=additional_data['shop_id'])

                if not is_exists:
                    data_toadd=CreateSupplierSchema(datas=supplier_data,shop_id=additional_data['shop_id'])
                    res=await SupplierService(session=session).create(data=data_toadd)

                    if not res:
                        raise BussinessError(
                            type=ErrorTypeSEnum.BUSSINESS_ERROR,
                            error=SagaStateErrorTypDict(
                                code=ErrorTypeSEnum.BUSSINESS_ERROR,
                                debug="May be invalid datas for the Supplier",
                                user_msg="Invalid data for the Suppliers"
                            ),
                            compensation=emit_copensation,
                            compensation_payload=compensation_payload
                        )
                ic(is_exists)
            if is_exists:
                res={'id':is_exists['id'],'datas':is_exists['datas']}
            else:
                res=res.model_dump(mode='json')
            ic(res)
            return SuccessMessagingTypDict(
                response=res,
                set_response=True,
                emit_payload=EventPublishingTypDict(
                    exchange_name='suppliers.purchase.purchase.exchange',
                    routing_key=generate_routingkey(domain='suppliers',work_for='purchase',action=RoutingkeyActions.CREATE,state=RoutingkeyState.COMPLETED,version=RoutingkeyVersions.V1),
                    payload={},
                    headers=self.headers
                ),
                emit_success=True,
                mark_completed=False
            )
        
        except (FatalError,BussinessError,RetryableError):
            raise

        except Exception as e:
            raise FatalError(
                type=ErrorTypeSEnum.FATAL_ERROR,
                error=SagaStateErrorTypDict(
                    code=ErrorTypeSEnum.FATAL_ERROR.value,
                    debug=serialize_exception(e),
                    user_msg="Something weent wrong, please try again later"
                ),
                compensation_payload=compensation_payload,
                compensation=emit_copensation
            )
        


    async def update(self):
        await self.create()
        
    async def revoke(self):
        event_data:dict=self.payload.get('data',{})
        supplier_data:dict=event_data.get('suppliers',{})
        additional_data=event_data.get('additional_data')
        created_barcodes=True if event_data.get('products',{}).get('created_barcodes',None) else False


        async with AsyncSupplierLocalSession() as session:
            if len(supplier_data)>0:
                await SupplierService(session=session).delete(supplier_id=supplier_data.get('id',''),shop_id=additional_data['shop_id'])
            

        compensation_payload=EventPublishingTypDict(
            exchange_name="suppliers.purchase.products.exchange",
            routing_key=generate_routingkey(
                domain="suppliers",
                work_for="purchase",
                action=RoutingkeyActions.CREATE,
                state=RoutingkeyState.FAILED,
                version=RoutingkeyVersions.V1
            ),
            headers=self.headers,
            payload={}
        )

        mark_completed=created_barcodes

        return SuccessMessagingTypDict(
            response={},
            set_response=False,
            emit_payload=compensation_payload,
            emit_success=mark_completed,
            mark_completed=mark_completed
        )
    

    

    async def delete(self):
        ...