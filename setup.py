#!/usr/bin/env python3
#
## @file setup.py
#
# Copyright (c) 2017 - 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

from setuptools import setup

setup(name='edkrepo',
      version='2.0.0',
      description='The edkrepo tools',
      packages=['edkrepo', 'edkrepo.commands', 'edkrepo.commands.arguments', 'edkrepo.commands.humble',
                'edkrepo.git_automation', 'edkrepo.common', 'edkrepo.common.workspace_maintenance',
                'edkrepo.common.workspace_maintenance.humble', 'edkrepo.config', 'edkrepo.config.humble',
                'edkrepo_manifest_parser', 'project_utils'],
      package_data={
         },
      include_package_data=True,
      entry_points={
          'console_scripts': [
              'edkrepo = edkrepo.edkrepo_entry_point:main',
              'command_completion_edkrepo = edkrepo.command_completion_edkrepo:main'
              ]
          }
      )
