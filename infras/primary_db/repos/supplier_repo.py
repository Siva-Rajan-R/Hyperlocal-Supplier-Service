from models.repo_models.base_repo_model import BaseRepoModel
from ..models.supplier_model import Suppliers,String
from sqlalchemy.dialects.postgresql import insert
from ..main import AsyncSession
from sqlalchemy import select,update,delete,or_,and_,func,case
from datetime import datetime, timezone
from schemas.v1.supplier_schemas.db_schemas import CreateSupplierDbSchema,UpdateSupplierDbSchema,DeleteSupplierDbSchema
from schemas.v1.supplier_schemas.request_schemas import CreateSupplierSchema,UpdateSupplierSchema,DeleteSupplierSchema,GetAllSupplierSchema,GetSupplierById,GetSupplierByShopIdSchema,UpdateOutstandingSupplierSchema
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


    @start_db_transaction
    async def get_next_sequence(self, shop_id: str, start_from: int) -> int:
        from sqlalchemy import text
        seq_name = f"seq_supplier_{shop_id.replace('-', '_').lower()}"
        await self.session.execute(text(f"CREATE SEQUENCE IF NOT EXISTS {seq_name} START WITH {start_from}"))
        res = await self.session.execute(text(f"SELECT nextval('{seq_name}')"))
        return res.scalar_one()

    @start_db_transaction
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
    

    @start_db_transaction
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
        if getattr(data, "entity_name", None) and getattr(data, "entity_id", None):
            try:
                from ..models.supplier_model import SupplierOutstandingHistory
                import uuid
                history_record = SupplierOutstandingHistory(
                    id=str(uuid.uuid4()),
                    supplier_id=data.id,
                    shop_id=data.shop_id,
                    cleared_amount=data.cleared_amount if data.cleared_amount is not None else 0.0,
                    outstanding_amount=data.outstanding_amount if data.outstanding_amount is not None else (data.outstanding_infos.amount if data.outstanding_infos else 0.0),
                    payment_method=getattr(data, "payment_method", "N/A") or "N/A",
                    entity_name=data.entity_name,
                    entity_id=data.entity_id,
                    invoice_no=getattr(data, "invoice_no", None),
                    notes=getattr(data, "notes", None) or f"Cleared outstanding for {data.entity_name}"
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
        if getattr(data, 'has_outstanding', None) is not None:
            from sqlalchemy import Float
            amount_expr = func.cast(Suppliers.outstanding_infos['amount'].astext, Float)
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
        if getattr(data, 'has_outstanding', None) is not None:
            from sqlalchemy import Float
            amount_expr = func.cast(Suppliers.outstanding_infos['amount'].astext, Float)
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

    async def get_outstanding_history(self, supplier_id: str, shop_id: str):
        from ..models.supplier_model import SupplierOutstandingHistory
        stmt = select(SupplierOutstandingHistory).where(
            SupplierOutstandingHistory.supplier_id == supplier_id,
            SupplierOutstandingHistory.shop_id == shop_id
        ).order_by(SupplierOutstandingHistory.created_at.desc())
        records = (await self.session.execute(stmt)).scalars().all()
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
    
