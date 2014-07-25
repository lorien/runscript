from setuptools import setup, find_packages
import os

ROOT = os.path.dirname(os.path.realpath(__file__))
version = __import__('runscript').__version__

setup(
    name = 'runscript',
    version = version,
    description = 'Simple script launcher',
    long_description = open(os.path.join(ROOT, 'README.rst')).read(),
    url = 'http://github.com/lorien/runscript',
    author = 'Gregory Petukhov',
    author_email = 'lorien@lorien.name',

    packages = find_packages(),
    include_package_data = True,
    scripts = ('bin/run',),

    license = "MIT",
    keywords = "script cli utility run launch task",
    classifiers = (
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        #'Programming Language :: Python :: 3.3',
        'License :: OSI Approved :: MIT License',
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ),
)
