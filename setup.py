import os

from setuptools import find_packages, setup

ROOT = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(ROOT, "README.rst"), encoding="utf-8") as inp:
    README_CONTENT = inp.read()
setup(
    name="runscript",
    version="0.2.11",
    description="Simple script launcher",
    long_description=README_CONTENT,
    url="http://github.com/lorien/runscript",
    author="Gregory Petukhov",
    author_email="lorien@lorien.name",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "run=runscript.cli:process_command_line",
            "grun=runscript_gevent.cli:process_command_line",
        ],
    },
    license="MIT",
    keywords="script cli utility run launch task",
    install_requires=["setproctitle"],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        # 'Programming Language :: Python :: 3.3',
        "License :: OSI Approved :: MIT License",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
)
