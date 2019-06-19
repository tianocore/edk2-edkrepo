#!/usr/bin/env python3
#
## @file
# edk_manifest_validation.py
#
# Copyright (c) 2018- 2019, Intel Corporation. All rights reserved.<BR>
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
        self._manifestfile = manifest_file

    def validate_parsing(self):
        try:
            self._manifest_xmldata = ManifestXml(self._manifestfile)
            return ("PARSING", True, None)  # (validation type, status, message)
        except Exception as e_message:
            self._manifest_xmldata = None
            return ("PARSING", False, e_message)

    def validate_codename(self, project):
            if not self._manifest_xmldata:
                return ('CODENAME', False, 'Cannot find a manifest for project {}'.format(project))
            elif project != self._manifest_xmldata.project_info.codename:
                return ("CODENAME", False, MANIFEST_NAME_INCONSISTENT.format(project, self._manifest_xmldata.project_info.codename, self._manifestfile))
            else:
                return ("CODENAME", True, None)

    def validate_case_insensitive_single_match(self, project, project_list, ci_index_filename):
        matches = [x for x in project_list if self.case_insensitive_equal(project, x)]
        if len(matches) == 0 or len(matches) > 1:
            return ("DUPLICATE", False, INDEX_DUPLICATE_NAMES.format(project, ci_index_filename))
        else:
            return ("DUPLICATE", True, None)

    def case_insensitive_equal(self, str1, str2):
        return unicodedata.normalize("NFKD", str1.casefold()) == unicodedata.normalize("NFKD", str2.casefold())

def validate_manifestfiles(manifestfile_list=[]):
    manifestfile_validation = {}
    for manifest_filepath in manifestfile_list:
        manifest_obj = None
        validate_parsing = None
        val_codename = None
        results = []
        # Validate parsing and add results
        manifest_obj = ValidateManifest(manifest_filepath)
        validate_parsing = manifest_obj.validate_parsing()
        results.append(validate_parsing)

        # Validate code name and add results
        if manifest_obj._manifest_xmldata:
            val_codename = manifest_obj.validate_codename(manifest_obj._manifest_xmldata.project_info.codename)
            results.append(val_codename)
            manifestfile_validation[manifest_filepath] = results
        else:
            results.append(('CODENAME', False, 'Cannot process codename validation'))
        manifestfile_validation[manifest_filepath] = results
    return manifestfile_validation

def validate_manifestrepo(global_manifest_directory, verify_archived=False):
    manifestfile_validation = {}
    # Open CiIndex.xml and parse the data
    ci_index_filename = os.path.join(global_manifest_directory, 'CiIndex.xml')
    ci_index_xml = CiIndexXml(ci_index_filename)
    # Check every entry in the CiIndex.xml file to verify consistency
    project_list = ci_index_xml.project_list
    if verify_archived:
        project_list.extend(ci_index_xml.archived_project_list)
    for project in project_list:
        manifest_filepath = None
        manifest_obj = None
        validate_parsing = None
        val_name_duplication = None
        results = []
        # Get project XML file path
        project_path = os.path.normpath(ci_index_xml.get_project_xml(project))

        # Validate parsing and add results
        manifest_filepath = os.path.join(global_manifest_directory, project_path)
        manifest_obj = ValidateManifest(manifest_filepath)
        validate_parsing = manifest_obj.validate_parsing()
        results.append(validate_parsing)

        # Validate Code name and add results
        val_codename = manifest_obj.validate_codename(project)
        results.append(val_codename)

        # Verify that name not already used and add results.  The name is not case sensitive.
        val_name_duplication = manifest_obj.validate_case_insensitive_single_match(project, project_list, ci_index_filename)
        results.append(val_name_duplication)

        # Add all results to a dictionary with file path as key
        manifestfile_validation[manifest_filepath] = results
    return manifestfile_validation

def get_manifest_validation_status(manifestfile_validation):
    # Check for all validation results and print status.
    manifest_error = False
    for manifestfile in manifestfile_validation.keys():
        for result in manifestfile_validation[manifestfile]:
            if not result[1]:
                manifest_error = True
                break  # break for first error

    return manifest_error

def print_manifest_errors(manifestfile_validation):
    print(VERIFY_ERROR_HEADER)
    for manifestfile in manifestfile_validation.keys():
        for result in manifestfile_validation[manifestfile]:
            if not result[1]:
                print ("File name: {} ".format(manifestfile))
                print ("Error type: {} ".format(result[0]))
                print("Error message: {} \n".format(result[2]))
def main():
    parser = argparse.ArgumentParser()
    # Add mutually exclusive arguments group
    mutex = parser.add_mutually_exclusive_group()
    mutex.add_argument("-a", '--all', help="CiIndex xml directory path to validate all manifest files")
    mutex.add_argument('--files', nargs='+', help="List of manifest xml file paths for validation ")
    args = parser.parse_args()

    # Validate list of  manifest files
    if args.files:
        manifestfile_validation = validate_manifestfiles(args.files)
    # Validate all manifest files in CiIndex xml
    elif args.all:
        manifestfile_validation = validate_manifestrepo(args.all)

    # Check for all validation results and print status.
    manifest_error = get_manifest_validation_status(manifestfile_validation)

    # Check status.If any error print errors and raise exception.
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
