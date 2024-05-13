import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dsboot",
    version="0.1",
    author="Peter Thomassen",
    author_email="peter@desec.io",
    description="Generate signaling records for Authenticated DNSSEC Bootstrapping from existing zones.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/desec-io/dsboot",
    packages=setuptools.find_packages(),
    install_requires=['dnspython>=2.6.1'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Topic :: Internet :: Name Service (DNS)",
    ],
    entry_points = {
        'console_scripts': ['dsboot_generate=dsboot.commands.generate:main'],
    }
)
