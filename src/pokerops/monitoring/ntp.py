import datetime
import json
import platform

import ntplib
import typer

app = typer.Typer(help="NTP monitoring commands")


@app.command("drift")
def ntp_drift_cmd(
    peer: str = typer.Option("time.cloudflare.com", help="NTP peer address"),
    log_id: str = typer.Option("ntp-drift", help="Log identifier"),
    location: str = typer.Option("", help="Location identifier"),
    environment: str = typer.Option("", help="Environment name"),
    function: str = typer.Option("", help="Function identifier"),
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
        "@timestamp": datetime.datetime.fromtimestamp(reply.tx_time, datetime.timezone.utc).isoformat(),
        "ntp_peer_address": peer,
        "ntp_peer_offset": abs(reply.offset),
        "host": {
            "name": platform.node(),
        },
        "fields": {
            "log": {"description": log_id},
        },
    }
    log = {"log": {"description": log_id}}
    location = {} if location == "" else {"location": location}
    environment = {} if environment == "" else {"environment": environment}
    function = {} if function == "" else {"function": function}
    fields = {"fields": {**log, **location, **environment, **function}}
    data = {**drift, **fields}
    print(json.dumps(data))
