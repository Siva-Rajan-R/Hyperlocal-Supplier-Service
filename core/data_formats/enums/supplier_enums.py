from enum import Enum
from typing import Optional,List


class SupplierOutstandingUpdateTypeEnums(str,Enum):
    INCREMENT="INCREMENT"
    DECREMENT="DECREMENT"
    DIRECT="DIRECT"