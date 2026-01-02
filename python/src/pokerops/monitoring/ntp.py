import datetime
import json
import platform

import ntplib
import pokerops.monitoring.tools as tools
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
) -> None:
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
    data = {**drift, **tools.fields(log_id, location, environment, function)}
    print(json.dumps(data))
