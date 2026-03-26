#!/usr/bin/env python3
#
## @file
# repo_case_conflict_solver.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import unicodedata
import tempfile

import edkrepo.common.ui_functions as ui_functions
from edkrepo.common.humble import CASE_CONFLICT_SCRUB, CASE_CONFLICT_FOUND
from edkrepo.common.humble import CASE_CONFLICT_NONE, CASE_CONFLICT_DELETED
from edkrepo.common.humble import CASE_CONFLICT_DELETING_REF, CASE_CONFLICT_DELETE_FAILED
from edkrepo.common.humble import STALE_REFLOG_SCRUB, STALE_REFLOG_DELETING_FILE, STALE_REFLOG_DELETING_DIR
from edkrepo.config.tool_config import CI_INDEX_FILE_NAME
from edkrepo.common.workspace_maintenance.manifest_repos_maintenance import list_available_manifest_repos
from edkrepo.config.config_factory import GlobalConfig, GlobalUserConfig
from edkrepo_manifest_parser.edk_manifest import CiIndexXml, ManifestXml

_str_cache = {}
def _case_insensitive_equal(str1, str2):
    # Note: This function is performance sensitive. It has been written to
    # minimize case conversions and enumerations
    str1_casefold = _str_cache.get(str1)
    if str1_casefold is None:
        str1_casefold = unicodedata.normalize("NFKD", str1.casefold())
        _str_cache[str1] = str1_casefold
    str2_casefold = _str_cache.get(str2)
    if str2_casefold is None:
        str2_casefold = unicodedata.normalize("NFKD", str2.casefold())
        _str_cache[str2] = str2_casefold
    return str1_casefold == str2_casefold

def _normalize_url(url):
    # Strip trailing slashes, optional .git suffix, then casefold so that URL
    # comparisons are insensitive to both case and common formatting differences.
    url = url.rstrip('/')
    if url.lower().endswith('.git'):
        url = url[:-4]
    return url.casefold()

def get_known_good_refs(repo):
    """
    Build a frozenset of known-good remote-qualified ref names by scanning
    the locally-cached global manifest repositories.  A ref is "known good"
    when it is referenced by at least one active or archived project combination
    in any manifest that is associated with a remote of *repo*.

    The returned strings have the form ``<remote_name>/<branch_or_tag>``,
    mirroring the path components stored under ``.git/refs/remotes/``.

    No network access is performed; if no manifest cache exists or the edkrepo
    configuration is unavailable, an empty frozenset is returned silently so
    the caller can fall back to the uppercase heuristic.

    Args:
        repo: GitPython Repo object

    Returns:
        frozenset of known-good ref path strings (e.g. ``{'origin/MyBranch'}``)
    """
    try:
        cfg_file = GlobalConfig()
        user_cfg_file = GlobalUserConfig()
    except Exception:
        return frozenset()

    try:
        cfg_manifest_repos, user_cfg_manifest_repos, _ = list_available_manifest_repos(
            cfg_file, user_cfg_file)
    except Exception:
        return frozenset()

    # Build a mapping from normalized URL → set of remote names for this repo.
    url_to_remotes = {}
    for remote in repo.remotes:
        for url in remote.urls:
            norm = _normalize_url(url)
            url_to_remotes.setdefault(norm, set()).add(remote.name)

    if not url_to_remotes:
        return frozenset()

    known_refs = set()
    for manifest_repo, cfg_obj in (
        [(r, cfg_file) for r in cfg_manifest_repos] +
        [(r, user_cfg_file) for r in user_cfg_manifest_repos]):

        manifest_dir = cfg_obj.manifest_repo_abs_path(manifest_repo)
        if not os.path.isdir(manifest_dir):
            continue

        try:
            ci_index_xml = CiIndexXml(os.path.join(manifest_dir, CI_INDEX_FILE_NAME))
        except Exception:
            continue

        all_projects = list(ci_index_xml.project_list) + list(ci_index_xml.archived_project_list)
        for project in all_projects:
            try:
                xml_file = ci_index_xml.get_project_xml(project)
                manifest = ManifestXml(
                    os.path.normpath(os.path.join(manifest_dir, xml_file)))
            except Exception:
                continue

            all_combos = list(manifest.combinations) + list(manifest.archived_combinations)
            for combo in all_combos:
                try:
                    sources = manifest.get_repo_sources(combo.name)
                except Exception:
                    continue
                for source in sources:
                    norm = _normalize_url(source.remote_url)
                    remote_names = url_to_remotes.get(norm)
                    if remote_names is None:
                        continue
                    for remote_name in remote_names:
                        if source.branch:
                            known_refs.add(remote_name + '/' + source.branch)
                        if source.tag:
                            known_refs.add(remote_name + '/' + source.tag)

    return frozenset(known_refs)

def check_for_case_conflicts(ref_list, known_good_refs=frozenset()):
    conflicting_refs = []
    path_tree = [{}, []]

    def _combine_ref_paths(parent_path, child_path):
        if parent_path == '':
            return child_path
        else:
            return '/'.join((parent_path, child_path))

    def _find_node(sub_tree, path):
        current_path = path.split('/')
        remaining_path = '/'.join(current_path[1:])
        current_path = current_path[0]
        if current_path in sub_tree[0]:
            current_tree = sub_tree[0][current_path]
            if remaining_path == '':
                return current_tree
            else:
                return _find_node(current_tree, remaining_path)
        raise ValueError('{} not in tree'.format(path))

    def _add_conflicts_from_sub_tree(sub_tree, parent_path, force=False):
        for ref in sub_tree[1]:
            if force or any(char.isupper() for char in ref):
                if len(_find_node(path_tree, parent_path)[0]) == 0:
                    conflicting_refs.append((ref, parent_path))
                else:
                    conflicting_refs.append((ref, '{}/*'.format(parent_path)))
        for key in sub_tree[0]:
            _add_conflicts_from_sub_tree(sub_tree[0][key], parent_path, force)

    def _is_known_good(parent_path, component):
        full = _combine_ref_paths(parent_path, component)
        return any(r == full or r.startswith(full + '/') for r in known_good_refs)

    def _check_for_conflicts(sub_tree, parent_path=''):
        already_added = []
        for path in sub_tree[0]:
            for path2 in sub_tree[0]:
                if path != path2 and _case_insensitive_equal(path, path2):
                    if path in already_added:
                        continue
                    # Prefer manifest-defined ref names regardless of case
                    if known_good_refs:
                        path_good  = _is_known_good(parent_path, path)
                        path2_good = _is_known_good(parent_path, path2)
                        if path_good and not path2_good:
                            # path2 is bad; path is the manifest-defined ref.
                            already_added.append(path2)
                            _add_conflicts_from_sub_tree(
                                sub_tree[0][path2],
                                _combine_ref_paths(parent_path, path),
                                force=True)
                            continue
                        elif path2_good and not path_good:
                            # path is bad; path2 is the manifest-defined ref.
                            # Mark path2 handled so it is not re-processed when
                            # it becomes the outer loop variable.
                            already_added.append(path2)
                            _add_conflicts_from_sub_tree(
                                sub_tree[0][path],
                                _combine_ref_paths(parent_path, path2),
                                force=True)
                            continue
                    # The ref names are not manifest-defined ref names, or both
                    # refs are known-good. In both cases, the lowercase variant
                    # is preferred.
                    bad_path = None
                    if any(char.isupper() for char in path):
                        bad_path = path
                    if any(char.isupper() for char in path2):
                        if bad_path is None:
                            bad_path = path2
                        else:
                            bad_path = None
                    if bad_path is not None:
                        if bad_path == path:
                            already_added.append(path2)
                            _add_conflicts_from_sub_tree(sub_tree[0][path], _combine_ref_paths(parent_path, path2))
                        else:
                            # bad_path == path2: path is good, path2 is bad.
                            # This pair will be resolved when path2 becomes the
                            # outer loop variable.
                            pass
                    else:
                        _add_conflicts_from_sub_tree(sub_tree[0][path], _combine_ref_paths(parent_path, path))
            _check_for_conflicts(sub_tree[0][path], _combine_ref_paths(parent_path, path))

    for ref in ref_list:
        paths = ref.split('/')
        current_tree = path_tree
        for path in paths:
            if path not in current_tree[0]:
                current_tree[0][path] = [{}, []]
            current_tree = current_tree[0][path]
        current_tree[1].append(ref)

    _check_for_conflicts(path_tree)
    return conflicting_refs

def _get_local_remote_refs(git_dir):
    """Get all remote refs from .git/refs/remotes/ directory structure."""
    refs = []
    remotes_dir = os.path.join(git_dir, 'refs', 'remotes')

    if not os.path.exists(remotes_dir):
        return refs

    for root, _, files in os.walk(remotes_dir):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, remotes_dir)
            ref_name = 'refs/remotes/' + rel_path.replace('\\', '/')
            refs.append(ref_name)

    return refs

def _get_packed_remote_refs(git_dir):
    """Get all remote refs from .git/packed-refs file."""
    refs = []
    packed_refs_file = os.path.join(git_dir, 'packed-refs')

    if not os.path.exists(packed_refs_file):
        return refs

    with open(packed_refs_file, 'r', encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            if line.startswith('^'):
                continue
            parts = line.split()
            if len(parts) >= 2:
                ref_name = parts[1]
                if ref_name.startswith('refs/remotes/'):
                    refs.append(ref_name)

    return refs

def _delete_ref_from_filesystem(git_dir, ref_name):
    """Delete a ref from .git/refs/remotes/ directory."""
    if not ref_name.startswith('refs/remotes/'):
        return False

    rel_path = ref_name[len('refs/remotes/'):]
    file_path = os.path.join(git_dir, 'refs', 'remotes', rel_path.replace('/', os.sep))

    if os.path.exists(file_path):
        try:
            os.remove(file_path)

            # Clean up empty directories
            parent_dir = os.path.dirname(file_path)
            remotes_dir = os.path.join(git_dir, 'refs', 'remotes')
            while parent_dir != remotes_dir:
                try:
                    if os.path.isdir(parent_dir) and not os.listdir(parent_dir):
                        os.rmdir(parent_dir)
                        parent_dir = os.path.dirname(parent_dir)
                    else:
                        break
                except OSError:
                    break

            return True
        except OSError as e:
            ui_functions.print_warning_msg(CASE_CONFLICT_DELETE_FAILED.format(ref_name, e), header=False)
            return False

    return False

def _scrub_packed_refs(git_dir, refs_to_delete):
    """Remove specified refs from .git/packed-refs file.

    Returns:
        frozenset of ref names that were removed from packed-refs.
    """
    packed_refs_file = os.path.join(git_dir, 'packed-refs')

    if not os.path.exists(packed_refs_file):
        return frozenset()

    with open(packed_refs_file, 'r', encoding='utf-8') as fh:
        lines = fh.readlines()

    deleted_refs = set()
    new_lines = []
    skip_next_peeled = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('^'):
            if not skip_next_peeled:
                new_lines.append(line)
            else:
                skip_next_peeled = False
            continue

        if stripped.startswith('#') or not stripped:
            new_lines.append(line)
            continue

        parts = stripped.split()
        if len(parts) >= 2:
            ref_name = parts[1]
            if ref_name in refs_to_delete:
                deleted_refs.add(ref_name)
                skip_next_peeled = True
                continue

        new_lines.append(line)
        skip_next_peeled = False

    if deleted_refs:
        # Write atomically: write to a temp file beside packed-refs, then
        # rename over the original. This prevents corruption if the process
        # is interrupted between the open() and the final write.
        tmp_fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(packed_refs_file))
        try:
            with os.fdopen(tmp_fd, 'wb') as fh:
                for line in new_lines:
                    fh.write(line.rstrip('\r\n').encode('utf-8'))
                    fh.write(b'\n')
            os.replace(tmp_path, packed_refs_file)  # atomic on POSIX; best-effort on Windows
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    return frozenset(deleted_refs)

def scrub_repo_case_conflicts(repo, verbose=False):
    """
    Scrub case-conflicting remote refs from a git repository.

    Removes "bad" refs (those with uppercase letters) that conflict with
    lowercase refs, allowing git operations to work properly on
    case-insensitive filesystems (Windows, macOS). Only refs/remotes/*
    refs are touched to prevent data loss.

    Args:
        repo: GitPython Repo object
        verbose: If True, print verbose detail about refs found

    Returns:
        Number of conflicting refs deleted
    """
    ui_functions.print_info_msg(CASE_CONFLICT_SCRUB, header=False)

    git_dir = repo.git_dir

    # Get all remote refs from both filesystem and packed-refs
    filesystem_refs = _get_local_remote_refs(git_dir)
    packed_refs = _get_packed_remote_refs(git_dir)
    all_refs = sorted(set(filesystem_refs + packed_refs))

    # Strip 'refs/remotes/' prefix for conflict checking
    ref_names_only = []
    for ref in all_refs:
        if ref.startswith('refs/remotes/'):
            ref_names_only.append(ref[len('refs/remotes/'):])

    known_good_refs = get_known_good_refs(repo)
    conflicting_refs = check_for_case_conflicts(sorted(ref_names_only), known_good_refs)

    if not conflicting_refs:
        if verbose:
            ui_functions.print_info_msg(CASE_CONFLICT_NONE, header=False)
        return 0

    ui_functions.print_info_msg(CASE_CONFLICT_FOUND.format(len(conflicting_refs)), header=False)
    if verbose:
        for ref, conflict_location in conflicting_refs:
            ui_functions.print_info_msg(CASE_CONFLICT_DELETING_REF.format(ref, conflict_location), header=False)

    # Build set of full ref names to delete
    refs_to_delete = set()
    for ref, _ in conflicting_refs:
        refs_to_delete.add('refs/remotes/' + ref)

    # Delete from filesystem and packed-refs
    deleted_from_fs = set()
    for ref in refs_to_delete:
        if _delete_ref_from_filesystem(git_dir, ref):
            deleted_from_fs.add(ref)
    deleted_from_packed = _scrub_packed_refs(git_dir, refs_to_delete)
    deleted = len(deleted_from_fs | deleted_from_packed)

    ui_functions.print_info_msg(CASE_CONFLICT_DELETED.format(deleted), header=False)
    return deleted

def scrub_stale_remote_reflogs(repo, verbose=False):
    """
    Delete reflog files under .git/logs/refs/remotes/ that have no corresponding
    live ref in .git/refs/remotes/ or packed-refs.

    On case-insensitive filesystems (Windows, macOS) a stale reflog file left
    behind after a prune can block git from creating a new hierarchical ref
    whose path reuses the stale file's name as a directory component, producing
    the error "unable to create directory for '.git/logs/refs/remotes/...': No
    such file or directory".  Deleting the orphaned log file unblocks the
    subsequent fetch.

    Args:
        repo:    GitPython Repo object
        verbose: If True, print each file and directory as it is deleted

    Returns:
        Number of stale reflog files deleted
    """
    ui_functions.print_info_msg(STALE_REFLOG_SCRUB, header=False)

    git_dir = repo.git_dir
    logs_remotes_dir = os.path.join(git_dir, 'logs', 'refs', 'remotes')
    if not os.path.exists(logs_remotes_dir):
        return 0

    # Build a lower-cased set of live ref paths relative to refs/remotes/ so
    # that comparison is case-insensitive on case-insensitive filesystems.
    all_refs = sorted(_get_local_remote_refs(git_dir) + _get_packed_remote_refs(git_dir))
    live_refs = set()
    for ref in all_refs:
        if ref.startswith('refs/remotes/'):
            live_refs.add(ref[len('refs/remotes/'):].replace('/', os.sep).lower())

    deleted = 0
    # Walk bottom-up so directories can be pruned after their files are removed.
    for root, dirs, files in os.walk(logs_remotes_dir, topdown=False):
        for filename in files:
            log_file = os.path.join(root, filename)
            rel_path = os.path.relpath(log_file, logs_remotes_dir).lower()
            if rel_path not in live_refs:
                try:
                    os.remove(log_file)
                    deleted += 1
                    if verbose:
                        ui_functions.print_info_msg(STALE_REFLOG_DELETING_FILE.format(log_file), header=False)
                except OSError:
                    pass
        for dirname in dirs:
            dir_path = os.path.join(root, dirname)
            try:
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    if verbose:
                        ui_functions.print_info_msg(STALE_REFLOG_DELETING_DIR.format(dir_path), header=False)
            except OSError:
                pass

    return deleted
