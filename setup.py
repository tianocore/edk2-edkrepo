#!/usr/bin/env python3
#
## @file
# setup.py
#
# Copyright (c) 2017- 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

from setuptools import setup

setup(name='edkrepo',
      version='2.0.0',
      description='The edkrepo tools',
      packages=['edkrepo', 'edkrepo.commands', 'edkrepo.common', 'edkrepo.config', 'edkrepo_manifest_parser', 'project_utils'],
      package_data={
         },
      include_package_data=True,
      entry_points={
          'console_scripts': [
              'edkrepo = edkrepo.edkrepo_entry_point:main'
              ]
          }
      )
