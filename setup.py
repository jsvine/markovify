import sys
from setuptools import setup, find_packages

setup(
    name="markovify",
    version="0.3.1",
    description="A simple, extensible Markov chain generator. Uses include generating random semi-plausible sentences based on an existing text.",
    long_description="",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.4"
    ],
    keywords="markov chain text",
    author="Jeremy Singer-Vine",
    author_email="jsvine@gmail.com",
    url="http://github.com/jsvine/markovify",
    license="MIT",
    packages=find_packages(exclude=["test",]),
    namespace_packages=[],
    include_package_data=False,
    zip_safe=False,
    install_requires=[
        "unidecode",
    ],
    tests_require=[],
    test_suite="test"
)
