#!/usr/bin/env python3
#
## @file
# edk_manifest_validation.py
#
# Copyright (c) 2018 - 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import os
import argparse
import unicodedata
import sys
import traceback

from edkrepo_manifest_parser.edk_manifest import CiIndexXml, ManifestXml
from edkrepo.common.humble import MANIFEST_NAME_INCONSISTENT
from edkrepo.common.humble import INDEX_DUPLICATE_NAMES
from edkrepo.common.edkrepo_exception import EdkrepoVerificationException
from edkrepo.common.humble import VERIFY_ERROR_HEADER

class ValidateManifest:
    # Note: manifest_file must be a path to the manifest file not the file itself
    def __init__(self, manifest_file):
        """Store the path to the manifest file for later validation."""
        self._manifestfile = manifest_file

    def validate_parsing(self):
        """Attempt to parse the manifest XML file; return a (type, status, message) result tuple."""
        self._manifest_xmldata, error = _try_parse_manifest_xml(self._manifestfile)
        if error is None:
            return ("PARSING", True, None)
        return ("PARSING", False, error)

    def validate_codename(self, project):
        """Verify the manifest codename matches the expected project name; return a (type, status, message) result tuple."""
        if not self._manifest_xmldata:
            return ('CODENAME', False, 'Cannot find a manifest for project {}'.format(project))
        elif project != self._manifest_xmldata.project_info.codename:
            return ("CODENAME", False, MANIFEST_NAME_INCONSISTENT.format(project, self._manifest_xmldata.project_info.codename, self._manifestfile))
        else:
            return ("CODENAME", True, None)

    def validate_case_insensitive_single_match(self, project, project_list, ci_index_filename):
        """Verify the project name appears exactly once in project_list using case-insensitive comparison; return a (type, status, message) result tuple."""
        matches = self.list_entries(project, project_list)
        if len(matches) == 0 or len(matches) > 1:
            return ("DUPLICATE", False, INDEX_DUPLICATE_NAMES.format(project, ci_index_filename))
        else:
            return ("DUPLICATE", True, None)
    
    def list_entries(self, project, project_list):
        """Return all entries in project_list that case-insensitively match project."""
        return [x for x in project_list if self.case_insensitive_equal(project, x)]

    def case_insensitive_equal(self, str1, str2):
        """Return True if str1 and str2 are equal under Unicode NFKD case-folding normalization."""
        return unicodedata.normalize("NFKD", str1.casefold()) == unicodedata.normalize("NFKD", str2.casefold())

def _try_parse_manifest_xml(manifest_file):
    """Attempt to construct a ManifestXml from *manifest_file*; return ``(xmldata, None)`` on success or ``(None, exception)`` on failure."""
    try:
        return ManifestXml(manifest_file), None
    except Exception as e_message:
        return None, e_message

def _collect_file_validation_results(manifest_filepath):
    """Validate parsing and codename for a single manifest file; return a list of (type, status, message) result tuples."""
    manifest_obj = ValidateManifest(manifest_filepath)
    results = []
    validate_parsing = manifest_obj.validate_parsing()
    results.append(validate_parsing)
    if manifest_obj._manifest_xmldata:
        val_codename = manifest_obj.validate_codename(manifest_obj._manifest_xmldata.project_info.codename)
        results.append(val_codename)
    else:
        results.append(('CODENAME', False, 'Cannot process codename validation'))
    return results

def _resolve_project_manifest_path(ci_index_xml, global_manifest_directory, project):
    """Return the absolute filesystem path to the manifest XML file for the given project."""
    project_path = os.path.normpath(ci_index_xml.get_project_xml(project))
    return os.path.join(global_manifest_directory, project_path)

def _collect_project_validation_results(manifest_filepath, project, project_list, ci_index_filename):
    """Run parsing, codename, and deduplication validations for one project; return a list of (type, status, message) result tuples."""
    manifest_obj = ValidateManifest(manifest_filepath)
    results = []
    validate_parsing = manifest_obj.validate_parsing()
    results.append(validate_parsing)
    val_codename = manifest_obj.validate_codename(project)
    results.append(val_codename)
    val_name_duplication = manifest_obj.validate_case_insensitive_single_match(project, project_list, ci_index_filename)
    results.append(val_name_duplication)
    return results

def validate_manifestfiles(manifestfile_list=[]):
    """Validate parsing and codename for each manifest file in the list; return a dict mapping filepath to result lists."""
    manifestfile_validation = {}
    for manifest_filepath in manifestfile_list:
        manifestfile_validation[manifest_filepath] = _collect_file_validation_results(manifest_filepath)
    return manifestfile_validation

def validate_manifestrepo(global_manifest_directory, verify_archived=False):
    """Validate all manifest files referenced by CiIndex.xml; return a dict mapping filepath to result lists."""
    manifestfile_validation = {}
    ci_index_filename = os.path.join(global_manifest_directory, 'CiIndex.xml')
    ci_index_xml = CiIndexXml(ci_index_filename)
    project_list = ci_index_xml.project_list
    if verify_archived:
        project_list.extend(ci_index_xml.archived_project_list)
    for project in project_list:
        manifest_filepath = _resolve_project_manifest_path(ci_index_xml, global_manifest_directory, project)
        results = _collect_project_validation_results(manifest_filepath, project, project_list, ci_index_filename)
        manifestfile_validation[manifest_filepath] = results
    return manifestfile_validation

def get_manifest_validation_status(manifestfile_validation):
    """Verify the validation status of all manifest files; return True if any failure is detected, False otherwise."""
    manifest_error = False
    for manifestfile in manifestfile_validation.keys():
        for result in manifestfile_validation[manifestfile]:
            if not result[1]:
                manifest_error = True
                break
    return manifest_error

def print_manifest_errors(manifestfile_validation):
    """Print the error header and details for every failed validation result in the dict."""
    print(VERIFY_ERROR_HEADER)
    for manifestfile in manifestfile_validation.keys():
        for result in manifestfile_validation[manifestfile]:
            if not result[1]:
                print ("File name: {} ".format(manifestfile))
                print ("Error type: {} ".format(result[0]))
                print("Error message: {} \n".format(result[2]))

def main():
    """Parse CLI arguments and run manifest validation, printing results or raising on failure."""
    parser = argparse.ArgumentParser()
    mutex = parser.add_mutually_exclusive_group()
    mutex.add_argument("-a", '--all', help="CiIndex xml directory path to validate all manifest files")
    mutex.add_argument('--files', nargs='+', help="List of manifest xml file paths for validation ")
    args = parser.parse_args()

    if args.files:
        manifestfile_validation = validate_manifestfiles(args.files)
    elif args.all:
        manifestfile_validation = validate_manifestrepo(args.all)

    manifest_error = get_manifest_validation_status(manifestfile_validation)

    if not manifest_error:
        print("Manifest validation status: PASS \n")
    else:
        print_manifest_errors(manifestfile_validation)
        raise EdkrepoVerificationException(("Manifest validation status: FAIL \n"))
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)
        