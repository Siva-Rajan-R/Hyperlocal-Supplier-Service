from ..main import BASE
from sqlalchemy import Column, String, ForeignKey, Integer, Float, TIMESTAMP, func, BigInteger, Identity
from sqlalchemy.dialects.postgresql import JSONB



class Suppliers(BASE):
    __tablename__ = "suppliers"
    id = Column(String, primary_key=True)
    sequence_id=Column(BigInteger,Identity(always=True),nullable=False)
    ui_id=Column(String,nullable=False,index=True)
    shop_id=Column(String, nullable=False)
    name=Column(String,nullable=False)
    contact_person_infos=Column(JSONB)
    contact_infos=Column(JSONB,nullable=True)
    location_infos=Column(JSONB)
    outstanding_infos=Column(JSONB)
    gst_no=Column(String,nullable=True)
    additional_infos=Column(JSONB,nullable=True)


    created_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now())
    updated_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())


class SupplierOutstandingHistory(BASE):
    __tablename__ = "supplier_outstanding_history"
    id = Column(String, primary_key=True)
    supplier_id = Column(String, ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_id = Column(String, nullable=False)
    cleared_amount = Column(Float, nullable=False)
    outstanding_amount = Column(Float, nullable=False)
    payment_method = Column(String, nullable=False)
    entity_name = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    notes = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())