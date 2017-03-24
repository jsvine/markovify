from setuptools import setup, find_packages
import sys, os

NAME = "markovify"
HERE = os.path.abspath(os.path.dirname(__file__))

version_ns = {}
with open(os.path.join(HERE, NAME, '__version__.py')) as f:
    exec(f.read(), {}, version_ns)

setup(
    name="markovify",
    version=version_ns['__version__'],
    description="A simple, extensible Markov chain generator. Uses include generating random semi-plausible sentences based on an existing text.",
    long_description="",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
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
