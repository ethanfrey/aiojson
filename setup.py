from setuptools import setup, find_packages

setup(
    name = 'aiojson',
    version = '0.1',
    author = 'Ethan Frey',
    author_email = 'ethanfrey@users.noreply.github.com',
    url = 'https://github.com/ethanfrey/aiojson',
    license = 'BSD',
    description = 'Iterative JSON parser for asyncio streams',
    long_description = open('README.rst').read(),

    classifiers = [
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    packages = find_packages(),
)
