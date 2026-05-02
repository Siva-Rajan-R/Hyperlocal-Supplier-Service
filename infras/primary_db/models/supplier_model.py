from ..main import BASE
from sqlalchemy import Column, String,ForeignKey,Integer,TIMESTAMP,func,BigInteger,Identity
from sqlalchemy.dialects.postgresql import JSONB



class Suppliers(BASE):
    __tablename__ = "suppliers"
    id = Column(String, primary_key=True)
    sequence_id=Column(BigInteger,Identity(always=True),nullable=False)
    ui_id=Column(BigInteger,Identity(always=True),nullable=False)
    shop_id=Column(String, nullable=False)
    name=Column(String,nullable=False)
    contact_info=Column(JSONB,nullable=True)
    mobile_number=Column(String,nullable=False)
    email=Column(String,nullable=True)
    gst_no=Column(String,nullable=True)
    datas=Column(JSONB,nullable=True)

    created_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now())
    updated_at=Column(TIMESTAMP(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())