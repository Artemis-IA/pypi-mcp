"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def sample_package_info():
    """Sample PyPI package info response."""
    return {
        "info": {
            "name": "requests",
            "version": "2.31.0",
            "summary": "Python HTTP for Humans.",
            "description": "A great library for HTTP requests.",
            "author": "Kenneth Reitz",
            "license": "Apache-2.0",
            "home_page": "https://requests.readthedocs.io",
            "requires_python": ">=3.7",
            "classifiers": [
                "Development Status :: 5 - Production/Stable",
                "Programming Language :: Python :: 3",
            ],
            "requires_dist": [
                "charset-normalizer (<4,>=2)",
                "idna (<4,>=2.5)",
                "urllib3 (<3,>=1.21.1)",
                "certifi (>=2017.4.17)",
            ],
            "project_urls": {
                "Documentation": "https://requests.readthedocs.io",
                "Source": "https://github.com/psf/requests",
            },
        },
        "releases": {
            "2.31.0": [
                {"packagetype": "bdist_wheel", "python_version": "py3"},
                {"packagetype": "sdist", "python_version": "source"},
            ],
            "2.30.0": [
                {"packagetype": "bdist_wheel", "python_version": "py3"},
            ],
        },
        "urls": [
            {"packagetype": "bdist_wheel", "python_version": "py3"},
            {"packagetype": "sdist", "python_version": "source"},
        ],
    }
