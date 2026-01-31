"""
Logging utilities.

Configures structured logging for the agent system.
"""

import logging
import sys
from pathlib import Path


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured logger
        
    TODO:
    - Configure structured logging
    - Setup file handlers
    - Add context processors
    """
    # Create logs directory
    log_dir = Path("./data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "agent.log")
        ]
    )
    
    logger = logging.getLogger("payment_agent")
    logger.info(f"Logging initialized at {log_level} level")
    
    return logger
