#!/usr/bin/env python3
"""
Test Script für das Monitoring-System
Testet das Speichern von Metriken-Reports
"""

import asyncio
from shared.apis.search_grounding import GoogleSearchGrounding
from shared.monitoring.metrics import get_metrics_collector

async def test_metrics_collection():
    """Testet die Metriken-Sammlung"""
    print("\n" + "="*80)
    print("  📊 Testing Metrics Collection")
    print("="*80)
    
    # Initialize client
    client = GoogleSearchGrounding()
    
    # Hole Metrics Collector
    metrics = get_metrics_collector("test_monitoring")
    
    print("\n✅ Metrics Collector initialisiert")
    print(f"   Collector Name: {metrics.name}")
    print(f"   Session Start: {metrics.session_start}")
    
    # Führe einen einfachen Test durch
    print("\n🔍 Führe Test-API-Call durch...")
    result = await client.search_book_market_data(
        isbn="9780316769174",
        title="The Catcher in the Rye",
        author="J.D. Salinger"
    )
    
    print(f"\n✅ API Call erfolgreich")
    print(f"   Found Data: {result.get('found_data', False)}")
    print(f"   Confidence: {result.get('confidence', 0.0)}")
    
    # Speichere Metriken-Report
    print("\n💾 Speichere Metriken-Report...")
    report_path = metrics.save_report()
    print(f"✅ Report gespeichert: {report_path}")
    
    # Zeige Summary
    print("\n📊 Metriken-Summary:")
    summary = metrics.get_summary()
    print(f"   Session Duration: {summary['session_duration_seconds']:.2f}s")
    print(f"   Total Errors: {summary['total_errors']}")
    
    if summary['api_metrics']:
        print("\n   API Metriken:")
        for api_name, stats in summary['api_metrics'].items():
            print(f"   - {api_name}:")
            print(f"     Calls: {stats['total_calls']}")
            print(f"     Success Rate: {stats['success_rate']*100:.1f}%")
            print(f"     Avg Duration: {stats['avg_duration_ms']:.2f}ms")
    
    if summary['confidence_metrics']:
        print("\n   Confidence Metriken:")
        for op_name, stats in summary['confidence_metrics'].items():
            print(f"   - {op_name}:")
            print(f"     Operations: {stats['total_operations']}")
            print(f"     Avg Confidence: {stats['avg_confidence']*100:.1f}%")
    
    print("\n" + "="*80)
    print("  ✅ Metrics Collection Test erfolgreich!")
    print("="*80 + "\n")

if __name__ == "__main__":
    asyncio.run(test_metrics_collection())