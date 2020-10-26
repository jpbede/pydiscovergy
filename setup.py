from setuptools import setup

setup(
    name='pydiscovergy',
    version='0.0.4',
    packages=['pydiscovergy'],
    url='https://github.com/jpbede/pydiscovergy',
    license='MIT',
    author='Jan-Philipp Benecke',
    author_email='jan-philipp.benecke@jpbe.de',
    description='Python library for interacting with discovergy smart meters api',
    install_requires=['requests', 'requests-oauthlib']
)
