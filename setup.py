import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Hana-net",
    version="0.0.1",
    author="Mohsen Tahmasebi",
    author_email="moh53n@outlook.com",
    description="multi-sensor project to monitor DNS connectivity and Internet blocking status",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/moh53n/Hana",
    project_urls={
        "Bug Tracker": "https://github.com/moh53n/Hana/issues",
    },
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)
