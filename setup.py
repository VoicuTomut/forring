from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="gpp",
    version="0.1.0",
    author="Andrei",
    author_email="tomutvoicuandrei@gmail.com",
    description="A real estate application with Streamlit interface",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/forring",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 0.1 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
    },
    entry_points={
        "console_scripts": [
            "forring=app.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "forring": ["data/*", "templates/*", "static/*"],
    },
)