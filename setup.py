import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="zotero-meta-analysis-toolkit", 
    version="0.0.1",
    author="Eric Thrift",
    author_email="dried.fish.matters@umanitoba.ca",
    description="Command-line tool to support basic meta-analysis using a library managed in Zotero",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DriedFishMatters/zotero-meta-analysis-toolkit",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    requires=[
        "pyzotero",
        "click",
        "unicodecsv",
        "pandas"
    ]
)
