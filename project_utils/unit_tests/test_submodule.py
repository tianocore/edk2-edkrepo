from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

import git
import pytest

from project_utils import submodule


@pytest.mark.parametrize('mode', ['all', 'recursive', 'selected'])
@pytest.mark.parametrize('failures', [0, 1, 2, 3])
def test_update_retries_only_update_command(mode, failures):
    repo = MagicMock()
    selected = [SimpleNamespace(path='dependency', recursive=True)] if mode == 'selected' else None
    sync_cmd = ['git', 'submodule', 'sync']
    update_cmd = ['git', 'submodule', 'update', '--init']
    if mode != 'all':
        sync_cmd.append('--recursive')
        update_cmd.append('--recursive')
    if selected:
        sync_cmd.extend(['--', 'dependency'])
        update_cmd.extend(['--', 'dependency'])
    else:
        update_cmd.append('--filter=tree:0')
    failure = git.GitCommandError(update_cmd, 128, stderr='Could not connect to proxy')
    success = (0, 'Submodule checked out', '')
    repo.git.execute.side_effect = [
        '' if selected else 'tree:0', (0, '', ''),
    ] + [failure] * failures + [success]

    with patch.object(submodule.time, 'sleep') as sleep, \
         patch.object(submodule.ui_functions, 'print_info_msg') as info, \
         patch.object(submodule.ui_functions, 'display_git_output') as display:
        if failures == 3:
            with pytest.raises(git.GitCommandError) as raised:
                submodule._update(repo, selected, verbose=True, recursive=mode == 'recursive')
            assert raised.value is failure
            assert display.call_args_list == [call((0, '', ''), True)]
        else:
            submodule._update(repo, selected, verbose=True, recursive=mode == 'recursive')
            assert display.call_args_list == [call((0, '', ''), True), call(success, True)]

        attempts = min(failures + 1, 3)
        assert repo.git.execute.call_args_list == [
            call(['git', 'config', 'remote.origin.partialclonefilter']),
            call(sync_cmd, with_extended_output=True, with_stdout=True),
        ] + [call(update_cmd, with_extended_output=True, with_stdout=True)] * attempts
        assert sleep.call_args_list == [call(5)] * (attempts - 1)
        assert info.call_count == attempts - 1


@pytest.mark.parametrize('failure', [KeyboardInterrupt(), OSError('process could not start')])
def test_update_retry_preserves_other_exceptions(failure):
    repo = MagicMock()
    repo.git.execute.side_effect = failure
    cmd = ['git', 'submodule', 'update', '--init']

    with patch.object(submodule.time, 'sleep') as sleep:
        with pytest.raises(type(failure)) as raised:
            submodule._update_with_retry(repo, cmd)
        assert raised.value is failure
        repo.git.execute.assert_called_once_with(cmd, with_extended_output=True, with_stdout=True)
        sleep.assert_not_called()


def test_update_does_not_retry_sync_failure():
    repo = MagicMock()
    failure = git.GitCommandError(['git', 'submodule', 'sync'], 128, stderr='sync failed')
    repo.git.execute.side_effect = ['tree:0', failure]

    with patch.object(submodule.time, 'sleep') as sleep:
        with pytest.raises(git.GitCommandError) as raised:
            submodule._update(repo)
        assert raised.value is failure
        assert repo.git.execute.call_count == 2
        sleep.assert_not_called()