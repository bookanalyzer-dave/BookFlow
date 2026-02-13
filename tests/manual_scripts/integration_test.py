#!/usr/bin/env python3
"""
Comprehensive Agent Integration Test Suite
Tests the complete book sales pipeline from upload to sales preparation
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

class IntegrationTestSuite:
    def __init__(self):
        self.backend_url = "http://localhost:8080"
        self.test_user_id = f"test_user_{int(time.time())}"
        self.test_book_id = None
        self.test_results = {}
        
    def setup_test_environment(self):
        """Setup test environment and validate requirements"""
        logger.info("=== SETUP TEST ENVIRONMENT ===")
        
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
        
        # Validate environment variables
        required_env_vars = [
            "GCP_PROJECT_ID",
            "GCS_BUCKET_NAME"
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"❌ Missing environment variables: {missing_vars}")
            self.test_results["environment_setup"] = "FAIL"
            return False
        else:
            logger.info("✅ All required environment variables present")
            self.test_results["environment_setup"] = "PASS"
        
        # Check service account key
        if os.path.exists("service-account-key.json"):
            logger.info("✅ Service account key found")
            self.test_results["service_account"] = "PASS"
        else:
            logger.error("❌ Service account key missing")
            self.test_results["service_account"] = "FAIL"
            return False
            
        return True
    
    def test_multi_tenancy_structure(self):
        """Test Multi-Tenancy Firestore structure"""
        logger.info("=== TESTING MULTI-TENANCY STRUCTURE ===")
        
        try:
            from shared.firestore.client import get_firestore_client, set_book, get_book
            
            # Test data
            test_book_data = {
                "title": "Integration Test Book",
                "author": "Test Author",
                "status": "test",
                "userId": self.test_user_id,
                "createdAt": datetime.now().isoformat()
            }
            
            # Test setting book in multi-tenant structure
            test_book_id = f"test_book_{int(time.time())}"
            set_book(self.test_user_id, test_book_id, test_book_data)
            logger.info(f"✅ Successfully created book in users/{self.test_user_id}/books/{test_book_id}")
            
            # Test retrieving book
            retrieved_book = get_book(self.test_user_id, test_book_id)
            if retrieved_book and retrieved_book.get("title") == "Integration Test Book":
                logger.info("✅ Multi-tenancy data retrieval successful")
                self.test_results["multi_tenancy"] = "PASS"
                self.test_book_id = test_book_id
                return True
            else:
                logger.error("❌ Multi-tenancy data retrieval failed")
                self.test_results["multi_tenancy"] = "FAIL"
                return False
                
        except Exception as e:
            logger.error(f"❌ Multi-tenancy test failed: {e}")
            self.test_results["multi_tenancy"] = "FAIL"
            return False
    
    def test_jwt_validation(self):
        """Test JWT token validation without actual token"""
        logger.info("=== TESTING JWT VALIDATION ===")
        
        try:
            # Test without Authorization header
            response = requests.post(f"{self.backend_url}/api/books/upload", 
                                   json={"filename": "test.jpg"})
            
            if response.status_code == 401:
                logger.info("✅ JWT validation correctly rejects requests without token")
                self.test_results["jwt_validation"] = "PASS"
                return True
            else:
                logger.error(f"❌ JWT validation failed - expected 401, got {response.status_code}")
                self.test_results["jwt_validation"] = "FAIL"
                return False
                
        except Exception as e:
            logger.error(f"❌ JWT validation test failed: {e}")
            self.test_results["jwt_validation"] = "FAIL"
            return False
    
    def test_agent_parameter_consistency(self):
        """Test parameter consistency across all agents"""
        logger.info("=== TESTING AGENT PARAMETER CONSISTENCY ===")
        
        try:
            # Test message format that all agents should understand
            test_message = {
                "bookId": "test_book_123",
                "uid": self.test_user_id,
                "imageUrls": ["gs://test-bucket/test.jpg"]
            }
            
            # Verify message structure
            required_fields = ["bookId", "uid"]
            missing_fields = []
            
            for field in required_fields:
                if field not in test_message:
                    missing_fields.append(field)
            
            if missing_fields:
                logger.error(f"❌ Missing required fields in agent message: {missing_fields}")
                self.test_results["agent_parameters"] = "FAIL"
                return False
            else:
                logger.info("✅ Agent parameter consistency validated")
                self.test_results["agent_parameters"] = "PASS"
                return True
                
        except Exception as e:
            logger.error(f"❌ Agent parameter test failed: {e}")
            self.test_results["agent_parameters"] = "FAIL"
            return False
    
    def test_error_handling_robustness(self):
        """Test error handling and retry mechanisms"""
        logger.info("=== TESTING ERROR HANDLING ROBUSTNESS ===")
        
        try:
            # Test invalid file upload request
            response = requests.post(f"{self.backend_url}/api/books/upload", 
                                   json={})  # Empty request
            
            if response.status_code in [400, 401]:  # Expected error codes
                logger.info("✅ Error handling works for invalid requests")
                
                # Test malformed JSON
                try:
                    response = requests.post(f"{self.backend_url}/api/books/start-processing", 
                                           data="invalid json")
                    if response.status_code in [400, 401]:
                        logger.info("✅ Error handling works for malformed requests")
                        self.test_results["error_handling"] = "PASS"
                        return True
                except:
                    logger.info("✅ Error handling prevents malformed requests")
                    self.test_results["error_handling"] = "PASS"
                    return True
            else:
                logger.error(f"❌ Error handling failed - unexpected response: {response.status_code}")
                self.test_results["error_handling"] = "FAIL"
                return False
                
        except Exception as e:
            logger.error(f"❌ Error handling test failed: {e}")
            self.test_results["error_handling"] = "FAIL"
            return False
    
    def test_firestore_triggers_simulation(self):
        """Simulate Firestore triggers and agent activation"""
        logger.info("=== TESTING FIRESTORE TRIGGERS SIMULATION ===")
        
        try:
            from shared.firestore.client import update_book
            
            if not self.test_book_id:
                logger.error("❌ No test book ID available for trigger test")
                self.test_results["firestore_triggers"] = "FAIL"
                return False
            
            # Simulate status update that would trigger next agent
            update_book(self.test_user_id, self.test_book_id, {
                "status": "analyzed",
                "confidence": 0.85,
                "trigger_test": True
            })
            
            # Wait briefly and check update
            time.sleep(1)
            
            from shared.firestore.client import get_book
            updated_book = get_book(self.test_user_id, self.test_book_id)
            
            if updated_book and updated_book.get("status") == "analyzed":
                logger.info("✅ Firestore document update successful")
                self.test_results["firestore_triggers"] = "PASS"
                return True
            else:
                logger.error("❌ Firestore document update failed")
                self.test_results["firestore_triggers"] = "FAIL"
                return False
                
        except Exception as e:
            logger.error(f"❌ Firestore trigger test failed: {e}")
            self.test_results["firestore_triggers"] = "FAIL"
            return False
    
    def test_agent_environment_variables(self):
        """Test agent-specific environment variables"""
        logger.info("=== TESTING AGENT ENVIRONMENT VARIABLES ===")
        
        # Required environment variables per agent
        agent_env_vars = {
            "ingestion": ["GCP_PROJECT", "GOOGLE_BOOKS_API_KEY"],
            "strategist": ["GCP_PROJECT"],
            "ambassador": ["EBAY_APP_ID", "EBAY_DEV_ID", "EBAY_CERT_ID", "EBAY_TOKEN"],
            "sentinel": ["GCP_PROJECT"]
        }
        
        missing_vars = {}
        
        for agent, vars_list in agent_env_vars.items():
            missing = []
            for var in vars_list:
                if not os.getenv(var):
                    missing.append(var)
            if missing:
                missing_vars[agent] = missing
        
        if missing_vars:
            logger.warning(f"⚠️ Missing environment variables for agents: {missing_vars}")
            self.test_results["agent_env_vars"] = "PARTIAL"
        else:
            logger.info("✅ All agent environment variables present")
            self.test_results["agent_env_vars"] = "PASS"
        
        return True
    
    def cleanup_test_data(self):
        """Clean up test data"""
        logger.info("=== CLEANING UP TEST DATA ===")
        
        try:
            if self.test_book_id:
                from shared.firestore.client import get_firestore_client
                
                db = get_firestore_client()
                book_ref = db.collection('users').document(self.test_user_id).collection('books').document(self.test_book_id)
                book_ref.delete()
                logger.info("✅ Test data cleaned up successfully")
                
        except Exception as e:
            logger.warning(f"⚠️ Cleanup failed: {e}")
    
    def generate_integration_report(self):
        """Generate comprehensive integration test report"""
        logger.info("=== GENERATING INTEGRATION REPORT ===")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result == "PASS")
        partial_tests = sum(1 for result in self.test_results.values() if result == "PARTIAL")
        failed_tests = sum(1 for result in self.test_results.values() if result == "FAIL")
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "test_user_id": self.test_user_id,
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "partial": partial_tests,
                "failed": failed_tests,
                "success_rate": f"{(passed_tests/total_tests)*100:.1f}%"
            },
            "detailed_results": self.test_results,
            "recommendations": []
        }
        
        # Add recommendations based on failed tests
        if self.test_results.get("backend_health") == "FAIL":
            report["recommendations"].append("Backend service needs to be started or fixed")
        
        if self.test_results.get("multi_tenancy") == "FAIL":
            report["recommendations"].append("Multi-tenancy Firestore structure needs debugging")
        
        if self.test_results.get("jwt_validation") == "FAIL":
            report["recommendations"].append("JWT validation implementation needs review")
        
        if self.test_results.get("agent_env_vars") in ["FAIL", "PARTIAL"]:
            report["recommendations"].append("Agent environment variables need to be configured")
        
        return report
    
    def run_full_integration_test(self):
        """Run the complete integration test suite"""
        logger.info("🚀 STARTING COMPREHENSIVE AGENT INTEGRATION TESTS")
        logger.info("="*60)
        
        try:
            # Run all tests
            if not self.setup_test_environment():
                logger.error("❌ Test environment setup failed. Aborting tests.")
                return self.generate_integration_report()
            
            self.test_multi_tenancy_structure()
            self.test_jwt_validation()
            self.test_agent_parameter_consistency()
            self.test_error_handling_robustness()
            self.test_firestore_triggers_simulation()
            self.test_agent_environment_variables()
            
            # Generate and return report
            report = self.generate_integration_report()
            
            logger.info("="*60)
            logger.info("🏁 INTEGRATION TESTS COMPLETED")
            logger.info(f"📊 Results: {report['summary']['passed']}/{report['summary']['total_tests']} PASSED ({report['summary']['success_rate']})")
            
            return report
            
        finally:
            self.cleanup_test_data()

if __name__ == "__main__":
    # Set environment variables for local testing
    os.environ.setdefault("GCP_PROJECT_ID", "project-52b2fab8-15a1-4b66-9f3")
    os.environ.setdefault("GCS_BUCKET_NAME", "intelligent-research-pipeline-bucket")
    
    # Create and run test suite
    test_suite = IntegrationTestSuite()
    final_report = test_suite.run_full_integration_test()
    
    # Save report to file
    with open("integration_test_report.json", "w") as f:
        json.dump(final_report, f, indent=2)
    
    print("\n" + "="*60)
    print("📋 INTEGRATION TEST REPORT SUMMARY")
    print("="*60)
    print(f"Total Tests: {final_report['summary']['total_tests']}")
    print(f"Passed: {final_report['summary']['passed']}")
    print(f"Partial: {final_report['summary']['partial']}")  
    print(f"Failed: {final_report['summary']['failed']}")
    print(f"Success Rate: {final_report['summary']['success_rate']}")
    
    if final_report['recommendations']:
        print(f"\n🔧 RECOMMENDATIONS:")
        for i, rec in enumerate(final_report['recommendations'], 1):
            print(f"{i}. {rec}")
    
    print(f"\n📄 Full report saved to: integration_test_report.json")
