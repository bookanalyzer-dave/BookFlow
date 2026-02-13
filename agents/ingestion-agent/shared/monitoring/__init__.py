"""
Produktions-Monitoring und Logging System

Dieses Modul bietet strukturiertes Logging und Metriken-Tracking für die Produktionsumgebung.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class ProductionLogger:
    """Strukturiertes Logging für Produktion"""
    
    def __init__(self, name: str, log_dir: str = "logs"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Verhindere doppelte Handler
        if self.logger.handlers:
            return
        
        # Erstelle log directory
        Path(log_dir).mkdir(exist_ok=True)
        
        # File Handler für alle Logs
        fh = logging.FileHandler(f"{log_dir}/{name}.log", encoding='utf-8')
        fh.setLevel(logging.INFO)
        
        # File Handler für Errors
        fh_error = logging.FileHandler(f"{log_dir}/{name}_errors.log", encoding='utf-8')
        fh_error.setLevel(logging.ERROR)
        
        # Console Handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        fh_error.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(fh_error)
        self.logger.addHandler(ch)
    
    def log_api_call(self, api_name: str, endpoint: str, 
                     duration_ms: float, success: bool, 
                     metadata: Optional[Dict] = None):
        """Log API calls mit Metriken"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "api": api_name,
            "endpoint": endpoint,
            "duration_ms": duration_ms,
            "success": success,
            "metadata": metadata or {}
        }
        
        if success:
            self.logger.info(f"API_CALL: {json.dumps(log_data)}")
        else:
            self.logger.error(f"API_CALL_FAILED: {json.dumps(log_data)}")
    
    def log_performance(self, operation: str, duration_ms: float, 
                       metrics: Dict[str, Any]):
        """Log Performance-Metriken"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "duration_ms": duration_ms,
            "metrics": metrics
        }
        self.logger.info(f"PERFORMANCE: {json.dumps(log_data)}")
    
    def log_confidence(self, operation: str, confidence: float, 
                      details: Optional[Dict] = None):
        """Log Konfidenz-Scores"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "confidence": confidence,
            "details": details or {}
        }
        
        if confidence < 0.7:
            self.logger.warning(f"LOW_CONFIDENCE: {json.dumps(log_data)}")
        else:
            self.logger.info(f"CONFIDENCE: {json.dumps(log_data)}")
    
    def log_error(self, operation: str, error: Exception, 
                  context: Optional[Dict] = None):
        """Log Fehler mit vollständigem Context"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        self.logger.error(f"ERROR: {json.dumps(log_data)}", exc_info=True)
    
    def log_grounding(self, query: str, num_results: int, 
                     has_support: bool, confidence: float):
        """Log Search Grounding Activity"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "num_results": num_results,
            "has_support": has_support,
            "confidence": confidence
        }
        self.logger.info(f"GROUNDING: {json.dumps(log_data)}")
    
    def info(self, message: str):
        """Standard info log"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Standard warning log"""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Standard error log"""
        self.logger.error(message)
    
    def debug(self, message: str):
        """Standard debug log"""
        self.logger.debug(message)


# Globaler Logger für einfachen Zugriff
_default_logger = None

def get_logger(name: str = "production", log_dir: str = "logs") -> ProductionLogger:
    """Hole oder erstelle einen Logger"""
    global _default_logger
    if _default_logger is None or _default_logger.logger.name != name:
        _default_logger = ProductionLogger(name, log_dir)
    return _default_logger


# Export metrics collector from metrics module
from shared.monitoring.metrics import get_metrics_collector, MetricsCollector

__all__ = ['ProductionLogger', 'get_logger', 'get_metrics_collector', 'MetricsCollector']