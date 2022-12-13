#!/usr/bin/env python3
#
## @file
# edk_manifest.py
#
# Copyright (c) 2017 - 2020, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

# Standard imports
import xml.etree.ElementTree as ET
from collections import namedtuple
import os
import copy
import json

# 3rd party imports
#   None planned at this time


#
# All the namedtuple data structures that consumers of this module will need.
#
ProjectInfo = namedtuple('ProjectInfo', ['codename', 'description', 'dev_leads', 'reviewers', 'org', 'short_name'])
GeneralConfig = namedtuple('GeneralConfig', ['default_combo', 'current_combo', 'pin_path', 'source_manifest_repo'])
RemoteRepo = namedtuple('RemoteRepo', ['name', 'url'])
RepoHook = namedtuple('RepoHook', ['source', 'dest_path', 'dest_file', 'remote_url'])
Combination = namedtuple('Combination', ['name', 'description', 'venv_enable'])
RepoSource = namedtuple('RepoSource', ['root', 'remote_name', 'remote_url', 'branch', 'commit', 'sparse',
                                       'enable_submodule', 'tag', 'venv_cfg', 'patch_set'])
PatchSet = namedtuple('PatchSet', ['remote', 'name', 'parent_sha', 'fetch_branch'])
PatchOperation = namedtuple('PatchOperation',['type', 'file', 'sha', 'source_remote', 'source_branch'])
SparseSettings = namedtuple('SparseSettings', ['sparse_by_default'])
SparseData = namedtuple('SparseData', ['combination', 'remote_name', 'always_include', 'always_exclude'])

FolderToFolderMapping = namedtuple('FolderToFolderMapping', ['project1', 'project2', 'remote_name', 'folders'])
FolderToFolderMappingFolder = namedtuple('FolderToFolderMappingFolder', ['project1_folder', 'project2_folder',
                                                                         'excludes'])
FolderToFolderMappingFolderExclude = namedtuple('FolderToFolderMappingFolderExclude', ['path'])

SubmoduleAlternateRemote = namedtuple('SubmoduleAlternateRemote', ['remote_name', 'original_url', 'alternate_url'])
SubmoduleInitPath = namedtuple('SubmoduleInitPath', ['remote_name', 'combo', 'recursive', 'path'])

REQUIRED_ATTRIB_ERROR_MSG = "Required attribute malformed in <{}>: {}"
NO_ASSOCIATED_REMOTE = 'There are no remotes associated with the ClientGitHook entry:\nsource:{} destination:{}' \
                       '\nThis hook will not be installed, updated or deleted.\n'
NO_REMOTE_EXISTS_WITH_NAME = 'There are no remotes with the name: {} listed in the manifest file.'
PIN_COMBO_ERROR = "Pin \"{}\" Pin did not have a single <Combination> tag."
DUPLICATE_TAG_ERROR = "Duplicate <{}> tag not allowed: '{}' (Note: check <include>'s"
COMBO_INVALIDINPUT_ERROR = "Invalid input: {} not found in 'combinations' property"
COMBO_UNKNOWN_ERROR = "Could not find a Combination named '{}' in '{}'"
ATTRIBUTE_MISSING_ERROR = "Missing required attribute. Must specify either 'branch' or 'commit' for each <Source>."
INVALID_COMBO_DEFINITION_ERROR = "Can not specify branch or commit or tag along with patchSet"
GENERAL_CONFIG_MISSING_ERROR = "Unable to locate <GeneralConfig>"
SOURCELIST_EMPTY_ERROR = "Invalid input: empty values in source list"
INVALID_PROJECTNAME_ERROR = "Invalid input: {} not found in CiIndexXml"
UNSUPPORTED_TYPE_ERROR = "{} is not a supported xml type: {}"
INVALID_XML_ERROR = "{} is not a valid xml file ({})"
PATCHSET_UNKNOWN_ERROR = "Could not find a PatchSet named '{}' in '{}'"
REMOTE_DIFFERENT_ERROR = "The remote for Patchset {}/{} is different from {}/{}"
NO_PATCHSET_IN_COMBO = "The Combination: {} does not have any Patchsets."
NO_PATCHSET_EXISTS = "The Patchset: {} does not exist"
INVALID_PATCHSET_NAME_ERROR = "The Patchset cannot be named: {}. Please rename the Patchset"

class BaseXmlHelper():
    def __init__(self, fileref, xml_types):
        self._fileref = fileref
        try:
            file_ext = os.path.splitext(fileref)[1]
            if file_ext == '.xml':
                self._tree = ET.ElementTree(file=fileref)  # fileref can be a filename or filestream
            elif file_ext == '.json':
                self._tree = self._json_to_xml(fileref)
            else:
                raise TypeError(INVALID_XML_ERROR.format(fileref, et_error))
        except Exception as et_error:
            raise TypeError(INVALID_XML_ERROR.format(fileref, et_error))

        self._xml_type = self._tree.getroot().tag
        if self._xml_type not in xml_types:
            raise TypeError(UNSUPPORTED_TYPE_ERROR.format(fileref, self._xml_type))

    def _json_to_xml(self, fileref):
        with open(fileref, 'r') as f:
            json_in = json.load(f)

        root = ET.Element('placeholder')
        tree = ET.ElementTree(root)

        self._build_etree_node(json_in, root)
        tree._setroot(root[0])

        self._pretty_format(tree.getroot())
        return tree


    def _build_etree_node(self, current_dict, parent):
        '''
        Build ElementTree node as a subelement of parent node.
        '''
        node_tag = current_dict['name']

        # attribs
        if 'attrib' in current_dict.keys():
            node_attribs = current_dict['attrib']
        else:
            node_attribs = {}

        # construct this subelement
        node = ET.SubElement(parent, node_tag, attrib=node_attribs)

        # text
        if 'text' in current_dict.keys():
            node.text = current_dict['text']

        # tail
        if 'tail' in current_dict.keys():
            node.tail = current_dict['tail']

        # children
        if 'children' in current_dict.keys():
            for child_dict in current_dict['children']:
                # append child to this node
                self._build_etree_node(child_dict, node)


    def _pretty_format(self, current, parent=None, index=-1, depth=0):
        for i, node in enumerate(current):
            self._pretty_format(node, current, i, depth + 1)
        if parent is not None:
            if index == 0:
                parent.text = '\n' + ('  ' * depth)

#
#  This class will parse and the Index XML file and provide the data to the caller
#
class CiIndexXml(BaseXmlHelper):
    def __init__(self, fileref):
        super().__init__(fileref, 'ProjectList')
        self._projects = {}
        for element in self._tree.iter(tag='Project'):
            proj = _Project(element)
            # Todo: add check for unique
            self._projects[proj.name] = proj

    @property
    def project_list(self):
        proj_names = []
        for proj in self._projects.values():
            if proj.archived is False:
                proj_names.append(proj.name)
        return proj_names

    @property
    def archived_project_list(self):
        proj_names = []
        for proj in self._projects.values():
            if proj.archived is True:
                proj_names.append(proj.name)
        return proj_names

    def get_project_xml(self, project_name):
        if project_name in self._projects:
            return self._projects[project_name].xmlPath
        else:
            raise ValueError(INVALID_PROJECTNAME_ERROR.format(project_name))


class _Project():
    def __init__(self, element):
        try:
            self.name = element.attrib['name']
            self.xmlPath = element.attrib['xmlPath']
        except KeyError as k:
            raise KeyError(REQUIRED_ATTRIB_ERROR_MSG.format(k, element.tag))
        try:
            # if the archived attrib is not explicitly set to true, then assume false
            self.archived = (element.attrib['archived'].lower() == 'true')
        except Exception:
            self.archived = False


#
#  This class will parse and the manifest XML file and populate the named
#  tuples defined above to provide abstracted access to the manifest data
#
class ManifestXml(BaseXmlHelper):
    def __init__(self, fileref):
        # Most of the attributes of this class are intended to be private as they are used for
        # internally gathering and storing the manifest data. As such, all access to them should be
        # done through the provided methods to ensure future compatibility if the xml schema changes
        super().__init__(fileref, ['Pin', 'Manifest'])
        self._project_info = None
        self._general_config = None
        self._remotes = {}                    # dict of _Remote objs, with Remote.name as key
        self._client_hook_list = []
        self._combinations = {}               # dict of _Combination objs, with Combination.name as key
        self._combo_sources = {}              # dict of _RepoSource obj lists, with Combination.name as key
        self._dsc_list = []
        self._sparse_settings = None          # A single instance of platform sparse checkout settings
        self._sparse_data = []                # List of SparseData objects
        self._commit_templates = {}           # dict of commit message templates with the remote name as the key
        self._folder_to_folder_mappings = []  # List of FolderToFolderMapping objects
        self._submodule_alternate_remotes = []
        self._submodule_init_list = []
        self._patch_sets = {}
        self._patch_set_operations = {}

        #
        # Append include XML's to the Manifest etree before parsing
        #
        tree_root = self._tree.getroot()
        incl_path = os.path.dirname(os.path.abspath(fileref))
        for include_elem in self._tree.iter(tag='Include'):
            incl_file = os.path.join(incl_path, include_elem.attrib['xml'])
            try:
                include_tree = ET.ElementTree(file=incl_file)
            except Exception:
                raise TypeError("{} is not a valid xml file".format(incl_file))
            for elem in include_tree.iterfind('*'):
                if elem.tag != 'ProjectInfo' and elem.tag != 'GeneralConfig':
                    tree_root.append(elem)
            # remove include tags after added to etree to prevent feedback issues
            tree_root.remove(include_elem)

        #
        # parse <RemoteList> tags
        #
        for subroot in self._tree.iter(tag='RemoteList'):
            for element in subroot.iter(tag='Remote'):
                self._add_unique_item(_RemoteRepo(element), self._remotes, element.tag)

        #
        # parse <ProjectInfo> tags
        #
        subroot = self._tree.find('ProjectInfo')
        self._project_info = _ProjectInfo(subroot)

        #
        # parse <GeneralConfig> tags
        #
        subroot = self._tree.find('GeneralConfig')
        self._general_config = _GeneralConfig(subroot)

        #
        # parse <ClientGitHookList> tags
        # requires RemoteList to be parsed first
        #
        for subroot in self._tree.iter(tag='ClientGitHookList'):
            for element in subroot.iter(tag='ClientGitHook'):
                self._client_hook_list.append(_RepoHook(element, self._remotes))

        #
        # Parse <SubmoduleAlternateRemotes>
        # Requires RemoteList to be parsed first
        #
        for subroot in self._tree.iter(tag='SubmoduleAlternateRemotes'):
            for element in subroot.iter(tag='SubmoduleAlternateRemote'):
                self._submodule_alternate_remotes.append(_SubmoduleAlternateRemote(element, self._remotes))

        #
        # Determine submodule initialization paths
        #
        for subroot in self._tree.iter(tag='SelectiveSubmoduleInitList'):
            for element in subroot.iter(tag='Submodule'):
                self._submodule_init_list.append(_SubmoduleInitEntry(element))

        #
        # parse <CombinationList> tags
        # requires RemoteList to be parsed first
        #
        if self._xml_type == 'Pin':
            combos_list = self._tree.findall('CombinationList')
            if len(combos_list) == 1:
                combos = self._tree.find('CombinationList').findall('Combination')
            else:
                combos = self._tree.findall('Combination')
            if len(combos) != 1:
                raise KeyError(PIN_COMBO_ERROR.format(fileref))

            # <CombinationList> container tag not required for pin files
            if self._tree.find('CombinationList') is None:
                combolist = ET.SubElement(tree_root, 'CombinationList')
                combolist.append(combos[0])
                tree_root.remove(combos[0])

        for subroot in self._tree.iter(tag='CombinationList'):
            for element in subroot.iter(tag='Combination'):
                combo = _Combination(element)

                # add the combo obj to the combinations and combo_sources dicts
                self._add_combo_source(element, combo)

        if self._xml_type == 'Pin':
            # done with Pin parsing at this point, so exit init
            # remaining tag types are unique to manifest xml (for now...)
            return

        #
        # parse <DscList> tags
        #
        for subroot in self._tree.iter(tag='DscList'):
            for element in subroot.iter(tag='Dsc'):
                self._dsc_list.append(element.text)

        #
        # Process <SparseCheckout> tag
        #
        subroot = self._tree.find('SparseCheckout')
        if subroot is not None:
            try:
                self._sparse_settings = _SparseSettings(subroot.find('SparseSettings'))
            except KeyError as k:
                raise KeyError(REQUIRED_ATTRIB_ERROR_MSG.format(k, subroot.tag))
            for sparse_data in subroot.iter(tag='SparseData'):
                self._sparse_data.append(_SparseData(sparse_data))

        #
        # Process any commit log templates that may exist (optional)
        #
        subroot = self._tree.find('CommitTemplates')
        if subroot is not None:
            for template_element in subroot.iter(tag='Template'):
                try:
                    remote_name = template_element.attrib['remoteName']
                    template_text = template_element.text
                except KeyError as k:
                    raise KeyError(REQUIRED_ATTRIB_ERROR_MSG.format(k, subroot.tag))
                self._commit_templates[remote_name] = template_text

        #
        # Process <FolderToFolderMappingList> tag
        #
        subroot = self._tree.find('FolderToFolderMappingList')
        if subroot is not None:
            for f2f_mapping in subroot.iter(tag='FolderToFolderMapping'):
                self._folder_to_folder_mappings.append(_FolderToFolderMapping(f2f_mapping))

        #
        # Process <PatchSets> tag
        #
        subroot = self._tree.find('PatchSets')
        if subroot is not None:
            for patchset in subroot.iter(tag='PatchSet'):
                if patchset.attrib['name'] == "main" or patchset.attrib['name'] == "master":
                    raise ValueError(INVALID_PATCHSET_NAME_ERROR.format(patchset.attrib['name']))
                self._patch_sets[(patchset.attrib['name'], getattr(_PatchSet(patchset).tuple, "remote"))] =_PatchSet(patchset).tuple
                operations = []
                for subelem in patchset:
                    operations.append(_PatchSetOperations(subelem).tuple)
                self._patch_set_operations[(patchset.attrib['name'], getattr(_PatchSet(patchset).tuple, "remote"))] = operations
        return

    def is_pin_file(self):
        if self._xml_type == 'Pin':
            return True
        else:
            return False

    def add_combo(self, element):
        self._tree.find('CombinationList').append(element)
        combo = _Combination(element)
        self._add_combo_source(element, combo)

    def _add_combo_source(self, subroot, combo):
        # create a list of _RepoSource objs from the <Source> tags in subroot
        # and add it to the __combo_sources dictionary
        self._add_unique_item(combo, self._combinations, subroot.tag)
        temp_sources = []
        for element in subroot.iter(tag='Source'):
            temp_sources.append(_RepoSource(element, self._remotes))
        self._combo_sources[combo.name] = temp_sources

    def _add_unique_item(self, obj, item_dict, tag):
        # add the 'obj' to 'dict', or raise error if it already exists
        if obj.name in item_dict:
            raise KeyError(DUPLICATE_TAG_ERROR.format(tag, obj.name))
        item_dict[obj.name] = obj

    def _tuple_list(self, obj_list):
        tuples = []
        for obj in obj_list:
            tuples.append(obj.tuple)
        return tuples

    #
    # EdkManifestLib properties and methods
    # These will convert the internal classes and attributes into the architecurally
    # defined lists and tuples that the caller is expecting.
    #
    @property
    def project_info(self):
        return self._project_info.tuple

    @property
    def general_config(self):
        return self._general_config.tuple

    @property
    def remotes(self):
        return self._tuple_list(self._remotes.values())

    @property
    def combinations(self):
        return self._tuple_list([x for x in self._combinations.values() if not x.archived])

    @property
    def archived_combinations(self):
        return self._tuple_list([x for x in self._combinations.values() if x.archived])

    def get_repo_sources(self, combo_name):
        if combo_name in self._combo_sources:
            return self._tuple_list(self._combo_sources[combo_name])
        elif combo_name.startswith('Pin:'):
            # If currently checked out onto a pin file reture the sources in the
            # default combo
            return self._tuple_list(self._combo_sources[self.general_config.default_combo])
        else:
            raise ValueError(COMBO_INVALIDINPUT_ERROR.format(combo_name))

    @property
    def repo_hooks(self):
        return self._tuple_list(self._client_hook_list)

    @property
    def dsc_list(self):
        return self._dsc_list

    @property
    def sparse_settings(self):
        if self._sparse_settings:
            return self._sparse_settings.tuple
        return None

    @property
    def sparse_data(self):
        return self._tuple_list(self._sparse_data)

    @property
    def folder_to_folder_mappings(self):
        f2f_tuples = []
        for f2f_mapping in self._folder_to_folder_mappings:
            folders = f2f_mapping.folders
            folder_tuples = []
            for folder in folders:
                f = copy.deepcopy(folder)
                f.excludes = self._tuple_list(folder.excludes)
                folder_tuples.append(f.tuple)
            m = copy.deepcopy(f2f_mapping)
            m.folders = folder_tuples
            f2f_tuples.append(m.tuple)
        return f2f_tuples

    @property
    def current_combo(self):
        return self.general_config.current_combo

    def get_combo_element(self, name):
        combinations = self._tree.find('CombinationList')
        for combo in combinations.iter(tag='Combination'):
            if combo.attrib['name'] == name:
                return copy.deepcopy(combo)
        raise ValueError(COMBO_UNKNOWN_ERROR.format(name, self._fileref))

    @property
    def commit_templates(self):
        return self._commit_templates

    @property
    def submodule_alternate_remotes(self):
        return self._tuple_list(self._submodule_alternate_remotes)

    def get_submodule_alternates_for_remote(self, remote_name):
        alternates = []
        for alternate in self._submodule_alternate_remotes:
            if alternate.remote_name == remote_name:
                alternates.append(alternate.tuple)
        return alternates

    def get_submodule_init_paths(self, remote_name=None, combo=None):
        submodule_list = []
        if remote_name is None and combo is None:
            submodule_list = self._tuple_list(self._submodule_init_list)
        elif remote_name is not None and combo is None:
            submodule_list = self._tuple_list(
                [x for x in self._submodule_init_list if x.remote_name == remote_name])
        elif remote_name is None and combo is not None:
            submodule_list = self._tuple_list(
                [x for x in self._submodule_init_list if x.combo == combo or x.combo is None])
        else:
            submodule_list = self._tuple_list(
                [x for x in self._submodule_init_list
                 if x.remote_name == remote_name and (x.combo == combo or x.combo is None)])
        return submodule_list

    def write_current_combo(self, combo_name, filename=None):
        #
        # Updates the CurrentClonedCombo tag of _tree attribute and writes the entire tree out to the
        # file specified. If no file is given, then the file used to instantiate this object will be used.
        # Note: It will also strip all the comments from the file
        #
        if self._xml_type == 'Pin':
            # raise Warning("This method is not supported for Pin xmls")
            return
        if filename is None:
            filename = self._fileref

        subroot = self._tree.find('GeneralConfig')
        if subroot is None:
            raise KeyError(GENERAL_CONFIG_MISSING_ERROR)

        element = subroot.find('CurrentClonedCombo')
        if element is None:
            element = ET.SubElement(subroot, 'CurrentClonedCombo')
            element.tail = '\n'

        element.attrib['combination'] = combo_name
        self._tree.write(filename)
        self._general_config.curr_combo = combo_name

    def write_source_manifest_repo(self, manifest_repo, filename=None):
        '''
        Writes the name of the source manifest repository to the
        general config sections of the manifest file.
        '''
        if filename is None:
            filename = self._fileref
        subroot = self._tree.find('GeneralConfig')
        if subroot is None:
            raise KeyError(GENERAL_CONFIG_MISSING_ERROR)

        element = subroot.find('SourceManifestRepository')
        if element is None:
            element = ET.SubElement(subroot, 'SourceManifestRepository')
            element.tail = '\n'
        element.attrib['manifest_repo'] = manifest_repo
        self._tree.write(filename)
        self._general_config.source_manifest_repo = manifest_repo

    def write_tree(self, filename=None):
        self._tree.write(filename)

    def _dfs_traverse_etree(self, node):
        '''
        Traverse ElementTree to construct JSON equivalent.
        '''
        current_dict = {}
        current_dict['name'] = node.tag

        # attribs
        if node.attrib:
            current_dict['attrib'] = node.attrib

        # text
        if node.text and (not node.text.isspace()):
            current_dict['text'] = node.text

        # tail
        if node.tail:
            current_dict['tail'] = node.tail

        # dfs recurse
        if list(node):
            current_dict['children'] = [self._dfs_traverse_etree(child) for child in node]

        return current_dict

    def generate_pin_etree(self, description, combo_name, repo_source_list):
        pin_tree = ET.ElementTree(ET.Element('Pin'))
        pin_root = pin_tree.getroot()

        subroot_m = self._tree.find('ProjectInfo')
        pin_root.append(subroot_m)
        project_root = pin_root.find('ProjectInfo')
        for elem in list(project_root):
            if elem.tag != 'CodeName' and elem.tag != 'Description':
                project_root.remove(elem)
        project_root.find('Description').text = description

        subroot_m = self._tree.find('GeneralConfig')
        pin_root.append(subroot_m)
        config_root = pin_root.find('GeneralConfig')
        for elem in list(config_root):
            if elem.tag != 'StitchConfigPath' and elem.tag != 'WitConfigPath' and elem.tag != 'CurrentClonedCombo':
                config_root.remove(elem)

        subroot_m = self._tree.find('BinaryList')
        if subroot_m is not None:
            pin_root.append(subroot_m)

        hook_root = ET.SubElement(pin_root, 'ClientGitHookList')

        submodule_alt_url_root = None
        if self._tree.find('SubmoduleAlternateRemotes'):
            submodule_alt_url_root = ET.SubElement(pin_root, 'SubmoduleAlternateRemotes')

        selective_submodules_root = None
        if self._tree.find('SelectiveSubmoduleInitList'):
            selective_submodules_root = ET.SubElement(pin_root, 'SelectiveSubmoduleInitList')

        remote_root = ET.SubElement(pin_root, 'RemoteList')
        source_root = ET.SubElement(pin_root, 'Combination')
        source_root.attrib['name'] = self._combinations[combo_name].name

        # Add tags for each RepoSource tuple in the list provided
        # Only one of Branch or SHA is required to write PIN and checkout code
        for src_tuple in repo_source_list:
            if (src_tuple.root is None or src_tuple.remote_name is None or src_tuple.remote_url is
                    None or (src_tuple.commit is None and src_tuple.branch is None and src_tuple.tag is None)):
                raise ValueError("Invalid input: empty values in source list")

            # the data to create the remote elements could also be retrieved
            # from __remotes, but this is easier
            elem = ET.SubElement(remote_root, 'Remote', {'name': src_tuple.remote_name})
            elem.text = src_tuple.remote_url
            elem.tail = '\n    '

            for subroot_hook in self._tree.iter('ClientGitHookList'):
                for hook_element in subroot_hook.iter('ClientGitHook'):
                    if hook_element.attrib['remote'] == src_tuple.remote_name:
                        hook_root.append(hook_element)

            for subroot_submodule_alt_url in self._tree.iter('SubmoduleAlternateRemotes'):
                for alt_url_element in subroot_submodule_alt_url.iter('SubmoduleAlternateRemote'):
                    if alt_url_element.attrib['remote'] == src_tuple.remote_name:
                        submodule_alt_url_root.append(alt_url_element)

            for subroot_selective_subs in self._tree.iter('SelectiveSubmoduleInitList'):
                for selective_sub in subroot_selective_subs.iter('Submodule'):
                    if selective_sub.attrib['remote'] == src_tuple.remote_name:
                        if 'combo' in selective_sub.attrib and selective_sub.attrib['combo'] != combo_name:
                            continue
                        selective_submodules_root.append(selective_sub)

            sparse = 'true' if src_tuple.sparse else 'false'
            sub = 'true' if src_tuple.enable_submodule else 'false'
            # Write the source element based on what value branch or commit is available.
            if src_tuple.commit:
                if src_tuple.branch:
                    if src_tuple.tag:
                        elem = ET.SubElement(source_root, 'Source', {'localRoot': src_tuple.root,
                                                                     'remote': src_tuple.remote_name,
                                                                     'branch': src_tuple.branch,
                                                                     'commit': src_tuple.commit,
                                                                     'sparseCheckout': sparse,
                                                                     'enableSubmodule': sub,
                                                                     'tag': src_tuple.tag})
                    else:
                        elem = ET.SubElement(source_root, 'Source', {'localRoot': src_tuple.root,
                                                                     'remote': src_tuple.remote_name,
                                                                     'branch': src_tuple.branch,
                                                                     'commit': src_tuple.commit,
                                                                     'sparseCheckout': sparse,
                                                                     'enableSubmodule': sub})
                elif src_tuple.branch is None and src_tuple.tag:
                    elem = ET.SubElement(source_root, 'Source', {'localRoot': src_tuple.root,
                                                                 'remote': src_tuple.remote_name,
                                                                 'commit': src_tuple.commit,
                                                                 'sparseCheckout': sparse,
                                                                 'enableSubmodule': sub,
                                                                 'tag': src_tuple.tag})
                elif src_tuple.branch is None and src_tuple.tag is None:
                    elem = ET.SubElement(source_root, 'Source', {'localRoot': src_tuple.root,
                                                                 'remote': src_tuple.remote_name,
                                                                 'commit': src_tuple.commit,
                                                                 'sparseCheckout': sparse,
                                                                 'enableSubmodule': sub})
            else:
                raise ValueError('Pin.xml cannot be generated with an empty commit value')

            elem.tail = '\n    '

        # fixup formating for readability (in order)
        pin_root.text = '\n  '
        list(project_root)[-1].tail = '\n  '
        list(config_root)[-1].tail = '\n  '
        hook_root.text = '\n    '
        hook_root.tail = '\n\n  '
        if submodule_alt_url_root:
            submodule_alt_url_root.text = '\n    '
            submodule_alt_url_root.tail = '\n\n  '
            list(submodule_alt_url_root)[-1].tail = '\n  '
        if selective_submodules_root:
            selective_submodules_root.text = '\n    '
            selective_submodules_root.tail = '\n\n  '
            list(selective_submodules_root)[-1].tail = '\n  '
        remote_root.text = '\n    '
        remote_root.tail = '\n\n  '
        list(remote_root)[-1].tail = '\n  '
        source_root.text = '\n    '
        source_root.tail = '\n'
        list(source_root)[-1].tail = '\n  '

        return pin_tree

    def generate_pin_xml(self, description, combo_name, repo_source_list, filename=None):
        # Filename should be .xml
        pin_tree = self.generate_pin_etree(description, combo_name, repo_source_list)
        pin_tree.write(filename)

    def generate_pin_json(self, description, combo_name, repo_source_list, filename=None):
        # Filename should be .json
        pin_tree = self.generate_pin_etree(description, combo_name, repo_source_list)
        pin_root = pin_tree.getroot()

        json_out = self._dfs_traverse_etree(pin_root)

        with open(filename, 'w') as f:
            f.write(json.dumps(json_out, indent=2))

    def _compare_elements(self, element1, element2):
        if element1.tag != element2.tag:
            return False
        if element1.text != element2.text:
            return False
        if element1.tail != element2.tail:
            if element1.tail is not None:
                tail1 = element1.tail.strip()
            else:
                tail1 = ''
            if element2.tail is not None:
                tail2 = element2.tail.strip()
            else:
                tail2 = ''
            if tail1 != tail2:
                return False
        if element1.attrib != element2.attrib:
            return False
        if len(element1) != len(element2):
            return False
        return all(self._compare_elements(e1, e2) for e1, e2 in zip(element1, element2))

    def equals(self, other, ignore_current_combo=False):
        status = self._compare_elements(self._tree.getroot(), other._tree.getroot())
        if not status:
            tree1 = copy.deepcopy(self._tree.getroot())
            tree2 = copy.deepcopy(other._tree.getroot())
            subroot = tree1.find('GeneralConfig')
            if subroot is None:
                return False
            if ignore_current_combo:
                element = subroot.find('CurrentClonedCombo')
                if element is None:
                    element = ET.SubElement(subroot, 'CurrentClonedCombo')
                    element.tail = '\n'
                element.attrib['combination'] = ''
            element = subroot.find('SourceManifestRepository')
            if element is None:
                element = ET.SubElement(subroot, 'SourceManifestRepository')
                element.tail ='\n'
            element.attrib['manifest_repo'] = ''
            subroot = tree2.find('GeneralConfig')
            if subroot is None:
                return False
            if ignore_current_combo:
                element = subroot.find('CurrentClonedCombo')
                if element is None:
                    element = ET.SubElement(subroot, 'CurrentClonedCombo')
                    element.tail = '\n'
                element.attrib['combination'] = ''
            element = subroot.find('SourceManifestRepository')
            if element is None:
                element = ET.SubElement(subroot, 'SourceManifestRepository')
                element.tail ='\n'
            element.attrib['manifest_repo'] = ''
            status = self._compare_elements(tree1, tree2)
        return status

    def __eq__(self, other):
        return self.equals(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def get_all_patchsets(self):
        '''
        Returns a list of all the patchsets defined in the manifest file
        '''
        patchsets = []
        for patch in self._patch_sets.keys():
            patchsets.append(self._patch_sets[patch])
        return patchsets

    def get_patchset(self, name, remote):
        if (name, remote) in self._patch_sets.keys():
            for patchset in self._patch_sets.keys():
                if patchset[0] == name and patchset[1] == remote:
                    return self._patch_sets[(name, remote)]
        else:
            raise KeyError(NO_PATCHSET_EXISTS.format(name))

    def get_patchsets_for_combo(self, combo=None):
        patchsets = {}
        if combo is None:
            sources = self._combo_sources
            for combo, source in sources.items():
                for reposource in source:
                    if reposource.patch_set is not None:
                        patchsets[combo]=self.get_patchset(reposource.patch_set, reposource.remote_name)
            return patchsets
        else:
            sources = self._combo_sources[combo]
            for reposource in sources:
                if reposource.patch_set is not None:
                        patchsets[combo]=self.get_patchset(reposource.patch_set, reposource.remote_name)

            if len(patchsets):
                return patchsets
            else:
                raise KeyError(NO_PATCHSET_IN_COMBO.format(combo))


    def get_parent_patchset_operations(self, name, remote, patch_set_operations):
        '''
        This method takes the input name and a list for storing the operations as its parameters. It recursively
        calls itself to check if there is a parent patchset for the given patchset and if there is, it checks if
        the remotes are same. If not, it throws a ValueError. These operations are appended to the patch_set_operations
        list.
        '''
        parent_sha = self._patch_sets[(name, remote)][2]
        if (parent_sha, remote) in self._patch_sets:
            if self._patch_sets[(parent_sha, remote)][0] == self._patch_sets[(name, remote)][0]:
                self.get_parent_patchset_operations(parent_sha, remote, patch_set_operations)
                patch_set_operations.append(self._patch_set_operations[(parent_sha, remote)])
            else:
                raise ValueError(REMOTE_DIFFERENT_ERROR.format(parent_sha, self._patch_sets[parent_sha][0],
                name, self._patch_sets[name][0]))

    def get_patchset_operations(self, name, remote):
        '''
        This method returns a list of patchset operations. If name of the patchset is provided as a parameter,
        it gives the operations of that patchset otherwise operations of all patchsets are returned.
        The parent patchset's operations are listed first if there are any.
        '''
        patch_set_operations = []
        if (name, remote) in self._patch_sets:
            self.get_parent_patchset_operations(name, remote, patch_set_operations)
            patch_set_operations.append(self._patch_set_operations[(name, remote)])
            return patch_set_operations
        raise ValueError(PATCHSET_UNKNOWN_ERROR.format(name, self._fileref))

class _PatchSet():
    def __init__(self, element):
        try:
            self.remote = element.attrib['remote']
            self.name = element.attrib['name']
            self.parentSha = element.attrib['parentSha']
            self.fetchBranch = element.attrib['fetchBranch']
        except KeyError as k:
            raise KeyError(REQUIRED_ATTRIB_ERROR_MSG.format(k, element.tag))

    def __eq__(self, other_patchset):
        if isinstance(other_patchset, _PatchSet):
            return (self.name, self.remote, self.parentSha, self.fetchBranch) == \
            (other_patchset.name, other_patchset.remote, other_patchset.parentSha, other_patchset.fetchBranch)
        return False

    @property
    def tuple(self):
        return PatchSet(self.remote, self.name, self.parentSha, self.fetchBranch)

class _PatchSetOperations():
    def __init__(self, element):
        self.type = element.tag
        try:
            self.file = element.attrib['file']
        except KeyError as k:
            self.file = None
        try:
            self.sha = element.attrib['sha']
        except KeyError as k:
            self.sha = None
        try:
            self.source_remote = element.attrib['sourceRemote']
        except KeyError as k:
            self.source_remote = None
        try:
            self.source_branch = element.attrib['sourceBranch']
        except KeyError as k:
            self.source_branch = None

    @property
    def tuple(self):
        return PatchOperation(self.type, self.file, self.sha, self.source_remote, self.source_branch)

class _ProjectInfo():
    def __init__(self, element):
        try:
            self.codename = element.find('CodeName').text
            self.descript = element.find('Description').text
        except KeyError as k:
            raise KeyError(REQUIRED_ATTRIB_ERROR_MSG.format(k, element.tag))

        try:
            self.lead_list = []
            for lead in element.findall('DevLead'):
                self.lead_list.append(lead.text)
        except Exception:
            self.lead_list = None

        try:
            self.org = element.find('Org').text
        except Exception:
            self.org = None

        try:
            self.short_name = element.find('ShortName').text
        except Exception:
            self.short_name = None

        try:
            self.reviewer_list = []
            subroot = element.find('LeadReviewers')
            for reviewer in subroot.iter(tag='Reviewer'):
                self.reviewer_list.append(reviewer.text)
        except Exception:
            self.reviewer_list = None

    @property
    def tuple(self):
        return ProjectInfo(self.codename, self.descript, self.lead_list, self.reviewer_list, self.org, self.short_name)


class _GeneralConfig():
    def __init__(self, element):
        try:
            self.pin_path = element.find('PinPath').text
        except Exception:
            self.pin_path = None
        try:
            self.default_combo = element.find('DefaultCombo').attrib['combination']
        except Exception:
            self.default_combo = None
        try:
            self.curr_combo = element.find('CurrentClonedCombo').attrib['combination']
        except Exception:
            self.curr_combo = None
        try:
            self.source_manifest_repo = element.find('SourceManifestRepository').attrib['manifest_repo']
        except:
            self.source_manifest_repo = None

    @property
    def tuple(self):
        return GeneralConfig(self.default_combo, self.curr_combo, self.pin_path, self.source_manifest_repo)


class _RemoteRepo():
    def __init__(self, element):
        try:
            self.name = element.attrib['name']
            self.url = element.text
        except KeyError as k:
            raise KeyError(REQUIRED_ATTRIB_ERROR_MSG.format(k, element.tag))

    @property
    def tuple(self):
        return RemoteRepo(self.name, self.url)


class _RepoHook():
    def __init__(self, element, remotes):
        try:
            self.source = element.attrib['source']
            self.dest_path = element.attrib['destination']
        except KeyError as k:
            raise KeyError(REQUIRED_ATTRIB_ERROR_MSG.format(k, element.tag))
        try:
            self.remote_url = remotes[element.attrib['remote']].url
        except Exception:
            self.remote_url = None
            print(NO_ASSOCIATED_REMOTE.format(self.source, self.dest_path))
        try:
            self.dest_file = element.attrib['destination_file']
        except Exception:
            self.dest_file = None

    @property
    def tuple(self):
        return RepoHook(self.source, self.dest_path, self.dest_file, self.remote_url)


class _Combination():
    def __init__(self, element):
        try:
            self.name = element.attrib['name']
        except KeyError as k:
            raise KeyError(REQUIRED_ATTRIB_ERROR_MSG.format(k, element.tag))
        try:
            self.description = element.attrib['description']
        except Exception:
            self.description = None   # description is optional attribute
        try:
            self.archived = (element.attrib['archived'].lower() == 'true')
        except Exception:
            self.archived = False
        try:
            self.venv_enable = (element.attrib['venv_enable'].lower() == 'true')
        except Exception:
            self.venv_enable = False

    @property
    def tuple(self):
        return Combination(self.name, self.description, self.venv_enable)


class _RepoSource():
    def __init__(self, element, remotes):
        try:
            self.root = element.attrib['localRoot']
            self.remote_name = element.attrib['remote']
            self.remote_url = remotes[element.attrib['remote']].url
        except KeyError as k:
            raise KeyError(REQUIRED_ATTRIB_ERROR_MSG.format(k, element.tag))
        try:
            self.branch = element.attrib['branch']
        except Exception:
            self.branch = None
        try:
            self.commit = element.attrib['commit']
        except Exception:
            self.commit = None
        try:
            self.tag = element.attrib['tag']
        except Exception:
            self.tag = None
        try:
            self.patch_set = element.attrib['patchSet']
        except Exception:
            self.patch_set = None
        try:
            # if the sparse attrib is not explicitly set to true, then assume false
            self.sparse = (element.attrib['sparseCheckout'].lower() == 'true')
        except Exception:
            self.sparse = False
        try:
            # If enableSubmodule is not set to True then default to False
            self.enableSub = (element.attrib['enableSubmodule'].lower() == 'true')
        except Exception:
            try:
                # Adding backwards compatibility with pin files that used incorrect attribute
                self.enableSub = (element.attrib['enable_submodule'].lower() == 'true')
            except Exception:
                self.enableSub = False
        try:
            self.venv_cfg = (element.attrib['venv_cfg'])
        except:
            self.venv_cfg = None

        if self.branch is None and self.commit is None and self.tag is None and self.patch_set is None:
            raise KeyError(ATTRIBUTE_MISSING_ERROR)

        if self.patch_set is not None and (self.branch is not None or self.commit is not None or self.tag is not None):
            raise ValueError(INVALID_COMBO_DEFINITION_ERROR)

    @property
    def tuple(self):
        return RepoSource(self.root, self.remote_name, self.remote_url, self.branch,
                          self.commit, self.sparse, self.enableSub, self.tag, self.venv_cfg, self.patch_set)


class _SparseSettings():
    def __init__(self, element):
        self.sparse_by_default = False
        try:
            self.sparse_by_default = (element.attrib['sparseByDefault'].lower() == 'true')
        except Exception:
            pass

    @property
    def tuple(self):
        return SparseSettings(self.sparse_by_default)


class _SparseData():
    def __init__(self, element):
        self.combination = None
        self.remote_name = None
        self.always_include = []
        self.always_exclude = []
        try:
            self.combination = element.attrib['combination']
        except Exception:
            pass
        try:
            self.remote_name = element.attrib['remote']
        except Exception:
            pass
        for includes in element.iter(tag='AlwaysInclude'):
            self.always_include.extend(includes.text.split('|'))
        for includes in element.iter(tag='AlwaysExclude'):
            self.always_exclude.extend(includes.text.split('|'))

    @property
    def tuple(self):
        return SparseData(self.combination, self.remote_name, self.always_include, self.always_exclude)


class _FolderToFolderMappingFolderExclude():
    def __init__(self, element):
        self.path = None
        try:
            self.path = element.attrib['path']
        except Exception:
            pass

    @property
    def tuple(self):
        return FolderToFolderMappingFolderExclude(self.path)


class _FolderToFolderMappingFolder():
    def __init__(self, element):
        self.project1_folder = None
        self.project2_folder = None
        self.excludes = []
        try:
            self.project1_folder = element.attrib['project1']
        except Exception:
            pass
        try:
            self.project2_folder = element.attrib['project2']
        except Exception:
            pass
        for exclude in element.iter(tag='Exclude'):
            self.excludes.append(_FolderToFolderMappingFolderExclude(exclude))

    @property
    def tuple(self):
        return FolderToFolderMappingFolder(self.project1_folder, self.project2_folder, self.excludes)


class _FolderToFolderMapping():
    def __init__(self, element):
        self.project1 = None
        self.project2 = None
        self.remote_name = None
        self.folders = []
        try:
            self.project1 = element.attrib['project1']
        except Exception:
            pass
        try:
            self.project2 = element.attrib['project2']
        except Exception:
            pass
        try:
            self.remote_name = element.attrib['remote']
        except Exception:
            pass
        for folder in element.iter(tag='Folder'):
            self.folders.append(_FolderToFolderMappingFolder(folder))
        for folder in element.iter(tag='File'):
            self.folders.append(_FolderToFolderMappingFolder(folder))

    @property
    def tuple(self):
        return FolderToFolderMapping(self.project1, self.project2, self.remote_name, self.folders)


class _SubmoduleAlternateRemote():
    def __init__(self, element, remotes):
        try:
            self.remote_name = element.attrib['remote']
            self.originalUrl = element.attrib['originalUrl']
            self.altUrl = element.text
        except KeyError as k:
            raise KeyError(REQUIRED_ATTRIB_ERROR_MSG.format(k, element.tag))

        if self.remote_name not in remotes:
            raise KeyError(NO_REMOTE_EXISTS_WITH_NAME.format(self.remote_name))

    @property
    def tuple(self):
        return SubmoduleAlternateRemote(self.remote_name, self.originalUrl, self.altUrl)


class _SubmoduleInitEntry():
    def __init__(self, element):
        try:
            self.remote_name = element.attrib['remote']
            self.path = element.text
        except KeyError as k:
            raise KeyError(REQUIRED_ATTRIB_ERROR_MSG.format(k, element.tag))
        try:
            self.combo = element.attrib['combo']
        except Exception:
            self.combo = None
        try:
            self.recursive = element.attrib['recursive'].lower() == 'true'
        except Exception:
            self.recursive = False

    @property
    def tuple(self):
        return SubmoduleInitPath(self.remote_name, self.combo, self.recursive, self.path)


#
# Optional entry point for debug and validation of the CiIndexXml & ManifestXml classes
#
def main():
    import argparse
    import traceback
    import sys

    separator_string = '----------------------------------------------------------------'
    project_header_string = '\nProject Name:    Project XML Path'

    parser = argparse.ArgumentParser()
    parser.add_argument("InputFile", help="Xml file to parse", nargs='?', default="manifest.xml")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Increased verbosity including exception tracebacks')

    args = parser.parse_args()

    # Attempt initial parse as index file
    print('\nAttempting to parse {} as an Index.xml file ...'.format(args.InputFile))
    print(separator_string)
    try:
        test_index = CiIndexXml(args.InputFile)
        project_list = test_index.project_list
        print('\nActive Projects')
        print(project_header_string)
        for project in project_list:
            index = project_list.index(project)
            print('{} : {}'.format(str(project_list[index]), str(test_index.get_project_xml(project_list[index]))))
        print('\nArchived Projects')
        archived_list = test_index.archived_project_list
        print(project_header_string)
        for project in archived_list:
            index = archived_list.index(project)
            print('{} : {}'.format(str(archived_list[index]), str(test_index.get_project_xml(archived_list[index]))))
        print(separator_string)
        print('\nSuccessfully parsed {} as an Index.xml file.\nExiting ...\n'.format(args.InputFile))
        print(separator_string)
        sys.exit(0)
    except (TypeError, ValueError):
        print('{} is an invalid Index.xml file or an invalid xml file.'.format(args.InputFile))
        if args.verbose:
            traceback.print_exc()

    print(separator_string)
    print('\nAttempting to parse {} as a Manifest or Pin file ...'.format(args.InputFile))
    print(separator_string)
    try:
        test_manifest = ManifestXml(args.InputFile)

        if test_manifest.is_pin_file():
            print('\n{} determined to be a pin file'.format(args.InputFile))

        print('\nProjectInfo:')
        print(test_manifest.project_info)

        print("\nGeneralConfig:")
        print(test_manifest.general_config)

        print("\nRemotes:")
        print(test_manifest.remotes)
        print('\nClient Git Hooks')
        print(test_manifest.repo_hooks)
        print('\nSubmodule Alternate Remotes')
        print(test_manifest.submodule_alternate_remotes)

        print('\nGet Submodule Alternates for Remote')
        for remote in test_manifest.remotes:
            alts = test_manifest.get_submodule_alternates_for_remote(remote.name)
            if alts:
                print('\nSubmodule Alternates for Remote: {}'.format(remote.name))
                for alt in alts:
                    print(alt)

        print('\nGet Submodule Init Objects')
        print('\nAll:')
        for entry in test_manifest.get_submodule_init_paths():
            print('+ {}'.format(entry))
        print('\nPer Remote:')
        for remote in test_manifest.remotes:
            for entry in test_manifest.get_submodule_init_paths(remote.name):
                print('+ {}'.format(entry))
        print('\nCurrent Combo:')
        current_combo = test_manifest.general_config.current_combo
        for entry in test_manifest.get_submodule_init_paths(combo=current_combo):
            print('+ {}'.format(entry))
        print('\nCurrent Combo Per Remote:')
        for remote in test_manifest.remotes:
            for entry in test_manifest.get_submodule_init_paths(remote.name, current_combo):
                print('+ {}'.format(entry))

        if not test_manifest.is_pin_file():
            print('\nSparse settings:')
            print(test_manifest.sparse_settings)
            print('\nSparse data:')
            print(test_manifest.sparse_data)

            print('\nCommit templates:')
            print(test_manifest.commit_templates)

            print('\nDsc List:')
            print(test_manifest.dsc_list)

            print('\nFolder to Folder Mapping')
            print(test_manifest.folder_to_folder_mappings)

        combos = test_manifest.combinations
        print('\nCombinations')
        print(combos)

        print('\nget_repo_sources by combo:')
        for combo in combos:
            index = combos.index(combo)
            print('get_repo_sources({}) = '.format(combos[index].name))
            print(test_manifest.get_repo_sources(combos[index].name))

            print('\nAttempting to write TestPin.xml')
            pin_combo = []
            for src in test_manifest.get_repo_sources(combos[0].name):
                if src.commit is None:
                    pin_combo.append(src._replace(commit='TESTHASH1234'))
                else:
                    pin_combo.append(src)
            test_manifest.generate_pin_xml('TestPin', combos[0].name, pin_combo, 'TestPin.xml')

            print('\nAttempting to write TESTCOMBO to current combo field of TestManifest.xml')
            test_manifest.write_current_combo('TESTCOMBO', 'TestManifest.xml')
            print('Updated current combo: {}'.format(test_manifest.general_config.current_combo))

        print('\nPatchsets:')
        print(test_manifest.get_all_patchsets)
        print('\nTest Patchset:')
        print(test_manifest.get_patchset("test", "firmware.boot.uefi.iafw.devops.ci.cr.tools"))
        print('\nPatchset Operations:\n')
        print(test_manifest.get_patchset_operations("test", "firmware.boot.uefi.iafw.devops.ci.cr.tools"))
        print('\nPatchsets for a specific combo:')
        print(test_manifest.get_patchsets_for_combo("edkrepo_3.0.3"))

        print(separator_string)
        if test_manifest.is_pin_file():
            print('Successfully parsed {} as a pin file.\nExiting...'.format(args.InputFile))
        else:
            print('Successfully parsed {} as a manifest file.\nExiting...'.format(args.InputFile))
        print(separator_string)
        sys.exit(0)

    except (TypeError, KeyError, ValueError):
        print('{} is an invalid Manifest or Pin file or an invalid xml file.'.format(args.InputFile))
        if args.verbose:
            traceback.print_exc()


if __name__ == "__main__":
    main()
