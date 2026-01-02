import datetime
import json
import platform

import ntplib
import typer

app = typer.Typer(help="NTP monitoring commands")


@app.command("drift")
def ntp_drift_cmd(
    peer: str = typer.Option("time.cloudflare.com", help="NTP peer address"),  # pyright: ignore[reportCallInDefaultInitializer]
    location: str = typer.Option("", help="Location identifier"),  # pyright: ignore[reportCallInDefaultInitializer]
    environment: str = typer.Option("", help="Environment name"),  # pyright: ignore[reportCallInDefaultInitializer]
    function: str = typer.Option("", help="Function identifier"),  # pyright: ignore[reportCallInDefaultInitializer]
    log_id: str = typer.Option("ntp-drift", help="Log identifier"),  # pyright: ignore[reportCallInDefaultInitializer]
) -> None:
    return ntp_drift(peer, location, environment, function, log_id)


def ntp_drift(
    peer: str,
    location: str,
    environment: str,
    function: str,
    log_id: str = "ntp-drift",
):
    client = ntplib.NTPClient()
    reply = client.request("time.cloudflare.com")  # pyright: ignore[reportUnknownMemberType]
    drift = {
        "@timestamp": datetime.datetime.fromtimestamp(reply.tx_time, datetime.UTC).isoformat(),
        "ntp_peer_address": peer,
        "ntp_peer_offset": abs(reply.offset),
        "host": {
            "name": platform.node(),
        },
        "fields": {
            "log": {"description": log_id},
        },
    }
    log_field = {"log": {"description": log_id}}
    location_field = {} if location == "" else {"location": location}
    environment_field = {} if environment == "" else {"environment": environment}
    function_field = {} if function == "" else {"function": function}
    fields = {"fields": {**log_field, **location_field, **environment_field, **function_field}}
    data = {**drift, **fields}
    print(json.dumps(data))
