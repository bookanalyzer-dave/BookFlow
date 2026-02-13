"""
Metriken-Tracking System für API-Aufrufe und Performance

Dieses Modul sammelt und aggregiert Metriken über API-Nutzung, Kosten und Performance.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path


@dataclass
class APIMetrics:
    """Tracks API usage and costs"""
    api_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_duration_ms: float = 0.0
    avg_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    estimated_cost: float = 0.0
    
    def record_call(self, duration_ms: float, success: bool, cost: float = 0.0):
        """Registriere einen API-Call"""
        self.total_calls += 1
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
        
        self.total_duration_ms += duration_ms
        self.avg_duration_ms = self.total_duration_ms / self.total_calls
        self.min_duration_ms = min(self.min_duration_ms, duration_ms)
        self.max_duration_ms = max(self.max_duration_ms, duration_ms)
        self.estimated_cost += cost
    
    @property
    def success_rate(self) -> float:
        """Berechne Success Rate"""
        return self.successful_calls / self.total_calls if self.total_calls > 0 else 0.0
    
    @property
    def failure_rate(self) -> float:
        """Berechne Failure Rate"""
        return self.failed_calls / self.total_calls if self.total_calls > 0 else 0.0
    
    def to_dict(self) -> Dict:
        """Konvertiere zu Dictionary"""
        data = asdict(self)
        data['success_rate'] = self.success_rate
        data['failure_rate'] = self.failure_rate
        # Bereinige inf-Werte
        if data['min_duration_ms'] == float('inf'):
            data['min_duration_ms'] = 0.0
        return data


@dataclass
class ConfidenceMetrics:
    """Tracks confidence scores"""
    operation: str
    total_operations: int = 0
    avg_confidence: float = 0.0
    min_confidence: float = 1.0
    max_confidence: float = 0.0
    low_confidence_count: int = 0  # < 0.7
    medium_confidence_count: int = 0  # 0.7 - 0.85
    high_confidence_count: int = 0  # > 0.85
    _total_confidence: float = 0.0
    
    def record_confidence(self, confidence: float):
        """Registriere einen Confidence Score"""
        self.total_operations += 1
        self._total_confidence += confidence
        self.avg_confidence = self._total_confidence / self.total_operations
        self.min_confidence = min(self.min_confidence, confidence)
        self.max_confidence = max(self.max_confidence, confidence)
        
        if confidence < 0.7:
            self.low_confidence_count += 1
        elif confidence < 0.85:
            self.medium_confidence_count += 1
        else:
            self.high_confidence_count += 1
    
    def to_dict(self) -> Dict:
        """Konvertiere zu Dictionary"""
        return {
            'operation': self.operation,
            'total_operations': self.total_operations,
            'avg_confidence': self.avg_confidence,
            'min_confidence': self.min_confidence,
            'max_confidence': self.max_confidence,
            'low_confidence_count': self.low_confidence_count,
            'medium_confidence_count': self.medium_confidence_count,
            'high_confidence_count': self.high_confidence_count,
            'low_confidence_percent': (self.low_confidence_count / self.total_operations * 100) if self.total_operations > 0 else 0.0
        }


class MetricsCollector:
    """Sammelt und aggregiert Metriken"""
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.api_metrics: Dict[str, APIMetrics] = {}
        self.confidence_metrics: Dict[str, ConfidenceMetrics] = {}
        self.session_start = datetime.now()
        self.total_errors: int = 0
        self.error_types: Dict[str, int] = {}
    
    def record_api_call(self, api_name: str, duration_ms: float, 
                       success: bool, cost: float = 0.0):
        """Registriere einen API-Call"""
        if api_name not in self.api_metrics:
            self.api_metrics[api_name] = APIMetrics(api_name=api_name)
        
        self.api_metrics[api_name].record_call(duration_ms, success, cost)
    
    def record_confidence(self, operation: str, confidence: float):
        """Registriere einen Confidence Score"""
        if operation not in self.confidence_metrics:
            self.confidence_metrics[operation] = ConfidenceMetrics(operation=operation)
        
        self.confidence_metrics[operation].record_confidence(confidence)
    
    def record_error(self, error_type: str):
        """Registriere einen Fehler"""
        self.total_errors += 1
        self.error_types[error_type] = self.error_types.get(error_type, 0) + 1
    
    def get_summary(self) -> Dict:
        """Erstelle eine Zusammenfassung aller Metriken"""
        session_duration = (datetime.now() - self.session_start).total_seconds()
        
        return {
            "collector_name": self.name,
            "session_start": self.session_start.isoformat(),
            "session_duration_seconds": session_duration,
            "total_errors": self.total_errors,
            "error_types": self.error_types,
            "api_metrics": {
                name: metrics.to_dict()
                for name, metrics in self.api_metrics.items()
            },
            "confidence_metrics": {
                name: metrics.to_dict()
                for name, metrics in self.confidence_metrics.items()
            },
            "summary": {
                "total_api_calls": sum(m.total_calls for m in self.api_metrics.values()),
                "total_cost": sum(m.estimated_cost for m in self.api_metrics.values()),
                "overall_success_rate": self._calculate_overall_success_rate(),
                "avg_response_time_ms": self._calculate_avg_response_time()
            }
        }
    
    def _calculate_overall_success_rate(self) -> float:
        """Berechne die gesamte Success Rate"""
        total_calls = sum(m.total_calls for m in self.api_metrics.values())
        successful_calls = sum(m.successful_calls for m in self.api_metrics.values())
        return successful_calls / total_calls if total_calls > 0 else 0.0
    
    def _calculate_avg_response_time(self) -> float:
        """Berechne die durchschnittliche Response Time"""
        total_duration = sum(m.total_duration_ms for m in self.api_metrics.values())
        total_calls = sum(m.total_calls for m in self.api_metrics.values())
        return total_duration / total_calls if total_calls > 0 else 0.0
    
    def save_report(self, filename: Optional[str] = None, output_dir: str = "logs"):
        """Speichere einen Metriken-Report"""
        Path(output_dir).mkdir(exist_ok=True)
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_report_{self.name}_{timestamp}.json"
        
        filepath = Path(output_dir) / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.get_summary(), f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    def get_api_stats(self, api_name: str) -> Optional[Dict]:
        """Hole Statistiken für eine spezifische API"""
        if api_name in self.api_metrics:
            return self.api_metrics[api_name].to_dict()
        return None
    
    def get_top_apis_by_calls(self, limit: int = 5) -> List[Dict]:
        """Hole die Top APIs nach Anzahl der Calls"""
        sorted_apis = sorted(
            self.api_metrics.items(),
            key=lambda x: x[1].total_calls,
            reverse=True
        )
        return [
            {"api": name, **metrics.to_dict()}
            for name, metrics in sorted_apis[:limit]
        ]
    
    def get_top_apis_by_cost(self, limit: int = 5) -> List[Dict]:
        """Hole die Top APIs nach Kosten"""
        sorted_apis = sorted(
            self.api_metrics.items(),
            key=lambda x: x[1].estimated_cost,
            reverse=True
        )
        return [
            {"api": name, **metrics.to_dict()}
            for name, metrics in sorted_apis[:limit]
        ]
    
    def reset(self):
        """Setze alle Metriken zurück"""
        self.api_metrics.clear()
        self.confidence_metrics.clear()
        self.session_start = datetime.now()
        self.total_errors = 0
        self.error_types.clear()


# Globaler Metrics Collector
_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector(name: str = "global") -> MetricsCollector:
    """Hole oder erstelle den globalen Metrics Collector"""
    global _global_collector
    if _global_collector is None or _global_collector.name != name:
        _global_collector = MetricsCollector(name)
    return _global_collector