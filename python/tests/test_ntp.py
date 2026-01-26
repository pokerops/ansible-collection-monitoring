"""Tests for NTP drift functionality."""

import json
from unittest.mock import MagicMock, patch

import pytest
from pokerops.monitoring.ntp import ntp_drift


@pytest.fixture
def mock_ntp_response():
    """Mock NTP response."""
    response = MagicMock()
    response.tx_time = 1704067200.0  # 2024-01-01 00:00:00 UTC
    response.offset = 0.005  # 5ms offset
    return response


def test_ntp_drift_success(mock_ntp_response, capsys):
    """Test successful NTP drift check."""
    with patch("pokerops.monitoring.ntp.ntplib.NTPClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.request.return_value = mock_ntp_response
        mock_client_class.return_value = mock_client

        # Call the function
        ntp_drift(
            peer="time.cloudflare.com",
            location="test-location",
            environment="test-env",
            function="test-function",
            log_id="test-log",
        )

        # Verify NTP client was called
        mock_client.request.assert_called_once_with("time.cloudflare.com")

        # Capture and verify output
        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert output["ntp_peer_address"] == "time.cloudflare.com"
        assert output["ntp_peer_offset"] == 0.005
        assert output["fields"]["location"] == "test-location"
        assert output["fields"]["environment"] == "test-env"
        assert output["fields"]["function"] == "test-function"
        assert output["fields"]["log"]["description"] == "test-log"
        assert "timestamp" in output
        assert "host" in output
        assert "name" in output["host"]


def test_ntp_drift_with_negative_offset(capsys):
    """Test NTP drift with negative offset (should be absolute value)."""
    mock_response = MagicMock()
    mock_response.tx_time = 1704067200.0
    mock_response.offset = -0.010  # -10ms offset

    with patch("pokerops.monitoring.ntp.ntplib.NTPClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.request.return_value = mock_response
        mock_client_class.return_value = mock_client

        ntp_drift(
            peer="test.ntp.server",
            location="test",
            environment="test",
            function="test",
        )

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        # Offset should be absolute value
        assert output["ntp_peer_offset"] == 0.010


def test_ntp_drift_default_log_id(mock_ntp_response, capsys):
    """Test NTP drift with default log_id."""
    with patch("pokerops.monitoring.ntp.ntplib.NTPClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.request.return_value = mock_ntp_response
        mock_client_class.return_value = mock_client

        ntp_drift(
            peer="test.ntp.server",
            location="test",
            environment="test",
            function="test",
        )

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        # Should use default log_id
        assert output["fields"]["log"]["description"] == "ntp-drift"


def test_ntp_drift_json_format(mock_ntp_response, capsys):
    """Test that output is valid JSON."""
    with patch("pokerops.monitoring.ntp.ntplib.NTPClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client.request.return_value = mock_ntp_response
        mock_client_class.return_value = mock_client

        ntp_drift(
            peer="test.ntp.server",
            location="test",
            environment="test",
            function="test",
        )

        captured = capsys.readouterr()

        # Should not raise JSONDecodeError
        output = json.loads(captured.out)

        # Verify structure
        assert isinstance(output, dict)
        assert isinstance(output["fields"], dict)
        assert isinstance(output["host"], dict)
