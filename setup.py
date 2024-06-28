from setuptools import find_packages, setup

setup(
    name="easycit",
    version="0.1",
    packages=find_packages(include=["easycit", "easycit.*"]),
    install_requires=[
        "click",
        "requests",
        "beautifulsoup4",
        "click-default-group",
    ],
    tests_require=[
        "pytest",
    ],
    entry_points={
        "console_scripts": [
            "easycit=easycit.cli:cli",
        ],
    },
)
