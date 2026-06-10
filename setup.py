from setuptools import setup, find_packages

setup(
    name="kronos-trading-dashboard",
    version="0.1.0",
    description="Kronos K-line prediction + 6-Agent A-stock analysis dashboard",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Trader",
    url="https://github.com/yourname/kronos-trading-dashboard",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "torch>=2.0.0",
        "huggingface_hub>=0.20.0",
        "tqdm>=4.64.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
