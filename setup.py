#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name="lit_label_studio",
    version="0.0.1",
    description="label studio",
    author="Robert S Lee",
    author_email="sangkyulee@gmail.com",
    url="https://github.com/robert-s-lee/lit_label_studio",
    install_requires=[
        "lightning",
        "virtualenv",
        "lit_bashwork @ https://github.com/robert-s-lee/lit_bashwork/archive/refs/tags/0.0.1.tar.gz",
    ],
    packages=find_packages(),
    include_package_data=True,
    package_data={'': ['nginx-8080.conf']},    
)
