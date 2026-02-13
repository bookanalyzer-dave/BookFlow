#!/usr/bin/env python3
"""
Script to set CORS configuration on a Cloud Storage bucket.
"""

from google.cloud import storage

def set_bucket_cors():
    """Set CORS configuration on the bucket."""
    
    bucket_name = "project-52b2fab8-15a1-4b66-9f3-book-images"
    project_id = "project-52b2fab8-15a1-4b66-9f3"
    
    # Initialize the storage client with explicit project ID
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    
    # Define CORS configuration
    cors_configuration = [
        {
            "origin": ["*"],
            "method": ["GET", "HEAD", "PUT", "POST", "DELETE", "OPTIONS"],
            "responseHeader": [
                "Content-Type",
                "Content-Length",
                "x-goog-resumable",
                "Access-Control-Allow-Origin"
            ],
            "maxAgeSeconds": 3600
        }
    ]
    
    # Set the CORS configuration
    bucket.cors = cors_configuration
    bucket.patch()
    
    print(f"✓ CORS configuration successfully set on bucket: {bucket_name}")
    print(f"✓ Configuration: {cors_configuration}")
    
    # Verify the configuration
    bucket.reload()
    print(f"✓ Verified CORS configuration: {bucket.cors}")

if __name__ == "__main__":
    set_bucket_cors()
