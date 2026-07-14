"""
Unit tests for data loader utility.
"""

import csv
import json
import tempfile
from pathlib import Path
import pytest
from datetime import datetime

from utils.data_loader import (
    map_header,
    parse_payment_status,
    parse_payment_method,
    parse_error_code,
    parse_datetime,
    load_payment_records
)
from simulation.models import PaymentStatus, PaymentMethod, ErrorCode


def test_map_header():
    headers = ["TxID", "Time_Stamp", "Method", "Acquirer"]
    assert map_header(headers, ["payment_id", "transaction_id", "tx_id"]) == "TxID"
    assert map_header(headers, ["timestamp", "time"]) == "Time_Stamp"
    assert map_header(headers, ["payment_method", "method"]) == "Method"
    assert map_header(headers, ["bank", "provider", "gateway", "acquirer"]) == "Acquirer"
    assert map_header(headers, ["nonexistent"]) == ""


def test_parse_payment_status():
    assert parse_payment_status("SUCCESS") == PaymentStatus.SUCCESS
    assert parse_payment_status("successful") == PaymentStatus.SUCCESS
    assert parse_payment_status("COMPLETED") == PaymentStatus.SUCCESS
    assert parse_payment_status("FAILED") == PaymentStatus.FAILED
    assert parse_payment_status("declined") == PaymentStatus.FAILED
    assert parse_payment_status("TIMEOUT") == PaymentStatus.TIMEOUT
    assert parse_payment_status("PENDING") == PaymentStatus.PENDING
    assert parse_payment_status(None) == PaymentStatus.PENDING


def test_parse_payment_method():
    assert parse_payment_method("UPI") == PaymentMethod.UPI
    assert parse_payment_method("credit_card") == PaymentMethod.CREDIT_CARD
    assert parse_payment_method("CC") == PaymentMethod.CREDIT_CARD
    assert parse_payment_method("DEBIT CARD") == PaymentMethod.DEBIT_CARD
    assert parse_payment_method("NET_BANKING") == PaymentMethod.NET_BANKING
    assert parse_payment_method("wallet") == PaymentMethod.WALLET
    assert parse_payment_method(None) == PaymentMethod.UPI


def test_parse_error_code():
    assert parse_error_code("none", PaymentStatus.SUCCESS) == ErrorCode.NONE
    assert parse_error_code("INSUFFICIENT_FUNDS", PaymentStatus.FAILED) == ErrorCode.INSUFFICIENT_FUNDS
    assert parse_error_code("timeout", PaymentStatus.FAILED) == ErrorCode.BANK_TIMEOUT
    assert parse_error_code("INVALID_CREDENTIALS", PaymentStatus.FAILED) == ErrorCode.INVALID_CREDENTIALS
    assert parse_error_code("NETWORK_ERROR", PaymentStatus.FAILED) == ErrorCode.NETWORK_ERROR
    assert parse_error_code("RATE_LIMIT", PaymentStatus.FAILED) == ErrorCode.RATE_LIMIT_EXCEEDED
    assert parse_error_code("GATEWAY", PaymentStatus.FAILED) == ErrorCode.GATEWAY_ERROR
    assert parse_error_code("FRAUD", PaymentStatus.FAILED) == ErrorCode.FRAUD_SUSPECTED
    assert parse_error_code("unknown", PaymentStatus.FAILED) == ErrorCode.TECHNICAL_ERROR
    assert parse_error_code(None, PaymentStatus.FAILED) == ErrorCode.TECHNICAL_ERROR


def test_parse_datetime():
    dt = parse_datetime("2026-07-14T15:05:18Z")
    assert isinstance(dt, datetime)
    assert dt.year == 2026
    assert dt.month == 7
    assert dt.day == 14
    
    dt2 = parse_datetime("2026-07-14 15:05:18")
    assert dt2.hour == 15
    assert dt2.minute == 5


def test_load_payment_records_csv():
    headers = ["transaction_id", "timestamp", "method", "provider", "amount", "currency", "status", "error", "duration_ms"]
    row1 = ["tx_01", "2026-07-14T15:00:00Z", "UPI", "HDFC", "100.0", "INR", "SUCCESS", "NONE", "150"]
    row2 = ["tx_02", "2026-07-14T15:01:00Z", "CC", "ICICI", "200.0", "INR", "FAILED", "TIMEOUT", "3000"]
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as temp_csv:
        writer = csv.writer(temp_csv)
        writer.writerow(headers)
        writer.writerow(row1)
        writer.writerow(row2)
        temp_csv_path = temp_csv.name
        
    try:
        records = load_payment_records(temp_csv_path)
        assert len(records) == 2
        assert records[0].payment_id == "tx_01"
        assert records[0].status == PaymentStatus.SUCCESS
        assert records[0].amount == 100.0
        assert records[0].bank == "HDFC"
        
        assert records[1].payment_id == "tx_02"
        assert records[1].status == PaymentStatus.FAILED
        assert records[1].error_code == ErrorCode.BANK_TIMEOUT
        assert records[1].latency_ms == 3000
    finally:
        Path(temp_csv_path).unlink()


def test_load_payment_records_json():
    data = [
        {
            "id": "tx_json_1",
            "time": "2026-07-14T15:00:00Z",
            "type": "UPI",
            "gateway": "SBI",
            "amount": 50.0,
            "status": "SUCCESS"
        },
        {
            "id": "tx_json_2",
            "time": "2026-07-14T15:02:00Z",
            "type": "CC",
            "gateway": "AXIS",
            "amount": 150.0,
            "status": "FAILED",
            "reason": "FRAUD"
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_json:
        json.dump(data, temp_json)
        temp_json_path = temp_json.name
        
    try:
        records = load_payment_records(temp_json_path)
        assert len(records) == 2
        assert records[0].payment_id == "tx_json_1"
        assert records[0].payment_method == PaymentMethod.UPI
        assert records[0].status == PaymentStatus.SUCCESS
        
        assert records[1].payment_id == "tx_json_2"
        assert records[1].error_code == ErrorCode.FRAUD_SUSPECTED
        assert records[1].status == PaymentStatus.FAILED
    finally:
        Path(temp_json_path).unlink()
