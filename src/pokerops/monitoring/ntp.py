import datetime
import json
import platform

import ntplib
import typer

app = typer.Typer(help="NTP monitoring commands")


@app.command("drift")
def ntp_drift_cmd(
    location: str = typer.Option(..., help="Location identifier"),  # pyright: ignore[reportCallInDefaultInitializer]
    environment: str = typer.Option(..., help="Environment name"),  # pyright: ignore[reportCallInDefaultInitializer]
    function: str = typer.Option(..., help="Function identifier"),  # pyright: ignore[reportCallInDefaultInitializer]
    log_id: str = typer.Option("ntp-drift", help="Log identifier"),  # pyright: ignore[reportCallInDefaultInitializer]
) -> None:
    return ntp_drift(location, environment, function, log_id)


def ntp_drift(
    location: str,
    environment: str,
    function: str,
    log_id: str = "ntp-drift",
):
    client = ntplib.NTPClient()
    reply = client.request("time.cloudflare.com")  # pyright: ignore[reportUnknownMemberType]
    data = {
        "@timestamp": datetime.datetime.fromtimestamp(reply.tx_time, datetime.timezone.utc).isoformat(),
        "ntp_peer_address": "time.cloudflare.com",
        "ntp_peer_offset": abs(reply.offset),
        "host": {
            "name": platform.node(),
        },
        "fields": {
            "location": location,
            "environment": environment,
            "function": function,
            "log": {"description": log_id},
        },
    }
    print(json.dumps(data))
