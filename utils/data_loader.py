"""
Data Loader Utility.

Provides functions to load and parse transaction records from CSV and JSON formats,
mapping them to the PaymentRecord dataclass for processing by the metrics and agent loops.
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Union

from simulation.models import PaymentRecord, PaymentStatus, PaymentMethod, ErrorCode

logger = logging.getLogger(__name__)


def map_header(headers: List[str], target_keys: List[str]) -> str:
    """Finds the first header in headers that matches one of the target keys."""
    headers_lower = [h.lower().replace("_", "").replace(" ", "") for h in headers]
    for target in target_keys:
        normalized_target = target.lower().replace("_", "").replace(" ", "")
        if normalized_target in headers_lower:
            idx = headers_lower.index(normalized_target)
            return headers[idx]
    return ""


def parse_payment_status(status_str: Any) -> PaymentStatus:
    """Safely parses payment status string into PaymentStatus enum."""
    if not status_str:
        return PaymentStatus.PENDING
    status_str = str(status_str).upper().strip()
    if status_str in ["SUCCESS", "SUCCESSFUL", "COMPLETED", "PAID"]:
        return PaymentStatus.SUCCESS
    if status_str in ["FAILED", "FAILURE", "FAIL", "DECLINED"]:
        return PaymentStatus.FAILED
    if status_str in ["TIMEOUT", "TIMED_OUT", "EXPIRED"]:
        return PaymentStatus.TIMEOUT
    if status_str in ["PENDING", "PROCESSING", "SUBMITTED"]:
        return PaymentStatus.PENDING
    return PaymentStatus.PENDING


def parse_payment_method(method_str: Any) -> PaymentMethod:
    """Safely parses payment method string into PaymentMethod enum."""
    if not method_str:
        return PaymentMethod.UPI
    method_str = str(method_str).upper().strip().replace(" ", "_")
    if "UPI" in method_str:
        return PaymentMethod.UPI
    if "CREDIT" in method_str or method_str == "CC":
        return PaymentMethod.CREDIT_CARD
    if "DEBIT" in method_str or method_str == "DC":
        return PaymentMethod.DEBIT_CARD
    if "NET" in method_str or "BANKING" in method_str or method_str == "NB":
        return PaymentMethod.NET_BANKING
    if "WALLET" in method_str:
        return PaymentMethod.WALLET
    return PaymentMethod.UPI


def parse_error_code(error_str: Any, status: PaymentStatus) -> ErrorCode:
    """Safely parses error code string into ErrorCode enum."""
    if status == PaymentStatus.SUCCESS:
        return ErrorCode.NONE
    if not error_str:
        return ErrorCode.TECHNICAL_ERROR
    
    error_str = str(error_str).upper().strip().replace(" ", "_")
    if "INSUFFICIENT" in error_str or "FUNDS" in error_str or "BALANCE" in error_str:
        return ErrorCode.INSUFFICIENT_FUNDS
    if "TIMEOUT" in error_str or "TIME_OUT" in error_str:
        return ErrorCode.BANK_TIMEOUT
    if "CREDENTIAL" in error_str or "PASSWORD" in error_str or "AUTH" in error_str or "PIN" in error_str:
        return ErrorCode.INVALID_CREDENTIALS
    if "NETWORK" in error_str or "CONNECTION" in error_str or "CONNECT" in error_str:
        return ErrorCode.NETWORK_ERROR
    if "RATE" in error_str or "LIMIT" in error_str or "THROTTLE" in error_str:
        return ErrorCode.RATE_LIMIT_EXCEEDED
    if "GATEWAY" in error_str:
        return ErrorCode.GATEWAY_ERROR
    if "FRAUD" in error_str or "SUSPECT" in error_str:
        return ErrorCode.FRAUD_SUSPECTED
    if "TECHNICAL" in error_str or "SYSTEM" in error_str or "INTERNAL" in error_str:
        return ErrorCode.TECHNICAL_ERROR
    
    return ErrorCode.TECHNICAL_ERROR


def parse_datetime(dt_str: Any) -> datetime:
    """Parse datetime string into datetime object, supporting ISO 8601 formats."""
    if isinstance(dt_str, datetime):
        return dt_str
    
    dt_str = str(dt_str).strip()
    try:
        # Standard ISO format (e.g. 2026-07-14T15:05:18)
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except ValueError:
        pass
        
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%d/%m/%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S"]:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
            
    # Fallback to current time
    logger.warning(f"Could not parse date string: {dt_str}. Falling back to now.")
    return datetime.utcnow()


def record_from_dict(row: Dict[str, Any], headers: List[str]) -> PaymentRecord:
    """Construct a PaymentRecord from a dictionary row using mapped headers."""
    # Find mappings
    id_header = map_header(headers, ["payment_id", "transaction_id", "tx_id", "id"])
    time_header = map_header(headers, ["timestamp", "time", "date", "created_at"])
    method_header = map_header(headers, ["payment_method", "method", "type"])
    bank_header = map_header(headers, ["bank", "provider", "gateway", "acquirer"])
    amount_header = map_header(headers, ["amount", "value", "price"])
    currency_header = map_header(headers, ["currency", "ccy"])
    status_header = map_header(headers, ["status", "state", "result"])
    err_header = map_header(headers, ["error_code", "error", "err_code", "reason"])
    latency_header = map_header(headers, ["latency_ms", "latency", "duration_ms", "duration", "time_taken"])
    retry_header = map_header(headers, ["retry_count", "retries", "retry"])
    merchant_header = map_header(headers, ["merchant_id", "merchant"])
    customer_header = map_header(headers, ["customer_id", "customer"])

    # Extract values with fallbacks
    payment_id = str(row.get(id_header)) if id_header and row.get(id_header) is not None else f"tx_{int(datetime.utcnow().timestamp() * 1000)}"
    timestamp = parse_datetime(row.get(time_header)) if time_header else datetime.utcnow()
    payment_method = parse_payment_method(row.get(method_header)) if method_header else PaymentMethod.UPI
    bank = str(row.get(bank_header, "UNKNOWN_BANK")) if bank_header else "UNKNOWN_BANK"
    
    try:
        amount = float(row.get(amount_header, 0.0)) if amount_header else 0.0
    except (ValueError, TypeError):
        amount = 0.0
        
    currency = str(row.get(currency_header, "INR")) if currency_header else "INR"
    status = parse_payment_status(row.get(status_header)) if status_header else PaymentStatus.PENDING
    error_code = parse_error_code(row.get(err_header), status) if err_header else (ErrorCode.NONE if status == PaymentStatus.SUCCESS else ErrorCode.TECHNICAL_ERROR)
    
    try:
        latency_ms = int(float(row.get(latency_header, 100))) if latency_header and row.get(latency_header) is not None else 100
    except (ValueError, TypeError):
        latency_ms = 100
        
    try:
        retry_count = int(row.get(retry_header, 0)) if retry_header and row.get(retry_header) is not None else 0
    except (ValueError, TypeError):
        retry_count = 0
        
    merchant_id = str(row.get(merchant_header)) if merchant_header and row.get(merchant_header) is not None else None
    customer_id = str(row.get(customer_header)) if customer_header and row.get(customer_header) is not None else None

    # Put other columns into metadata
    metadata = {}
    known_headers = {id_header, time_header, method_header, bank_header, amount_header, currency_header,
                     status_header, err_header, latency_header, retry_header, merchant_header, customer_header}
    for k, v in row.items():
        if k not in known_headers:
            metadata[k] = v

    return PaymentRecord(
        payment_id=payment_id,
        timestamp=timestamp,
        payment_method=payment_method,
        bank=bank,
        amount=amount,
        currency=currency,
        status=status,
        error_code=error_code,
        latency_ms=latency_ms,
        retry_count=retry_count,
        merchant_id=merchant_id,
        customer_id=customer_id,
        metadata=metadata
    )


def load_payment_records(file_path: Union[str, Path]) -> List[PaymentRecord]:
    """
    Load payment records from a CSV or JSON file.
    
    Args:
        file_path: Path to the data file.
        
    Returns:
        Chronologically sorted list of PaymentRecord objects.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Transaction file not found: {file_path}")
        
    records: List[PaymentRecord] = []
    
    if path.suffix.lower() == ".json":
        with open(path, "r") as f:
            data = json.load(f)
            
        if isinstance(data, list):
            # List of transaction dicts
            for item in data:
                if isinstance(item, dict):
                    headers = list(item.keys())
                    records.append(record_from_dict(item, headers))
        elif isinstance(data, dict) and "payments" in data:
            payments = data["payments"]
            if isinstance(payments, list):
                for item in payments:
                    if isinstance(item, dict):
                        headers = list(item.keys())
                        records.append(record_from_dict(item, headers))
        else:
            raise ValueError("Unsupported JSON format. Expected list of records or dictionary containing a 'payments' list.")
            
    elif path.suffix.lower() == ".csv":
        with open(path, "r", newline="") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            for row in reader:
                records.append(record_from_dict(row, headers))
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}. Please provide a .csv or .json file.")

    # Sort chronologically by timestamp
    records.sort(key=lambda x: x.timestamp)
    logger.info(f"Loaded {len(records)} payment records from {file_path}")
    return records
