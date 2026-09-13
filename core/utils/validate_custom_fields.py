from typing import List, Dict
from fastapi import HTTPException
from icecream import ic
from hyperlocal_platform.core.models.req_res_models import ErrorResponseTypDict

def validate_and_filter_custom_fields(payload_custom_fields: Dict, defined_custom_fields: List[Dict]) -> Dict:
    """
    Validates the provided custom fields against the defined custom fields.
    - If no defined custom fields, ignore the payload and return {}.
    - Checks for missing required fields and raises HTTPException.
    - Filters out any fields in payload that are not defined.
    """
    if not defined_custom_fields or not isinstance(defined_custom_fields, list):
        return {}

    defined_by_name = {field['field_name']: field for field in defined_custom_fields if isinstance(field, dict) and 'field_name' in field}
    defined_by_id = {field['id']: field for field in defined_custom_fields if isinstance(field, dict) and 'id' in field}
    payload_custom_fields = payload_custom_fields or {}
    ic(defined_by_name, defined_by_id, payload_custom_fields)

    # Check for required fields
    for field in defined_custom_fields:
        if not isinstance(field, dict):
            continue
        if field.get('required'):
            name = field.get('field_name')
            fid = field.get('id')
            val = payload_custom_fields.get(name) or payload_custom_fields.get(fid)
            if val is None or (isinstance(val, str) and not val.strip()):
                label = field.get('label_name') or name or "Custom Field"
                raise HTTPException(
                    status_code=400,
                    detail=ErrorResponseTypDict(
                        status_code=400,
                        msg="Missing Required Custom Field",
                        description=f"The custom field '{label}' is required.",
                        success=False
                    )
                )

    # Filter out unknown fields and build valid custom fields
    valid_custom_fields = {}
    for key, value in payload_custom_fields.items():
        if key in defined_by_id:
            valid_custom_fields[key] = value
        elif key in defined_by_name:
            valid_custom_fields[defined_by_name[key]['id']] = value
            
    ic(valid_custom_fields)
    return valid_custom_fields
