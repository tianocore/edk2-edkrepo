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
MANIFEST_FILE_PATH = '/fake/path/manifest.xml'
CI_INDEX_PATH = '/fake/CiIndex.xml'
PROJECT1_NAME = 'ProjectA'
PROJECT2_NAME = 'ProjectB'

REMOTE_NAME = 'origin'
REMOTE_URL = 'https://example.com/repo.git'

REQUIRED_ATTRIB_SPLIT_CHAR = '<'

# Common XML attribute key names shared across multiple test modules
ATTRIB_NAME = 'name'
ATTRIB_REMOTE = 'remote'
FIELD_ATTRIB = 'attrib'
ATTRIB_ARCHIVED = 'archived'
ATTRIB_BOOL_TRUE = 'true'
ATTRIB_BOOL_FALSE = 'false'
ATTRIB_PATH = 'path'
ATTRIB_DESCRIPTION = 'description'
ATTRIB_FILE = 'file'
ATTRIB_SOURCE = 'source'
ARCHIVED_TRUE_UPPER = 'TRUE'
TAG_EXCLUDE = 'Exclude'
EXCLUDE_PATH = 'exclude/some/path'
FIELD_REMOTE_NAME = 'remote_name'
ATTRIB_PROJECT1 = 'project1'
ATTRIB_PROJECT2 = 'project2'
PROJECT1_FOLDER = 'project1/path'
PROJECT2_FOLDER = 'project2/path'
ATTRIB_COMBINATION = 'combination'
COMMIT = 'abc123'
BRANCH = 'main'
PATCHSET_NAME = 'ps_name'
TAG_MANIFEST = 'Manifest'
TAG_PIN = 'Pin'
UNKNOWN = 'Unknown'
HELLO = 'hello'
UPSTREAM = 'upstream'
DEV = 'dev'

# Common parametrize field strings shared across multiple test modules
PARAM_FIELD_NAME = 'field_name'
PARAM_FIELD_AND_EXPECTED = 'field_name, expected_value'
PARAM_MISSING_ATTRIB = 'missing_attrib'
PARAM_ATTRIB_VALUE_FIELD = 'attrib_key, attrib_value, field_name'
PARAM_ATTRIB_VAL_FIELD_EXPECTED = 'attrib_key, attrib_val, field_name, expected'

# Common pytest parametrize IDs shared across multiple test modules
ID_NO_MATCH = 'no_match'
ID_MISSING = 'missing'
ID_REMOTE_MISSING = 'remote_missing'
ID_REMOTE_NAME_PRESENT = 'remote_name_present'

# Common validation result strings shared across multiple test modules
BAD_XML_MSG = 'bad xml'
RESULT_PARSING = 'PARSING'
RESULT_CODENAME = 'CODENAME'
RESULT_DUPLICATE = 'DUPLICATE'

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

def make_find_map_element(find_map=None, dev_leads=None, tag=None):
    """Build a mock element whose ``find()`` returns from *find_map* and ``findall()`` returns *dev_leads*; *dev_leads* defaults to ``[]``."""
    elem = MagicMock()
    if tag is not None:
        elem.tag = tag
    fm = find_map if find_map is not None else {}
    elem.find.side_effect = lambda t: fm.get(t)
    elem.findall.return_value = dev_leads if dev_leads is not None else []
    return elem

