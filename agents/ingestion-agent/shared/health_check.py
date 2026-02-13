"""
Health Check Helper for All Agents
==================================

Provides standardized health check functionality for all agents
including dependency checks (Firestore, GCS, Vertex AI).

Usage in agent:
    from shared.health_check import create_health_check_handler
    
    @app.route('/health', methods=['GET'])
    def health():
        return create_health_check_handler(
            agent_name="ingestion-agent",
            check_firestore=True,
            check_gcs=True,
            check_vertex_ai=True
        )()
"""

import os
from datetime import datetime
from typing import Dict, Callable
from flask import jsonify

def create_health_check_handler(
    agent_name: str,
    check_firestore: bool = True,
    check_gcs: bool = False,
    check_vertex_ai: bool = False
) -> Callable:
    """
    Create a health check handler for an agent
    
    Args:
        agent_name: Name of the agent
        check_firestore: Whether to check Firestore connection
        check_gcs: Whether to check GCS connection
        check_vertex_ai: Whether to check Vertex AI availability
        
    Returns:
        Flask route handler function
    """
    
    def health_check():
        """Health check endpoint"""
        status = "healthy"
        checks = {}
        
        # Basic info
        info = {
            "agent": agent_name,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": os.getenv("AGENT_VERSION", "1.0.0-alpha"),
            "environment": os.getenv("ENVIRONMENT", "development")
        }
        
        # Firestore check
        if check_firestore:
            try:
                from shared.firestore.client import get_firestore_client
                db = get_firestore_client()
                # Quick connectivity test
                list(db.collection('users').limit(1).stream())
                checks["firestore"] = "connected"
            except Exception as e:
                checks["firestore"] = f"error: {str(e)}"
                status = "degraded"
        
        # GCS check
        if check_gcs:
            try:
                from google.cloud import storage  # type: ignore
                client = storage.Client()
                bucket_name = os.getenv("GCS_BUCKET_NAME")
                if bucket_name:
                    bucket = client.bucket(bucket_name)
                    bucket.exists()  # Quick existence check
                    checks["gcs"] = "connected"
                else:
                    checks["gcs"] = "not configured"
            except Exception as e:
                checks["gcs"] = f"error: {str(e)}"
                status = "degraded"
        
        # Vertex AI check
        if check_vertex_ai:
            try:
                from google.cloud import aiplatform  # type: ignore
                project = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
                location = os.getenv("VERTEX_AI_LOCATION", "europe-west1")
                if project:
                    aiplatform.init(project=project, location=location)
                    checks["vertex_ai"] = "initialized"
                else:
                    checks["vertex_ai"] = "not configured"
            except Exception as e:
                checks["vertex_ai"] = f"error: {str(e)}"
                status = "degraded"
        
        info["status"] = status
        info["checks"] = checks
        
        # Return appropriate status code
        status_code = 200 if status == "healthy" else 503
        
        return jsonify(info), status_code
    
    return health_check


def create_simple_health_check(agent_name: str) -> Callable:
    """
    Create a simple health check that only returns basic info
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        Flask route handler function
    """
    
    def health_check():
        """Simple health check endpoint"""
        return jsonify({
            "agent": agent_name,
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": os.getenv("AGENT_VERSION", "1.0.0-alpha")
        }), 200
    
    return health_check


# Example usage for Cloud Functions (non-Flask)
def cloud_function_health_check(
    agent_name: str,
    check_firestore: bool = True,
    check_gcs: bool = False,
    check_vertex_ai: bool = False
) -> Dict:
    """
    Health check for Cloud Functions (returns dict, not Flask response)
    
    Args:
        agent_name: Name of the agent
        check_firestore: Whether to check Firestore connection
        check_gcs: Whether to check GCS connection
        check_vertex_ai: Whether to check Vertex AI availability
        
    Returns:
        Health check result as dictionary
    """
    status = "healthy"
    checks = {}
    
    # Firestore check
    if check_firestore:
        try:
            from shared.firestore.client import get_firestore_client
            db = get_firestore_client()
            list(db.collection('users').limit(1).stream())
            checks["firestore"] = "connected"
        except Exception as e:
            checks["firestore"] = f"error: {str(e)}"
            status = "degraded"
    
    # GCS check
    if check_gcs:
        try:
            from google.cloud import storage  # type: ignore
            client = storage.Client()
            bucket_name = os.getenv("GCS_BUCKET_NAME")
            if bucket_name:
                bucket = client.bucket(bucket_name)
                bucket.exists()
                checks["gcs"] = "connected"
            else:
                checks["gcs"] = "not configured"
        except Exception as e:
            checks["gcs"] = f"error: {str(e)}"
            status = "degraded"
    
    # Vertex AI check
    if check_vertex_ai:
        try:
            from google.cloud import aiplatform  # type: ignore
            project = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
            location = os.getenv("VERTEX_AI_LOCATION", "europe-west1")
            if project:
                aiplatform.init(project=project, location=location)
                checks["vertex_ai"] = "initialized"
            else:
                checks["vertex_ai"] = "not configured"
        except Exception as e:
            checks["vertex_ai"] = f"error: {str(e)}"
            status = "degraded"
    
    return {
        "agent": agent_name,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.getenv("AGENT_VERSION", "1.0.0-alpha"),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "checks": checks
    }