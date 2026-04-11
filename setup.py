from setuptools import setup, find_packages

setup(
    name="gitpulse",
    version="0.1.0",
    description="Autonomous GitHub career agent that scores profiles against job descriptions, scans live internships, and opens real PRs",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "anthropic>=0.39.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "gitpulse=gitpulse.cli:main",
        ],
    },
)
