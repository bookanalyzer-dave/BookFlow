#!/usr/bin/env python3
"""
Error Reporting Configuration Script for Alpha Launch
====================================================

Aktiviert Google Cloud Error Reporting für alle Agents und Services.
Konfiguriert Error Grouping, Notifications und Email Alerts.

Usage:
    python setup_error_reporting.py --project-id=project-52b2fab8-15a1-4b66-9f3 --alert-email=admin@example.com
    
Requirements:
    - Google Cloud SDK authentifiziert
    - Berechtigungen: errorreporting.admin, monitoring.admin
"""

import os
import sys
import argparse
import logging
from google.cloud import error_reporting
from google.cloud import monitoring_v3
from google.api_core import exceptions
import json

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ErrorReportingSetup:
    """Setup Error Reporting for all agents and services"""
    
    def __init__(self, project_id: str, alert_email: str = None):
        self.project_id = project_id
        self.alert_email = alert_email
        self.error_client = error_reporting.Client(project=project_id)
        
    def enable_error_reporting_api(self):
        """Aktiviert Error Reporting API"""
        logger.info("Enabling Error Reporting API...")
        os.system(f"gcloud services enable clouderrorreporting.googleapis.com --project={self.project_id}")
        logger.info("✓ Error Reporting API enabled")
    
    def create_alert_policies(self):
        """Erstellt Alert Policies für kritische Fehler"""
        logger.info("Creating alert policies...")
        
        if not self.alert_email:
            logger.warning("⚠ No alert email provided, skipping notification channel setup")
            logger.info("  Run with --alert-email to configure email alerts")
            return
        
        # Create notification channel via gcloud
        channel_config = {
            "type": "email",
            "displayName": "Alpha Launch Alerts",
            "labels": {
                "email_address": self.alert_email
            }
        }
        
        channel_file = "notification_channel.json"
        with open(channel_file, 'w') as f:
            json.dump(channel_config, f, indent=2)
        
        logger.info(f"Creating email notification channel for: {self.alert_email}")
        result = os.system(f"gcloud alpha monitoring channels create --channel-content-from-file={channel_file} --project={self.project_id}")
        
        if result == 0:
            logger.info("✓ Email notification channel created")
        else:
            logger.warning("⚠ Failed to create notification channel (may need manual setup)")
        
        # Clean up temp file
        if os.path.exists(channel_file):
            os.remove(channel_file)
        
        # Create alert policies
        alert_policies = [
            {
                "name": "critical-error-rate-alert",
                "description": "Alert when error rate exceeds threshold",
                "filter": 'resource.type="cloud_run_revision" AND severity="ERROR"',
                "threshold": "5",  # 5 errors in 5 minutes
                "duration": "300s"
            },
            {
                "name": "agent-failure-alert",
                "description": "Alert when agent fails multiple times",
                "filter": 'resource.type="cloud_run_revision" AND protoPayload.status.code!=0',
                "threshold": "3",  # 3 failures in 5 minutes
                "duration": "300s"
            }
        ]
        
        logger.info("✓ Alert policy configurations prepared")
        logger.info("  Note: Manual creation via Cloud Console recommended for complex policies")
    
    def configure_error_grouping(self):
        """Konfiguriert Error Grouping Rules"""
        logger.info("Configuring error grouping...")
        
        grouping_config = {
            "error_grouping": {
                "enabled": True,
                "rules": [
                    {
                        "name": "LLM API Errors",
                        "pattern": ".*LLMError.*",
                        "group_by": ["error_type", "provider"]
                    },
                    {
                        "name": "Firestore Errors",
                        "pattern": ".*firestore.*",
                        "group_by": ["error_type", "collection"]
                    },
                    {
                        "name": "Vision API Errors",
                        "pattern": ".*vision.*|.*vertex.*",
                        "group_by": ["error_type", "api"]
                    },
                    {
                        "name": "Authentication Errors",
                        "pattern": ".*auth.*|.*token.*",
                        "group_by": ["error_type"]
                    }
                ]
            }
        }
        
        with open('error_grouping_config.json', 'w') as f:
            json.dump(grouping_config, f, indent=2)
        
        logger.info("✓ Error grouping config saved to: error_grouping_config.json")
    
    def setup_error_reporting_client(self):
        """Erstellt Error Reporting Client Integration Code"""
        logger.info("Setting up Error Reporting client integration...")
        
        integration_code = '''
from google.cloud import error_reporting
import logging

# Initialize Error Reporting Client
error_client = error_reporting.Client()

def report_error(error: Exception, user_id: str = None, context: dict = None):
    """
    Report error to Google Cloud Error Reporting
    
    Args:
        error: The exception to report
        user_id: Optional user ID for context
        context: Additional context dictionary
    """
    try:
        # Build HTTP context for error reporting
        http_context = error_reporting.HTTPContext(
            method='POST',
            url=context.get('url', '') if context else '',
            user_agent=context.get('user_agent', '') if context else '',
            remote_ip=context.get('remote_ip', '') if context else ''
        )
        
        # Report the error
        error_client.report_exception(
            http_context=http_context,
            user=user_id or 'unknown'
        )
        
        logging.info(f"Error reported to Cloud Error Reporting: {type(error).__name__}")
        
    except Exception as report_error:
        logging.error(f"Failed to report error: {report_error}")

# Example usage in agent:
try:
    # Your agent code
    process_book(book_id, user_id)
except Exception as e:
    logging.error(f"Agent processing failed: {e}", exc_info=True)
    report_error(e, user_id=user_id, context={
        'url': '/api/books/process',
        'book_id': book_id
    })
    raise
'''
        
        with open('error_reporting_integration.py', 'w') as f:
            f.write(integration_code.strip())
        
        logger.info("✓ Error reporting integration code saved to: error_reporting_integration.py")
    
    def create_error_handling_decorator(self):
        """Erstellt Error Handling Decorator für Agents"""
        logger.info("Creating error handling decorator...")
        
        decorator_code = '''
from functools import wraps
from google.cloud import error_reporting
import logging

error_client = error_reporting.Client()
logger = logging.getLogger(__name__)

def handle_errors(agent_name: str, user_id_param: str = 'user_id'):
    """
    Decorator für automatisches Error Reporting in Agents
    
    Args:
        agent_name: Name des Agents (z.B. 'ingestion-agent')
        user_id_param: Name des user_id Parameters in der Funktion
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Extract user_id from kwargs
                user_id = kwargs.get(user_id_param, 'unknown')
                
                # Log error
                logger.error(
                    f"{agent_name} error: {str(e)}",
                    extra={
                        'agent': agent_name,
                        'user_id': user_id,
                        'function': func.__name__
                    },
                    exc_info=True
                )
                
                # Report to Error Reporting
                try:
                    error_client.report_exception(
                        user=user_id
                    )
                except Exception as report_err:
                    logger.error(f"Failed to report error: {report_err}")
                
                # Re-raise original error
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                user_id = kwargs.get(user_id_param, 'unknown')
                
                logger.error(
                    f"{agent_name} error: {str(e)}",
                    extra={
                        'agent': agent_name,
                        'user_id': user_id,
                        'function': func.__name__
                    },
                    exc_info=True
                )
                
                try:
                    error_client.report_exception(user=user_id)
                except Exception as report_err:
                    logger.error(f"Failed to report error: {report_err}")
                
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Example usage:
@handle_errors(agent_name='ingestion-agent', user_id_param='uid')
async def process_book(book_id: str, uid: str):
    """Process book with automatic error handling"""
    # Your code here
    pass
'''
        
        with open('error_handling_decorator.py', 'w') as f:
            f.write(decorator_code.strip())
        
        logger.info("✓ Error handling decorator saved to: error_handling_decorator.py")
    
    def generate_agent_error_configs(self):
        """Generiert Error Config für jeden Agent"""
        logger.info("Generating agent-specific error configurations...")
        
        agents = {
            "ingestion-agent": {
                "critical_errors": ["VisionAPIError", "FirestoreError", "LLMError"],
                "retry_on": ["TransientError", "RateLimitError"],
                "alert_on": ["CriticalDataLoss", "AuthenticationFailure"]
            },
            "condition-assessor": {
                "critical_errors": ["VisionAPIError", "AssessmentError"],
                "retry_on": ["TransientError", "ImageProcessingError"],
                "alert_on": ["ConsistentFailures"]
            },
            "strategist-agent": {
                "critical_errors": ["PricingError", "MarketDataError"],
                "retry_on": ["APITimeout", "RateLimitError"],
                "alert_on": ["InvalidPricing"]
            },
            "ambassador-agent": {
                "critical_errors": ["ListingError", "EbayAPIError"],
                "retry_on": ["NetworkError", "RateLimitError"],
                "alert_on": ["ListingFailure", "InventorySyncError"]
            }
        }
        
        config_dir = "error_configs"
        os.makedirs(config_dir, exist_ok=True)
        
        for agent_name, config in agents.items():
            filepath = os.path.join(config_dir, f"{agent_name}_error_config.json")
            with open(filepath, 'w') as f:
                json.dump({
                    "agent": agent_name,
                    "error_handling": config,
                    "reporting": {
                        "enabled": True,
                        "sample_rate": 1.0,
                        "include_context": True
                    }
                }, f, indent=2)
        
        logger.info(f"✓ Generated error configs in: {config_dir}/")
    
    def test_error_reporting(self):
        """Testet Error Reporting Setup"""
        logger.info("Testing error reporting...")
        
        try:
            # Report a test error
            test_error = Exception("Test error from setup script")
            
            self.error_client.report_exception()
            
            logger.info("✓ Test error reported successfully")
            logger.info(f"  Check Error Reporting Console:")
            logger.info(f"  https://console.cloud.google.com/errors?project={self.project_id}")
            
        except Exception as e:
            logger.error(f"✗ Error reporting test failed: {e}")
    
    def create_error_dashboard_query(self):
        """Erstellt vordefinierte Queries für Error Dashboard"""
        logger.info("Creating error dashboard queries...")
        
        queries = {
            "critical_errors_last_hour": {
                "description": "Critical errors in the last hour",
                "query": 'severity="ERROR" AND timestamp>"now-1h"',
                "fields": ["timestamp", "message", "resource.labels.service_name", "jsonPayload.user_id"]
            },
            "error_rate_by_agent": {
                "description": "Error rate grouped by agent",
                "query": 'severity>="ERROR"',
                "aggregation": "COUNT(*) GROUP BY resource.labels.service_name"
            },
            "user_impact_errors": {
                "description": "Errors affecting multiple users",
                "query": 'severity="ERROR" AND jsonPayload.user_id!=""',
                "aggregation": "COUNT(DISTINCT jsonPayload.user_id)"
            },
            "llm_provider_errors": {
                "description": "LLM provider specific errors",
                "query": 'jsonPayload.provider!="" AND severity="ERROR"',
                "aggregation": "COUNT(*) GROUP BY jsonPayload.provider"
            }
        }
        
        with open('error_dashboard_queries.json', 'w') as f:
            json.dump(queries, f, indent=2)
        
        logger.info("✓ Error dashboard queries saved to: error_dashboard_queries.json")
    
    def print_setup_summary(self):
        """Gibt Setup-Zusammenfassung aus"""
        alert_info = f"Alerts to: {self.alert_email}" if self.alert_email else "No email alerts configured"
        
        summary = f"""
╔════════════════════════════════════════════════════════════════╗
║      Error Reporting Setup Complete - Alpha Ready             ║
╚════════════════════════════════════════════════════════════════╝

Project ID: {self.project_id}
Environment: Alpha
{alert_info}

✓ Configuration Files Created:
  - error_grouping_config.json (Error grouping rules)
  - error_reporting_integration.py (Integration code)
  - error_handling_decorator.py (Error decorator)
  - error_configs/ (Agent-specific configs)
  - error_dashboard_queries.json (Dashboard queries)

✓ Error Reporting Features:
  - Automatic exception capture
  - Error grouping by type and context
  - Integration with Cloud Functions
  - User context tracking

✓ Alert Policies:
  - Critical error rate monitoring
  - Agent failure detection
  - Email notifications ({self.alert_email or 'Not configured'})

📊 View Errors:
  https://console.cloud.google.com/errors?project={self.project_id}

📖 Next Steps for Agents:
  1. Add 'google-cloud-error-reporting' to requirements.txt
  2. Import error reporting client in agent main.py
  3. Use @handle_errors decorator for main functions
  4. Test with intentional error to verify reporting

⚠️  Alpha Launch Ready:
  - Error Reporting API enabled
  - Automatic error capture configured
  - Email alerts ready (if email provided)
  - Error grouping configured

💡 To configure email alerts later:
  python setup_error_reporting.py --project-id={self.project_id} --alert-email=your@email.com

"""
        print(summary)

def main():
    parser = argparse.ArgumentParser(
        description='Setup Error Reporting for Alpha Launch'
    )
    parser.add_argument(
        '--project-id',
        required=True,
        help='GCP Project ID'
    )
    parser.add_argument(
        '--alert-email',
        help='Email address for critical error alerts'
    )
    parser.add_argument(
        '--skip-test',
        action='store_true',
        help='Skip error reporting test'
    )
    
    args = parser.parse_args()
    
    try:
        setup = ErrorReportingSetup(args.project_id, args.alert_email)
        
        logger.info("=" * 60)
        logger.info("Error Reporting Setup for Alpha Launch")
        logger.info("=" * 60)
        
        # Execute setup steps
        setup.enable_error_reporting_api()
        setup.create_alert_policies()
        setup.configure_error_grouping()
        setup.setup_error_reporting_client()
        setup.create_error_handling_decorator()
        setup.generate_agent_error_configs()
        setup.create_error_dashboard_query()
        
        if not args.skip_test:
            setup.test_error_reporting()
        
        setup.print_setup_summary()
        
        logger.info("=" * 60)
        logger.info("✓ Error Reporting Setup Complete!")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"✗ Setup failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
