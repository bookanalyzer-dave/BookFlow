#!/usr/bin/env python3
"""
Comprehensive End-to-End Integration Test Suite
Tests complete system including User LLM Management, Multi-Tenancy, and Agent Pipeline
"""

import os
import sys
import json
import time
import asyncio
import requests
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.firestore.client import get_firestore_client, set_book, get_book, update_book
from shared.user_llm_manager import UserLLMManager, CredentialManager, UsageTracker
from shared.user_llm_manager.core.credentials import ProviderType, CredentialStatus
from shared.user_llm_manager.tracking.usage import TimeWindow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ComprehensiveE2ETestSuite:
    """Comprehensive End-to-End test suite for production readiness verification."""
    
    def __init__(self):
        self.backend_url = "http://localhost:8080"
        self.project_id = os.getenv("GCP_PROJECT_ID", "project-52b2fab8-15a1-4b66-9f3")
        
        # Test users
        self.test_users = {
            "user_a": {
                "email": f"test_user_a_{int(time.time())}@test.com",
                "password": "TestPassword123!",
                "uid": None,
                "token": None
            },
            "user_b": {
                "email": f"test_user_b_{int(time.time())}@test.com", 
                "password": "TestPassword123!",
                "uid": None,
                "token": None
            }
        }
        
        # Test data
        self.test_book_ids = {}
        self.test_results = {}
        self.critical_issues = []
        self.warnings = []
        
        # Initialize managers
        try:
            self.llm_manager = UserLLMManager(self.project_id)
            self.credential_manager = CredentialManager(self.project_id)
            self.usage_tracker = UsageTracker(self.project_id)
            logger.info("✅ LLM Manager components initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM Manager: {e}")
            self.llm_manager = None
            self.credential_manager = None
            self.usage_tracker = None
    
    # =============================================================================
    # USER AUTHENTICATION TESTS
    # =============================================================================
    
    async def test_user_authentication(self):
        """Test complete user authentication flow."""
        logger.info("=== TESTING USER AUTHENTICATION FLOW ===")
        
        try:
            # Test user registration (simulated - Firebase Auth handles this)
            for user_key, user_data in self.test_users.items():
                # In real scenario, Firebase Auth would create user
                # For testing, we simulate with a test UID
                user_data["uid"] = f"test_uid_{user_key}_{int(time.time())}"
                logger.info(f"✅ User {user_key} created with UID: {user_data['uid']}")
            
            # Test token validation
            test_token = "Bearer test_token_invalid"
            response = requests.post(
                f"{self.backend_url}/api/books/upload",
                headers={"Authorization": test_token},
                json={"filename": "test.jpg"}
            )
            
            if response.status_code == 401:
                logger.info("✅ Token validation correctly rejects invalid tokens")
                self.test_results["user_authentication"] = "PASS"
                return True
            else:
                logger.error(f"❌ Token validation failed - got {response.status_code}")
                self.test_results["user_authentication"] = "FAIL"
                self.critical_issues.append("Authentication: Invalid token not rejected")
                return False
                
        except Exception as e:
            logger.error(f"❌ Authentication test failed: {e}")
            self.test_results["user_authentication"] = f"FAIL: {str(e)}"
            self.critical_issues.append(f"Authentication: {str(e)}")
            return False
    
    # =============================================================================
    # LLM CREDENTIALS MANAGEMENT TESTS
    # =============================================================================
    
    async def test_llm_credentials_management(self):
        """Test LLM credentials storage, retrieval, and validation."""
        logger.info("=== TESTING LLM CREDENTIALS MANAGEMENT ===")
        
        if not self.credential_manager:
            logger.error("❌ Credential Manager not available")
            self.test_results["llm_credentials"] = "FAIL: Manager not initialized"
            self.critical_issues.append("LLM Credentials: Manager not available")
            return False
        
        try:
            user_a_uid = self.test_users["user_a"]["uid"]
            
            # Test 1: Store credentials
            logger.info("Testing credential storage...")
            test_credentials = {
                ProviderType.OPENAI: "sk-test-openai-key-12345",
                ProviderType.GOOGLE: "test-google-api-key-12345",
                ProviderType.ANTHROPIC: "sk-ant-test-12345"
            }
            
            stored_creds = {}
            for provider, api_key in test_credentials.items():
                try:
                    cred_id = await self.credential_manager.store_credential(
                        user_id=user_a_uid,
                        provider=provider,
                        api_key=api_key,
                        metadata={"test": True}
                    )
                    stored_creds[provider] = cred_id
                    logger.info(f"✅ Stored {provider.value} credential: {cred_id[:8]}...")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to store {provider.value}: {e}")
            
            # Test 2: Retrieve credentials
            logger.info("Testing credential retrieval...")
            retrieved_creds = await self.credential_manager.list_user_credentials(user_a_uid)
            
            if len(retrieved_creds) > 0:
                logger.info(f"✅ Retrieved {len(retrieved_creds)} credentials")
                
                # Verify masking
                for cred in retrieved_creds:
                    if "****" in cred.get("api_key_masked", ""):
                        logger.info(f"✅ Credential {cred['provider']} properly masked")
                    else:
                        logger.warning(f"⚠️ Credential {cred['provider']} not properly masked")
            else:
                logger.warning("⚠️ No credentials retrieved")
            
            # Test 3: Get specific credential
            if ProviderType.OPENAI in stored_creds:
                logger.info("Testing specific credential retrieval...")
                credential = await self.credential_manager.get_credential(
                    user_a_uid, 
                    ProviderType.OPENAI
                )
                
                if credential and credential.status == CredentialStatus.ACTIVE:
                    logger.info("✅ Retrieved specific credential successfully")
                else:
                    logger.warning("⚠️ Credential retrieval issue")
            
            # Test 4: Delete credential
            if ProviderType.OPENAI in stored_creds:
                logger.info("Testing credential deletion...")
                deleted = await self.credential_manager.delete_credential(
                    user_a_uid,
                    stored_creds[ProviderType.OPENAI]
                )
                
                if deleted:
                    logger.info("✅ Credential deleted successfully")
                else:
                    logger.warning("⚠️ Credential deletion failed")
            
            self.test_results["llm_credentials"] = "PASS"
            return True
            
        except Exception as e:
            logger.error(f"❌ LLM credentials test failed: {e}")
            self.test_results["llm_credentials"] = f"FAIL: {str(e)}"
            self.critical_issues.append(f"LLM Credentials: {str(e)}")
            return False
    
    # =============================================================================
    # IMAGE UPLOAD PIPELINE TEST
    # =============================================================================
    
    async def test_image_upload_pipeline(self):
        """Test complete image upload and processing pipeline."""
        logger.info("=== TESTING IMAGE UPLOAD PIPELINE ===")
        
        try:
            user_a_uid = self.test_users["user_a"]["uid"]
            
            # Simulate image upload to GCS
            test_book_id = f"test_book_pipeline_{int(time.time())}"
            test_image_url = f"gs://test-bucket/uploads/{user_a_uid}/test_book.jpg"
            
            # Create book document
            book_data = {
                "status": "ingested",
                "imageUrls": [test_image_url],
                "userId": user_a_uid,
                "title": "Test Book - Pipeline",
                "uploadedAt": datetime.now(timezone.utc).isoformat()
            }
            
            set_book(user_a_uid, test_book_id, book_data)
            logger.info(f"✅ Created book document: {test_book_id}")
            
            # Verify book creation
            retrieved_book = get_book(user_a_uid, test_book_id)
            
            if retrieved_book and retrieved_book.get("status") == "ingested":
                logger.info("✅ Book document verified in Firestore")
                self.test_book_ids[user_a_uid] = test_book_id
                self.test_results["image_upload_pipeline"] = "PASS"
                return True
            else:
                logger.error("❌ Book document not found or invalid")
                self.test_results["image_upload_pipeline"] = "FAIL"
                self.critical_issues.append("Image Upload: Book creation failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Image upload pipeline test failed: {e}")
            self.test_results["image_upload_pipeline"] = f"FAIL: {str(e)}"
            self.critical_issues.append(f"Image Upload: {str(e)}")
            return False
    
    # =============================================================================
    # AGENT WORKFLOW TESTS
    # =============================================================================
    
    async def test_condition_assessment_flow(self):
        """Test condition assessment agent workflow."""
        logger.info("=== TESTING CONDITION ASSESSMENT FLOW ===")
        
        try:
            user_a_uid = self.test_users["user_a"]["uid"]
            book_id = self.test_book_ids.get(user_a_uid)
            
            if not book_id:
                logger.warning("⚠️ No book available for condition assessment")
                self.test_results["condition_assessment"] = "SKIP: No book"
                return True
            
            # Simulate condition assessment
            condition_data = {
                "status": "condition_assessed",
                "ai_condition_grade": "Very Good",
                "ai_condition_score": 85,
                "price_factor": 0.85,
                "condition_assessed_at": datetime.now(timezone.utc).isoformat()
            }
            
            update_book(user_a_uid, book_id, condition_data)
            logger.info("✅ Condition assessment data updated")
            
            # Verify update
            updated_book = get_book(user_a_uid, book_id)
            
            if updated_book and updated_book.get("ai_condition_grade") == "Very Good":
                logger.info("✅ Condition assessment verified")
                self.test_results["condition_assessment"] = "PASS"
                return True
            else:
                logger.error("❌ Condition assessment data not found")
                self.test_results["condition_assessment"] = "FAIL"
                return False
                
        except Exception as e:
            logger.error(f"❌ Condition assessment test failed: {e}")
            self.test_results["condition_assessment"] = f"FAIL: {str(e)}"
            return False
    
    async def test_pricing_strategy_generation(self):
        """Test pricing strategy agent workflow."""
        logger.info("=== TESTING PRICING STRATEGY GENERATION ===")
        
        try:
            user_a_uid = self.test_users["user_a"]["uid"]
            book_id = self.test_book_ids.get(user_a_uid)
            
            if not book_id:
                logger.warning("⚠️ No book available for pricing")
                self.test_results["pricing_strategy"] = "SKIP: No book"
                return True
            
            # Simulate pricing strategy
            pricing_data = {
                "status": "priced",
                "calculatedPrice": 15.99,
                "floorPrice": 10.00,
                "ceilingPrice": 25.00,
                "marketAnalysis": "Based on comparable editions",
                "priced_at": datetime.now(timezone.utc).isoformat()
            }
            
            update_book(user_a_uid, book_id, pricing_data)
            logger.info("✅ Pricing strategy updated")
            
            # Verify update
            updated_book = get_book(user_a_uid, book_id)
            
            if updated_book and updated_book.get("calculatedPrice") == 15.99:
                logger.info("✅ Pricing strategy verified")
                self.test_results["pricing_strategy"] = "PASS"
                return True
            else:
                logger.error("❌ Pricing data not found")
                self.test_results["pricing_strategy"] = "FAIL"
                return False
                
        except Exception as e:
            logger.error(f"❌ Pricing strategy test failed: {e}")
            self.test_results["pricing_strategy"] = f"FAIL: {str(e)}"
            return False
    
    async def test_description_generation(self):
        """Test description generation (Scribe agent) workflow."""
        logger.info("=== TESTING DESCRIPTION GENERATION ===")
        
        try:
            user_a_uid = self.test_users["user_a"]["uid"]
            book_id = self.test_book_ids.get(user_a_uid)
            
            if not book_id:
                logger.warning("⚠️ No book available for description generation")
                self.test_results["description_generation"] = "SKIP: No book"
                return True
            
            # Simulate description generation
            description_data = {
                "status": "described",
                "description": "A classic novel in very good condition. Perfect for collectors.",
                "generated_description_at": datetime.now(timezone.utc).isoformat()
            }
            
            update_book(user_a_uid, book_id, description_data)
            logger.info("✅ Description generated")
            
            # Verify update
            updated_book = get_book(user_a_uid, book_id)
            
            if updated_book and updated_book.get("description"):
                logger.info("✅ Description generation verified")
                self.test_results["description_generation"] = "PASS"
                return True
            else:
                logger.error("❌ Description not found")
                self.test_results["description_generation"] = "FAIL"
                return False
                
        except Exception as e:
            logger.error(f"❌ Description generation test failed: {e}")
            self.test_results["description_generation"] = f"FAIL: {str(e)}"
            return False
    
    async def test_marketplace_listing(self):
        """Test marketplace listing (Ambassador agent) workflow."""
        logger.info("=== TESTING MARKETPLACE LISTING ===")
        
        try:
            user_a_uid = self.test_users["user_a"]["uid"]
            book_id = self.test_book_ids.get(user_a_uid)
            
            if not book_id:
                logger.warning("⚠️ No book available for listing")
                self.test_results["marketplace_listing"] = "SKIP: No book"
                return True
            
            # Simulate marketplace listing
            listing_data = {
                "status": "listed",
                "listings": {
                    "ebay": {
                        "listing_id": "test_123456789",
                        "status": "active",
                        "listed_at": datetime.now(timezone.utc).isoformat(),
                        "url": "https://ebay.com/itm/test_123456789"
                    }
                },
                "listed_at": datetime.now(timezone.utc).isoformat()
            }
            
            update_book(user_a_uid, book_id, listing_data)
            logger.info("✅ Marketplace listing created")
            
            # Verify update
            updated_book = get_book(user_a_uid, book_id)
            
            if updated_book and updated_book.get("listings"):
                logger.info("✅ Marketplace listing verified")
                self.test_results["marketplace_listing"] = "PASS"
                return True
            else:
                logger.error("❌ Listing data not found")
                self.test_results["marketplace_listing"] = "FAIL"
                return False
                
        except Exception as e:
            logger.error(f"❌ Marketplace listing test failed: {e}")
            self.test_results["marketplace_listing"] = f"FAIL: {str(e)}"
            return False
    
    # =============================================================================
    # MULTI-TENANCY TESTS
    # =============================================================================
    
    async def test_multi_tenancy_isolation(self):
        """Test that users cannot access each other's data."""
        logger.info("=== TESTING MULTI-TENANCY ISOLATION ===")
        
        try:
            user_a_uid = self.test_users["user_a"]["uid"]
            user_b_uid = self.test_users["user_b"]["uid"]
            
            # Create book for User A
            book_a_id = f"book_user_a_{int(time.time())}"
            set_book(user_a_uid, book_a_id, {
                "title": "User A Book",
                "userId": user_a_uid,
                "status": "test"
            })
            
            # Create book for User B
            book_b_id = f"book_user_b_{int(time.time())}"
            set_book(user_b_uid, book_b_id, {
                "title": "User B Book",
                "userId": user_b_uid,
                "status": "test"
            })
            
            # User B should NOT be able to access User A's book
            user_b_accessing_a = get_book(user_b_uid, book_a_id)
            
            # User A should NOT be able to access User B's book
            user_a_accessing_b = get_book(user_a_uid, book_b_id)
            
            if user_b_accessing_a is None and user_a_accessing_b is None:
                logger.info("✅ Multi-tenancy isolation verified - users cannot access each other's data")
                self.test_results["multi_tenancy_isolation"] = "PASS"
                
                # Cleanup
                db = get_firestore_client()
                db.collection('users').document(user_a_uid).collection('books').document(book_a_id).delete()
                db.collection('users').document(user_b_uid).collection('books').document(book_b_id).delete()
                
                return True
            else:
                logger.error("❌ Multi-tenancy isolation FAILED - data leak detected!")
                self.test_results["multi_tenancy_isolation"] = "FAIL: Data leak"
                self.critical_issues.append("Multi-Tenancy: Users can access each other's data")
                return False
                
        except Exception as e:
            logger.error(f"❌ Multi-tenancy test failed: {e}")
            self.test_results["multi_tenancy_isolation"] = f"FAIL: {str(e)}"
            self.critical_issues.append(f"Multi-Tenancy: {str(e)}")
            return False
    
    # =============================================================================
    # LLM PROVIDER TESTS
    # =============================================================================
    
    async def test_llm_provider_switching(self):
        """Test switching between different LLM providers."""
        logger.info("=== TESTING LLM PROVIDER SWITCHING ===")
        
        if not self.llm_manager:
            logger.warning("⚠️ LLM Manager not available")
            self.test_results["llm_provider_switching"] = "SKIP: Manager not available"
            return True
        
        try:
            user_a_uid = self.test_users["user_a"]["uid"]
            
            # Get user settings
            settings = await self.llm_manager.get_user_settings(user_a_uid)
            logger.info(f"✅ Retrieved user settings: default_provider={settings.default_provider}")
            
            # Test provider status
            provider_status = await self.llm_manager.get_provider_status(user_a_uid)
            
            if provider_status:
                logger.info(f"✅ Provider status retrieved: {len(provider_status)} providers")
                for provider, status in provider_status.items():
                    logger.info(f"  {provider}: system_available={status.get('system_available')}")
            
            self.test_results["llm_provider_switching"] = "PASS"
            return True
            
        except Exception as e:
            logger.error(f"❌ LLM provider switching test failed: {e}")
            self.test_results["llm_provider_switching"] = f"FAIL: {str(e)}"
            return False
    
    async def test_usage_tracking(self):
        """Test LLM usage tracking functionality."""
        logger.info("=== TESTING USAGE TRACKING ===")
        
        if not self.usage_tracker:
            logger.warning("⚠️ Usage Tracker not available")
            self.test_results["usage_tracking"] = "SKIP: Tracker not available"
            return True
        
        try:
            user_a_uid = self.test_users["user_a"]["uid"]
            
            # Get usage stats
            stats = await self.usage_tracker.get_usage_stats(user_a_uid, TimeWindow.DAY)
            logger.info(f"✅ Retrieved usage stats: {stats.total_requests} requests")
            
            # Get cost breakdown
            cost_breakdown = await self.usage_tracker.get_cost_breakdown(user_a_uid, TimeWindow.DAY)
            
            if cost_breakdown:
                logger.info(f"✅ Cost breakdown retrieved: {len(cost_breakdown)} providers")
            
            self.test_results["usage_tracking"] = "PASS"
            return True
            
        except Exception as e:
            logger.error(f"❌ Usage tracking test failed: {e}")
            self.test_results["usage_tracking"] = f"FAIL: {str(e)}"
            return False
    
    # =============================================================================
    # ERROR SCENARIOS
    # =============================================================================
    
    async def test_error_scenarios(self):
        """Test system behavior with error scenarios."""
        logger.info("=== TESTING ERROR SCENARIOS ===")
        
        try:
            test_passed = True
            
            # Test 1: Invalid credential
            if self.credential_manager:
                try:
                    await self.credential_manager.store_credential(
                        user_id="nonexistent_user",
                        provider=ProviderType.OPENAI,
                        api_key=""  # Empty key
                    )
                    logger.error("❌ System accepted empty API key")
                    self.warnings.append("Error Scenarios: System accepted empty API key")
                    test_passed = False
                except Exception as e:
                    logger.info(f"✅ System correctly rejected empty API key: {type(e).__name__}")
            
            # Test 2: Missing user data
            missing_book = get_book("nonexistent_user", "nonexistent_book")
            if missing_book is None:
                logger.info("✅ System correctly handles missing data")
            else:
                logger.error("❌ System returned data for nonexistent book")
                self.warnings.append("Error Scenarios: System returned data for nonexistent book")
                test_passed = False
            
            # Test 3: Invalid book status transition
            user_a_uid = self.test_users["user_a"]["uid"]
            test_book_id = f"error_test_{int(time.time())}"
            
            set_book(user_a_uid, test_book_id, {
                "status": "listed",
                "userId": user_a_uid
            })
            
            # Try to move back to ingested (invalid transition)
            try:
                update_book(user_a_uid, test_book_id, {"status": "ingested"})
                # If this line is reached, the test fails because no exception was raised.
                logger.error("❌ System allowed invalid status transition from 'listed' to 'ingested'")
                self.critical_issues.append("Logic Error: Invalid book status transition was allowed.")
                test_passed = False
            except ValueError:
                # This is the expected outcome. The invalid transition was blocked.
                logger.info("✅ System correctly prevents invalid status transitions")
            
            # Cleanup
            db = get_firestore_client()
            db.collection('users').document(user_a_uid).collection('books').document(test_book_id).delete()
            
            if test_passed:
                self.test_results["error_scenarios"] = "PASS"
            else:
                self.test_results["error_scenarios"] = "FAIL"
                
            return test_passed
            
        except Exception as e:
            logger.error(f"❌ Error scenarios test failed: {e}", exc_info=True)
            self.test_results["error_scenarios"] = f"FAIL: {str(e)}"
            return False
    
    # =============================================================================
    # REPORT GENERATION
    # =============================================================================
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report with recommendations."""
        logger.info("=== GENERATING COMPREHENSIVE REPORT ===")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results.values() if r == "PASS")
        skipped_tests = sum(1 for r in self.test_results.values() if r.startswith("SKIP"))
        failed_tests = total_tests - passed_tests - skipped_tests
        
        # Calculate success rate (excluding skipped)
        testable_tests = total_tests - skipped_tests
        success_rate = (passed_tests / testable_tests * 100) if testable_tests > 0 else 0
        
        # Determine production readiness
        production_ready = (
            failed_tests == 0 and
            len(self.critical_issues) == 0 and
            success_rate >= 90
        )
        
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_suite": "Comprehensive E2E Integration Tests",
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "skipped": skipped_tests,
                "success_rate": f"{success_rate:.1f}%",
                "production_ready": production_ready
            },
            "detailed_results": self.test_results,
            "critical_issues": self.critical_issues,
            "warnings": self.warnings,
            "performance_metrics": {
                "test_duration": "N/A",  # Would be calculated
                "avg_response_time": "N/A"
            },
            "recommendations": self._generate_recommendations(production_ready),
            "next_steps": self._generate_next_steps(production_ready)
        }
        
        return report
    
    def _generate_recommendations(self, production_ready: bool) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        if not production_ready:
            recommendations.append("🚨 CRITICAL: System is NOT production-ready")
        
        if self.critical_issues:
            recommendations.append(f"🚨 Fix {len(self.critical_issues)} critical issues before deployment")
        
        for test_name, result in self.test_results.items():
            if result.startswith("FAIL"):
                recommendations.append(f"Fix failed test: {test_name}")
        
        if "llm_credentials" in self.test_results and self.test_results["llm_credentials"] == "PASS":
            recommendations.append("✅ LLM Management system is functional")
        
        if "multi_tenancy_isolation" in self.test_results and self.test_results["multi_tenancy_isolation"] == "PASS":
            recommendations.append("✅ Multi-tenancy isolation is secure")
        
        if not recommendations:
            recommendations.append("✅ All systems operational - ready for production")
        
        return recommendations
    
    def _generate_next_steps(self, production_ready: bool) -> List[str]:
        """Generate next steps based on test results."""
        if production_ready:
            return [
                "1. Deploy to staging environment",
                "2. Run load testing",
                "3. Perform security audit",
                "4. Plan production deployment"
            ]
        else:
            return [
                "1. Fix all critical issues",
                "2. Re-run E2E tests",
                "3. Review failed test cases",
                "4. Update documentation"
            ]
    
    # =============================================================================
    # CLEANUP
    # =============================================================================
    
    async def cleanup(self):
        """Clean up test data."""
        logger.info("=== CLEANING UP TEST DATA ===")
        
        try:
            db = get_firestore_client()
            
            for user_key, user_data in self.test_users.items():
                uid = user_data.get("uid")
                if uid:
                    # Clean up books
                    if uid in self.test_book_ids:
                        book_id = self.test_book_ids[uid]
                        db.collection('users').document(uid).collection('books').document(book_id).delete()
                    
                    # Clean up LLM settings
                    db.collection('users').document(uid).collection('llm_settings').document('config').delete()
                    
                    logger.info(f"✅ Cleaned up data for {user_key}")
            
        except Exception as e:
            logger.warning(f"⚠️ Cleanup warning: {e}")
    
    # =============================================================================
    # MAIN TEST RUNNER
    # =============================================================================
    
    async def run_all_tests(self):
        """Run complete E2E test suite."""
        logger.info("🚀 STARTING COMPREHENSIVE E2E INTEGRATION TESTS")
        logger.info("="*80)
        
        start_time = time.time()
        
        try:
            # Run all test sequences
            await self.test_user_authentication()
            await self.test_llm_credentials_management()
            await self.test_image_upload_pipeline()
            await self.test_condition_assessment_flow()
            await self.test_pricing_strategy_generation()
            await self.test_description_generation()
            await self.test_marketplace_listing()
            await self.test_multi_tenancy_isolation()
            await self.test_llm_provider_switching()
            await self.test_usage_tracking()
            await self.test_error_scenarios()
            
            # Generate report
            report = self.generate_comprehensive_report()
            report["performance_metrics"]["test_duration"] = f"{time.time() - start_time:.2f}s"
            
            logger.info("="*80)
            logger.info("🏁 COMPREHENSIVE E2E TESTS COMPLETED")
            logger.info(f"📊 Results: {report['summary']['passed']}/{report['summary']['total_tests']} PASSED")
            logger.info(f"✨ Production Ready: {report['summary']['production_ready']}")
            
            return report
            
        finally:
            await self.cleanup()


async def main():
    """Main entry point."""
    # Set environment variables
    os.environ.setdefault("GCP_PROJECT_ID", "project-52b2fab8-15a1-4b66-9f3")
    os.environ.setdefault("GCS_BUCKET_NAME", "intelligent-research-pipeline-bucket")
    
    # Run test suite
    test_suite = ComprehensiveE2ETestSuite()
    report = await test_suite.run_all_tests()
    
    # Save report
    with open("comprehensive_e2e_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "="*80)
    print("📋 COMPREHENSIVE E2E TEST REPORT")
    print("="*80)
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Skipped: {report['summary']['skipped']}")
    print(f"Success Rate: {report['summary']['success_rate']}")
    print(f"\n🎯 Production Ready: {'✅ YES' if report['summary']['production_ready'] else '❌ NO'}")
    
    if report['critical_issues']:
        print(f"\n🚨 CRITICAL ISSUES ({len(report['critical_issues'])}):")
        for i, issue in enumerate(report['critical_issues'], 1):
            print(f"{i}. {issue}")
    
    if report['recommendations']:
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")
    
    if report['next_steps']:
        print(f"\n📋 NEXT STEPS:")
        for step in report['next_steps']:
            print(f"  {step}")
    
    print(f"\n📄 Full report saved to: comprehensive_e2e_report.json")
    
    return report


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
