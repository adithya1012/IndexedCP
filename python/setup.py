from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="indexcp",
    version="1.0.0",
    author="IndexedCP Contributors",
    description="Python client for secure, efficient, and resumable file transfer with filesystem buffering",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mieweb/IndexedCP",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "indexcp=bin.indexcp:main",
        ],
    },
    include_package_data=True,
)
