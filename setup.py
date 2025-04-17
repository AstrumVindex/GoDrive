# setup.py
from setuptools import setup, find_packages

setup(
    name="drive_bot",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'python-telegram-bot',
        'google-api-python-client',
        'google-auth-oauthlib'
    ]
)