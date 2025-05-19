from setuptools import setup, find_packages

setup(
    name="email_ai_system",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "openai",
        "python-dotenv",
        "imapclient",
        "sqlalchemy",
    ],
    extras_require={
        'test': [
            'pytest',
            'pytest-cov',
            'pytest-mock',
        ],
    },
    python_requires=">=3.7",
    author="Your Name",
    author_email="your.email@example.com",
    description="An email-based appointment booking system",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
) 