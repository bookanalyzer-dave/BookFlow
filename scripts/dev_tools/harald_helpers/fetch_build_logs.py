import os
from google.cloud import logging

# Set up logging client
client = logging.Client()
build_id = "8bc25290-7a47-4920-bd9e-7ddde85164e5"  # Letzter fehlgeschlagener Build
project_id = "project-52b2fab8-15a1-4b66-9f3"

# Advanced Filter: Nur ERROR und CRITICAL, die zum Build gehören
filter_str = (
    f'resource.type="build" AND '
    f'resource.labels.build_id="{build_id}" AND '
    f'severity>=ERROR'
)

print(f"--- FETCHING LOGS FOR BUILD {build_id} ---")
try:
    entries = client.list_entries(filter_=filter_str, order_by=logging.DESCENDING, max_results=20)
    found_any = False
    for entry in entries:
        found_any = True
        print(f"[{entry.severity}] {entry.timestamp}: {entry.payload}")
    
    if not found_any:
        # Fallback: Versuche Text-Payloads ohne Severity-Filter (für Build-Output)
        print("--- NO ERRORS FOUND via Filter. Checking raw text payload... ---")
        filter_raw = (
            f'resource.type="build" AND '
            f'resource.labels.build_id="{build_id}"'
        )
        entries_raw = client.list_entries(filter_=filter_raw, order_by=logging.DESCENDING, max_results=50)
        for entry in entries_raw:
             # Suche nach "error" im Text
             if hasattr(entry, 'text_payload') and "error" in str(entry.text_payload).lower():
                 print(f"[RAW TEXT] {entry.timestamp}: {entry.text_payload}")
                 found_any = True
        
        if not found_any:
            print("--- STILL NOTHING. Trying Cloud Build specific log resource... ---")

except Exception as e:
    print(f"FAILED TO FETCH LOGS: {e}")
