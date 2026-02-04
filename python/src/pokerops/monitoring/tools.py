import datetime
import platform
from typing import Dict, Optional, Union

Field = Dict[str, str]
Fields = Dict[str, Union[str, "Fields"]]


def metadata(
    location: str,
    environment: str,
    function: str,
    log_id: str,
    timestamp: Optional[datetime.datetime] = None,
) -> Fields:
    if timestamp is None:
        timestamp = datetime.datetime.now(datetime.timezone.utc)
    timestamp_field: Field = {"timestamp": timestamp.isoformat()}
    host_field: Fields = {"host": {"name": platform.node()}}
    log_field: Fields = {"log": {"description": log_id}}
    location_field: Field = {} if location == "" else {"location": location}
    environment_field: Field = {} if environment == "" else {"environment": environment}
    function_field: Field = {} if function == "" else {"function": function}
    fields_field: Fields = {"fields": {**log_field, **location_field, **environment_field, **function_field}}
    _metadata = {**timestamp_field, **host_field, **fields_field}
    return _metadata
