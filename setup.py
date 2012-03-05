import os
import sys
from setuptools import setup
import mtfTools

requirements = []
if sys.version_info < (2, 7):
    requirements.append('argparse>=1.2.1')

setup(
    name='mtfTools',
    version=mtfTools.__version__,
    description=mtfTools.__doc__.strip(),
    download_url='https://github.com/MG-RAST/mtfTools',
    author=mtfTools.__author__,
    license=mtfTools.__licence__,
    packages=['mtfTools'],
    entry_points={
        'console_scripts': [
            'mtf = mtfTools.main',
        ],
    },
    install_requires=requirements,
    classifiers=[],
)