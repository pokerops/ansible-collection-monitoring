import datetime
import platform

type Field = dict[str, str]
type Fields = dict[str, str | Fields]


def metadata(
    location: str,
    environment: str,
    function: str,
    log_id: str,
    timestamp: datetime.datetime | None = None,
) -> Fields:
    if timestamp is None:
        timestamp = datetime.datetime.now(datetime.UTC)
    timestamp_field: Field = {"timestamp": timestamp.isoformat()}
    host_field: Fields = {"host": {"name": platform.node()}}
    log_field: Fields = {"log": {"description": log_id}}
    location_field: Field = {} if location == "" else {"location": location}
    environment_field: Field = {} if environment == "" else {"environment": environment}
    function_field: Field = {} if function == "" else {"function": function}
    fields_field: Fields = {"fields": {**log_field, **location_field, **environment_field, **function_field}}
    metadata = {**timestamp_field, **host_field, **fields_field}
    return metadata
