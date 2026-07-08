#!/usr/bin/env python3
#
## @file
# test_cache_command.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import sys
import os
from collections import defaultdict
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from edkrepo.commands.cache_command import (
    _resolve_manifest,
    _create_cache_json_object,
    _get_manifest,
    _get_used_refs,
    _get_used_refs_patchset,
    _get_operation_remote,
    _flatten_list,
)
from edkrepo.common.edkrepo_exception import EdkrepoCacheException


class TestCacheCommand:
    """Unit tests for all private helper functions in edkrepo/commands/cache_command.py."""

    REMOTE_NAME = "origin"
    REMOTE_URL = "https://example.com/repo.git"
    REMOTE_UPSTREAM = "upstream"
    REMOTE_PATCHSET = "patchset_remote"
    REMOTE_EXPLICIT = "explicit_remote"

    CACHE_REPO1_PATH = "/cache/repo1"
    CACHE_REPO2_PATH = "/cache/repo2"
    CACHE_REPO1_URL = "https://example.com/repo1.git"
    CACHE_REPO2_URL = "https://example.com/repo2.git"

    COMMIT_SHA = "abc123"
    BRANCH_NAME = "main"
    BRANCH_FEATURE = "feature"
    TAG_NAME = "v1.0"
    PATCHSET_NAME = "ps1"
    COMBO_NAME = "combo1"

    SHA_HEAD = "headsha123"
    SHA_CHERRYPICK = "sha_cp"
    SHA_REVERT = "sha_rv"
    SHA_APPLY = "sha_apply"
    SHA_FROM_PATCHSET = "sha_from_patchset"

    PROJECT_NAME = "MyProject"
    PROJECT_NAME_MISSING = "MissingProject"
    SOURCE_MANIFEST_REPO = "repo1"
    MANIFEST_PATH_EXISTING = "/some/manifest.xml"
    MANIFEST_PATH_RESOLVED = "/resolved/manifest.xml"
    MANIFEST_PATH_BAD = "/bad/manifest.xml"

    # Helper factories

    @staticmethod
    def _make_source(remote_name="origin", remote_url="https://example.com/repo.git",
                     commit=None, tag=None, branch=None, patch_set=None):
        src = MagicMock()
        src.remote_name = remote_name
        src.remote_url = remote_url
        src.commit = commit
        src.tag = tag
        src.branch = branch
        src.patch_set = patch_set
        return src

    @staticmethod
    def _make_operation(op_type, sha, source_remote=None):
        op = MagicMock()
        op.type = op_type
        op.sha = sha
        op.source_remote = source_remote
        return op

    @staticmethod
    def _make_info_item(path, remote, url):
        item = MagicMock()
        item.path = path
        item.remote = remote
        item.url = url
        return item

    @staticmethod
    def _make_manifest_with_sources(sources):
        manifest = MagicMock()
        combo = MagicMock()
        combo.name = "combo1"
        manifest.combinations = [combo]
        manifest.get_repo_sources.return_value = sources
        return manifest

    @staticmethod
    def _make_manifest_with_patchset_ops(operations):
        manifest = MagicMock()
        patchset = MagicMock()
        patchset.name = "ps1"
        patchset.remote = "origin"
        manifest.get_patchset.return_value = patchset
        manifest.get_patchset_operations.return_value = [operations]
        return manifest, patchset

    # _create_cache_json_object

    def test_normal_info_list_produces_correct_dicts(self):
        mock_info_items = [
            self._make_info_item(self.CACHE_REPO1_PATH, self.REMOTE_NAME, self.CACHE_REPO1_URL),
            self._make_info_item(self.CACHE_REPO2_PATH, self.REMOTE_UPSTREAM, self.CACHE_REPO2_URL),
        ]

        result = _create_cache_json_object(mock_info_items)

        assert len(result) == 2
        assert result[0] == {
            'path': self.CACHE_REPO1_PATH,
            'remote': self.REMOTE_NAME,
            'url': self.CACHE_REPO1_URL,
        }
        assert result[1] == {
            'path': self.CACHE_REPO2_PATH,
            'remote': self.REMOTE_UPSTREAM,
            'url': self.CACHE_REPO2_URL,
        }

    def test_empty_info_list_returns_empty_list(self):
        result = _create_cache_json_object([])

        assert result == []

    # _get_manifest

    @patch('edkrepo.commands.cache_command.os.path.exists', return_value=True)
    @patch('edkrepo.commands.cache_command.ManifestXml')
    def test_project_is_existing_file_loads_manifest_directly(self, mock_manifest_xml, mock_exists):
        config = {'cfg_file': MagicMock(), 'user_cfg_file': MagicMock()}
        expected_manifest = MagicMock()
        mock_manifest_xml.return_value = expected_manifest

        result = _get_manifest(self.MANIFEST_PATH_EXISTING, config)

        mock_manifest_xml.assert_called_once_with(self.MANIFEST_PATH_EXISTING)
        assert result is expected_manifest

    @patch('edkrepo.commands.cache_command.os.path.exists', return_value=False)
    @patch('edkrepo.commands.cache_command.find_project_in_all_indices',
           return_value=("repo", "cfg", "/resolved/manifest.xml"))
    @patch('edkrepo.commands.cache_command.ManifestXml')
    def test_project_name_found_in_indices(self, mock_manifest_xml, mock_find, mock_exists):
        config = {'cfg_file': MagicMock(), 'user_cfg_file': MagicMock()}
        expected_manifest = MagicMock()
        mock_manifest_xml.return_value = expected_manifest

        result = _get_manifest(self.PROJECT_NAME, config)

        mock_manifest_xml.assert_called_once_with(self.MANIFEST_PATH_RESOLVED)
        assert result is expected_manifest

    @patch('edkrepo.commands.cache_command.os.path.exists', return_value=False)
    @patch('edkrepo.commands.cache_command.find_project_in_all_indices', side_effect=Exception("not found"))
    def test_project_name_not_found_raises_load_exception(self, mock_find, mock_exists):
        config = {'cfg_file': MagicMock(), 'user_cfg_file': MagicMock()}

        with pytest.raises(EdkrepoCacheException):
            _get_manifest(self.PROJECT_NAME_MISSING, config)

    @patch('edkrepo.commands.cache_command.os.path.exists', return_value=True)
    @patch('edkrepo.commands.cache_command.ManifestXml', side_effect=Exception("bad xml"))
    def test_manifest_parse_failure_raises_parse_exception(self, mock_manifest_xml, mock_exists):
        config = {'cfg_file': MagicMock(), 'user_cfg_file': MagicMock()}

        with pytest.raises(EdkrepoCacheException):
            _get_manifest(self.MANIFEST_PATH_BAD, config)

    # _resolve_manifest

    @patch('edkrepo.commands.cache_command._get_manifest')
    def test_project_arg_provided_delegates_to_get_manifest(self, mock_get_manifest):
        args = MagicMock()
        args.project = self.PROJECT_NAME
        args.source_manifest_repo = self.SOURCE_MANIFEST_REPO
        config = {'cfg_file': MagicMock(), 'user_cfg_file': MagicMock()}
        expected_manifest = MagicMock()
        mock_get_manifest.return_value = expected_manifest

        result = _resolve_manifest(args, config)

        mock_get_manifest.assert_called_once_with(self.PROJECT_NAME, config, self.SOURCE_MANIFEST_REPO)
        assert result is expected_manifest

    @patch('edkrepo.commands.cache_command.get_workspace_manifest')
    def test_no_project_arg_workspace_manifest_found(self, mock_get_workspace_manifest):
        args = MagicMock()
        args.project = None
        args.source_manifest_repo = None
        config = {'cfg_file': MagicMock(), 'user_cfg_file': MagicMock()}
        expected_manifest = MagicMock()
        mock_get_workspace_manifest.return_value = expected_manifest

        result = _resolve_manifest(args, config)

        assert result is expected_manifest

    @patch('edkrepo.commands.cache_command.get_workspace_manifest', side_effect=Exception("no workspace"))
    def test_no_project_arg_workspace_manifest_not_found(self, mock_get_workspace_manifest):
        args = MagicMock()
        args.project = None
        args.source_manifest_repo = None
        config = {'cfg_file': MagicMock(), 'user_cfg_file': MagicMock()}

        result = _resolve_manifest(args, config)

        assert result is None

    # _get_used_refs

    def test_uncached_commit_is_included(self):
        source = self._make_source(remote_name=self.REMOTE_NAME, commit=self.COMMIT_SHA)
        cache_obj = MagicMock()
        cache_obj.is_sha_cached.return_value = False
        manifest = self._make_manifest_with_sources([source])

        result = _get_used_refs(manifest, cache_obj)

        assert self.REMOTE_NAME in result
        assert self.COMMIT_SHA in result[self.REMOTE_NAME]

    def test_already_cached_commit_is_excluded(self):
        source = self._make_source(remote_name=self.REMOTE_NAME, commit=self.COMMIT_SHA)
        cache_obj = MagicMock()
        cache_obj.is_sha_cached.return_value = True
        manifest = self._make_manifest_with_sources([source])

        result = _get_used_refs(manifest, cache_obj)

        assert self.REMOTE_NAME not in result

    def test_uncached_tag_is_included(self):
        source = self._make_source(remote_name=self.REMOTE_NAME, tag=self.TAG_NAME)
        cache_obj = MagicMock()
        cache_obj.is_sha_cached.return_value = False
        manifest = self._make_manifest_with_sources([source])

        result = _get_used_refs(manifest, cache_obj)

        assert self.REMOTE_NAME in result
        assert self.TAG_NAME in result[self.REMOTE_NAME]

    @patch('edkrepo.commands.cache_command.get_latest_sha', return_value="headsha123")
    def test_branch_with_uncached_head_sha_is_included(self, mock_get_latest_sha):
        source = self._make_source(remote_name=self.REMOTE_NAME, branch=self.BRANCH_NAME)
        cache_obj = MagicMock()
        cache_obj.is_sha_cached.return_value = False
        manifest = self._make_manifest_with_sources([source])

        result = _get_used_refs(manifest, cache_obj)

        assert self.REMOTE_NAME in result
        assert self.BRANCH_NAME in result[self.REMOTE_NAME]

    @patch('edkrepo.commands.cache_command.get_latest_sha', return_value=None)
    def test_branch_with_unresolvable_head_sha_is_included(self, mock_get_latest_sha):
        source = self._make_source(remote_name=self.REMOTE_NAME, branch=self.BRANCH_FEATURE)
        cache_obj = MagicMock()
        manifest = self._make_manifest_with_sources([source])

        result = _get_used_refs(manifest, cache_obj)

        assert self.REMOTE_NAME in result
        assert self.BRANCH_FEATURE in result[self.REMOTE_NAME]

    @patch('edkrepo.commands.cache_command._get_used_refs_patchset')
    def test_source_with_patchset_delegates_to_get_used_refs_patchset(self, mock_get_used_refs_patchset):
        source = self._make_source(remote_name=self.REMOTE_NAME, patch_set=self.PATCHSET_NAME)
        cache_obj = MagicMock()
        manifest = self._make_manifest_with_sources([source])
        mock_get_used_refs_patchset.return_value = defaultdict(
            list, {self.REMOTE_NAME: [self.SHA_FROM_PATCHSET]}
        )

        result = _get_used_refs(manifest, cache_obj)

        mock_get_used_refs_patchset.assert_called_once_with(manifest, source)
        assert self.SHA_FROM_PATCHSET in result[self.REMOTE_NAME]

    # _get_used_refs_patchset

    def test_cherrypick_and_revert_operations_are_collected(self):
        op_cp = self._make_operation('CherryPick', self.SHA_CHERRYPICK, source_remote=self.REMOTE_NAME)
        op_rv = self._make_operation('Revert', self.SHA_REVERT, source_remote=self.REMOTE_NAME)
        source = self._make_source(remote_name=self.REMOTE_NAME, patch_set=self.PATCHSET_NAME)
        manifest, _ = self._make_manifest_with_patchset_ops([op_cp, op_rv])

        result = _get_used_refs_patchset(manifest, source)

        assert self.SHA_CHERRYPICK in result[self.REMOTE_NAME]
        assert self.SHA_REVERT in result[self.REMOTE_NAME]

    def test_unsupported_operation_types_are_ignored(self):
        op_other = self._make_operation('Apply', self.SHA_APPLY, source_remote=self.REMOTE_NAME)
        source = self._make_source(remote_name=self.REMOTE_NAME, patch_set=self.PATCHSET_NAME)
        manifest, _ = self._make_manifest_with_patchset_ops([op_other])

        result = _get_used_refs_patchset(manifest, source)

        assert result == defaultdict(list)

    # _get_operation_remote

    def test_operation_with_source_remote_returns_source_remote(self):
        patchset = MagicMock()
        patchset.remote = self.REMOTE_PATCHSET
        operation = MagicMock()
        operation.source_remote = self.REMOTE_EXPLICIT

        result = _get_operation_remote(patchset, operation)

        assert result == self.REMOTE_EXPLICIT

    def test_operation_without_source_remote_returns_patchset_remote(self):
        patchset = MagicMock()
        patchset.remote = self.REMOTE_PATCHSET
        operation = MagicMock()
        operation.source_remote = None

        result = _get_operation_remote(patchset, operation)

        assert result == self.REMOTE_PATCHSET

    # _flatten_list

    def test_nested_list_is_flattened(self):
        result = _flatten_list([[1, 2], [3, 4], [5]])

        assert result == [1, 2, 3, 4, 5]

    def test_empty_list_returns_empty_list(self):
        result = _flatten_list([])

        assert result == []
