import logging
import pandas as pd
from datetime import datetime, timedelta

def setup_logger(name):
    """Setup logger with console and file handlers"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler
    fh = logging.FileHandler('logs/app.log')
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    return logger

def date_range(start_date, end_date):
    """Generate list of dates between start and end"""
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def safe_divide(a, b):
    """Safe division, returns 0 if denominator is 0"""
    return a / b if b != 0 else 0