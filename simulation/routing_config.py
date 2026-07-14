"""
Routing config for payment simulator.
Allows the agent executor to dynamically adjust active banks and retry settings in real-time.
"""

ROUTING_STATE = {
    "active_banks": [
        "HDFC Bank",
        "ICICI Bank",
        "State Bank of India",
        "Axis Bank",
        "Kotak Mahindra Bank",
        "Yes Bank",
        "IDFC First Bank",
        "Paytm Payments Bank"
    ],
    "suppressed_banks": [],
    "retry_limits": {},
}

def reset_routing():
    ROUTING_STATE["active_banks"] = [
        "HDFC Bank",
        "ICICI Bank",
        "State Bank of India",
        "Axis Bank",
        "Kotak Mahindra Bank",
        "Yes Bank",
        "IDFC First Bank",
        "Paytm Payments Bank"
    ]
    ROUTING_STATE["suppressed_banks"] = []
    ROUTING_STATE["retry_limits"] = {}
