from setuptools import setup, find_packages

with open("README.rst", "r") as fh:
    long_description = fh.read()

setup(
    name="spade-fiware-artifacts",
    version="0.1.1",
    author="Manel Soler Sanz",
    author_email="manelbng@gmail.com",
    description="A toolkit for multi-agent systems to interact with FIWARE's context management system",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    keywords="spade-fiware-artifacts",
    url="https://github.com/sosanzma/SPADE-FIWARE-Artifacts",
    packages=find_packages(exclude=["test*"]),
    install_requires=[

        "spade_artifact==0.2.1"
    ],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "spade_fiware_artifacts=spade_fiware_artifacts.__main__:main",
        ],
    },
    license="MIT License",
)