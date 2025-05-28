from setuptools import setup, find_packages
import os

# Read README file safely
def read_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as fh:
            return fh.read()
    except (FileNotFoundError, UnicodeDecodeError):
        return ""

# Core requirements (hardcoded to avoid circular dependency issues)
def get_requirements():
    return [
        "streamlit>=1.28.0",
        "pydantic>=2.0.0",
        "pandas>=1.5.0",
        "numpy>=1.24.0",
        "pillow>=9.5.0",
        "python-dateutil>=2.8.0",
        "requests>=2.31.0",
    ]

setup(
    name="gpp",
    version="0.1.0",
    author="Andrei",
    author_email="tomutvoicuandrei@gmail.com",
    description="GPP - Global Property Platform: A comprehensive property management system",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    url="https://github.com/VoicuTomut/forring.git",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Real Estate Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    python_requires=">=3.8",
    install_requires=get_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "gpp=app:main",  # Updated to match your app structure
        ],
    },
    include_package_data=True,
    package_data={
        "gpp": [
            "data/*",
            "LOGO/*",
            "*.md",
        ],
        "": ["*.txt", "*.md"],
    },
    # Ensure data files are included
    zip_safe=False,
)