#!/usr/bin/env python3
"""
System Monitoring Dashboard

Zeigt Logs, Metriken und Performance-Statistiken für das Monitoring-System an.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import argparse


def print_header(title: str, width: int = 80):
    """Druckt einen formatierten Header"""
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def print_section(title: str, width: int = 80):
    """Druckt einen formatierten Section-Header"""
    print("\n" + "-" * width)
    print(f"  {title}")
    print("-" * width)


def read_log_file(log_path: str, num_lines: int = 100) -> List[str]:
    """Liest die letzten N Zeilen aus einer Log-Datei"""
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return lines[-num_lines:]
    except FileNotFoundError:
        return []
    except Exception as e:
        return [f"Error reading log file: {e}"]


def parse_log_line(line: str) -> Dict[str, Any]:
    """Parsed eine Log-Zeile in ihre Komponenten"""
    try:
        # Format: timestamp - name - level - message
        parts = line.split(' - ', 3)
        if len(parts) >= 4:
            return {
                'timestamp': parts[0],
                'name': parts[1],
                'level': parts[2],
                'message': parts[3].strip()
            }
    except:
        pass
    return {'raw': line.strip()}


def analyze_logs(lines: List[str]) -> Dict[str, Any]:
    """Analysiert Log-Zeilen und extrahiert Statistiken"""
    stats = {
        'total': len(lines),
        'info': 0,
        'warning': 0,
        'error': 0,
        'api_calls': 0,
        'performance': 0,
        'confidence': 0,
        'grounding': 0
    }
    
    for line in lines:
        parsed = parse_log_line(line)
        level = parsed.get('level', '')
        message = parsed.get('message', '')
        
        if level == 'INFO':
            stats['info'] += 1
        elif level == 'WARNING':
            stats['warning'] += 1
        elif level == 'ERROR':
            stats['error'] += 1
        
        if 'API_CALL' in message:
            stats['api_calls'] += 1
        if 'PERFORMANCE' in message:
            stats['performance'] += 1
        if 'CONFIDENCE' in message:
            stats['confidence'] += 1
        if 'GROUNDING' in message:
            stats['grounding'] += 1
    
    return stats


def load_metrics_report(log_dir: str = "logs") -> Dict[str, Any]:
    """Lädt den neuesten Metrics Report"""
    log_path = Path(log_dir)
    if not log_path.exists():
        return {}
    
    # Finde neuesten metrics_report
    reports = list(log_path.glob("metrics_report_*.json"))
    if not reports:
        return {}
    
    latest = max(reports, key=lambda p: p.stat().st_mtime)
    
    try:
        with open(latest, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


def display_logs(log_dir: str = "logs", num_lines: int = 100, 
                 log_name: str = "search_grounding"):
    """Zeigt Log-Einträge an"""
    print_header("📋 LOG VIEWER")
    
    log_path = Path(log_dir) / f"{log_name}.log"
    
    if not log_path.exists():
        print(f"❌ Log-Datei nicht gefunden: {log_path}")
        return
    
    print(f"\n📁 Log-Datei: {log_path}")
    print(f"📊 Zeige letzte {num_lines} Einträge\n")
    
    lines = read_log_file(str(log_path), num_lines)
    
    if not lines:
        print("Keine Log-Einträge gefunden.")
        return
    
    # Analyse
    stats = analyze_logs(lines)
    
    print_section("Log Statistiken")
    print(f"  Gesamt Einträge: {stats['total']}")
    print(f"  INFO:    {stats['info']} ({stats['info']/stats['total']*100:.1f}%)")
    print(f"  WARNING: {stats['warning']} ({stats['warning']/stats['total']*100:.1f}%)")
    print(f"  ERROR:   {stats['error']} ({stats['error']/stats['total']*100:.1f}%)")
    print(f"\n  API Calls:    {stats['api_calls']}")
    print(f"  Performance:  {stats['performance']}")
    print(f"  Confidence:   {stats['confidence']}")
    print(f"  Grounding:    {stats['grounding']}")
    
    # Zeige letzte Einträge
    print_section(f"Letzte {min(20, len(lines))} Log-Einträge")
    for line in lines[-20:]:
        parsed = parse_log_line(line)
        level = parsed.get('level', '')
        
        # Color coding
        if level == 'ERROR':
            print(f"🔴 {line.strip()}")
        elif level == 'WARNING':
            print(f"🟡 {line.strip()}")
        elif level == 'INFO':
            print(f"🟢 {line.strip()}")
        else:
            print(f"   {line.strip()}")


def display_errors(log_dir: str = "logs", log_name: str = "search_grounding"):
    """Zeigt nur Fehler-Logs an"""
    print_header("🔴 ERROR LOGS")
    
    error_log_path = Path(log_dir) / f"{log_name}_errors.log"
    
    if not error_log_path.exists():
        print(f"✅ Keine Fehler-Log-Datei gefunden (keine Fehler aufgetreten)")
        return
    
    lines = read_log_file(str(error_log_path), 50)
    
    if not lines:
        print("✅ Keine Fehler aufgezeichnet!")
        return
    
    print(f"\n📁 Fehler-Log-Datei: {error_log_path}")
    print(f"📊 Anzahl Fehler: {len(lines)}\n")
    
    for line in lines:
        print(f"🔴 {line.strip()}")


def display_metrics(log_dir: str = "logs"):
    """Zeigt Metriken-Dashboard an"""
    print_header("📊 METRIKEN DASHBOARD")
    
    metrics = load_metrics_report(log_dir)
    
    if not metrics:
        print("❌ Keine Metriken gefunden. Führe zuerst einen Test aus!")
        return
    
    print(f"\n⏱️  Session Start: {metrics.get('session_start', 'N/A')}")
    print(f"⏱️  Session Dauer: {metrics.get('session_duration_seconds', 0):.2f} Sekunden")
    print(f"❌ Gesamte Fehler: {metrics.get('total_errors', 0)}")
    
    # API Metriken
    api_metrics = metrics.get('api_metrics', {})
    if api_metrics:
        print_section("🌐 API Metriken")
        
        for api_name, stats in api_metrics.items():
            print(f"\n  API: {api_name}")
            print(f"    Calls: {stats.get('total_calls', 0)}")
            print(f"    Erfolg: {stats.get('successful_calls', 0)}")
            print(f"    Fehler: {stats.get('failed_calls', 0)}")
            print(f"    Success Rate: {stats.get('success_rate', 0)*100:.1f}%")
            print(f"    Ø Duration: {stats.get('avg_duration_ms', 0):.2f} ms")
            print(f"    Min Duration: {stats.get('min_duration_ms', 0):.2f} ms")
            print(f"    Max Duration: {stats.get('max_duration_ms', 0):.2f} ms")
            print(f"    Geschätzte Kosten: ${stats.get('estimated_cost', 0):.4f}")
    
    # Confidence Metriken
    confidence_metrics = metrics.get('confidence_metrics', {})
    if confidence_metrics:
        print_section("🎯 Confidence Metriken")
        
        for op_name, stats in confidence_metrics.items():
            print(f"\n  Operation: {op_name}")
            print(f"    Operationen: {stats.get('total_operations', 0)}")
            print(f"    Ø Confidence: {stats.get('avg_confidence', 0)*100:.1f}%")
            print(f"    Min: {stats.get('min_confidence', 0)*100:.1f}%")
            print(f"    Max: {stats.get('max_confidence', 0)*100:.1f}%")
            print(f"    Low (<70%): {stats.get('low_confidence_count', 0)} ({stats.get('low_confidence_percent', 0):.1f}%)")
            print(f"    Medium (70-85%): {stats.get('medium_confidence_count', 0)}")
            print(f"    High (>85%): {stats.get('high_confidence_count', 0)}")
    
    # Summary
    summary = metrics.get('summary', {})
    if summary:
        print_section("📈 Zusammenfassung")
        print(f"  Total API Calls: {summary.get('total_api_calls', 0)}")
        print(f"  Total Kosten: ${summary.get('total_cost', 0):.4f}")
        print(f"  Overall Success Rate: {summary.get('overall_success_rate', 0)*100:.1f}%")
        print(f"  Ø Response Time: {summary.get('avg_response_time_ms', 0):.2f} ms")
    
    # Error Types
    error_types = metrics.get('error_types', {})
    if error_types:
        print_section("⚠️  Fehler-Typen")
        for error_type, count in error_types.items():
            print(f"  {error_type}: {count}")


def display_system_info(log_dir: str = "logs"):
    """Zeigt System-Informationen an"""
    print_header("🖥️  SYSTEM INFO")
    
    log_path = Path(log_dir)
    
    # Check if logs directory exists
    if log_path.exists():
        print(f"\n✅ Logs-Verzeichnis: {log_path.absolute()}")
        
        # List all log files
        log_files = list(log_path.glob("*.log"))
        json_files = list(log_path.glob("*.json"))
        
        print(f"\n📁 Log-Dateien ({len(log_files)}):")
        for log_file in sorted(log_files):
            size = log_file.stat().st_size
            modified = datetime.fromtimestamp(log_file.stat().st_mtime)
            print(f"  - {log_file.name} ({size} bytes, modified: {modified.strftime('%Y-%m-%d %H:%M:%S')})")
        
        print(f"\n📊 Metriken-Dateien ({len(json_files)}):")
        for json_file in sorted(json_files):
            size = json_file.stat().st_size
            modified = datetime.fromtimestamp(json_file.stat().st_mtime)
            print(f"  - {json_file.name} ({size} bytes, modified: {modified.strftime('%Y-%m-%d %H:%M:%S')})")
    else:
        print(f"\n❌ Logs-Verzeichnis nicht gefunden: {log_path.absolute()}")
        print("   Führe zuerst einen Test aus, um Logs zu generieren!")


def main():
    parser = argparse.ArgumentParser(
        description="System Monitoring Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--logs', '-l',
        action='store_true',
        help='Zeige Log-Einträge an'
    )
    
    parser.add_argument(
        '--errors', '-e',
        action='store_true',
        help='Zeige nur Fehler-Logs an'
    )
    
    parser.add_argument(
        '--metrics', '-m',
        action='store_true',
        help='Zeige Metriken-Dashboard an'
    )
    
    parser.add_argument(
        '--system', '-s',
        action='store_true',
        help='Zeige System-Informationen an'
    )
    
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Zeige alles an (Standard)'
    )
    
    parser.add_argument(
        '--lines', '-n',
        type=int,
        default=100,
        help='Anzahl der anzuzeigenden Log-Zeilen (Standard: 100)'
    )
    
    parser.add_argument(
        '--log-dir',
        default='logs',
        help='Verzeichnis mit Log-Dateien (Standard: logs)'
    )
    
    parser.add_argument(
        '--log-name',
        default='search_grounding',
        help='Name der Log-Datei (Standard: search_grounding)'
    )
    
    args = parser.parse_args()
    
    # Wenn keine spezifische Option gewählt, zeige alles
    show_all = args.all or not (args.logs or args.errors or args.metrics or args.system)
    
    print("\n" + "=" * 80)
    print("  📊 SYSTEM MONITORING DASHBOARD")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 80)
    
    if show_all or args.system:
        display_system_info(args.log_dir)
    
    if show_all or args.metrics:
        display_metrics(args.log_dir)
    
    if show_all or args.errors:
        display_errors(args.log_dir, args.log_name)
    
    if show_all or args.logs:
        display_logs(args.log_dir, args.lines, args.log_name)
    
    print("\n" + "=" * 80)
    print("  Dashboard Ende")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()