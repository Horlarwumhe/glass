import setuptools

file = open('README.md')
description = file.read()
file.close()
setuptools.setup(
    name="glass-web",
    version="0.0.6",
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
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Server',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: Software Development :: Libraries :: Application Frameworks'

    ],
    python_requires='>=3.7',
)
