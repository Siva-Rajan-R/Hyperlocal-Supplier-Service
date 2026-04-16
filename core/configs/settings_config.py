from ..settings import SupplierSettings
from hyperlocal_platform.core.utils.settings_initializer import init_settings
from ..constants import ENV_PREFIX,SERVICE_NAME

SETTINGS:SupplierSettings=init_settings(settings=SupplierSettings,service_name=SERVICE_NAME,env_prefix=ENV_PREFIX)