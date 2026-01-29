from setuptools import setup, find_packages
import os

# Read README for long description
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='axion-hdl',
    version='1.0.0',
    author='Bugra Tufan',
    author_email='bugratufan97@gmail.com',
    description='Automated AXI4-Lite Register Interface Generator for VHDL modules',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/bugratufan/axion-hdl',
    project_urls={
        'Bug Tracker': 'https://github.com/bugratufan/axion-hdl/issues',
        'Documentation': 'https://github.com/bugratufan/axion-hdl/tree/main/docs',
        'Source Code': 'https://github.com/bugratufan/axion-hdl',
    },
    packages=find_packages(exclude=['tests', 'tests.*', 'examples', 'output', 'waveforms', 'work']),
    include_package_data=True,
    install_requires=[
        # No external dependencies - pure Python implementation
    ],
    extras_require={
        'gui': [
            'flask>=2.0',
            'watchdog>=2.0',
            'pytest-playwright>=0.4.0',
            'playwright>=1.40.0',
            'pytest-xdist>=3.0',
            'pytest-rerunfailures>=10.0',
        ],
        'dev': [
            'pytest>=7.0',
            'pytest-cov>=2.0',
            'pytest-playwright>=0.4.0',
            'playwright>=1.40.0',
            'pytest-xdist>=3.0',
            'pytest-rerunfailures>=10.0',
            'black>=21.0',
            'flake8>=3.9',
            'cocotb>=1.9.0',
            'cocotb-bus>=0.2.1',
            'cocotbext-axi>=0.1.24',
            'build>=0.7',
            'twine>=3.4',
            'flask>=2.0',
            'watchdog>=2.0',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)',
        'Topic :: Software Development :: Code Generators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Operating System :: OS Independent',
        'Environment :: Console',
        'Natural Language :: English',
    ],
    keywords=[
        'vhdl', 'axi', 'axi4-lite', 'fpga', 'hdl', 'register', 'generator',
        'hardware', 'eda', 'rtl', 'code-generation', 'automation'
    ],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'axion-hdl=axion_hdl.cli:main',
        ],
    },
)