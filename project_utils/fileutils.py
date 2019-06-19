#!/usr/bin/env python3
#
## @file
# fileutils.py
#
# Copyright (c) 2017- 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
import os
import copy

#
# Reads a file and returns the lines as a list
#
def read_lines(file_path, workspaces=None, project_path=None):
    global _file_utils_error_string

    #
    # Check to see if the file path is a complete path
    #
    tmp_file_name = os.path.normpath(file_path)
    if not os.path.isfile(tmp_file_name):
        #
        # Not a valid path so see if we can complete it using the workspace path
        #
        if isinstance(workspaces, list):
            tmp_file_name = find_in_workspace(tmp_file_name, workspaces, project_path)
        else:
            raise RuntimeError('Unable to find file: {0}'.format(tmp_file_name))

    #
    # Attempt to open the file
    #
    try:
        tmp_file = open(tmp_file_name, 'r')
    except:
        raise RuntimeError('Unable to open: {0}'.format(tmp_file_name))

    #
    # File open so read and then close
    #
    tmp_file_data = tmp_file.readlines()
    tmp_file.close()

    return tmp_file_data

#
# Writes the lines to a file.
#
def write_lines(file_path, file_lines):
    global _file_utils_error_string

    #
    # Clean up file lines by removing any trailing white space and making sure
    # it has a \n at the end of the line.
    #
    clean_lines = []
    for line in file_lines:
        clean_lines.append(line.rstrip() + '\n')

    #
    # Attempt to open/create the file
    #
    tmp_file_path = os.path.normpath(file_path)
    try:
        tmp_file = open(tmp_file_path, 'w')
    except:
        raise RuntimeError('Unable to open: {0}'.format(file_path))

    #
    # Now write the contents of the file
    #
    status = True
    try:
        tmp_file.writelines(clean_lines)
    except:
        status = False
        raise RuntimeError('Failed to write to: {0}'.format(tmp_file_path))
    finally:
        tmp_file.close()

    return status

#
# Finds a file in the list of workspaces
#
def find_in_workspace(file_path, workspace_list, project_path=None):
    global _file_utils_error_string

    full_path = None
    full_path_list = []
    full_path_list.extend(workspace_list)
    if not project_path is None:
        full_path_list.append(project_path)

    #
    # Check each workspace to see if the file can be found.
    #
    for path in full_path_list:
        path = os.path.join(path, file_path)
        path = os.path.normpath(path)
        if os.path.exists(path):
            full_path = path
            break

    #
    # If the file was not found report a warning for now and continue.
    #
    if full_path is None:
        raise RuntimeError('Not found in workspaces: {0}'.format(file_path))

    return full_path

def find_all_in_workspace(file_path, workspace_list, project_path=None):
    ret_list = []
    full_path_list = []
    full_path_list.extend(workspace_list)
    if project_path is not None:
        full_path_list.append(project_path)

    for w_path in full_path_list:
        try:
            ret_list.append(find_in_workspace(file_path, [w_path]))
        except:
            continue

    return ret_list

def find_best_rel_path(file_path, workspace_list, project_path=None):
    global _file_utils_error_string

    rel_path = file_path
    full_path_list = []
    full_path_list.extend(workspace_list)
    if project_path is not None:
        full_path_list.append(project_path)

    best_root_list = [x for x in full_path_list if file_path.startswith(x)][-1:]
    if len(best_root_list) != 1:
        raise RuntimeError('Not found in workspaces: {0}'.format(file_path))

    best_root = best_root_list[0]
    if not best_root.endswith(os.path.sep):
        best_root += os.path.sep
    return os.path.normpath(rel_path.replace(best_root, ''))

#
# Get the files directory.
#
def get_file_dir(file_path):
    ret_val = None

    ret_val = os.path.normpath(file_path)
    ret_val = os.path.abspath(ret_val)
    ret_val = os.path.dirname(ret_val)

    return ret_val

#
# Handles multiple workspace by creating an ordered list of
# workspaces to process.
#
def split_workspace(workspaces):
    global _file_utils_error_string

    tmp_list = []
    ret_list = []

    #
    # Split the workspace on the ';' for Windows
    #
    tmp_list = workspaces.split(';')

    #
    # Remove any workspaces that do not exist
    #
    for path in tmp_list:
        try:
            tmp_path = os.path.abspath(path)
            tmp_path = os.path.normpath(tmp_path)
            if os.path.exists(tmp_path):
                ret_list.append(tmp_path)
        except:
            raise RuntimeError('Faild to process workspace: {0}'.format(path))

    return ret_list

