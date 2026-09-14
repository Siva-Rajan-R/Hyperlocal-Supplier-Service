from models.repo_models.base_repo_model import BaseRepoModel
from ..models.supplier_model import Suppliers,String
from sqlalchemy.dialects.postgresql import insert
from ..main import AsyncSession
from sqlalchemy import select,update,delete,or_,and_,func,case
from datetime import datetime, timezone
from schemas.v1.supplier_schemas.db_schemas import CreateSupplierDbSchema,UpdateSupplierDbSchema,DeleteSupplierDbSchema
from schemas.v1.supplier_schemas.request_schemas import CreateSupplierSchema,UpdateSupplierSchema,DeleteSupplierSchema,GetAllSupplierSchema,GetSupplierById,GetSupplierByShopIdSchema,UpdateOutstandingSupplierSchema,GetSupplierOutstandingHistorySchema
from typing import Optional,List
from hyperlocal_platform.core.decorators.db_session_handler_dec import start_db_transaction
from hyperlocal_platform.core.enums.timezone_enum import TimeZoneEnum
from core.decorators.error_handler_dec import catch_errors
from icecream import ic



class SupplierRepo:
    def __init__(self, session:AsyncSession):
        self.session=session
        self.supplier_cols=(
            Suppliers.id,
            Suppliers.ui_id,
            Suppliers.shop_id,
            Suppliers.sequence_id,
            Suppliers.name,
            Suppliers.location_infos,
            Suppliers.contact_infos,
            Suppliers.contact_person_infos,
            Suppliers.outstanding_infos,
            Suppliers.additional_infos,
            Suppliers.gst_no,
            Suppliers.created_at,
            Suppliers.updated_at
        )


    async def get_next_sequence(self, shop_id: str, start_from: int) -> int:
        from sqlalchemy import text
        seq_name = f"seq_supplier_{shop_id.replace('-', '_').lower()}"
        await self.session.execute(text(f"CREATE SEQUENCE IF NOT EXISTS {seq_name} START WITH {start_from}"))
        res = await self.session.execute(text(f"SELECT nextval('{seq_name}')"))
        return res.scalar_one()

    async def create(self,data:CreateSupplierDbSchema)->dict | None:
        stmt=(
            insert(
                Suppliers
            )
            .values(**data.model_dump(mode="json",exclude_none=True,exclude_unset=True))
            .returning(*self.supplier_cols)
        )
        res=(await self.session.execute(stmt)).mappings().one_or_none()
        return res
    

    async def update(self,data:UpdateSupplierDbSchema)->dict|None:
        stmt=update(
            Suppliers
        ).where(
            and_(
                Suppliers.id==data.id,
                Suppliers.shop_id==data.shop_id
            )
        ).values(**data.model_dump(mode="json",exclude_none=True,exclude_unset=True)).returning(*self.supplier_cols)

        res=(await self.session.execute(stmt)).mappings().one_or_none()
        return res
    
    @start_db_transaction
    async def delete(self, data:DeleteSupplierSchema)->dict|None:
        stmt=delete(
            Suppliers
        ).where(Suppliers.id==data.id,Suppliers.shop_id==data.shop_id).returning(*self.supplier_cols)

        res=(await self.session.execute(stmt)).mappings().one_or_none()

        return res
    

    @start_db_transaction
    async def update_outstanding(self,data:UpdateOutstandingSupplierSchema):
        if getattr(data, "clear_entity_history", False) and getattr(data, "entity_id", None):
            try:
                from ..models.supplier_model import SupplierOutstandingHistory
                from sqlalchemy import or_
                del_conds = [
                    SupplierOutstandingHistory.entity_id == data.entity_id
                ]
                if getattr(data, "invoice_no", None):
                    del_conds.append(SupplierOutstandingHistory.invoice_no == data.invoice_no)
                    del_conds.append(SupplierOutstandingHistory.entity_id == data.invoice_no)
                if data.entity_id:
                    del_conds.append(SupplierOutstandingHistory.invoice_no == data.entity_id)

                del_stmt = delete(SupplierOutstandingHistory).where(
                    SupplierOutstandingHistory.supplier_id == data.id,
                    SupplierOutstandingHistory.shop_id == data.shop_id,
                    or_(*del_conds)
                )
                await self.session.execute(del_stmt)
                await self.session.flush()
                ic("Successfully deleted supplier outstanding history records for entity:", data.entity_id)
            except Exception as ex:
                ic("Error deleting supplier outstanding history:", ex)
        elif not getattr(data, "clear_entity_history", False) and (
            getattr(data, "entity_id", None) or 
            getattr(data, "entity_name", None) or 
            (data.cleared_amount is not None and data.cleared_amount > 0) or
            getattr(data, "type", None) == SupplierOutstandingUpdateTypeEnums.DECREMENT
        ):
            try:
                from ..models.supplier_model import SupplierOutstandingHistory
                import uuid
                cl_amt = data.cleared_amount if data.cleared_amount is not None else (data.outstanding_infos.amount if data.outstanding_infos else 0.0)
                history_record = SupplierOutstandingHistory(
                    id=str(uuid.uuid4()),
                    supplier_id=data.id,
                    shop_id=data.shop_id,
                    cleared_amount=cl_amt,
                    outstanding_amount=data.outstanding_amount if data.outstanding_amount is not None else (data.outstanding_infos.amount if data.outstanding_infos else 0.0),
                    payment_method=getattr(data, "payment_method", "CASH") or "CASH",
                    entity_name=getattr(data, "entity_name", "PURCHASE") or "PURCHASE",
                    entity_id=getattr(data, "entity_id", None),
                    invoice_no=getattr(data, "invoice_no", None),
                    notes=getattr(data, "notes", None) or f"Cleared outstanding of ₹{cl_amt}"
                )
                self.session.add(history_record)
                await self.session.flush()
                ic("Successfully added supplier outstanding history record in repo transaction")
            except Exception as ex:
                ic("Error saving supplier outstanding history in repo transaction:", ex)

        stmt=(
            update(
                Suppliers
            )
            .where(
                Suppliers.id==data.id,
                Suppliers.shop_id==data.shop_id
            )
            .values(
                outstanding_infos=data.outstanding_infos.model_dump(mode='json')
            )
            .returning(*self.supplier_cols)
        )

        res=(await self.session.execute(stmt)).mappings().one_or_none()
        if not res:
            fallback_stmt=(
                update(
                    Suppliers
                )
                .where(
                    Suppliers.id==data.id
                )
                .values(
                    outstanding_infos=data.outstanding_infos.model_dump(mode='json')
                )
                .returning(*self.supplier_cols)
            )
            res=(await self.session.execute(fallback_stmt)).mappings().one_or_none()
        return res
    

    async def get(self,data:GetAllSupplierSchema)-> List[dict] | []:
        cursor=(data.offset-1)*data.limit
        conds = []
        if data.query:
            search_term = f"%{data.query}%"
            conds.append(or_(
                Suppliers.id.ilike(search_term),
                Suppliers.ui_id.ilike(search_term),
                Suppliers.name.ilike(search_term),
                Suppliers.gst_no.ilike(search_term),
                Suppliers.contact_infos['phone_number'].astext.ilike(search_term),
                Suppliers.contact_infos['email'].astext.ilike(search_term)
            ))
        if getattr(data, 'from_date', None):
            try:
                from_dt = datetime.strptime(data.from_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                conds.append(Suppliers.created_at >= from_dt)
            except Exception:
                pass
        if getattr(data, 'to_date', None):
            try:
                to_date_str = data.to_date
                if len(to_date_str) <= 10:
                    to_date_str += ' 23:59:59'
                to_dt = datetime.strptime(to_date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                conds.append(Suppliers.created_at <= to_dt)
            except Exception:
                pass

        # Outstanding filter & exclusion handling
        from sqlalchemy import Float, literal
        amount_expr = func.coalesce(func.cast(Suppliers.outstanding_infos['amount'].astext, Float), 0.0)

        exclude_outstanding = getattr(data, 'exclude_outstanding', None)
        if exclude_outstanding is None:
            exclude_outstanding = (
                getattr(data, 'exclude_outstaitng', None) or
                getattr(data, 'exclude_outstanding_suppliers', None) or
                getattr(data, 'exclude_outstating', None)
            )

        exclude_non_outstanding = getattr(data, 'exclude_non_outstanding', None)
        if exclude_non_outstanding is None:
            exclude_non_outstanding = (
                getattr(data, 'exclude_non_outstating', None) or
                getattr(data, 'exclude_no_outstanding', None) or
                getattr(data, 'exclude_zero_outstanding', None) or
                getattr(data, 'exclude_without_outstanding', None)
            )

        if exclude_outstanding is True and exclude_non_outstanding is True:
            conds.append(literal(False))
        elif exclude_outstanding is True:
            conds.append(or_(Suppliers.outstanding_infos == None, amount_expr <= 0.0))
        elif exclude_non_outstanding is True:
            conds.append(and_(Suppliers.outstanding_infos != None, amount_expr > 0.0))
        elif getattr(data, 'has_outstanding', None) is not None:
            if data.has_outstanding:
                conds.append(and_(Suppliers.outstanding_infos != None, amount_expr > 0.0))
            else:
                conds.append(or_(Suppliers.outstanding_infos == None, amount_expr <= 0.0))

        stmt=(
            select(
                *self.supplier_cols
            )
        )
        if conds:
            stmt = stmt.where(and_(*conds))
        
        stmt = stmt.order_by(Suppliers.created_at.desc()).offset(offset=cursor).limit(limit=data.limit)
        res=(await self.session.execute(stmt)).mappings().all()
        return res
    

    async def getby_shop_id(self,data:GetSupplierByShopIdSchema)-> List[dict] | []:
        cursor=(data.offset-1)*data.limit
        conds = [Suppliers.shop_id==data.shop_id]
        if data.query:
            search_term = f"%{data.query}%"
            conds.append(or_(
                Suppliers.id.ilike(search_term),
                Suppliers.ui_id.ilike(search_term),
                Suppliers.name.ilike(search_term),
                Suppliers.gst_no.ilike(search_term),
                Suppliers.contact_infos['phone_number'].astext.ilike(search_term),
                Suppliers.contact_infos['email'].astext.ilike(search_term)
            ))
        if getattr(data, 'from_date', None):
            try:
                from_dt = datetime.strptime(data.from_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                conds.append(Suppliers.created_at >= from_dt)
            except Exception:
                pass
        if getattr(data, 'to_date', None):
            try:
                to_date_str = data.to_date
                if len(to_date_str) <= 10:
                    to_date_str += ' 23:59:59'
                to_dt = datetime.strptime(to_date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                conds.append(Suppliers.created_at <= to_dt)
            except Exception:
                pass

        # Outstanding filter & exclusion handling
        from sqlalchemy import Float, literal
        amount_expr = func.coalesce(func.cast(Suppliers.outstanding_infos['amount'].astext, Float), 0.0)

        exclude_outstanding = getattr(data, 'exclude_outstanding', None)
        if exclude_outstanding is None:
            exclude_outstanding = (
                getattr(data, 'exclude_outstaitng', None) or
                getattr(data, 'exclude_outstanding_suppliers', None) or
                getattr(data, 'exclude_outstating', None)
            )

        exclude_non_outstanding = getattr(data, 'exclude_non_outstanding', None)
        if exclude_non_outstanding is None:
            exclude_non_outstanding = (
                getattr(data, 'exclude_non_outstating', None) or
                getattr(data, 'exclude_no_outstanding', None) or
                getattr(data, 'exclude_zero_outstanding', None) or
                getattr(data, 'exclude_without_outstanding', None)
            )

        if exclude_outstanding is True and exclude_non_outstanding is True:
            conds.append(literal(False))
        elif exclude_outstanding is True:
            conds.append(or_(Suppliers.outstanding_infos == None, amount_expr <= 0.0))
        elif exclude_non_outstanding is True:
            conds.append(and_(Suppliers.outstanding_infos != None, amount_expr > 0.0))
        elif getattr(data, 'has_outstanding', None) is not None:
            if data.has_outstanding:
                conds.append(and_(Suppliers.outstanding_infos != None, amount_expr > 0.0))
            else:
                conds.append(or_(Suppliers.outstanding_infos == None, amount_expr <= 0.0))

        stmt=(
            select(
                *self.supplier_cols
            )
            .where(and_(*conds))
            .order_by(Suppliers.created_at.desc())
            .offset(offset=cursor).limit(limit=data.limit)
        )

        res=(await self.session.execute(stmt)).mappings().all()
        return res

    async def getby_id(self,data:GetSupplierById)-> dict:
        stmt=(
            select(
                *self.supplier_cols
            )
            .where(
                or_(Suppliers.id == data.id, Suppliers.ui_id == data.id),
                Suppliers.shop_id == data.shop_id
            )
        )
        res=(await self.session.execute(stmt)).mappings().one_or_none()
        if not res:
            fallback_stmt=(
                select(
                    *self.supplier_cols
                )
                .where(
                    or_(Suppliers.id == data.id, Suppliers.ui_id == data.id)
                )
            )
            res=(await self.session.execute(fallback_stmt)).mappings().one_or_none()
        return res

    async def get_outstanding_history(self, supplier_id: str, shop_id: str, data: Optional[GetSupplierOutstandingHistorySchema] = None):
        from ..models.supplier_model import SupplierOutstandingHistory
        stmt = select(SupplierOutstandingHistory).where(
            SupplierOutstandingHistory.supplier_id == supplier_id,
            SupplierOutstandingHistory.shop_id == shop_id
        ).order_by(SupplierOutstandingHistory.created_at.desc())
        records = (await self.session.execute(stmt)).scalars().all()

        exclude_cancel = False
        if data:
            exclude_cancel = any([
                getattr(data, "exclude_canceled", None) is True,
                getattr(data, "exclude_cancle", None) is True,
                getattr(data, "exclude_cancel", None) is True,
                getattr(data, "exclude_canceled_purchase", None) is True,
                getattr(data, "exclude_canceled_purchases", None) is True,
                getattr(data, "exclude_cancelled_purchases", None) is True,
                getattr(data, "exclude_cancelled", None) is True,
            ])

        if exclude_cancel:
            canceled_ids = set()

            # 1. Scan history records directly for cancellation notes to identify canceled entity_ids / invoice_nos
            for r in records:
                notes_lower = (r.notes or "").lower()
                if "canceled purchase" in notes_lower or "cancelled purchase" in notes_lower or "cancel purchase" in notes_lower:
                    if r.entity_id:
                        canceled_ids.add(str(r.entity_id))
                    if getattr(r, "invoice_no", None):
                        canceled_ids.add(str(r.invoice_no))

            # 2. Fetch from Mongo Read DB if available
            try:
                from infras.read_db import main as read_db_main
                if getattr(read_db_main, "CLIENT", None):
                    pur_coll = read_db_main.CLIENT['PurchaseServiceReadDb']['PurchaseCollections']
                    canceled_docs = await pur_coll.find(
                        {
                            "shop_id": shop_id,
                            "$or": [{"supplier_id": supplier_id}, {"supplier_infos.id": supplier_id}, {"supplier.supplier_id": supplier_id}],
                            "status": {"$in": ["CANCELED", "canceled", "CANCELLED", "cancelled"]}
                        },
                        {"id": 1, "purchase_id": 1, "invoice_no": 1}
                    ).to_list(length=None)
                    for d in canceled_docs:
                        if d.get("id"): canceled_ids.add(str(d["id"]))
                        if d.get("purchase_id"): canceled_ids.add(str(d["purchase_id"]))
                        if d.get("invoice_no"): canceled_ids.add(str(d["invoice_no"]))
            except Exception as e:
                ic(f"Error checking Mongo for canceled purchases: {e}")

            # 3. Check Purchase Service HTTP endpoint
            try:
                import os, httpx
                purchase_service_url = os.getenv("PURCHASE_SERVICE_URL", "http://127.0.0.1:8003")
                async with httpx.AsyncClient(timeout=3.0) as client:
                    resp = await client.get(f"{purchase_service_url}/purchases/by/supplier/{shop_id}/{supplier_id}?status=CANCELED&limit=100")
                    if resp.status_code == 200:
                        p_data = resp.json().get("data", [])
                        if isinstance(p_data, list):
                            for p in p_data:
                                if str(p.get("status", "")).upper() in ["CANCELED", "CANCELLED"]:
                                    if p.get("id"): canceled_ids.add(str(p["id"]))
                                    if p.get("purchase_id"): canceled_ids.add(str(p["purchase_id"]))
                                    if p.get("invoice_no"): canceled_ids.add(str(p["invoice_no"]))
            except Exception as e:
                ic(f"Error querying purchase service HTTP for canceled purchases: {e}")

            filtered_records = []
            for r in records:
                if r.entity_id and str(r.entity_id) in canceled_ids:
                    continue
                if r.invoice_no and str(r.invoice_no) in canceled_ids:
                    continue
                notes_lower = (r.notes or "").lower()
                if "canceled purchase" in notes_lower or "cancelled purchase" in notes_lower or "cancel purchase" in notes_lower:
                    continue
                filtered_records.append(r)
            records = filtered_records

        if data and getattr(data, "limit", None):
            offset = max(data.offset - 1, 0) if data.offset else 0
            records = records[offset:offset + data.limit]

        return [
            {
                "id": r.id,
                "supplier_id": r.supplier_id,
                "shop_id": r.shop_id,
                "cleared_amount": r.cleared_amount,
                "outstanding_amount": r.outstanding_amount,
                "payment_method": r.payment_method,
                "entity_name": r.entity_name,
                "entity_id": r.entity_id,
                "invoice_no": getattr(r, "invoice_no", None),
                "notes": r.notes,
                "created_at": r.created_at
            }
            for r in records
        ]
    
