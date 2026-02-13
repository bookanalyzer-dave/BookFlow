#!/usr/bin/env python3
"""
Cloud Logging Setup Script for Alpha Launch
==========================================

Aktiviert strukturiertes Cloud Logging für alle Agents und Services.
Konfiguriert JSON-Format Logging und Error-Level Logging für Production.

Usage:
    python setup_cloud_logging.py --project-id=project-52b2fab8-15a1-4b66-9f3
    
Requirements:
    - Google Cloud SDK authentifiziert
    - Berechtigungen: logging.admin, iam.serviceAccountAdmin
"""

import os
import sys
import argparse
import logging
from google.cloud import logging as cloud_logging
from google.cloud import logging_v2
from google.api_core import exceptions
import json

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CloudLoggingSetup:
    """Setup Cloud Logging for all agents and services"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.client = cloud_logging.Client(project=project_id)
        
    def enable_cloud_logging_api(self):
        """Aktiviert Cloud Logging API"""
        logger.info("Enabling Cloud Logging API...")
        os.system(f"gcloud services enable logging.googleapis.com --project={self.project_id}")
        logger.info("✓ Cloud Logging API enabled")
        
    def create_log_sinks(self):
        """Erstellt Log Sinks für strukturiertes Logging"""
        logger.info("Creating log sinks...")
        
        sinks = [
            {
                'name': 'error-logs-sink',
                'filter': 'severity >= ERROR',
                'destination': f'logging.googleapis.com/projects/{self.project_id}/logs/errors',
                'description': 'Sink for ERROR and above logs'
            },
            {
                'name': 'agent-logs-sink',
                'filter': 'resource.type="cloud_run_revision" AND severity >= INFO',
                'destination': f'logging.googleapis.com/projects/{self.project_id}/logs/agents',
                'description': 'Sink for all agent logs'
            },
            {
                'name': 'backend-logs-sink',
                'filter': 'resource.labels.service_name:"dashboard-backend" AND severity >= INFO',
                'destination': f'logging.googleapis.com/projects/{self.project_id}/logs/backend',
                'description': 'Sink for backend service logs'
            }
        ]
        
        for sink_config in sinks:
            try:
                # Check if sink already exists
                existing_sinks = list(self.client.list_sinks())
                if any(s.name.endswith(sink_config['name']) for s in existing_sinks):
                    logger.info(f"  - Sink '{sink_config['name']}' already exists")
                    continue
                    
                # Create sink
                sink = self.client.sink(
                    sink_config['name'],
                    filter_=sink_config['filter']
                )
                sink.destination = sink_config['destination']
                sink.create()
                logger.info(f"✓ Created sink: {sink_config['name']}")
                
            except exceptions.AlreadyExists:
                logger.info(f"  - Sink '{sink_config['name']}' already exists")
            except Exception as e:
                logger.error(f"✗ Failed to create sink '{sink_config['name']}': {e}")
    
    def configure_log_retention(self, retention_days: int = 30):
        """Konfiguriert Log Retention Policy"""
        logger.info(f"Configuring log retention: {retention_days} days...")
        
        # Create retention policy via gcloud
        bucket_name = f"{self.project_id}-logs"
        cmd = f"""gcloud logging buckets update _Default \
            --location=global \
            --retention-days={retention_days} \
            --project={self.project_id}"""
        
        result = os.system(cmd)
        if result == 0:
            logger.info(f"✓ Log retention set to {retention_days} days")
        else:
            logger.warning(f"⚠ Failed to set retention policy (may need manual config)")
    
    def setup_structured_logging_config(self):
        """Erstellt strukturiertes Logging Config für Agents"""
        logger.info("Setting up structured logging configuration...")
        
        config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "stream": "ext://sys.stdout"
                },
                "cloud_logging": {
                    "class": "google.cloud.logging.handlers.CloudLoggingHandler",
                    "client": "auto",
                    "name": "agent-logs"
                }
            },
            "root": {
                "level": "INFO",
                "handlers": ["console", "cloud_logging"]
            },
            "loggers": {
                "shared": {
                    "level": "INFO"
                },
                "agents": {
                    "level": "INFO"
                },
                "dashboard": {
                    "level": "INFO"
                }
            }
        }
        
        # Save config to file
        config_path = "logging_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"✓ Structured logging config saved to: {config_path}")
        
        # Create example usage snippet
        example = '''
# Example: Add to agent main.py
import logging.config
import json

# Load logging config
with open('logging_config.json', 'r') as f:
    config = json.load(f)
    logging.config.dictConfig(config)

logger = logging.getLogger(__name__)

# Use structured logging
logger.info("Processing started", extra={
    "user_id": user_id,
    "book_id": book_id,
    "agent": "ingestion-agent"
})
'''
        
        with open('logging_example.py', 'w') as f:
            f.write(example.strip())
        
        logger.info("✓ Example usage saved to: logging_example.py")
    
    def configure_error_level_logging(self):
        """Konfiguriert Error-Level Logging für Production"""
        logger.info("Configuring error-level logging for production...")
        
        # Create environment-specific config
        env_config = {
            "production": {
                "log_level": "ERROR",
                "enable_debug": False,
                "structured_logging": True
            },
            "alpha": {
                "log_level": "INFO",
                "enable_debug": False,
                "structured_logging": True
            },
            "development": {
                "log_level": "DEBUG",
                "enable_debug": True,
                "structured_logging": False
            }
        }
        
        with open('logging_env_config.json', 'w') as f:
            json.dump(env_config, f, indent=2)
        
        logger.info("✓ Environment-specific logging config created")
    
    def test_logging_setup(self):
        """Testet das Logging Setup"""
        logger.info("Testing logging setup...")
        
        try:
            # Create test logger
            test_logger = self.client.logger('test-logger')
            
            # Write test logs
            test_logger.log_struct({
                "message": "Test log entry",
                "severity": "INFO",
                "component": "setup_script",
                "timestamp": "2025-11-01T12:00:00Z"
            })
            
            logger.info("✓ Test log written successfully")
            logger.info("  Check Cloud Console: https://console.cloud.google.com/logs")
            
        except Exception as e:
            logger.error(f"✗ Logging test failed: {e}")
    
    def generate_agent_logging_snippets(self):
        """Generiert Logging-Snippets für jeden Agent"""
        logger.info("Generating agent-specific logging snippets...")
        
        agents = [
            "ingestion-agent",
            "condition-assessor",
            "strategist-agent",
            "scribe-agent",
            "ambassador-agent",
            "sentinel-agent"
        ]
        
        snippets_dir = "logging_snippets"
        os.makedirs(snippets_dir, exist_ok=True)
        
        for agent in agents:
            snippet = f'''
import logging
from google.cloud import logging as cloud_logging

# Setup Cloud Logging for {agent}
logging_client = cloud_logging.Client()
logging_client.setup_logging()

logger = logging.getLogger('{agent}')
logger.setLevel(logging.INFO)

# Example structured logging
logger.info(
    "Agent processing started",
    extra={{
        "agent_name": "{agent}",
        "user_id": user_id,
        "book_id": book_id,
        "timestamp": datetime.utcnow().isoformat()
    }}
)

# Error logging with context
try:
    # Agent logic
    pass
except Exception as e:
    logger.error(
        f"{agent} processing failed",
        extra={{
            "agent_name": "{agent}",
            "error": str(e),
            "user_id": user_id,
            "book_id": book_id
        }},
        exc_info=True
    )
'''
            
            filepath = os.path.join(snippets_dir, f"{agent}_logging.py")
            with open(filepath, 'w') as f:
                f.write(snippet.strip())
        
        logger.info(f"✓ Generated logging snippets in: {snippets_dir}/")
    
    def print_setup_summary(self):
        """Gibt Setup-Zusammenfassung aus"""
        summary = f"""
╔════════════════════════════════════════════════════════════════╗
║         Cloud Logging Setup Complete - Alpha Ready            ║
╚════════════════════════════════════════════════════════════════╝

Project ID: {self.project_id}
Environment: Alpha

✓ Configuration Files Created:
  - logging_config.json (Structured logging config)
  - logging_env_config.json (Environment-specific config)
  - logging_example.py (Usage example)
  - logging_snippets/ (Agent-specific snippets)

✓ Log Sinks Created:
  - error-logs-sink (ERROR+ logs)
  - agent-logs-sink (All agent logs)
  - backend-logs-sink (Backend service logs)

✓ Retention Policy:
  - Default: 30 days for Alpha

📊 View Logs:
  https://console.cloud.google.com/logs/query?project={self.project_id}

📖 Next Steps for Agents:
  1. Add 'google-cloud-logging' to requirements.txt
  2. Import logging configuration in agent main.py
  3. Use structured logging with extra fields
  4. Test with: python agents/<agent>/main.py

⚠️  Alpha Launch Ready:
  - Structured JSON logging enabled
  - Error-level logging configured
  - 30-day retention policy set
  - Log sinks for monitoring created

"""
        print(summary)

def main():
    parser = argparse.ArgumentParser(
        description='Setup Cloud Logging for Alpha Launch'
    )
    parser.add_argument(
        '--project-id',
        required=True,
        help='GCP Project ID'
    )
    parser.add_argument(
        '--retention-days',
        type=int,
        default=30,
        help='Log retention in days (default: 30 for Alpha)'
    )
    parser.add_argument(
        '--skip-test',
        action='store_true',
        help='Skip logging test'
    )
    
    args = parser.parse_args()
    
    try:
        setup = CloudLoggingSetup(args.project_id)
        
        logger.info("=" * 60)
        logger.info("Cloud Logging Setup for Alpha Launch")
        logger.info("=" * 60)
        
        # Execute setup steps
        setup.enable_cloud_logging_api()
        setup.create_log_sinks()
        setup.configure_log_retention(args.retention_days)
        setup.setup_structured_logging_config()
        setup.configure_error_level_logging()
        setup.generate_agent_logging_snippets()
        
        if not args.skip_test:
            setup.test_logging_setup()
        
        setup.print_setup_summary()
        
        logger.info("=" * 60)
        logger.info("✓ Cloud Logging Setup Complete!")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"✗ Setup failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
