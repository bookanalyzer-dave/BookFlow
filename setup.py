from setuptools import setup, find_packages

setup(
    name='shared',
    version='0.1',
    packages=find_packages(),
    # install_requires=[
        # # Cloud Functions & Google Cloud
        # "functions-framework>=3.0.0",
        # "google-cloud-storage>=2.14.0",
        # "google-cloud-vision>=3.5.0",
        # "google-cloud-pubsub>=2.18.0",
        # "google-cloud-aiplatform>=1.38.0",
        # "google-cloud-firestore>=2.13.0",
        # "google-cloud-secret-manager>=2.16.0",
        
        # # Web & HTTP
        # "flask>=3.0.0",
        # "requests>=2.31.0",
        
        # # Encryption & Security
        # "cryptography>=41.0.0",
        
        # # LLM Provider SDKs (for User LLM Manager)
        # "openai>=1.3.0",
        # "anthropic>=0.7.0",
        # "google-generativeai>=0.3.0",
        
        # # Data Structures
        # "dataclasses-json>=0.6.0",
        
        # # External APIs & Tools
        # "pyppeteer>=1.0.0",
        # "ebaysdk>=2.2.0",
        # "google-api-python-client>=2.100.0",
    # ],
)