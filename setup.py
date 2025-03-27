#!/usr/bin/env python3
"""Setup configuration for cursor-chat-extractor package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="cursor-chat-extractor",
    version="0.1.0",
    author="Cursor IDE Team",
    author_email="team@cursor.so",
    description="Extract chat history from Cursor IDE databases",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/getcursor/cursor-chat-extractor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "cursor-chat-extract=scripts.extract_responses:main",
        ],
    },
    package_data={
        "cursor_chat_extractor": ["py.typed"],
    },
) 