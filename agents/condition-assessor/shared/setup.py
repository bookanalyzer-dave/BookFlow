from setuptools import setup, find_packages

setup(
    name="shared",
    version="0.2.0",
    packages=find_packages(),
    install_requires=[
        "google-cloud-firestore",
        "google-cloud-secret-manager>=2.16.0",
        "google-genai>=0.8.0",
        "requests",
        "dataclasses-json",
        "aiohttp>=3.9.0"
    ],
)
