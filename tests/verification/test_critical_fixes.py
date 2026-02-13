"""
Test script for critical fixes validation
Tests the following:
1. Status transitions validation
2. Pub/Sub topic configuration
3. Requirements.txt validation
"""

import sys
import os

# Test 1: Verify Status Transitions
print("=" * 60)
print("TEST 1: Validating Status Transitions")
print("=" * 60)

try:
    from shared.firestore.client import VALID_STATUS_TRANSITIONS
    
    # Check that new transitions exist
    required_transitions = {
        "ingested": ["condition_assessment_pending", "failed"],
        "condition_assessment_pending": ["processing_condition", "failed"],
        "processing_condition": ["condition_assessed", "failed"],
        "delisted": ["listed"],
        "failed": ["ingested"]
    }
    
    all_valid = True
    for status, expected_transitions in required_transitions.items():
        actual = VALID_STATUS_TRANSITIONS.get(status, [])
        if actual != expected_transitions:
            print(f"❌ FAILED: {status} -> Expected: {expected_transitions}, Got: {actual}")
            all_valid = False
        else:
            print(f"✅ PASSED: {status} -> {expected_transitions}")
    
    if all_valid:
        print("\n✅ All status transitions are correctly configured!")
    else:
        print("\n❌ Some status transitions are incorrect!")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ ERROR importing VALID_STATUS_TRANSITIONS: {e}")
    sys.exit(1)

# Test 2: Verify Pub/Sub Configuration
print("\n" + "=" * 60)
print("TEST 2: Validating Pub/Sub Configuration")
print("=" * 60)

try:
    # Check if main.py has the condition_assessment_topic_path
    main_py_path = os.path.join("dashboard", "backend", "main.py")
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ("condition_assessment_topic", "Condition Assessment Topic variable"),
        ("trigger-condition-assessment", "Condition Assessment Topic name"),
        ("condition_assessment_topic_path", "Condition Assessment Topic path"),
        ("publisher.publish(condition_assessment_topic_path", "Pub/Sub publish call")
    ]
    
    all_present = True
    for check_str, description in checks:
        if check_str in content:
            print(f"✅ PASSED: {description} found")
        else:
            print(f"❌ FAILED: {description} NOT found")
            all_present = False
    
    if all_present:
        print("\n✅ Pub/Sub configuration is correct!")
    else:
        print("\n❌ Pub/Sub configuration is incomplete!")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ ERROR checking Pub/Sub configuration: {e}")
    sys.exit(1)

# Test 3: Verify Requirements
print("\n" + "=" * 60)
print("TEST 3: Validating Requirements")
print("=" * 60)

try:
    req_path = os.path.join("dashboard", "backend", "requirements.txt")
    with open(req_path, 'r', encoding='utf-8') as f:
        requirements = f.read()
    
    required_packages = [
        "google-cloud-pubsub",
        "google-cloud-firestore",
        "google-cloud-storage"
    ]
    
    all_present = True
    for pkg in required_packages:
        if pkg in requirements:
            print(f"✅ PASSED: {pkg} is in requirements.txt")
        else:
            print(f"❌ FAILED: {pkg} NOT in requirements.txt")
            all_present = False
    
    if all_present:
        print("\n✅ All required packages are present!")
    else:
        print("\n❌ Some required packages are missing!")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ ERROR checking requirements: {e}")
    sys.exit(1)

# Test 4: Verify .env.yaml cleanups
print("\n" + "=" * 60)
print("TEST 4: Validating .env.yaml Cleanups")
print("=" * 60)

try:
    # Check condition-assessor .env.yaml
    condition_assessor_env = os.path.join("agents", "condition-assessor", ".env.yaml")
    with open(condition_assessor_env, 'r', encoding='utf-8') as f:
        ca_content = f.read()
    
    # These should NOT be present anymore
    removed_vars = [
        "FINE_THRESHOLD",
        "VERY_FINE_THRESHOLD",
        "GOOD_THRESHOLD",
        "FAIR_THRESHOLD",
        "COVER_WEIGHT",
        "SPINE_WEIGHT",
        "PAGES_WEIGHT",
        "BINDING_WEIGHT",
        "FINE_PRICE_FACTOR",
        "VERY_FINE_PRICE_FACTOR"
    ]
    
    all_removed = True
    for var in removed_vars:
        if var in ca_content:
            print(f"❌ FAILED: {var} still present in condition-assessor/.env.yaml")
            all_removed = False
    
    if all_removed:
        print("✅ PASSED: Unused thresholds removed from condition-assessor/.env.yaml")
    
    # Check ingestion-agent .env.yaml
    ingestion_env = os.path.join("agents", "ingestion-agent", ".env.yaml")
    with open(ingestion_env, 'r', encoding='utf-8') as f:
        ing_content = f.read()
    
    # Count occurrences of LOG_LEVEL (should be only 1)
    log_level_count = ing_content.count("LOG_LEVEL:")
    if log_level_count == 1:
        print("✅ PASSED: Duplicate LOG_LEVEL removed from ingestion-agent/.env.yaml")
    else:
        print(f"❌ FAILED: LOG_LEVEL appears {log_level_count} times in ingestion-agent/.env.yaml")
        all_removed = False
    
    if all_removed:
        print("\n✅ .env.yaml files are properly cleaned up!")
    else:
        print("\n❌ .env.yaml cleanups incomplete!")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ ERROR checking .env.yaml files: {e}")
    sys.exit(1)

# Test 5: Verify .gitignore
print("\n" + "=" * 60)
print("TEST 5: Validating .gitignore")
print("=" * 60)

try:
    if os.path.exists(".gitignore"):
        with open(".gitignore", 'r', encoding='utf-8') as f:
            gitignore = f.read()
        
        if "agents/*/shared/" in gitignore:
            print("✅ PASSED: .gitignore contains entry for redundant shared copies")
        else:
            print("❌ FAILED: .gitignore missing entry for agents/*/shared/")
            sys.exit(1)
    else:
        print("❌ FAILED: .gitignore file not found")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ ERROR checking .gitignore: {e}")
    sys.exit(1)

# Final Summary
print("\n" + "=" * 60)
print("🎉 ALL CRITICAL FIXES VALIDATED SUCCESSFULLY!")
print("=" * 60)
print("\nSummary of implemented fixes:")
print("✅ 1. Pub/Sub publish for Condition Assessment added")
print("✅ 2. Status transitions extended with new states")
print("✅ 3. .env.yaml files cleaned up")
print("✅ 4. .gitignore created with redundant copies entry")
print("\nNext steps:")
print("- Deploy changes to production")
print("- Monitor condition assessment workflow")
print("- Test end-to-end flow with real books")
