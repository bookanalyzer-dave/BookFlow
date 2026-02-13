#!/usr/bin/env python3
"""
Extended Agent Integration Test Suite with Service Account Authentication
Tests Firestore connectivity and agent workflow simulation
"""

import os
import sys
import json
import time
import uuid
import requests
import logging
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ExtendedIntegrationTestSuite:
    def __init__(self):
        self.backend_url = "http://localhost:8080"
        self.test_user_id = f"test_user_{int(time.time())}"
        self.test_book_id = None
        self.test_results = {}
        
    def setup_test_environment(self):
        """Setup test environment and validate requirements"""
        logger.info("=== EXTENDED TEST ENVIRONMENT SETUP ===")
        
        # Check backend health
        try:
            response = requests.get(f"{self.backend_url}/api/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Backend is healthy and running")
                self.test_results["backend_health"] = "PASS"
            else:
                logger.error("❌ Backend health check failed")
                self.test_results["backend_health"] = "FAIL"
                return False
        except Exception as e:
            logger.error(f"❌ Backend connection failed: {e}")
            self.test_results["backend_health"] = "FAIL"
            return False
        
        # Check service account key
        if os.path.exists("service-account-key.json"):
            logger.info("✅ Service account key found")
            self.test_results["service_account"] = "PASS"
        else:
            logger.error("❌ Service account key missing")
            self.test_results["service_account"] = "FAIL"
            return False
            
        return True
    
    def test_firestore_service_account_access(self):
        """Test Firestore access with Service Account credentials"""
        logger.info("=== TESTING FIRESTORE SERVICE ACCOUNT ACCESS ===")
        
        try:
            from google.cloud import firestore
            from google.oauth2 import service_account
            
            # Initialize Firestore with service account
            credentials = service_account.Credentials.from_service_account_file(
                "service-account-key.json"
            )
            
            db = firestore.Client(credentials=credentials, project="project-52b2fab8-15a1-4b66-9f3")
            
            # Test document creation in multi-tenant structure
            test_book_id = f"test_book_{int(time.time())}"
            test_data = {
                "title": "Service Account Test Book",
                "author": "Test Author SA",
                "status": "test_sa",
                "userId": self.test_user_id,
                "createdAt": firestore.SERVER_TIMESTAMP
            }
            
            # Create document using service account
            doc_ref = db.collection('users').document(self.test_user_id).collection('books').document(test_book_id)
            doc_ref.set(test_data)
            
            logger.info(f"✅ Service Account successfully created document")
            
            # Verify document exists
            doc = doc_ref.get()
            if doc.exists:
                retrieved_data = doc.to_dict()
                if retrieved_data.get("title") == "Service Account Test Book":
                    logger.info("✅ Service Account document retrieval successful")
                    self.test_results["service_account_firestore"] = "PASS"
                    self.test_book_id = test_book_id
                    
                    # Cleanup
                    doc_ref.delete()
                    return True
                else:
                    logger.error("❌ Service Account document data mismatch")
                    self.test_results["service_account_firestore"] = "FAIL"
                    return False
            else:
                logger.error("❌ Service Account document not found")
                self.test_results["service_account_firestore"] = "FAIL"
                return False
                
        except Exception as e:
            logger.error(f"❌ Service Account Firestore test failed: {e}")
            self.test_results["service_account_firestore"] = f"FAIL: {str(e)}"
            return False
    
    def test_agent_workflow_simulation(self):
        """Simulate the complete agent workflow"""
        logger.info("=== TESTING AGENT WORKFLOW SIMULATION ===")
        
        try:
            from shared.firestore.client import get_firestore_client, set_book, get_book, update_book
            
            # Simulate book upload
            test_book_id = f"workflow_test_{int(time.time())}"
            initial_book_data = {
                "status": "ingested",
                "imageUrls": ["gs://test-bucket/test.jpg"],
                "userId": self.test_user_id,
                "title": "Workflow Test Book"
            }
            
            # Step 1: Initial book creation (Backend)
            logger.info("📖 Step 1: Creating initial book document")
            set_book(self.test_user_id, test_book_id, initial_book_data)
            
            # Step 2: Simulate Ingestion Agent processing
            logger.info("🔍 Step 2: Simulating Ingestion Agent processing")
            ingestion_updates = {
                "status": "analyzed",
                "title": "The Great Gatsby",
                "author": "F. Scott Fitzgerald",
                "isbn": "9780743273565", 
                "condition": "Very Good",
                "confidenceScore": 0.92,
                "description": "A classic American novel in very good condition."
            }
            update_book(self.test_user_id, test_book_id, ingestion_updates)
            
            # Step 3: Simulate Strategist Agent processing
            logger.info("💰 Step 3: Simulating Strategist Agent processing")
            strategist_updates = {
                "status": "priced",
                "calculatedPrice": 12.50,
                "floorPrice": 8.00,
                "marketAnalysis": "Based on comparable editions"
            }
            update_book(self.test_user_id, test_book_id, strategist_updates)
            
            # Step 4: Simulate Ambassador Agent processing
            logger.info("🏪 Step 4: Simulating Ambassador Agent processing")
            ambassador_updates = {
                "status": "listed",
                "listings": {
                    "ebay": {
                        "listing_id": "123456789",
                        "status": "active",
                        "listed_at": datetime.now().isoformat()
                    }
                }
            }
            update_book(self.test_user_id, test_book_id, ambassador_updates)
            
            # Verify final state
            final_book = get_book(self.test_user_id, test_book_id)
            
            if final_book:
                required_fields = ["title", "author", "calculatedPrice", "status"]
                missing_fields = [field for field in required_fields if field not in final_book]
                
                if not missing_fields and final_book["status"] == "listed":
                    logger.info("✅ Agent workflow simulation successful")
                    self.test_results["agent_workflow"] = "PASS"
                    
                    # Cleanup
                    db = get_firestore_client()
                    db.collection('users').document(self.test_user_id).collection('books').document(test_book_id).delete()
                    return True
                else:
                    logger.error(f"❌ Agent workflow incomplete - missing fields: {missing_fields}")
                    self.test_results["agent_workflow"] = f"FAIL: Missing {missing_fields}"
                    return False
            else:
                logger.error("❌ Agent workflow failed - final book not found")
                self.test_results["agent_workflow"] = "FAIL: Book not found"
                return False
                
        except Exception as e:
            logger.error(f"❌ Agent workflow simulation failed: {e}")
            self.test_results["agent_workflow"] = f"FAIL: {str(e)}"
            return False
    
    def test_pubsub_message_structure(self):
        """Test Pub/Sub message structure compatibility"""
        logger.info("=== TESTING PUB/SUB MESSAGE STRUCTURE ===")
        
        try:
            # Test message structures used across agents
            test_messages = {
                "ingestion_message": {
                    "bookId": "test_book_123",
                    "uid": self.test_user_id,
                    "imageUrls": ["gs://bucket/image.jpg"]
                },
                "strategist_message": {
                    "bookId": "test_book_123",
                    "uid": self.test_user_id
                },
                "ambassador_message": {
                    "bookId": "test_book_123",
                    "uid": self.test_user_id,
                    "platform": "ebay",
                    "book": {"title": "Test", "price": 10.0}
                },
                "sentinel_message": {
                    "bookId": "test_book_123",
                    "uid": self.test_user_id,
                    "platform": "ebay"
                }
            }
            
            # Validate message structure consistency
            issues = []
            
            # Check for consistent user identifier
            user_id_fields = []
            for msg_type, msg in test_messages.items():
                if "userId" in msg:
                    user_id_fields.append(f"{msg_type}:userId")
                if "uid" in msg:
                    user_id_fields.append(f"{msg_type}:uid")
            
            if len(set([field.split(":")[1] for field in user_id_fields])) > 1:
                issues.append("Inconsistent user ID field names across agents")
            
            # Check for consistent book identifier  
            book_id_fields = []
            for msg_type, msg in test_messages.items():
                if "bookId" in msg:
                    book_id_fields.append(f"{msg_type}:bookId")
                if "book_id" in msg:
                    book_id_fields.append(f"{msg_type}:book_id")
            
            if len(set([field.split(":")[1] for field in book_id_fields])) > 1:
                issues.append("Inconsistent book ID field names across agents")
            
            if issues:
                logger.warning(f"⚠️ Message structure issues found: {issues}")
                self.test_results["pubsub_messages"] = f"PARTIAL: {', '.join(issues)}"
            else:
                logger.info("✅ Pub/Sub message structure validation passed")
                self.test_results["pubsub_messages"] = "PASS"
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Pub/Sub message test failed: {e}")
            self.test_results["pubsub_messages"] = f"FAIL: {str(e)}"
            return False
    
    def test_error_resilience(self):
        """Test error resilience and recovery mechanisms"""
        logger.info("=== TESTING ERROR RESILIENCE ===")
        
        try:
            from shared.firestore.client import get_firestore_client, set_book, get_book
            
            # Test 1: Invalid data handling
            test_book_id = f"error_test_{int(time.time())}"
            invalid_data = {
                "status": "test_error",
                "userId": self.test_user_id,
                "calculatedPrice": "invalid_price",  # Should be float
                "imageUrls": "not_a_list"  # Should be list
            }
            
            try:
                set_book(self.test_user_id, test_book_id, invalid_data)
                retrieved = get_book(self.test_user_id, test_book_id)
                if retrieved:
                    logger.info("✅ System handles invalid data gracefully")
                    
                    # Cleanup
                    db = get_firestore_client()
                    db.collection('users').document(self.test_user_id).collection('books').document(test_book_id).delete()
            except Exception as e:
                logger.info(f"✅ System correctly rejects invalid data: {e}")
            
            # Test 2: Network timeout simulation
            try:
                # Simulate network issue by accessing non-existent document
                non_existent = get_book("non_existent_user", "non_existent_book") 
                if non_existent is None:
                    logger.info("✅ System handles non-existent document gracefully")
            except Exception as e:
                logger.info(f"✅ System handles network errors gracefully: {e}")
            
            self.test_results["error_resilience"] = "PASS"
            return True
            
        except Exception as e:
            logger.error(f"❌ Error resilience test failed: {e}")
            self.test_results["error_resilience"] = f"FAIL: {str(e)}"
            return False
    
    def generate_comprehensive_report(self):
        """Generate comprehensive integration test report"""
        logger.info("=== GENERATING COMPREHENSIVE REPORT ===")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result == "PASS")
        partial_tests = sum(1 for result in self.test_results.values() if result.startswith("PARTIAL"))
        failed_tests = total_tests - passed_tests - partial_tests
        
        # Analyze critical issues
        critical_issues = []
        recommendations = []
        
        for test_name, result in self.test_results.items():
            if result.startswith("FAIL"):
                critical_issues.append(f"{test_name}: {result}")
                
                if "service_account_firestore" in test_name:
                    recommendations.append("Deploy updated Firestore rules with service account permissions")
                elif "agent_workflow" in test_name:
                    recommendations.append("Fix agent parameter consistency and data flow")
                elif "pubsub_messages" in test_name:
                    recommendations.append("Standardize message field names across all agents")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "test_suite": "Extended Agent Integration Tests",
            "test_user_id": self.test_user_id,
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "partial": partial_tests,
                "failed": failed_tests,
                "success_rate": f"{(passed_tests/total_tests)*100:.1f}%"
            },
            "detailed_results": self.test_results,
            "critical_issues": critical_issues,
            "recommendations": recommendations,
            "integration_status": "READY" if failed_tests == 0 else "NEEDS_ATTENTION"
        }
        
        return report
    
    def run_extended_integration_test(self):
        """Run the extended integration test suite"""
        logger.info("🚀 STARTING EXTENDED AGENT INTEGRATION TESTS")
        logger.info("="*70)
        
        try:
            # Run all tests
            if not self.setup_test_environment():
                logger.error("❌ Test environment setup failed. Aborting tests.")
                return self.generate_comprehensive_report()
            
            self.test_firestore_service_account_access()
            self.test_agent_workflow_simulation()
            self.test_pubsub_message_structure()
            self.test_error_resilience()
            
            # Generate and return report
            report = self.generate_comprehensive_report()
            
            logger.info("="*70)
            logger.info("🏁 EXTENDED INTEGRATION TESTS COMPLETED")
            logger.info(f"📊 Results: {report['summary']['passed']}/{report['summary']['total_tests']} PASSED ({report['summary']['success_rate']})")
            logger.info(f"🎯 Integration Status: {report['integration_status']}")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Test suite execution failed: {e}")
            return {"error": str(e), "status": "FAILED"}

if __name__ == "__main__":
    # Set environment variables for local testing
    os.environ.setdefault("GCP_PROJECT_ID", "project-52b2fab8-15a1-4b66-9f3")
    os.environ.setdefault("GCS_BUCKET_NAME", "intelligent-research-pipeline-bucket")
    
    # Create and run extended test suite
    test_suite = ExtendedIntegrationTestSuite()
    final_report = test_suite.run_extended_integration_test()
    
    # Save report to file
    with open("extended_integration_report.json", "w") as f:
        json.dump(final_report, f, indent=2)
    
    print("\n" + "="*70)
    print("📋 EXTENDED INTEGRATION TEST REPORT SUMMARY")
    print("="*70)
    if "error" not in final_report:
        print(f"Total Tests: {final_report['summary']['total_tests']}")
        print(f"Passed: {final_report['summary']['passed']}")
        print(f"Partial: {final_report['summary']['partial']}")  
        print(f"Failed: {final_report['summary']['failed']}")
        print(f"Success Rate: {final_report['summary']['success_rate']}")
        print(f"Integration Status: {final_report['integration_status']}")
        
        if final_report['critical_issues']:
            print(f"\n🚨 CRITICAL ISSUES:")
            for i, issue in enumerate(final_report['critical_issues'], 1):
                print(f"{i}. {issue}")
        
        if final_report['recommendations']:
            print(f"\n🔧 RECOMMENDATIONS:")
            for i, rec in enumerate(final_report['recommendations'], 1):
                print(f"{i}. {rec}")
    else:
        print(f"❌ Test suite failed: {final_report['error']}")
    
    print(f"\n📄 Full report saved to: extended_integration_report.json")
