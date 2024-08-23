import re
from codecs import open
from os import path

from setuptools import setup

PACKAGE_NAME = "docstrfmt"
HERE = path.abspath(path.dirname(__file__))
with open(path.join(HERE, "README.rst"), encoding="utf-8") as fp:
    README = fp.read()
with open(path.join(HERE, PACKAGE_NAME, "const.py"), encoding="utf-8") as fp:
    VERSION = re.search('__version__ = "([^"]+)"', fp.read()).group(1)

extras_requires = {
    "ci": ["coveralls"],
    "d": ["aiohttp==3.*"],
    "dev": ["packaging", "pre-commit"],
    "test": ["pytest", "pytest-aiohttp"],
    "lint": ["flake8", "flynt", "isort"],
}
extras_requires["dev"] += extras_requires["test"] + extras_requires["lint"]

setup(
    name=PACKAGE_NAME,
    author="Joel Payne",
    author_email="lilspazjoekp@gmail.com",
    python_requires="~=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python",
        "Topic :: Documentation",
        "Topic :: Documentation :: Sphinx",
        "Topic :: Software Development :: Documentation",
        "Topic :: Utilities",
    ],
    description="A formatter for Sphinx flavored reStructuredText.",
    entry_points={
        "console_scripts": [
            "docstrfmt = docstrfmt.main:main",
            "docstrfmtd = docstrfmt.server:main [d]",
        ]
    },
    extras_require=extras_requires,
    install_requires=[
        "black==24.*",
        "click==8.*",
        "docutils==0.20.*",
        "libcst==1.*",
        "platformdirs==4.*",
        "sphinx>=7,<9",
        "tabulate==0.9.*",
        "toml==0.10.*",
    ],
    license="MIT",
    long_description=README,
    packages=["docstrfmt"],
    url="https://github.com/LilSpazJoekp/docstrfmt",
    version=VERSION,
)
