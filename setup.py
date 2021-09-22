from setuptools import setup

setup(
    name='pydiscovergy',
    version='1.1.1',
    packages=['pydiscovergy'],
    url='https://github.com/jpbede/pydiscovergy',
    license='MIT',
    author='Jan-Philipp Benecke',
    author_email='jan-philipp.benecke@jpbe.de',
    description='Async Python 3 library for interacting with Discovergy smart meters API',
    long_description="file: README.md",
    long_description_content_type="text/markdown",
    install_requires=['httpx', 'authlib'],
    python_requires='>=3.6'
)
