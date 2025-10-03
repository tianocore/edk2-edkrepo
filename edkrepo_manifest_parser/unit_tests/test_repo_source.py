#!/usr/bin/env python3
#
## @file
# test_repo_source.py
#
# Copyright (c) 2025, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import pytest
from collections import namedtuple
import sys
import os

# Add the parent directory to the system path to resolve imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from edk_manifest import _RepoSource, RepoSource, ATTRIBUTE_MISSING_ERROR

# Mock classes and data for testing
class MockElement:
    def __init__(self, attrib):
        self.attrib = attrib

class MockRemote:
    def __init__(self, url):
        self.url = url

def test_repo_source_init_valid_with_branch_commit_tag():
    element = MockElement({
        'localRoot': 'root_path',
        'remote': 'origin',
        'branch': 'main',
        'commit': 'abc123',
        'tag': 'v1.0',
        'sparseCheckout': 'true',
        'enableSubmodule': 'true',
        'venv_cfg': 'config.yaml',
        'blobless': 'false',
        'treeless': 'true'
    })
    remotes = {'origin': MockRemote('https://example.com/repo.git')}

    repo_source = _RepoSource(element, remotes)

    assert repo_source.root == 'root_path'
    assert repo_source.remote_name == 'origin'
    assert repo_source.remote_url == 'https://example.com/repo.git'
    assert repo_source.branch == 'main'
    assert repo_source.commit == 'abc123'
    assert repo_source.tag == 'v1.0'
    assert repo_source.patch_set is None
    assert repo_source.sparse is True
    assert repo_source.enableSub is True
    assert repo_source.venv_cfg == 'config.yaml'
    assert repo_source.blobless is False
    assert repo_source.treeless is True

def test_repo_source_init_valid_with_only_branch():
    element = MockElement({
        'localRoot': 'root_path',
        'remote': 'origin',
        'branch': 'main'
    })
    remotes = {'origin': MockRemote('https://example.com/repo.git')}

    repo_source = _RepoSource(element, remotes)

    assert repo_source.branch == 'main'
    assert repo_source.commit is None
    assert repo_source.tag is None

def test_repo_source_init_valid_with_only_commit():
    element = MockElement({
        'localRoot': 'root_path',
        'remote': 'origin',
        'commit': 'abc123'
    })
    remotes = {'origin': MockRemote('https://example.com/repo.git')}

    repo_source = _RepoSource(element, remotes)

    assert repo_source.branch is None
    assert repo_source.commit == 'abc123'
    assert repo_source.tag is None

def test_repo_source_init_valid_with_only_tag():
    element = MockElement({
        'localRoot': 'root_path',
        'remote': 'origin',
        'tag': 'v1.0'
    })
    remotes = {'origin': MockRemote('https://example.com/repo.git')}

    repo_source = _RepoSource(element, remotes)

    assert repo_source.branch is None
    assert repo_source.commit is None
    assert repo_source.tag == 'v1.0'

def test_repo_source_init_invalid_data():
    element = MockElement({
        'localRoot': 'root_path',
        'remote': 'origin'
    })
    remotes = {'origin': MockRemote('https://example.com/repo.git')}

    with pytest.raises(KeyError) as excinfo:
        _RepoSource(element, remotes)

    assert str(excinfo.value.args[0]) == ATTRIBUTE_MISSING_ERROR

# Test the tuple property
def test_repo_source_tuple():
    element = MockElement({
        'localRoot': 'root_path',
        'remote': 'origin',
        'branch': 'main',
        'commit': 'abc123',
        'sparseCheckout': 'true',
        'enableSubmodule': 'false'
    })
    remotes = {'origin': MockRemote('https://example.com/repo.git')}

    repo_source = _RepoSource(element, remotes)
    repo_tuple = repo_source.tuple

    expected_tuple = RepoSource(
        root='root_path',
        remote_name='origin',
        remote_url='https://example.com/repo.git',
        branch='main',
        commit='abc123',
        sparse=True,
        enable_submodule=False,
        tag=None,
        venv_cfg=None,
        patch_set=None,
        blobless=False,
        treeless=False,
        nested_repo=False
    )

    assert repo_tuple == expected_tuple

