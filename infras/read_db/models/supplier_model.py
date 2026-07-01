from pydantic import BaseModel,EmailStr
from typing import Optional


class SupplierStatsSchema(BaseModel):
    total_suppliers:Optional[int]=0
    total_outstanding:Optional[float]=0