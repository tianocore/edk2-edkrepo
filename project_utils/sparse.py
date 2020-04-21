#!/usr/bin/env python3
#
## @file
# sparse.py
#
# Copyright (c) 2017- 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
import os
import sys
import argparse
import copy
import collections
import git

if __name__ == "__main__":
    #
    # Add one directory level up from script directory to be in the python path.  This is to
    # allow for easier imports.
    #
    tool_root = os.path.dirname(sys.argv[0])
    tool_root = os.path.abspath(tool_root)
    tool_root = os.path.split(tool_root)[0]
    sys.path.append(tool_root)

# Attempt to import common code modules.
try:
    import project_utils.inftools as inftools
    import project_utils.fileutils as fileutils
except Exception as e:
    print('Import Failed: {0}'.format(e))
    sys.exit(2)

# Generic container to hold lists of used and unused objects.
class UsedUnused:
    def __init__(self):
        self.used = []
        self.unused = []

#
# Library specific data container
#
class LibData:
    def __init__(self, lib_class, inf_path, full_inf_path=None, override_inf_path=None):
        self.__lib_class = lib_class
        self.__inf_path = inf_path
        self.__override_inf_path = override_inf_path

    @property
    def lib_class(self):
        return self.__lib_class

    @property
    def inf_path(self):
        return self.__inf_path

    @property
    def override_inf_path(self):
        return self.__override_inf_path

#
# File location data
#
class FileData:
    def __init__(self, workspace, package, remaining):
        self.__workspace = workspace
        self.__package = package
        self.__remaining = remaining

    @property
    def workspace(self):
        return self.__workspace

    @property
    def package(self):
        return self.__package

    @property
    def package_path(self):
        return os.path.join(self.__workspace, self.__package)

    @property
    def full_path(self):
        return os.path.join(self.__workspace, self.__package, self.__remaining)

#
# Class for collecting file usage information
# Interfaces return True/Object on success and False/None on failure.
#
class FileUsage:
    def __init__(self):
        self.__dsc_info = inftools.BaseInf()
        self.__fdf_info = inftools.BaseInf()
        self.__lib_list = []
        self.__built_module_list = []
        self.__fw_binaries = []
        self.__workspace_list = []

    def init_data(self, dsc_file_lines, fdf_file_lines, workspace_list):
        #
        # Set the workspace list
        #
        self.__workspace_list = copy.deepcopy(workspace_list)

        #
        # Get the file lines without any comments for simpler processing
        #
        self.__dsc_info.init_data(inftools.clean_lines(dsc_file_lines))
        self.__fdf_info.init_data(inftools.clean_lines(fdf_file_lines))

        #
        # Now that we have the file info start filling in some of the other data
        #
        self.__lib_list = self.__find_libs()
        self.__built_module_list = self.__find_built_modules()
        self.__fw_binaries = self.__find_fw_binaries()

    #
    # Returns a list of packages that are used by the project.  In the case of multiple workspaces
    # only the first instance of the package will be listed.
    #
    def get_used_packages(self):
        #
        # Get a complete list of all items in the build
        #
        full_list = []
        lib_info = self.get_used_libs()
        full_list.extend(lib_info.used)
        full_list.extend(lib_info.unused)
        full_list.extend(self.get_built_modules())
        full_list.extend(self.get_fw_binaries())

        #
        # Skip modules that still have macros in the path.
        #
        tmp_list = []
        for rel_path in full_list:
            rel_path = rel_path.replace('\\', '/')
            macro_index = rel_path.find('$(')
            if macro_index >= 0:
                continue
            tmp_list.append(rel_path)
        full_list = tmp_list

        # Check dependencies for each driver on other packages.
        full_list = self.__check_dependencies(full_list)
        full_list.sort()

        #
        # Now loop through all of the these entries and extract the information that we
        # want.  This includes the workspace, package and remaining file path.
        #
        file_data_list = []
        for rel_path in full_list:
            try:
                full_path = fileutils.find_in_workspace(rel_path, self.__workspace_list)
            except:
                continue
            rel_path = fileutils.find_best_rel_path(full_path, self.__workspace_list)
            workspace = full_path.replace(os.path.normpath(rel_path), '').rstrip(os.path.sep)
            tmp_str = rel_path.replace('\\', '/')
            split_list = tmp_str.split('/', 1)
            if len(split_list) == 2:
                package = split_list[0]
                remaining_path = split_list[1]
            else:
                package = ''
                remaining_path = split_list[0]
            file_data_list.append(FileData(workspace, package, remaining_path))

        #
        # Now process the full list to create a list of packages being used by the
        # current platform and remove duplicates.
        #
        ret_list = []
        tmp_package_list = []
        for tmp_obj in file_data_list:
            if not tmp_obj.package_path in tmp_package_list:
                tmp_package_list.append(tmp_obj.package_path)
                ret_list.append(tmp_obj)

        return ret_list

    #
    # Returns a UsedUnused class populated with INF paths
    #
    def get_used_libs(self):
        ret_obj = UsedUnused()
        build_infs = []
        used_lib_names = []
        lib_class_names = []

        #
        # Process list and remove duplicate entries
        #
        for lib_obj in self.__lib_list:
            if not lib_obj.inf_path in build_infs:
                build_infs.append(lib_obj.inf_path)
            if not lib_obj.lib_class in lib_class_names:
                lib_class_names.append(lib_obj.lib_class)

        #
        # Now that we have a list of libraries we can append the list of modules that we are
        # building and check all of the library usage.
        #
        # NOTE: This only checks libs based on what INFs request.  It does not look at what
        #       was actually used by the platform.
        #
        build_infs.extend(self.__built_module_list)
        for inf in build_infs:
            #
            # Attempt to read the file and access the lines
            #
            try:
                inf_lines = fileutils.read_lines(inf, self.__workspace_list)
            except:
                continue
            inf_info = inftools.BaseInf()
            inf_info.init_data(inf_lines)

            #
            # Find all the LibraryClasses sections in the INF and add them to the list of
            # libraries used by the platform
            #
            for section in inf_info.get_sections():
                if section.startswith('LibraryClasses'):
                    for line in inf_info.get_section_lines(section):
                        tmp_line = inftools.clean_line(line)
                        if tmp_line == '':
                            continue
                        if not tmp_line in used_lib_names:
                            used_lib_names.append(tmp_line)

        #
        # Now determine only the libraries that need to be in the DSC
        # NOTE: NULL Libs are always assumed to be used...
        #
        for lib_obj in self.__lib_list:
            if lib_obj.lib_class in used_lib_names or lib_obj.lib_class == 'NULL':
                if not lib_obj.inf_path in ret_obj.used:
                    ret_obj.used.append(lib_obj.inf_path)
            else:
                if not lib_obj.inf_path in ret_obj.unused:
                    ret_obj.unused.append(lib_obj.inf_path)

        ret_obj.used.sort()
        ret_obj.unused.sort()

        return ret_obj

    #
    # Returns a list of modules that are built as part fo the project
    #
    def get_built_modules(self):
        ret_list = []

        #
        # Process modules removing any duplicates
        #
        for module in self.__built_module_list:
            if not module in ret_list:
                ret_list.append(module)
        ret_list.sort()

        return ret_list

    #
    # Returns a list of binaries included in the firmware image
    #
    def get_fw_binaries(self):
        ret_list = []

        #
        # Process entries removing any duplicates
        #
        for module in self.__fw_binaries:
            if not module in ret_list:
                ret_list.append(module)
        ret_list.sort()

        return ret_list

    #
    # Find all of the libraries used in the platform
    #
    def __find_libs(self):
        ret_list = []

        #
        # Determine all the sections that may include libraries
        #
        lib_sections = []
        comp_sections = []
        for section in self.__dsc_info.get_sections():
            if section.startswith('LibraryClasses'):
                lib_sections.append(section)
            elif section.startswith('Components'):
                comp_sections.append(section)

        #
        # Get all the libraries used by the platform
        #
        for section in lib_sections:
            for line in self.__dsc_info.get_section_lines(section):
                #
                # Pull the line apart to get the library name and path
                #
                if line.find('|') >= 0 and not line.startswith('!'):
                    lib_name, lib_path = line.split('|')
                    lib_name = lib_name.strip()
                    lib_path = lib_path.strip()
                    try:
                        full_lib_path = fileutils.find_in_workspace(lib_path, self.__workspace_list)
                    except:
                        continue

                    #
                    # Create new object with information and then add it to the list
                    #
                    ret_list.append(LibData(lib_name, lib_path, full_lib_path))

        #
        # Now go through all the overrides and see if any library overrides exist for drivers
        #
        for section in comp_sections:
            in_override = False
            in_lib_section = False
            override_name = None
            for line in self.__dsc_info.get_section_lines(section):
                #
                # Check to see if we are entering or leaving an override
                #
                if line.endswith('{'):
                    in_override = True
                    override_name = line.rstrip('{').strip()
                    continue
                elif line.endswith('}'):
                    in_override = False
                    in_lib_section = False
                    override_name = None
                    continue

                #
                # Check to see if this is a library override section
                #
                if line.startswith('<LibraryClasses'):
                    in_lib_section = True
                    continue
                elif line.startswith('<'):
                    in_lib_section = False
                    continue

                #
                # Log any libraries that we may find
                #
                if in_override and in_lib_section and not line.startswith('!'):
                    if line.find('|') >= 0:
                        lib_name, lib_path = line.split('|')
                        lib_name = lib_name.strip()
                        lib_path = lib_path.strip()
                        try:
                            full_lib_path = fileutils.find_in_workspace(lib_path, self.__workspace_list)
                        except:
                            continue

                        #
                        # Create the lib entry in the dictionary if needed
                        #
                        ret_list.append(LibData(lib_name, lib_path, full_lib_path, override_name))

        return ret_list

    #
    # Finds all modules that are being built by the project
    #
    def __find_built_modules(self):
        ret_list = []

        #
        # Get the component sections
        #
        comp_sections = []
        for section in self.__dsc_info.get_sections():
            if section.startswith('Components'):
                comp_sections.append(section)

        #
        # Find all the module entries
        #
        for section in comp_sections:
            in_override = False
            for line in self.__dsc_info.get_section_lines(section):
                #
                # Check to see if this is the start of an override section
                #
                if line.endswith('{'):
                    in_override = True
                    ret_list.append(line.rstrip('{').strip())
                    continue
                elif line.endswith('}'):
                    in_override = False
                    continue

                #
                # Check to see if we should log this line
                #
                if not in_override and not line.startswith('!'):
                    ret_list.append(line)

        return ret_list

    #
    # Checks driver dependencies on other packages by returning an updated file list that includes the
    # dependent DEC file entries.
    #
    def __check_dependencies(self, inf_list):
        ret_list = []

        #
        # Loop through all the entries
        #
        for inf_file in inf_list:
            #
            # Add INF to the list
            #
            if not inf_file in ret_list:
                ret_list.append(inf_file)

            #
            # Check to see if this is an INF
            #
            if not os.path.splitext(inf_file)[1].lower() == '.inf':
                continue

            #
            # Open the INF and find if any package dependencies exist
            #
            try:
                inf_lines = fileutils.read_lines(inf_file, self.__workspace_list)
            except:
                continue
            inf_info = inftools.BaseInf()
            inf_info.init_data(inftools.clean_lines(inf_lines))

            #
            # Determine the root path for the INF
            #
            inf_root_path = os.path.dirname(inf_file)

            #
            # Add dependencies to the list
            #
            for section in inf_info.get_sections():
                if section.startswith('Packages'):
                    for line in inf_info.get_section_lines(section):
                        if not line in ret_list:
                            ret_list.append(line)
                elif section.startswith('Binaries'):
                    for line in inf_info.get_section_lines(section):
                        tmp_line = line.split('|')[1].strip()
                        rel_path = os.path.normpath(os.path.join(inf_root_path, tmp_line))
                        if not rel_path in ret_list:
                            ret_list.append(rel_path)
                elif section.startswith('Sources'):
                    for line in inf_info.get_section_lines(section):
                        tmp_line = line.split('|')[0].strip()
                        rel_path = os.path.normpath(os.path.join(inf_root_path, tmp_line))
                        if not rel_path in ret_list:
                            ret_list.append(rel_path)

        return ret_list

    #
    # Finds all of the binaries used in the firmware images
    #
    def __find_fw_binaries(self):
        ret_list = []

        #
        # Search all the sections to find all the items in the firmware image.
        #
        for section in self.__fdf_info.get_sections():
            for line in self.__fdf_info.get_section_lines(section):
                #
                # Split the line into its component parts and clean the entries up
                #
                line_parts = []
                for part in line.split():
                    line_parts.append(part.strip())
                if len(line_parts) < 2:
                    continue

                #
                # Check all the lines to see if they are INF or SECTION statements.  These are
                # the easy to process entries.
                #
                if line_parts[0] == 'INF':
                    ret_list.append(line_parts[-1])
                    continue
                elif line_parts[0] == 'SECTION':
                    if line_parts[1] == 'PE32':
                        ret_list.append(line_parts[-1])
                    if line_parts[1] == 'RAW':
                        ret_list.append(line_parts[-1])
                    continue

                #
                # TODO:
                # Now we need to do more difficult processing if needed
                #

        return ret_list

class BuildInfo:
    def __init__(self, workspace_list=[]):
        self.__build_file_data = collections.defaultdict(dict)
        self.__build_data_init_done = False
        self.__prune_data = collections.defaultdict(set)
        self.__workspace_list = workspace_list
        self.__define_data = None
        self.__use_comments = False
        self.__sparse_file_name = os.path.join('.git', 'info', 'sparse-checkout')
        self.__sparse_all_files = ['/*']

    def find_sparse_checkout(self):
        ret_list = []
        for root in self.__workspace_list:
            try:
                repo = git.Repo(root)
            except:
                continue
            with repo.config_reader() as cr:
                if cr.has_option(section='core', option='sparsecheckout'):
                    if cr.get_value(section='core', option='sparsecheckout'):
                        ret_list.append(root)
        return ret_list

    def reset_sparse_checkout(self, disable=False):
        for root in self.__workspace_list:
            out_file = os.path.join(root, self.__sparse_file_name)
            if os.path.exists(out_file):
                try:
                    repo = git.Repo(root)
                except:
                    continue
                print('- {}'.format(root))
                fileutils.write_lines(out_file, self.__sparse_all_files)
                repo.head.reset(working_tree=True)
                if disable:
                    with repo.config_writer() as cw:
                        cw.set_value(section='core', option='sparsecheckout', value='false')

    def sparse_checkout(self, root=None, always_include=[], always_exclude=[]):
        """Performs a sparse checkout operation on a single repository"""
        local_prune_data = []
        for item in always_include:
            local_prune_data.append('/{}'.format(item))
        for item in always_exclude:
            local_prune_data.append('!/{}'.format(item))
        try:
            repo = git.Repo(root)
        except:
            return
        print('- {}'.format(root))
        out_file = os.path.join(root, self.__sparse_file_name)
        fileutils.write_lines(out_file, local_prune_data)
        with repo.config_writer() as cw:
            cw.set_value(section='core', option='sparsecheckout', value='true')
        repo.head.reset(working_tree=True)

def process_sparse_checkout(workspace_root, repo_list, current_combo, manifest):
    # Determine if sparse checkout support is enabled in the manifest.
    sparse_settings = manifest.sparse_settings
    if sparse_settings is None:
        raise RuntimeError('Sparse checkout not enabled in manifest file.')
    sparse_list = [x for x in repo_list if x.sparse]
    workspace_list = [workspace_root]
    workspace_list.extend([os.path.join(workspace_root, os.path.normpath(x.root)) for x in repo_list])

    # Filter sparse data entries that apply to the current combo or all combos
    # Build list in three steps (all, repo, combo) to make sure the priority is correct
    sparse_data = []
    sparse_data.extend([x for x in manifest.sparse_data if x.remote_name is None and x.combination is None])
    sparse_data.extend([x for x in manifest.sparse_data if x.remote_name is not None and x.combination is None])
    sparse_data.extend([x for x in manifest.sparse_data if x.remote_name is not None and x.combination == current_combo])

    # Create object that processes build information.
    build_info = BuildInfo(workspace_list)

    # Apply sparse checkout data to each repository
    for repo in sparse_list:
        always_exclude = []
        always_include = []
        for item in sparse_data:
            if item.remote_name is None or item.remote_name == repo.remote_name:
                always_include.extend(item.always_include)
                always_exclude.extend(item.always_exclude)
        root = os.path.join(workspace_root, os.path.normpath(repo.root))
        build_info.sparse_checkout(root, always_include, always_exclude)

#
# Check to see if the application is being run as a script or is just an import
#
if __name__ == "__main__":
    #
    # Program Information
    #
    __title__ = 'Sparse Checkout'
    __version__ = '0.03.00'
    __copyright__ = 'Copyright (c) 2017 - 2020, Intel Corporation. All rights reserved.'

    #
    # Processes command line arguments
    #
    def parse_arguments():
        parser = argparse.ArgumentParser()
        parser.add_argument('-r', action='store_true', dest='restore_full', default=False,
                help='Restores a full checkout of source and disables sparse checkout support.')
        args = parser.parse_args()

        return args

    #
    # Finds a common path prefix and verify that it exists as a directory.
    #
    def find_common_path(PathList):
        TmpPath = os.path.commonprefix(PathList)
        if not os.path.isdir(TmpPath):
            return None
        return TmpPath

    #
    # Reads in a set of project files (DSC and FDF) and uses them to determine the components that
    # are currently in use.  The tool can then be used to reduce the number of components found
    # in the tree.
    #
    def Main():
        # Display signon.
        print('{0} Version: {1}'.format(__title__, __version__))
        print(__copyright__)
        print('')

        # Parse command line arguments.
        args = parse_arguments()

        # Look for the manifest file for this project and workspace root.
        # Manifest location <workspace>/repo/Manifest.xml
        rel_manifest_path = os.path.join('repo', 'Manifest.xml')
        manifest_path = None
        work_root = os.getcwd()
        new_root = ''
        while True:
            manifest_path = os.path.join(work_root, os.path.normpath(rel_manifest_path))
            if os.path.isfile(manifest_path):
                break
            new_root = os.path.split(work_root)[0]
            if work_root == new_root:
                raise RuntimeError('Unable to determine project root.')
            work_root = new_root

        # Open manifest file using manifest parser.
        try:
            import edkrepo_manifest_parser.edk_manifest as edk_manifest
        except:
            raise RuntimeError('Unable to import manifest parser.')
        try:
            proj_xml = edk_manifest.ManifestXml(manifest_path)
        except:
            raise RuntimeError('Unable to process manifest: {}'.format(manifest_path))

        # Determine the current combination and get a list of repositories in the workspace.
        # This will be used to generate the workspace list.
        current_combo = proj_xml.general_config.current_combo
        repo_list = proj_xml.get_repo_sources(current_combo)

        # Revert to a non-sparse checkout...
        print('Resetting sparse checkout state...')
        workspace_list = [work_root]
        workspace_list.extend([os.path.join(work_root, os.path.normpath(x.root)) for x in repo_list])
        build_info = BuildInfo(workspace_list)
        build_info.reset_sparse_checkout()
        if args.restore_full:
            return 0

        # Process sparse checkout.
        print('Performing sparse checkout...')
        try:
            process_sparse_checkout(work_root, repo_list, current_combo, proj_xml)
        except RuntimeError as msg:
            print(msg)

        return 0

    ret_val = 255
    try:
        ret_val = Main()
    except KeyboardInterrupt:
        print('Caught keyboard interrupt...')
        ret_val = 0
    except Exception as e:
        print('Exiting: {}'.format(e))
    sys.exit(ret_val)
