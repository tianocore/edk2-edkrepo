#!/usr/bin/env python3
#
## @file
# helpers.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

from unittest.mock import MagicMock

ATTRIB_NAME    = 'name'
ATTRIB_PATH    = 'path'
ATTRIB_REMOTE  = 'remote'
ATTRIB_PROJECT1 = 'project1'
ATTRIB_PROJECT2 = 'project2'
ATTRIB_BOOL_TRUE  = 'true'
ATTRIB_BOOL_FALSE = 'false'

TAG_EXCLUDE = 'Exclude'

REMOTE_NAME = 'origin'
REMOTE_URL  = 'https://example.com/repo.git'

REQUIRED_ATTRIB_SPLIT_CHAR = '<'

ELEMENT_TAG_COMBINATION     = 'Combination'
ELEMENT_TAG_PATCHSET        = 'PatchSet'
ELEMENT_TAG_CHERRY_PICK     = 'CherryPick'
ELEMENT_TAG_PROJECT         = 'Project'
ELEMENT_TAG_PROJECT_INFO    = 'ProjectInfo'
ELEMENT_TAG_REMOTE_REPO     = 'RemoteRepo'
ELEMENT_TAG_CLIENT_GIT_HOOK = 'ClientGitHook'
ELEMENT_TAG_SOURCE          = 'Source'
ELEMENT_TAG_SUBMODULE_ALT   = 'SubmoduleAlternateRemote'
ELEMENT_TAG_SUBMODULE_INIT  = 'SubmoduleInitEntry'
ELEMENT_TAG_CI_PROJECT_LIST = 'ProjectList'
ELEMENT_TAG_MANIFEST        = 'Manifest'
ELEMENT_TAG_PIN             = 'Pin'

TAG_FOLDER         = 'Folder'
TAG_FILE           = 'File'
TAG_ALWAYS_INCLUDE = 'AlwaysInclude'
TAG_ALWAYS_EXCLUDE = 'AlwaysExclude'

CHILD_PIN_PATH             = 'PinPath'
CHILD_DEFAULT_COMBO        = 'DefaultCombo'
CHILD_CURR_COMBO           = 'CurrentClonedCombo'
CHILD_SOURCE_MANIFEST_REPO = 'SourceManifestRepository'
CHILD_CODE_NAME            = 'CodeName'
CHILD_DESCRIPT             = 'Description'
CHILD_ORG                  = 'Org'
CHILD_SHORT_NAME           = 'ShortName'
CHILD_LEAD_REVIEWERS       = 'LeadReviewers'

ATTRIB_ARCHIVED          = 'archived'
ATTRIB_COMBINATION       = 'combination'
ATTRIB_DESCRIPTION       = 'description'
ATTRIB_VENV_ENABLE       = 'venv_enable'
ATTRIB_XML_PATH          = 'xmlPath'
ATTRIB_MANIFEST_REPO     = 'manifest_repo'
ATTRIB_ORIGINAL_URL      = 'originalUrl'
ATTRIB_SPARSE_BY_DEFAULT = 'sparseByDefault'
ATTRIB_LOCAL_ROOT        = 'localRoot'
ATTRIB_BRANCH            = 'branch'
ATTRIB_COMMIT            = 'commit'
ATTRIB_TAG               = 'tag'
ATTRIB_PATCH_SET         = 'patchSet'
ATTRIB_SPARSE            = 'sparseCheckout'
ATTRIB_ENABLE_SUB        = 'enableSubmodule'
ATTRIB_ENABLE_SUB_LEGACY = 'enable_submodule'
ATTRIB_VENV_CFG          = 'venv_cfg'
ATTRIB_BLOBLESS          = 'blobless'
ATTRIB_TREELESS          = 'treeless'
ATTRIB_OWNER             = 'owner'
ATTRIB_REVIEW_TYPE       = 'reviewType'
ATTRIB_PR_STRATEGY       = 'prStrategy'
ATTRIB_SOURCE            = 'source'
ATTRIB_DESTINATION       = 'destination'
ATTRIB_DEST_FILE         = 'destination_file'
ATTRIB_PARENT_SHA        = 'parentSha'
ATTRIB_FETCH_BRANCH      = 'fetchBranch'
ATTRIB_FILE              = 'file'
ATTRIB_SHA               = 'sha'
ATTRIB_SOURCE_REMOTE     = 'sourceRemote'
ATTRIB_SOURCE_BRANCH     = 'sourceBranch'
ATTRIB_MERGE_STRATEGY    = 'mergeStrategy'
ATTRIB_COMBO             = 'combo'
ATTRIB_RECURSIVE         = 'recursive'
ARCHIVED_TRUE_UPPER      = 'TRUE'

FIELD_REMOTE_NAME          = 'remote_name'
FIELD_PROJECT1_FOLDER      = 'project1_folder'
FIELD_PROJECT2_FOLDER      = 'project2_folder'
FIELD_ALWAYS_INCLUDE       = 'always_include'
FIELD_ALWAYS_EXCLUDE       = 'always_exclude'
FIELD_PIN_PATH             = 'pin_path'
FIELD_DEFAULT_COMBO        = 'default_combo'
FIELD_CURR_COMBO           = 'curr_combo'
FIELD_SOURCE_MANIFEST_REPO = 'source_manifest_repo'
FIELD_ALT_URL              = 'altUrl'
FIELD_REVIEW_TYPE          = 'review_type'
FIELD_PR_STRATEGY          = 'pr_strategy'
FIELD_SPARSE               = 'sparse'
FIELD_ENABLE_SUB           = 'enableSub'
FIELD_NESTED_REPO          = 'nested_repo'
FIELD_SOURCE_REMOTE        = 'source_remote'
FIELD_SOURCE_BRANCH        = 'source_branch'
FIELD_MERGE_STRATEGY       = 'merge_strategy'
FIELD_FILE                 = 'file'
FIELD_SHA                  = 'sha'
FIELD_OWNER                = 'owner'

NO_REMOTE_SPLIT_CHAR = '{'

UNKNOWN_REMOTE = 'UnknownRemote'
ORIGINAL_URL   = 'https://example.com/submodule.git'
ALT_URL        = 'https://mirror.example.com/submodule.git'

PROJECT1_NAME   = 'ProjectA'
PROJECT2_NAME   = 'ProjectB'
PROJECT1_FOLDER = f'{PROJECT1_NAME}/src'
PROJECT2_FOLDER = f'{PROJECT2_NAME}/src'
EXCLUDE_PATH    = '/project/src/file.c'
PROJECT_XML_A   = f'{PROJECT1_NAME}/{PROJECT1_NAME}.xml'

MANIFEST_PATH       = '/fake/manifest.xml'
COMBO_NAME          = 'TestCombo'
PIN_PREFIX_COMBO    = 'Pin:some_pin'
UNKNOWN_COMBO       = 'UnknownCombo'
PATCHSET_NAME       = 'test_patch'
OTHER_PATCHSET_NAME = 'other_patch'
UNKNOWN_PATCHSET    = 'unknown_patch'
PARENT_REPO         = 'parent_repo'
NESTED_REPO         = 'parent_repo/child_repo'
INVALID_REPO_PATH   = 'invalid_path'
BRANCH              = 'main'

PIN_PATH             = '/path/to/pins'
DEFAULT_COMBO        = 'MainCombo'
CURR_COMBO           = 'ClonedCombo'
SOURCE_MANIFEST_REPO = 'MyManifestRepo'

TEST_PROJECT_NAME = 'TestProject'
PROJECT_XML_PATH  = f'{TEST_PROJECT_NAME}/{TEST_PROJECT_NAME}.xml'
DESCRIPT          = 'A test project description.'
LEAD              = 'lead@example.com'
ORG               = 'Intel'
SHORT_NAME        = 'TP'
REVIEWER          = 'reviewer@example.com'

OWNER       = 'owner@example.com'
REVIEW_TYPE = 'gerrit'
PR_STRATEGY = 'squash'

HOOK_SOURCE = 'hooks/commit-msg'
DEST_PATH   = '.git/hooks'
DEST_FILE   = 'commit-msg'

LOCAL_ROOT        = 'my_repo'
NESTED_LOCAL_ROOT = 'parent/child'
COMMIT            = 'abc123def456'
TAG               = 'v1.0.0'
PATCH_SET         = 'my_patch'
VENV_CFG          = 'venv.cfg'

COMBINATION    = 'main_combo'
INCLUDE_VALUE  = '/sparse/include/path'
EXCLUDE_VALUE  = '/sparse/exclude/path'
INCLUDE_MULTI  = '/path/a|/path/b|/path/c'
PIPE_SEPARATOR = '|'

COMBO_DESCRIPTION = 'A test combination.'

SUBMODULE_PATH_VALUE = '/modules/firmware'
SUBMODULE_COMBO      = 'my_combo'

OPS_FILE           = 'some/file.c'
OPS_SHA            = 'deadbeef01234567'
OPS_SOURCE_REMOTE  = 'upstream'
OPS_SOURCE_BRANCH  = 'feature-branch'
OPS_MERGE_STRATEGY = 'ours'

CI_INDEX_PATH       = '/fake/CiIndex.xml'
CI_UNKNOWN_PROJECT  = 'Unknown'
CI_DEFAULT_XML_PATH = 'fake_path.xml'

ATTRIB_FIELD_FIELDS                = 'attrib_key,attrib_value,field_name'
MISSING_ATTRIB_FIELDS              = 'missing_attrib'
CI_PARAMETRIZE_FIELDS              = 'archived_a,archived_b,expected'
COMBINATION_BOOL_FLAG_FIELDS       = 'attrib_name,attrib_value,field_name,expected'
COMBINATION_REQUIRED_FIELD_FIELDS  = 'field_name,expected'
PARAMETRIZE_FIELD_NAME             = 'field_name'
PROJECT_ARCHIVED_FLAG_FIELDS       = 'archived_value,expected'
BOOL_FLAG_FIELDS                   = 'attrib_val,expected'
REPO_SOURCE_BOOL_FIELD_FIELDS      = 'extra,field_name,expected'
REPO_SOURCE_PATCH_SET_COMBO_FIELDS = 'ref_attrib_key,ref_attrib_val'
SUBMODULE_ALT_PARSE_RAISES_FIELDS  = 'attrib'

ID_MIXED                = 'mixed'
ID_ALL_ARCHIVED         = 'all_archived'
ID_NONE_ARCHIVED        = 'none_archived'
ID_TRUE_LOWER           = 'true_lower'
ID_FALSE_LOWER          = 'false_lower'
ID_MISSING              = 'missing'
ID_TRUE_UPPER           = 'true_upper'
ID_ARCHIVED_TRUE_LOWER  = 'archived_true_lower'
ID_ARCHIVED_FALSE_LOWER = 'archived_false_lower'
ID_ARCHIVED_MISSING     = 'archived_missing'
ID_ARCHIVED_TRUE_UPPER  = 'archived_true_upper'
ID_VENV_TRUE            = 'venv_true'
ID_VENV_FALSE           = 'venv_false'
ID_VENV_MISSING         = 'venv_missing'
ID_PARENT_SHA           = 'parent_sha'
ID_FETCH_BRANCH         = 'fetch_branch'
ID_SPARSE_MISSING       = 'sparse_missing'
ID_SPARSE_TRUE          = 'sparse_true'
ID_SPARSE_FALSE         = 'sparse_false'
ID_ENABLE_SUB_MISSING   = 'enable_sub_missing'
ID_ENABLE_SUB_TRUE      = 'enable_sub_true'
ID_ENABLE_SUB_FALSE     = 'enable_sub_false'
ID_BLOBLESS_MISSING     = 'blobless_missing'
ID_BLOBLESS_TRUE        = 'blobless_true'
ID_BLOBLESS_FALSE       = 'blobless_false'
ID_TREELESS_MISSING     = 'treeless_missing'
ID_TREELESS_TRUE        = 'treeless_true'
ID_TREELESS_FALSE       = 'treeless_false'
ID_REMOTE_MISSING       = 'remote_missing'
ID_ORIGINAL_URL_MISSING = 'original_url_missing'


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
