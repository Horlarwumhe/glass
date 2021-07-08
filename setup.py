import setuptools
file = open('README.md')
description = file.read()
file.close()
setuptools.setup(
    name="glass",
    version="0.0.1",
    author="Horlarwumhe",
    author_email="amachiever4real@gmail.com",
    description="A library for building web applications",
    long_description=description,
    long_description_content_type="text/markdown",
    url="https://github.com/horlarwumhe/glass",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Topic :: Web Development'

    ],
    python_requires='>=3.7',
)
