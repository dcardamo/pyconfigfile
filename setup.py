#!/usr/bin/env python

from distutils.core import setup

setup(name="ConfigFile",
      version="1.0",
      description="Python user configuration file handler",
      author="Dan Cardamore",
      author_email="dan@hld.ca",
      url="http://www.hld.ca/opensource/CVSWEB/pyConfigFile",
	  data_files=[('tests', ['tests/config.py', 'tests/config.sh'])],
     )


