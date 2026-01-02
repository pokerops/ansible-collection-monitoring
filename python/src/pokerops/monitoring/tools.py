type Field = dict[str, str]
type Fields = dict[str, str | Fields]


def fields(
    location: str,
    environment: str,
    function: str,
    log_id: str = "ntp-drift",
) -> Fields:
    log_field: Fields = {"log": {"description": log_id}}
    location_field: Field = {} if location == "" else {"location": location}
    environment_field: Field = {} if environment == "" else {"environment": environment}
    function_field: Field = {} if function == "" else {"function": function}
    fields: Fields = {"fields": {**log_field, **location_field, **environment_field, **function_field}}
    return fields
