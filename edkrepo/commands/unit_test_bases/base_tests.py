#!/usr/bin/env python3
#
## @file
# base_tests.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import importlib
import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from edkrepo.commands.arguments import sparse_args
from edkrepo.common import edkrepo_exception


FAKE_WORKSPACE_PATH = '/fake/workspace'

CFG_FILE_KEY = 'cfg_file'
USER_CFG_FILE_KEY = 'user_cfg_file'


class BaseCommandTest:

    command_module = None

    @pytest.fixture
    def mock_config(self):
        """Return a config dict with mock cfg_file and user_cfg_file entries."""
        return {CFG_FILE_KEY: MagicMock(), USER_CFG_FILE_KEY: MagicMock()}

    @pytest.fixture
    def mock_get_workspace_manifest(self):
        """Patch get_workspace_manifest in the command module; yields the mock."""
        with patch('{}.get_workspace_manifest'.format(self.__class__.command_module)) as mock:
            yield mock

    @pytest.fixture
    def mock_get_workspace_path(self):
        """Patch get_workspace_path returning FAKE_WORKSPACE_PATH; yields the mock."""
        with patch('{}.get_workspace_path'.format(self.__class__.command_module),
                   return_value=FAKE_WORKSPACE_PATH) as mock:
            yield mock

    @pytest.fixture
    def mock_pull_all_manifest_repos(self):
        """Patch pull_all_manifest_repos in the command module; yields the mock."""
        with patch('{}.pull_all_manifest_repos'.format(self.__class__.command_module)) as mock:
            yield mock

    @pytest.fixture
    def mock_print_info_msg(self):
        """Patch ui_functions.print_info_msg in the command module; yields the mock."""
        with patch('{}.ui_functions.print_info_msg'.format(self.__class__.command_module)) as mock:
            yield mock

    @pytest.fixture
    def mock_print_warning_msg(self):
        """Patch ui_functions.print_warning_msg in the command module; yields the mock."""
        with patch('{}.ui_functions.print_warning_msg'.format(self.__class__.command_module)) as mock:
            yield mock

    @pytest.fixture
    def mock_sparse_checkout_enabled(self):
        """Patch sparse_checkout_enabled returning False; yields the mock."""
        with patch('{}.sparse_checkout_enabled'.format(self.__class__.command_module),
                   return_value=False) as mock:
            yield mock

    @pytest.fixture
    def mock_check_dirty_repos(self):
        """Patch check_dirty_repos in the command module; yields the mock."""
        with patch('{}.check_dirty_repos'.format(self.__class__.command_module)) as mock:
            yield mock

    @pytest.fixture
    def mock_sparse_checkout(self):
        """Patch sparse_checkout in the command module; yields the mock."""
        with patch('{}.sparse_checkout'.format(self.__class__.command_module)) as mock:
            yield mock

    @pytest.fixture
    def mock_reset_sparse_checkout(self):
        """Patch reset_sparse_checkout in the command module; yields the mock."""
        with patch('{}.reset_sparse_checkout'.format(self.__class__.command_module)) as mock:
            yield mock

    @pytest.fixture
    def mock_find_less(self):
        """Patch find_less returning no less tool; yields the mock."""
        with patch('{}.find_less'.format(self.__class__.command_module),
                   return_value=(None, False)) as mock:
            yield mock

    @pytest.fixture
    def mock_sys_exit(self):
        """Patch sys.exit in the command module; yields the mock."""
        with patch('{}.sys.exit'.format(self.__class__.command_module)) as mock:
            yield mock


METADATA_KEY_NAME = 'name'
METADATA_KEY_HELP_TEXT = 'help-text'
METADATA_KEY_ARGUMENTS = 'arguments'


class BaseTestSparseCommand(BaseCommandTest):
    @pytest.fixture
    def sparse_cmd(self):
        """Return a fresh SparseCommand instance from the module under test."""
        command_mod = importlib.import_module(self.__class__.command_module)
        return command_mod.SparseCommand()

    @pytest.fixture
    def mock_args(self):
        """Return a mock args namespace with enable, disable, and verbose set to safe defaults."""
        args = MagicMock()
        args.enable = False
        args.disable = False
        args.verbose = False
        return args

    @pytest.fixture(autouse=True)
    def mock_get_workspace_path(self):
        """Patch get_workspace_path returning FAKE_WORKSPACE_PATH; always active since run_command calls it unconditionally."""
        with patch('{}.get_workspace_path'.format(self.__class__.command_module),
                   return_value=FAKE_WORKSPACE_PATH) as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def mock_get_workspace_manifest(self):
        """Patch get_workspace_manifest with empty repo sources; always active since run_command calls it unconditionally."""
        with patch('{}.get_workspace_manifest'.format(self.__class__.command_module)) as mock:
            mock.return_value.get_repo_sources.return_value = []
            yield mock

    @pytest.fixture(autouse=True)
    def mock_sparse_checkout_enabled(self):
        """Patch sparse_checkout_enabled returning False; always active since run_command calls it unconditionally."""
        with patch('{}.sparse_checkout_enabled'.format(self.__class__.command_module),
                   return_value=False) as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def mock_print_info_msg(self):
        """Patch ui_functions.print_info_msg; always active to suppress status output while run_command executes."""
        with patch('{}.ui_functions.print_info_msg'.format(self.__class__.command_module)) as mock:
            yield mock

    @staticmethod
    def _run_and_expect_sparse_exception(sparse_cmd, mock_args, mock_config):
        """Execute run_command and assert EdkrepoSparseException is raised."""
        with pytest.raises(edkrepo_exception.EdkrepoSparseException):
            sparse_cmd.run_command(mock_args, mock_config)

    def test_init_creates_instance_without_error(self, sparse_cmd):
        """SparseCommand() must construct successfully with no positional arguments."""
        assert sparse_cmd is not None

    def test_run_command_enable_performs_sparse_checkout(self, sparse_cmd, mock_args, mock_config, mock_get_workspace_manifest, mock_check_dirty_repos, mock_sparse_checkout):
        """Enabling sparse when currently disabled must check dirty repos and perform the sparse checkout."""
        mock_args.enable = True
        manifest = mock_get_workspace_manifest.return_value

        sparse_cmd.run_command(mock_args, mock_config)

        mock_check_dirty_repos.assert_called_once_with(manifest, FAKE_WORKSPACE_PATH)
        mock_sparse_checkout.assert_called_once_with(FAKE_WORKSPACE_PATH, [], manifest)

    def test_run_command_disable_resets_sparse_checkout(self, sparse_cmd, mock_args, mock_config, mock_check_dirty_repos, mock_reset_sparse_checkout, mock_sparse_checkout_enabled):
        """Disabling sparse when currently enabled must reset the sparse checkout."""
        mock_args.disable = True
        mock_sparse_checkout_enabled.return_value = True

        sparse_cmd.run_command(mock_args, mock_config)

        mock_reset_sparse_checkout.assert_called_once_with(FAKE_WORKSPACE_PATH, [], True)

    @pytest.mark.parametrize('metadata_key, expected_value', [
        pytest.param(METADATA_KEY_NAME, 'sparse', id='name'),
        pytest.param(METADATA_KEY_HELP_TEXT, sparse_args.COMMAND_DESCRIPTION, id='help_text'),
    ])
    def test_get_metadata_returns_expected_top_level_field(self, sparse_cmd, metadata_key, expected_value):
        """get_metadata must report the correct command name and help text."""
        metadata = sparse_cmd.get_metadata()

        assert metadata[metadata_key] == expected_value

    @pytest.mark.parametrize('arg_name, expected_help_text', [
        pytest.param('enable', sparse_args.ENABLE_HELP, id='enable'),
        pytest.param('disable', sparse_args.DISABLE_HELP, id='disable'),
    ])
    def test_get_metadata_includes_argument_with_help_text(self, sparse_cmd, arg_name, expected_help_text):
        """get_metadata must include the enable/disable argument with its help text."""
        metadata = sparse_cmd.get_metadata()
        arg = next(arg for arg in metadata[METADATA_KEY_ARGUMENTS] if arg[METADATA_KEY_NAME] == arg_name)

        assert arg[METADATA_KEY_HELP_TEXT] == expected_help_text

    @pytest.mark.parametrize('enable, disable, checkout_enabled', [
        pytest.param(True, True, False, id='both_flags'),
        pytest.param(False, True, False, id='disable_already_disabled'),
        pytest.param(True, False, True, id='enable_already_enabled'),
    ])
    def test_run_command_raises_sparse_exception_for_invalid_state(self, sparse_cmd, mock_args, mock_config, mock_sparse_checkout_enabled, enable, disable, checkout_enabled):
        """Both flags set, disabling when already disabled, or enabling when already enabled must raise EdkrepoSparseException."""
        mock_args.enable = enable
        mock_args.disable = disable
        mock_sparse_checkout_enabled.return_value = checkout_enabled

        self._run_and_expect_sparse_exception(sparse_cmd, mock_args, mock_config)


SEND_REVIEW_OPEN_SOURCE_MODULE = 'edkrepo.commands.send_review_command'
PATCH_GET_GIT_CONFIG_EMAIL = '{}.common_repo_functions.get_git_config_email'.format(SEND_REVIEW_OPEN_SOURCE_MODULE)
PATCH_REPO = '{}.Repo'.format(SEND_REVIEW_OPEN_SOURCE_MODULE)
PATCH_GET_COMMITS_AHEAD = '{}.common_repo_functions.get_commits_ahead'.format(SEND_REVIEW_OPEN_SOURCE_MODULE)

PR_TITLE_WITH_SPECIAL_CHARS = 'My Title! (v2)'
CREATED_BRANCH_NAME = 'pull_request/test.user/2026-01-01_00-00/my_title_v2'

CHANGED_FILE_A_PATH = 'src/old_name.c'
CHANGED_FILE_B_PATH = 'src/new_name.c'
CHANGED_FILE_UNCHANGED_PATH = 'src/unchanged.c'

MATCH_BY_ROOT = 'root'
MATCH_BY_REMOTE_NAME = 'remote_name'

WORKSPACE_PATH = '/workspace'
REPO_REFERENCE = 'target_repo'
REPO_ROOT = 'Repos/TargetRepo'
REPO_BRANCH = 'main'
ORIGIN_REMOTE_NAME = 'origin'
OTHER_REMOTE_NAME = 'other_remote'
FAKE_COMMIT = 'commit'


class BaseTestSendReviewCommand(BaseCommandTest):

    @pytest.fixture
    def send_review_cmd(self):
        """Return a fresh SendReviewCommand instance from the module under test."""
        command_mod = importlib.import_module(self.__class__.command_module)
        return command_mod.SendReviewCommand()

    @pytest.fixture
    def mock_repo(self):
        """Return a mock git Repo whose create_head returns a branch stub with a fixed name."""
        repo = MagicMock()
        repo.create_head.return_value.name = CREATED_BRANCH_NAME
        return repo

    @pytest.fixture
    def mock_get_git_config_email(self):
        """Patch get_git_config_email in the open-source module; yields the mock."""
        with patch(PATCH_GET_GIT_CONFIG_EMAIL, return_value='test.user@example.com') as mock:
            yield mock

    @pytest.fixture
    def get_changed_file_list(self):
        """Return the get_changed_file_list function from the module under test."""
        command_mod = importlib.import_module(self.__class__.command_module)
        return command_mod.get_changed_file_list

    @pytest.fixture
    def modified_repo_class(self):
        """Return the ModifiedRepo class from the module under test."""
        command_mod = importlib.import_module(self.__class__.command_module)
        return command_mod.ModifiedRepo

    @pytest.fixture
    def mock_args(self):
        """Return a mock args namespace with send-review arguments set to safe defaults."""
        args = MagicMock()
        args.repository = None
        args.verbose = False
        args.dry_run = False
        args.override = False
        return args

    @pytest.fixture(autouse=True)
    def mock_get_workspace_path(self):
        """Patch config_factory.get_workspace_path returning FAKE_WORKSPACE_PATH; always active."""
        with patch('{}.config_factory.get_workspace_path'.format(self.__class__.command_module),
                   return_value=FAKE_WORKSPACE_PATH) as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def mock_get_workspace_manifest(self):
        """Patch config_factory.get_workspace_manifest; always active since run_command calls it unconditionally."""
        with patch('{}.config_factory.get_workspace_manifest'.format(self.__class__.command_module)) as mock:
            yield mock

    @pytest.fixture
    def mock_modified_repo_class(self):
        """Patch ModifiedRepo; used by run_command tests since run_command instantiates it unconditionally."""
        with patch('{}.ModifiedRepo'.format(self.__class__.command_module)) as mock:
            yield mock

    @pytest.fixture
    def mock_get_review_type(self):
        """Patch __get_review_type returning PR_FORK; used by run_command tests to short-circuit run_command."""
        command_mod = importlib.import_module(self.__class__.command_module)
        with patch.object(command_mod.SendReviewCommand, '_SendReviewCommand__get_review_type',
                          return_value=command_mod.Reviews.PR_FORK) as mock:
            yield mock

    @staticmethod
    def _run_and_expect_warning(send_review_cmd, mock_args, mock_config):
        """Execute run_command and assert EdkrepoWarningException is raised."""
        with pytest.raises(edkrepo_exception.EdkrepoWarningException):
            send_review_cmd.run_command(mock_args, mock_config)

    @staticmethod
    def _make_manifest_repo(root, remote_name, branch=REPO_BRANCH, patch_set=False):
        """Return a mock manifest repo source with the given root, remote name, branch, and patch_set flag."""
        manifest_repo = MagicMock()
        manifest_repo.root = root
        manifest_repo.remote_name = remote_name
        manifest_repo.branch = branch
        manifest_repo.patch_set = patch_set
        return manifest_repo

    @staticmethod
    def _make_manifest(repo_sources):
        """Return a mock manifest whose get_repo_sources returns the given repo sources."""
        manifest = MagicMock()
        manifest.get_repo_sources.return_value = repo_sources
        return manifest

    @staticmethod
    def _make_single_repo_manifest_with_git(patch_set=False):
        """Return (manifest_repo, manifest, mock_git_repo) for a single non-detached repo source at REPO_ROOT/ORIGIN_REMOTE_NAME."""
        manifest_repo = BaseTestSendReviewCommand._make_manifest_repo(root=REPO_ROOT, remote_name=ORIGIN_REMOTE_NAME, patch_set=patch_set)
        manifest = BaseTestSendReviewCommand._make_manifest([manifest_repo])
        mock_git_repo = MagicMock()
        mock_git_repo.head.is_detached = False
        return manifest_repo, manifest, mock_git_repo

    def test_init_creates_instance_without_error(self, send_review_cmd):
        """SendReviewCommand() must construct successfully with no positional arguments."""
        assert send_review_cmd is not None

    def test_create_pr_branch_raises_when_git_email_not_found(self, send_review_cmd, mock_repo):
        """_create_pr_branch must raise EdkRepoGitEmailNotFoundException when no git email is configured."""
        with patch(PATCH_GET_GIT_CONFIG_EMAIL, return_value=''):
            with pytest.raises(edkrepo_exception.EdkRepoGitEmailNotFoundException):
                send_review_cmd._create_pr_branch(MagicMock(), mock_repo, PR_TITLE_WITH_SPECIAL_CHARS)

    def test_create_pr_branch_creates_branch_with_normalized_name_and_returns_its_name(self, send_review_cmd, mock_repo, mock_get_git_config_email):
        """_create_pr_branch must create a head branch embedding the git username/normalized title and return its name."""
        result = send_review_cmd._create_pr_branch(MagicMock(), mock_repo, PR_TITLE_WITH_SPECIAL_CHARS)
        created_branch_name = mock_repo.create_head.call_args[0][0]

        assert created_branch_name.startswith('pull_request/test.user/')
        assert created_branch_name.endswith('my_title_v2')
        assert result == CREATED_BRANCH_NAME

    def test_create_pr_branch_prints_info_message_when_title_characters_are_stripped(self, send_review_cmd, mock_repo, mock_get_git_config_email):
        """_create_pr_branch must print an info message when non-alphanumeric characters are stripped from the title."""
        with patch('{}.ui_functions.print_info_msg'.format(SEND_REVIEW_OPEN_SOURCE_MODULE)) as mock_print:
            send_review_cmd._create_pr_branch(MagicMock(), mock_repo, PR_TITLE_WITH_SPECIAL_CHARS)

        mock_print.assert_called_once()

    def test_get_changed_file_list_returns_a_path_and_b_path_from_each_diff_entry(self, get_changed_file_list):
        """get_changed_file_list must return a set containing every a_path and b_path in the diff."""
        diff = [
            SimpleNamespace(a_path=CHANGED_FILE_A_PATH, b_path=CHANGED_FILE_B_PATH),
            SimpleNamespace(a_path=CHANGED_FILE_UNCHANGED_PATH, b_path=CHANGED_FILE_UNCHANGED_PATH),
        ]

        result = get_changed_file_list(diff)

        assert result == {CHANGED_FILE_A_PATH, CHANGED_FILE_B_PATH, CHANGED_FILE_UNCHANGED_PATH}

    def test_get_changed_file_list_returns_empty_set_for_empty_diff(self, get_changed_file_list):
        """get_changed_file_list must return an empty set when the diff contains no entries."""
        result = get_changed_file_list([])

        assert result == set()

    def test_with_repo_reference_and_detached_head_raises_exception(self, modified_repo_class):
        """ModifiedRepo must raise EdkrepoInvalidParametersException when the matched repo has a detached HEAD."""
        manifest_repo = self._make_manifest_repo(root=REPO_REFERENCE, remote_name=OTHER_REMOTE_NAME)
        manifest = self._make_manifest([manifest_repo])
        mock_git_repo = MagicMock()
        mock_git_repo.head.is_detached = True

        with patch(PATCH_REPO, return_value=mock_git_repo):
            with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException):
                modified_repo_class(manifest, WORKSPACE_PATH, REPO_REFERENCE)

    def test_with_repo_reference_not_found_raises_exception(self, modified_repo_class):
        """ModifiedRepo must raise EdkrepoInvalidParametersException when no manifest repo matches repo_reference."""
        manifest_repo = self._make_manifest_repo(root='unrelated_root', remote_name='unrelated_remote')
        manifest = self._make_manifest([manifest_repo])

        with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException):
            modified_repo_class(manifest, WORKSPACE_PATH, REPO_REFERENCE)

    def test_without_repo_reference_and_patch_set_raises_exception(self, modified_repo_class):
        """ModifiedRepo must raise EdkrepoInvalidParametersException when a repo source has a patch_set configured."""
        _, manifest, mock_git_repo = self._make_single_repo_manifest_with_git(patch_set=True)

        with patch(PATCH_REPO, return_value=mock_git_repo):
            with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException):
                modified_repo_class(manifest, WORKSPACE_PATH)

    def test_without_repo_reference_and_no_commits_ahead_raises_no_local_branches_exception(self, modified_repo_class):
        """ModifiedRepo must raise EdkrepoInvalidParametersException when no repo has commits ahead of its target branch."""
        _, manifest, mock_git_repo = self._make_single_repo_manifest_with_git()

        with patch(PATCH_REPO, return_value=mock_git_repo), \
             patch(PATCH_GET_COMMITS_AHEAD, return_value=[]):
            with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException):
                modified_repo_class(manifest, WORKSPACE_PATH)

    def test_without_repo_reference_and_multiple_modified_repos_raises_exception(self, modified_repo_class):
        """ModifiedRepo must raise EdkrepoInvalidParametersException when more than one repo has commits ahead."""
        manifest_repo_1 = self._make_manifest_repo(root='repo_one', remote_name=ORIGIN_REMOTE_NAME)
        manifest_repo_2 = self._make_manifest_repo(root='repo_two', remote_name=ORIGIN_REMOTE_NAME)
        manifest = self._make_manifest([manifest_repo_1, manifest_repo_2])
        mock_git_repo = MagicMock()
        mock_git_repo.head.is_detached = False

        with patch(PATCH_REPO, return_value=mock_git_repo), \
             patch(PATCH_GET_COMMITS_AHEAD, return_value=[FAKE_COMMIT]):
            with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException):
                modified_repo_class(manifest, WORKSPACE_PATH)

    def test_without_repo_reference_and_single_modified_repo_sets_manifest_and_git(self, modified_repo_class):
        """ModifiedRepo must set manifest and git from the single repo source that has commits ahead."""
        manifest_repo, manifest, mock_git_repo = self._make_single_repo_manifest_with_git()

        with patch(PATCH_REPO, return_value=mock_git_repo), \
             patch(PATCH_GET_COMMITS_AHEAD, return_value=[FAKE_COMMIT]):
            modified_repo = modified_repo_class(manifest, WORKSPACE_PATH)

        assert modified_repo.manifest is manifest_repo
        assert modified_repo.git is mock_git_repo

    def test_run_command_creates_modified_repo_with_workspace_and_manifest(self, send_review_cmd, mock_args, mock_config,
                                                                           mock_modified_repo_class,
                                                                           mock_get_workspace_manifest,
                                                                           mock_get_review_type):
        """run_command must build ModifiedRepo from the workspace manifest, workspace path, and requested repository."""
        self._run_and_expect_warning(send_review_cmd, mock_args, mock_config)

        mock_modified_repo_class.assert_called_once_with(
            mock_get_workspace_manifest.return_value, FAKE_WORKSPACE_PATH, mock_args.repository,
        )

    def test_run_command_calls_get_review_type_with_manifest_and_repo(self, send_review_cmd, mock_args, mock_config,
                                                                      mock_get_review_type, mock_get_workspace_manifest,
                                                                      mock_modified_repo_class):
        """run_command must resolve the review type from the workspace manifest and the modified repository."""
        self._run_and_expect_warning(send_review_cmd, mock_args, mock_config)

        mock_get_review_type.assert_called_once_with(
            mock_get_workspace_manifest.return_value, mock_modified_repo_class.return_value,
        )

    @pytest.mark.parametrize('match_attr', [
        pytest.param(MATCH_BY_ROOT, id='matches_by_root'),
        pytest.param(MATCH_BY_REMOTE_NAME, id='matches_by_remote_name'),
    ])
    def test_with_repo_reference_matching_repo_sets_manifest_and_git(self, modified_repo_class, match_attr):
        """ModifiedRepo must set manifest and git from the manifest repo matching repo_reference by root or remote name."""
        manifest_repo = self._make_manifest_repo(
            root=REPO_REFERENCE if match_attr == MATCH_BY_ROOT else REPO_ROOT,
            remote_name=REPO_REFERENCE if match_attr == MATCH_BY_REMOTE_NAME else OTHER_REMOTE_NAME,
        )
        manifest = self._make_manifest([manifest_repo])
        mock_git_repo = MagicMock()
        mock_git_repo.head.is_detached = False

        with patch(PATCH_REPO, return_value=mock_git_repo):
            modified_repo = modified_repo_class(manifest, WORKSPACE_PATH, REPO_REFERENCE)

        assert modified_repo.manifest is manifest_repo
        assert modified_repo.git is mock_git_repo


SETTING_USE_REFERENCE = 'use_reference'
SETTING_USE_DISSOCIATE = 'use_dissociate'

FAKE_REFERENCE_REPO_URL = 'https://example.com/repo.git'
FAKE_REFERENCE_REPO_PATH = '/local/ref/path'
FAKE_MANIFEST_REPO = 'fake_manifest_repo'
FAKE_MANIFEST_REPO_PATH = '/fake/manifest/repo'
FAKE_GLOBAL_MANIFEST_PATH = '/fake/manifest/TestProject.xml'
CLONE_MANIFEST_DIR = 'repo'
DEFAULT_COMBO = 'TestCombo'
MATCHED_COMBO = 'MyCombo'
UNMATCHED_COMBO = 'NoSuchCombo'
DUPLICATE_REPO_ROOT = 'dup_repo'
WORKSPACE_ENTRY = 'file.txt'
MANIFEST_NOT_FOUND_MSG = 'not found'
COMBO_NO_MATCH_MSG = 'no match'


class BaseTestCloneCommand(BaseCommandTest):

    @pytest.fixture
    def clone_cmd(self):
        """Return a fresh CloneCommand instance from the module under test."""
        command_mod = importlib.import_module(self.__class__.command_module)
        return command_mod.CloneCommand()

    @pytest.fixture
    def mock_args(self):
        """Return a mock args namespace with all clone arguments set to safe defaults."""
        args = MagicMock()
        args.Workspace = 'C:\\fake\\workspace'
        args.ProjectNameOrManifestFile = 'TestProject'
        args.Combination = None
        args.source_manifest_repo = None
        args.skip_submodule = False
        args.verbose = False
        args.sparse = False
        args.nosparse = False
        args.performance = False
        args.reference_if_able = False
        args.no_reference_if_able = False
        args.dissociate = False
        args.no_dissociate = False
        return args

    @pytest.fixture(autouse=True)
    def mock_pull_all_manifest_repos(self):
        """Patch manifest_repos_maintenance.pull_all_manifest_repos in the module under test; always active."""
        with patch('{}.manifest_repos_maintenance.pull_all_manifest_repos'.format(self.__class__.command_module)) as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def mock_get_subst_drive_dict(self):
        """Patch pathfix.get_subst_drive_dict returning an empty map; always active."""
        with patch('{}.pathfix.get_subst_drive_dict'.format(self.__class__.command_module), return_value={}) as mock:
            yield mock

    @pytest.fixture
    def run_command_setup(self, mock_config):
        """Activate all external patches for a successful run; yields key mocks as a namespace."""
        mock_config[USER_CFG_FILE_KEY].reference_repos_enabled_by_default = False
        mock_config[USER_CFG_FILE_KEY].reference_repos_dissociate_by_default = False
        manifest = MagicMock()
        manifest.is_pin_file.return_value = False
        manifest.general_config.default_combo = DEFAULT_COMBO
        manifest.get_repo_sources.return_value = []
        manifest.repo_hooks = []
        manifest.sparse_settings = None
        with patch('{}.os.path.isdir'.format(self.__class__.command_module), return_value=False), \
             patch('{}.os.makedirs'.format(self.__class__.command_module)), \
             patch('{}.manifest_repos_maintenance.list_available_manifest_repos'.format(self.__class__.command_module),
                   return_value=([FAKE_MANIFEST_REPO], [], [])), \
             patch('{}.manifest_repos_maintenance.find_project_in_all_indices'.format(self.__class__.command_module),
                   return_value=(FAKE_MANIFEST_REPO, MagicMock(), FAKE_GLOBAL_MANIFEST_PATH)), \
             patch('{}.manifest_repos_maintenance.get_manifest_repo_path'.format(self.__class__.command_module),
                   return_value=FAKE_MANIFEST_REPO_PATH), \
             patch('{}.common_repo_functions.verify_single_manifest'.format(self.__class__.command_module)), \
             patch('{}.common_repo_functions.update_editor_config'.format(self.__class__.command_module)), \
             patch('{}.shutil.copy'.format(self.__class__.command_module)), \
             patch('{}.edk_manifest.ManifestXml'.format(self.__class__.command_module), return_value=manifest), \
             patch('{}.manifest_repos_maintenance.find_source_manifest_repo'.format(self.__class__.command_module)), \
             patch('{}.common_repo_functions.write_included_config'.format(self.__class__.command_module), return_value={}), \
             patch('{}.common_repo_functions.write_conditional_include'.format(self.__class__.command_module)), \
             patch('{}.common_repo_functions.clone_repos'.format(self.__class__.command_module),
                   return_value=[]) as mock_clone_repos, \
             patch('{}.submodule_utils.maintain_submodules'.format(self.__class__.command_module)) as mock_maintain_submodules:
            yield SimpleNamespace(clone_repos=mock_clone_repos, maintain_submodules=mock_maintain_submodules, manifest=manifest)

    @staticmethod
    def _configure_reference_defaults(mock_config, enabled_by_default, dissociate_by_default):
        """Configure reference repository defaults on the user config file mock."""
        mock_config[USER_CFG_FILE_KEY].reference_repos_enabled_by_default = enabled_by_default
        mock_config[USER_CFG_FILE_KEY].reference_repos_dissociate_by_default = dissociate_by_default

    def test_init_creates_instance_without_error(self, clone_cmd):
        """CloneCommand() must construct successfully with no positional arguments."""
        assert clone_cmd is not None

    def test_get_metadata_includes_expected_argument_names(self, clone_cmd):
        """get_metadata must include exactly the expected set of argument names."""
        metadata = clone_cmd.get_metadata()
        arg_names = {arg[METADATA_KEY_NAME] for arg in metadata[METADATA_KEY_ARGUMENTS]}

        assert arg_names == {
            'Workspace', 'ProjectNameOrManifestFile', 'Combination', 'sparse', 'nosparse',
            'treeless', 'blobless', 'full', 'single-branch', 'no-tags', 'reference-if-able',
            'no-reference-if-able', 'dissociate', 'no-dissociate', 'skip-submodule', 'source-manifest-repo',
        }

    def test_resolve_reference_settings_uses_config_defaults(self, clone_cmd, mock_args, mock_config):
        """_resolve_reference_settings must return the defaults from config when no override flags are set."""
        self._configure_reference_defaults(mock_config, False, True)

        use_reference, use_dissociate, _ = clone_cmd._resolve_reference_settings(mock_args, mock_config)

        assert use_reference is False
        assert use_dissociate is True

    def test_resolve_reference_settings_builds_path_map_when_reference_enabled(self, clone_cmd, mock_args, mock_config):
        """When use_reference is True, _resolve_reference_settings must build reference_path_map from config."""
        self._configure_reference_defaults(mock_config, True, True)
        mock_config[USER_CFG_FILE_KEY].reference_repos_enabled_for = ['my_repo']
        mock_config[USER_CFG_FILE_KEY].get_reference_repo_url.return_value = FAKE_REFERENCE_REPO_URL
        mock_config[USER_CFG_FILE_KEY].get_reference_repo_path.return_value = FAKE_REFERENCE_REPO_PATH

        _, _, reference_path_map = clone_cmd._resolve_reference_settings(mock_args, mock_config)

        assert reference_path_map == {FAKE_REFERENCE_REPO_URL: FAKE_REFERENCE_REPO_PATH}

    def test_run_command_raises_when_workspace_is_not_empty(self, clone_cmd, mock_args, mock_config):
        """When the workspace directory exists and contains files, EdkrepoInvalidParametersException must be raised."""
        with patch('{}.os.path.isdir'.format(self.__class__.command_module), return_value=True), \
             patch('{}.os.listdir'.format(self.__class__.command_module), return_value=[WORKSPACE_ENTRY]):
            with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException):
                clone_cmd.run_command(mock_args, mock_config)

    def test_run_command_wraps_manifest_not_found_as_invalid_parameters(self, clone_cmd, mock_args, mock_config):
        """EdkrepoManifestNotFoundException from project lookup must become EdkrepoInvalidParametersException."""
        with patch('{}.os.path.isdir'.format(self.__class__.command_module), return_value=False), \
             patch('{}.os.makedirs'.format(self.__class__.command_module)), \
             patch('{}.manifest_repos_maintenance.list_available_manifest_repos'.format(self.__class__.command_module),
                   return_value=([], [], [])), \
             patch('{}.manifest_repos_maintenance.find_project_in_all_indices'.format(self.__class__.command_module),
                   side_effect=edkrepo_exception.EdkrepoManifestNotFoundException(MANIFEST_NOT_FOUND_MSG)):
            with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException):
                clone_cmd.run_command(mock_args, mock_config)

    def test_run_command_skips_submodules_when_flag_set(self, clone_cmd, mock_args, mock_config, run_command_setup):
        """maintain_submodules must not be called when skip_submodule is True."""
        mock_args.skip_submodule = True

        clone_cmd.run_command(mock_args, mock_config)

        run_command_setup.maintain_submodules.assert_not_called()

    def test_run_command_writes_matched_combo_when_combination_specified(self, clone_cmd, mock_args, mock_config, run_command_setup):
        """run_command must resolve args.Combination to a manifest combo name and write it as current."""
        mock_args.Combination = MATCHED_COMBO

        with patch('{}.common_repo_functions.combinations_in_manifest'.format(self.__class__.command_module)), \
             patch('{}.workspace_maintenance.case_insensitive_single_match'.format(self.__class__.command_module),
                   return_value=MATCHED_COMBO):
            clone_cmd.run_command(mock_args, mock_config)

        run_command_setup.manifest.write_current_combo.assert_called_once_with(MATCHED_COMBO)

    def test_run_command_raises_when_combination_does_not_match_manifest(self, clone_cmd, mock_args, mock_config, run_command_setup):
        """run_command must raise EdkrepoInvalidParametersException and clean up when the requested combination cannot be matched."""
        mock_args.Combination = UNMATCHED_COMBO
        expected_manifest_dir = os.path.join(os.path.abspath(mock_args.Workspace), CLONE_MANIFEST_DIR)

        with patch('{}.common_repo_functions.combinations_in_manifest'.format(self.__class__.command_module)), \
             patch('{}.workspace_maintenance.case_insensitive_single_match'.format(self.__class__.command_module),
                   side_effect=Exception(COMBO_NO_MATCH_MSG)), \
             patch('{}.shutil.rmtree'.format(self.__class__.command_module)) as mock_rmtree:
            with pytest.raises(edkrepo_exception.EdkrepoInvalidParametersException):
                clone_cmd.run_command(mock_args, mock_config)

        mock_rmtree.assert_called_once_with(expected_manifest_dir)

    def test_run_command_uses_current_combo_for_pin_file(self, clone_cmd, mock_args, mock_config, run_command_setup):
        """run_command must use the pin file's current_combo without writing a new current combo."""
        run_command_setup.manifest.is_pin_file.return_value = True
        run_command_setup.manifest.general_config.current_combo = 'PinCombo'

        clone_cmd.run_command(mock_args, mock_config)

        run_command_setup.manifest.write_current_combo.assert_not_called()
        run_command_setup.manifest.get_repo_sources.assert_called_once_with('PinCombo')

    def test_run_command_raises_when_local_roots_duplicated(self, clone_cmd, mock_args, mock_config, run_command_setup):
        """run_command must raise EdkrepoManifestInvalidException and clean up when repo sources share a local root."""
        dup_source_a = MagicMock()
        dup_source_a.root = DUPLICATE_REPO_ROOT
        dup_source_b = MagicMock()
        dup_source_b.root = DUPLICATE_REPO_ROOT
        run_command_setup.manifest.get_repo_sources.return_value = [dup_source_a, dup_source_b]
        expected_manifest_dir = os.path.join(os.path.abspath(mock_args.Workspace), CLONE_MANIFEST_DIR)

        with patch('{}.shutil.rmtree'.format(self.__class__.command_module)) as mock_rmtree:
            with pytest.raises(edkrepo_exception.EdkrepoManifestInvalidException):
                clone_cmd.run_command(mock_args, mock_config)

        mock_rmtree.assert_called_once_with(expected_manifest_dir)

    @pytest.mark.parametrize('enabled_by_default, dissociate_by_default, flag_name, setting, expected', [
        pytest.param(False, True, 'reference_if_able', SETTING_USE_REFERENCE, True, id='reference_if_able_enables'),
        pytest.param(True, True, 'no_reference_if_able', SETTING_USE_REFERENCE, False, id='no_reference_if_able_disables'),
        pytest.param(True, False, 'dissociate', SETTING_USE_DISSOCIATE, True, id='dissociate_enables'),
        pytest.param(True, True, 'no_dissociate', SETTING_USE_DISSOCIATE, False, id='no_dissociate_disables'),
    ])
    def test_resolve_reference_settings_flag_overrides_setting(self, clone_cmd, mock_args, mock_config, enabled_by_default, dissociate_by_default, flag_name, setting, expected):
        """A reference/dissociate flag on args must override the corresponding config default."""
        self._configure_reference_defaults(mock_config, enabled_by_default, dissociate_by_default)
        setattr(mock_args, flag_name, True)

        use_reference, use_dissociate, _ = clone_cmd._resolve_reference_settings(mock_args, mock_config)
        actual = use_reference if setting == SETTING_USE_REFERENCE else use_dissociate

        assert actual is expected

    @pytest.mark.parametrize('mock_attr', [
        pytest.param('clone_repos', id='clone_repos_called'),
        pytest.param('maintain_submodules', id='maintain_submodules_called'),
    ])
    def test_run_command_invokes_expected_action(self, clone_cmd, mock_args, mock_config, run_command_setup, mock_attr):
        """run_command must invoke the expected internal action during a successful clone."""
        clone_cmd.run_command(mock_args, mock_config)

        getattr(run_command_setup, mock_attr).assert_called_once()

    @pytest.mark.parametrize('sparse_settings_present, sparse_by_default, args_sparse, args_nosparse, expect_called', [
        pytest.param(False, False, True, False, False, id='no_sparse_settings_forces_disabled'),
        pytest.param(True, True, False, False, True, id='sparse_by_default_enables'),
        pytest.param(True, True, False, True, False, id='nosparse_overrides_sparse_by_default'),
        pytest.param(True, False, True, False, True, id='args_sparse_enables_when_settings_present'),
    ])
    def test_run_command_sparse_checkout_enable_logic(self, clone_cmd, mock_args, mock_config, run_command_setup, sparse_settings_present, sparse_by_default, args_sparse, args_nosparse, expect_called):
        """run_command must call sparse_checkout only when the resolved use_sparse flag is True."""
        mock_args.sparse = args_sparse
        mock_args.nosparse = args_nosparse
        if sparse_settings_present:
            sparse_settings = MagicMock()
            sparse_settings.sparse_by_default = sparse_by_default
            run_command_setup.manifest.sparse_settings = sparse_settings
        else:
            run_command_setup.manifest.sparse_settings = None

        with patch('{}.common_repo_functions.sparse_checkout'.format(self.__class__.command_module)) as mock_sparse_checkout:
            clone_cmd.run_command(mock_args, mock_config)

        if expect_called:
            mock_sparse_checkout.assert_called_once()
        else:
            mock_sparse_checkout.assert_not_called()
