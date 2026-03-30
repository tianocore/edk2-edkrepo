#!/usr/bin/env python3
#
## @file
# helpers.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

from unittest.mock import MagicMock

MANIFEST_PATH = '/fake/manifest.xml'
CI_INDEX_PATH = '/fake/CiIndex.xml'
PROJECT1_NAME = 'ProjectA'
PROJECT2_NAME = 'ProjectB'

REMOTE_NAME = 'origin'
REMOTE_URL  = 'https://example.com/repo.git'

REQUIRED_ATTRIB_SPLIT_CHAR = '<'

def make_mock_element(attrib, tag=None):
    """Build a mock element with the given *attrib* dict and an optional *tag*; leave tag unset when ``None``."""
    elem = MagicMock()
    elem.attrib = attrib if attrib is not None else {}
    if tag is not None:
        elem.tag = tag
    return elem

def make_mock_element_with_iter(attrib, iter_map=None):
    """Build a mock element whose ``iter(tag)`` returns children from *iter_map* keyed by tag string."""
    elem = MagicMock()
    elem.attrib = attrib if attrib is not None else {}
    im = iter_map if iter_map is not None else {}
    elem.iter.side_effect = lambda tag: iter(im.get(tag, []))
    return elem

def make_mock_element_with_text(attrib, text=None, tag=None):
    """Build a mock element with the given *attrib*, optional ``.text`` content, and optional *tag*."""
    elem = MagicMock()
    elem.attrib = attrib if attrib is not None else {}
    elem.text = text
    if tag is not None:
        elem.tag = tag
    return elem

def make_text_element(text):
    """Build a mock element whose ``.text`` attribute equals *text*."""
    elem = MagicMock()
    elem.text = text
    return elem

def make_attrib_element(attrib):
    """Build a mock element whose ``.attrib`` dict equals *attrib*."""
    elem = MagicMock()
    elem.attrib = attrib
    return elem

def make_mock_remotes(remote_name=None, url=None):
    """Build a remotes dict mapping *remote_name* to a mock with ``.url``; defaults to REMOTE_NAME and REMOTE_URL."""
    if remote_name is None:
        remote_name = REMOTE_NAME
    if url is None:
        url = REMOTE_URL
    mock_remote = MagicMock()
    mock_remote.url = url
    return {remote_name: mock_remote}

def make_empty_element():
    """Build a mock element with no attributes and no iter children."""
    return make_mock_element_with_iter({})

