#!/usr/bin/env python3
#
## @file
# base_tests.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

from unittest.mock import MagicMock, patch, mock_open
import importlib
import pytest
import json
import os

MANIFEST_PATH = '/fake/manifest.xml'
MANIFEST_FILE_PATH = '/fake/path/manifest.xml'
CI_INDEX_PATH = '/fake/CiIndex.xml'
PROJECT1_NAME = 'ProjectA'
PROJECT2_NAME = 'ProjectB'

REMOTE_NAME = 'origin'
REMOTE_URL = 'https://example.com/repo.git'

REQUIRED_ATTRIB_SPLIT_CHAR = '<'

# Common XML attribute key names shared across multiple test modules
ATTRIB_NAME = 'name'
ATTRIB_REMOTE = 'remote'
FIELD_ATTRIB = 'attrib'
ATTRIB_ARCHIVED = 'archived'
ATTRIB_BOOL_TRUE = 'true'
ATTRIB_BOOL_FALSE = 'false'
ATTRIB_PATH = 'path'
ATTRIB_DESCRIPTION = 'description'
ATTRIB_FILE = 'file'
ATTRIB_SOURCE = 'source'
ARCHIVED_TRUE_UPPER = 'TRUE'
TAG_EXCLUDE = 'Exclude'
EXCLUDE_PATH = 'exclude/some/path'
FIELD_REMOTE_NAME = 'remote_name'
ATTRIB_PROJECT1 = 'project1'
ATTRIB_PROJECT2 = 'project2'
PROJECT1_FOLDER = 'project1/path'
PROJECT2_FOLDER = 'project2/path'
ATTRIB_COMBINATION = 'combination'
COMMIT = 'abc123'
BRANCH = 'main'
PATCHSET_NAME = 'ps_name'
TAG_MANIFEST = 'Manifest'
TAG_PIN = 'Pin'
UNKNOWN = 'Unknown'
HELLO = 'hello'
UPSTREAM = 'upstream'
DEV = 'dev'

# Common parametrize field strings shared across multiple test modules
PARAM_FIELD_NAME = 'field_name'
PARAM_EXPECTED = 'expected'
PARAM_FIELD_AND_EXPECTED = '{}, expected_value'.format(PARAM_FIELD_NAME)
PARAM_MISSING_ATTRIB = 'missing_attrib'
PARAM_ATTRIB_VALUE_FIELD = 'attrib_key, attrib_value, {}'.format(PARAM_FIELD_NAME)
PARAM_ATTRIB_VAL_FIELD_EXPECTED = 'attrib_key, attrib_val, {}, {}'.format(PARAM_FIELD_NAME, PARAM_EXPECTED)

# Common pytest parametrize IDs shared across multiple test modules
ID_NO_MATCH = 'no_match'
ID_MISSING = 'missing'
ID_REMOTE_MISSING = 'remote_missing'
ID_REMOTE_NAME_PRESENT = 'remote_name_present'

# Common validation result strings shared across multiple test modules
BAD_XML_MSG = 'bad xml'
RESULT_PARSING = 'PARSING'
RESULT_CODENAME = 'CODENAME'
RESULT_DUPLICATE = 'DUPLICATE'

# Validation result tuple indices
TUPLE_INDEX_TYPE = 0
TUPLE_INDEX_STATUS = 1
TUPLE_INDEX_MESSAGE = 2

# Array/list indices and length constants
FIRST_ELEMENT_INDEX = 0
ZERO_LENGTH = 0
ONE_ITEM = 1
TWO_ITEMS = 2

# Indentation depth constant
INDENT_DEPTH_LEVEL_2 = 2

# Common class and function names for patching
CLASS_VALIDATE_MANIFEST = 'ValidateManifest'
CLASS_MANIFEST_XML = 'ManifestXml'
CLASS_CI_INDEX_XML = 'CiIndexXml'
CLASS_PROJECT = '_Project'
FUNC_COLLECT_FILE_RESULTS = '_collect_file_validation_results'
FUNC_RESOLVE_PATH = '_resolve_project_manifest_path'
FUNC_COLLECT_PROJECT_RESULTS = '_collect_project_validation_results'
FUNC_COLLECT_INVALID_BRANCH = '_collect_invalid_branch_results'
FUNC_LOAD_TREE = '_load_tree'
FUNC_JSON_LOAD = 'json.load'
MODULE_BUILTINS_PRINT = 'builtins.print'
MODULE_ET = 'ET'

# Common attribute names
ATTR_CHILDREN = '_children'

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

def make_find_map_element(find_map=None, dev_leads=None, tag=None):
    """Build a mock element whose ``find()`` returns from *find_map* and ``findall()`` returns *dev_leads*; *dev_leads* defaults to ``[]``."""
    elem = MagicMock()
    if tag is not None:
        elem.tag = tag
    fm = find_map if find_map is not None else {}
    elem.find.side_effect = lambda t: fm.get(t)
    elem.findall.return_value = dev_leads if dev_leads is not None else []
    return elem


PROJECT1_NAME_LOWER = PROJECT1_NAME.lower()
ACTUAL_CODENAME = 'ActualCodename'
HELLO_UPPER = 'Hello'
STR_FOO = 'foo'
STR_BAR = 'bar'
CASE_EQUAL_FIELDS = 'str1,str2,{}'.format(PARAM_EXPECTED)
ID_SAME_CASE = 'same_case'
ID_DIFF_CASE = 'different_case'
ID_UNEQUAL = 'unequal'
SINGLE_MATCH_FAIL_FIELDS = 'project,project_list,expected_msg'
ID_MULTIPLE_MATCHES = 'multiple_matches'
MANIFEST_PATH_2 = '/fake/path/manifest2.xml'
CANNOT_PROCESS_MSG = 'Cannot process codename validation'
PARSE_PASS = (RESULT_PARSING, True, None)
PARSE_FAIL = (RESULT_PARSING, False, BAD_XML_MSG)
CODENAME_PASS = (RESULT_CODENAME, True, None)
DUPLICATE_PASS = (RESULT_DUPLICATE, True, None)
CODENAME_HARDCODED_FAIL = (RESULT_CODENAME, False, CANNOT_PROCESS_MSG)
FILE_RESULTS = [PARSE_PASS, CODENAME_PASS]
FAILURE_RESULTS = [PARSE_FAIL, CODENAME_PASS]
PROJECT_LIST = [PROJECT1_NAME, PROJECT2_NAME]
PROJECT_XML_A = '{}/{}.xml'.format(PROJECT1_NAME, PROJECT1_NAME)
PROJECT_RESULTS = [PARSE_PASS, CODENAME_PASS, DUPLICATE_PASS]
MANIFEST_DIR = '/fake/manifest/dir'
VALIDATION_STATUS_FIELDS = 'data, expected'
ID_ALL_PASS = 'all_pass'
ID_ONE_FAIL = 'one_fail'
ID_EMPTY_DICT = 'empty_dict'
FILE_NAME_FMT = 'File name: {} '
ERROR_TYPE_FMT = 'Error type: {} '
ERROR_MSG_FMT = 'Error message: {} \n'
EXPECTED_PRINT_COUNT = 4
EXPECTED_COLLECT_PROJECT_COUNT = 2


class BaseTestValidateManifest:

    validation_module: str = None

    @pytest.fixture
    def mock_validate_manifest(self):
        """Patch ValidateManifest for the duration of a test; yields the mock class for per-test configuration."""
        with patch('{}.{}'.format(self.__class__.validation_module, CLASS_VALIDATE_MANIFEST)) as mock:
            yield mock

    @pytest.fixture
    def mock_collect_file_results(self):
        """Patch _collect_file_validation_results for the duration of a test; yields the mock for per-test configuration."""
        with patch('{}.{}'.format(self.__class__.validation_module, FUNC_COLLECT_FILE_RESULTS)) as mock:
            yield mock

    @pytest.fixture
    def mock_ci_index_cls(self):
        """Patch CiIndexXml for the duration of a test; yields the mock class for per-test configuration."""
        with patch('{}.{}'.format(self.__class__.validation_module, CLASS_CI_INDEX_XML)) as mock:
            yield mock

    @pytest.fixture
    def mock_resolve_path(self):
        """Patch _resolve_project_manifest_path for the duration of a test; yields the mock for per-test configuration."""
        with patch('{}.{}'.format(self.__class__.validation_module, FUNC_RESOLVE_PATH)) as mock:
            yield mock

    @pytest.fixture
    def mock_collect_project_results(self):
        """Patch _collect_project_validation_results for the duration of a test; yields the mock for per-test configuration."""
        with patch('{}.{}'.format(self.__class__.validation_module, FUNC_COLLECT_PROJECT_RESULTS)) as mock:
            yield mock

    @pytest.fixture
    def mock_print(self):
        """Patch builtins.print for the duration of a test; yields the mock for assertion."""
        with patch(MODULE_BUILTINS_PRINT) as mock:
            yield mock

    @pytest.fixture
    def mock_manifest_xml(self):
        """Patch ManifestXml; yields a configured mock class whose return_value is a fresh MagicMock instance exposed as mock_cls.instance."""
        with patch('{}.{}'.format(self.__class__.validation_module, CLASS_MANIFEST_XML)) as mock_cls:
            instance = MagicMock()
            mock_cls.return_value = instance
            mock_cls.instance = instance
            yield mock_cls

    @pytest.fixture
    def vm(self):
        """Return a ValidateManifest instance initialized with MANIFEST_PATH."""
        vm_module = importlib.import_module(self.__class__.validation_module)
        return vm_module.ValidateManifest(MANIFEST_PATH)

    @staticmethod
    def _make_mock_ci_index(mock_ci_index_cls, project_list, archived_project_list):
        """Configure a mock CiIndexXml class so its instance returns the given project and archived lists."""
        mock_ci = mock_ci_index_cls.return_value
        mock_ci.project_list = list(project_list)
        mock_ci.archived_project_list = list(archived_project_list)
        return mock_ci

    @staticmethod
    def _make_mock_project_validator(mock_cls, parse_result):
        """Configure a mock ValidateManifest class so its instance returns the given parse result and passing validations; validate_branch_names returns [] so it contributes no results."""
        mock_vm = mock_cls.return_value
        mock_vm.validate_parsing.return_value = parse_result
        mock_vm.validate_branch_names.return_value = []
        mock_vm.validate_codename.return_value = CODENAME_PASS
        mock_vm.validate_case_insensitive_single_match.return_value = DUPLICATE_PASS
        return mock_vm

    @staticmethod
    def _setup_file_validator_mock(mock_validate_manifest, parse_result, xmldata):
        """Configure the ValidateManifest instance mock with the given parse result and _manifest_xmldata; return mock_vm."""
        mock_vm = mock_validate_manifest.return_value
        mock_vm.validate_parsing.return_value = parse_result
        mock_vm._manifest_xmldata = xmldata
        return mock_vm

    @staticmethod
    def _setup_manifestrepo_mocks(mock_ci_index_cls, mock_collect_project_results):
        """Configure CiIndexXml with one active and one archived project and set collect-project mock to return PROJECT_RESULTS."""
        BaseTestValidateManifest._make_mock_ci_index(mock_ci_index_cls, [PROJECT1_NAME], [PROJECT2_NAME])
        mock_collect_project_results.return_value = PROJECT_RESULTS

    @staticmethod
    def _make_obj_with_codename(validation_module, codename):
        """Build a ValidateManifest instance whose _manifest_xmldata reports the given codename."""
        vm_module = importlib.import_module(validation_module)
        obj = vm_module.ValidateManifest(MANIFEST_PATH)
        mock_data = MagicMock()
        mock_data.project_info.codename = codename
        obj._manifest_xmldata = mock_data
        return obj

    @staticmethod
    def _call_single_match(vm, project, project_list):
        """Call validate_case_insensitive_single_match with CI_INDEX_PATH as the index filename."""
        return vm.validate_case_insensitive_single_match(project, project_list, CI_INDEX_PATH)

    @staticmethod
    def _assert_parsing_result(vm, expected_result, expected_xmldata):
        """Call validate_parsing on vm and assert both the result tuple and _manifest_xmldata."""
        result = vm.validate_parsing()
        assert result == expected_result
        assert vm._manifest_xmldata is expected_xmldata

    def _call_collect_project_results(self, mock_validate_manifest, parse_result):
        """Set up the ValidateManifest mock, invoke _collect_project_validation_results, assert three results, and return (mock_vm, result)."""
        validation_mod = importlib.import_module(self.__class__.validation_module)
        mock_vm = self._make_mock_project_validator(mock_validate_manifest, parse_result)
        result = validation_mod._collect_project_validation_results(
            MANIFEST_FILE_PATH, PROJECT1_NAME, PROJECT_LIST, CI_INDEX_PATH
        )
        assert len(result) == 3
        return mock_vm, result

    def _call_print_errors(self, results):
        """Build a single-entry validation dict keyed by MANIFEST_FILE_PATH and invoke print_manifest_errors."""
        validation_mod = importlib.import_module(self.__class__.validation_module)
        validation_mod.print_manifest_errors({MANIFEST_FILE_PATH: results})

    def _call_validate_codename(self, codename, project):
        """Build a ValidateManifest with the given codename and return the result of validate_codename."""
        return self._make_obj_with_codename(self.__class__.validation_module, codename).validate_codename(project)

    def _assert_try_parse_result(self, expected_xmldata, expected_error):
        """Call _try_parse_manifest_xml and assert both returned values."""
        vm_module = importlib.import_module(self.__class__.validation_module)
        xmldata, error = vm_module._try_parse_manifest_xml(MANIFEST_PATH)
        assert xmldata is expected_xmldata
        assert error is expected_error

    def test_try_parse_manifest_xml_returns_xmldata_on_success(self, mock_manifest_xml):
        """When ManifestXml succeeds, must return (xmldata, None) with the constructed instance."""
        self._assert_try_parse_result(mock_manifest_xml.instance, None)

    def test_try_parse_manifest_xml_returns_none_and_exception_on_failure(self, mock_manifest_xml):
        """When ManifestXml raises, must return (None, exception) with the original exception."""
        exc = TypeError(BAD_XML_MSG)
        mock_manifest_xml.side_effect = exc
        self._assert_try_parse_result(None, exc)

    def test_validate_parsing_success(self, vm, mock_manifest_xml):
        """When ManifestXml succeeds, must return ("PARSING", True, None) and set _manifest_xmldata."""
        self._assert_parsing_result(vm, (RESULT_PARSING, True, None), mock_manifest_xml.instance)

    def test_validate_parsing_failure(self, vm, mock_manifest_xml):
        """When ManifestXml raises, must return ("PARSING", False, error) and set _manifest_xmldata to None."""
        exc = TypeError(BAD_XML_MSG)
        mock_manifest_xml.side_effect = exc
        self._assert_parsing_result(vm, (RESULT_PARSING, False, exc), None)

    def test_validate_codename_fails_when_no_manifest_data(self, vm):
        """When _manifest_xmldata is None, must return ('CODENAME', False, message containing the project name)."""
        vm._manifest_xmldata = None

        result = vm.validate_codename(PROJECT1_NAME)

        assert result[TUPLE_INDEX_TYPE] == RESULT_CODENAME
        assert result[TUPLE_INDEX_STATUS] is False
        assert PROJECT1_NAME in str(result[TUPLE_INDEX_MESSAGE])

    def test_validate_codename_succeeds_when_codename_matches(self):
        """When _manifest_xmldata.project_info.codename equals the project, must return ('CODENAME', True, None)."""
        result = self._call_validate_codename(PROJECT1_NAME, PROJECT1_NAME)

        assert result == (RESULT_CODENAME, True, None)

    def test_validate_codename_fails_when_codename_mismatches(self):
        """When _manifest_xmldata.project_info.codename differs from the project, must return ('CODENAME', False, message)."""
        result = self._call_validate_codename(ACTUAL_CODENAME, PROJECT1_NAME)

        assert result[TUPLE_INDEX_TYPE] == RESULT_CODENAME
        assert result[TUPLE_INDEX_STATUS] is False
        assert result[TUPLE_INDEX_MESSAGE] is not None

    def test_validate_case_insensitive_single_match_exactly_one_match(self, vm):
        """When exactly one case-insensitive match is found, must return ('DUPLICATE', True, None)."""
        result = self._call_single_match(vm, PROJECT1_NAME, [PROJECT1_NAME, PROJECT2_NAME])

        assert result == (RESULT_DUPLICATE, True, None)

    def test_list_entries_returns_matching_entries(self, vm):
        """When the project list contains case-insensitive matches, must return all of them."""
        project_list = [PROJECT1_NAME, PROJECT1_NAME_LOWER, PROJECT2_NAME]

        result = vm.list_entries(PROJECT1_NAME_LOWER, project_list)

        assert PROJECT1_NAME in result
        assert PROJECT1_NAME_LOWER in result
        assert PROJECT2_NAME not in result

    def test_list_entries_returns_empty_when_no_matches(self, vm):
        """When no entries match the project name, must return an empty list."""
        result = vm.list_entries(UNKNOWN, [PROJECT1_NAME, PROJECT2_NAME])

        assert result == []

    def test_resolve_project_manifest_path_returns_normalized_joined_path(self):
        """The returned path equals os.path.join(MANIFEST_DIR, os.path.normpath(get_project_xml(project)))."""
        validation_mod = importlib.import_module(self.__class__.validation_module)
        mock_ci_index = MagicMock()
        mock_ci_index.get_project_xml.return_value = PROJECT_XML_A

        result = validation_mod._resolve_project_manifest_path(mock_ci_index, MANIFEST_DIR, PROJECT1_NAME)

        expected = os.path.join(MANIFEST_DIR, os.path.normpath(PROJECT_XML_A))
        assert result == expected
        mock_ci_index.get_project_xml.assert_called_once_with(PROJECT1_NAME)

    def test_collect_project_validation_results_all_validations_pass(self, mock_validate_manifest):
        """When all three ValidateManifest methods return passing tuples, the result contains exactly three passing entries."""
        _, result = self._call_collect_project_results(mock_validate_manifest, PARSE_PASS)

        assert result[TWO_ITEMS][TUPLE_INDEX_TYPE] == RESULT_DUPLICATE
        assert all(entry[TUPLE_INDEX_STATUS] is True for entry in result)

    def test_collect_project_validation_results_parsing_fails_three_results_returned(self, mock_validate_manifest):
        """When parsing fails, all three validators still run and three results are returned with the first having False status."""
        mock_vm, result = self._call_collect_project_results(mock_validate_manifest, PARSE_FAIL)

        assert result[FIRST_ELEMENT_INDEX][TUPLE_INDEX_STATUS] is False
        mock_vm.validate_codename.assert_called_once_with(PROJECT1_NAME)
        mock_vm.validate_case_insensitive_single_match.assert_called_once_with(
            PROJECT1_NAME, PROJECT_LIST, CI_INDEX_PATH
        )

    def test_validate_manifestrepo_without_archived_only_active_projects_processed(
            self, mock_ci_index_cls, mock_resolve_path, mock_collect_project_results):
        """When verify_archived=False, only active projects are iterated and the dict contains exactly one entry."""
        validation_mod = importlib.import_module(self.__class__.validation_module)
        self._setup_manifestrepo_mocks(mock_ci_index_cls, mock_collect_project_results)
        mock_resolve_path.return_value = MANIFEST_FILE_PATH

        result = validation_mod.validate_manifestrepo(MANIFEST_DIR, verify_archived=False)

        mock_collect_project_results.assert_called_once()
        assert list(result.keys()) == [MANIFEST_FILE_PATH]

    def test_validate_manifestrepo_with_archived_active_and_archived_processed(
            self, mock_ci_index_cls, mock_resolve_path, mock_collect_project_results):
        """When verify_archived=True, both active and archived projects are iterated and the dict contains two entries."""
        validation_mod = importlib.import_module(self.__class__.validation_module)
        self._setup_manifestrepo_mocks(mock_ci_index_cls, mock_collect_project_results)
        mock_resolve_path.side_effect = [MANIFEST_FILE_PATH, MANIFEST_PATH_2]

        result = validation_mod.validate_manifestrepo(MANIFEST_DIR, verify_archived=True)

        assert mock_collect_project_results.call_count == EXPECTED_COLLECT_PROJECT_COUNT
        assert set(result.keys()) == {MANIFEST_FILE_PATH, MANIFEST_PATH_2}

    def test_print_manifest_errors_prints_header_and_details_for_failures(self, mock_print):
        """When the dict contains a failing result, VERIFY_ERROR_HEADER and the file/type/message lines are all printed."""
        validation_mod = importlib.import_module(self.__class__.validation_module)
        self._call_print_errors(FAILURE_RESULTS)

        mock_print.assert_any_call(validation_mod.VERIFY_ERROR_HEADER)
        mock_print.assert_any_call(FILE_NAME_FMT.format(MANIFEST_FILE_PATH))
        mock_print.assert_any_call(ERROR_TYPE_FMT.format(RESULT_PARSING))
        mock_print.assert_any_call(ERROR_MSG_FMT.format(BAD_XML_MSG))
        assert mock_print.call_count == EXPECTED_PRINT_COUNT

    def test_print_manifest_errors_all_passing_only_header_printed(self, mock_print):
        """When all results are passing, only VERIFY_ERROR_HEADER is printed and no error detail lines follow."""
        validation_mod = importlib.import_module(self.__class__.validation_module)
        self._call_print_errors(FILE_RESULTS)

        mock_print.assert_called_once_with(validation_mod.VERIFY_ERROR_HEADER)

    @pytest.mark.parametrize(VALIDATION_STATUS_FIELDS, [
        pytest.param({MANIFEST_FILE_PATH: FILE_RESULTS}, False, id=ID_ALL_PASS),
        pytest.param({MANIFEST_FILE_PATH: FAILURE_RESULTS}, True, id=ID_ONE_FAIL),
        pytest.param({}, False, id=ID_EMPTY_DICT),
    ])
    def test_get_manifest_validation_status(self, data, expected):
        """Verify all manifests in the dict; parametrized over all-pass, one-fail, and empty-dict scenarios."""
        validation_mod = importlib.import_module(self.__class__.validation_module)
        assert validation_mod.get_manifest_validation_status(data) is expected

    @pytest.mark.parametrize(SINGLE_MATCH_FAIL_FIELDS, [
        pytest.param(UNKNOWN, [PROJECT1_NAME, PROJECT2_NAME], UNKNOWN, id=ID_NO_MATCH),
        pytest.param(PROJECT1_NAME, [PROJECT1_NAME, PROJECT1_NAME_LOWER], PROJECT1_NAME, id=ID_MULTIPLE_MATCHES),
    ])
    def test_validate_case_insensitive_single_match_fails(self, vm, project, project_list, expected_msg):
        """Must return ('DUPLICATE', False, message) when no match or multiple matches are found."""
        result = self._call_single_match(vm, project, project_list)

        assert result[TUPLE_INDEX_TYPE] == RESULT_DUPLICATE
        assert result[TUPLE_INDEX_STATUS] is False
        assert expected_msg in str(result[TUPLE_INDEX_MESSAGE])

    @pytest.mark.parametrize(CASE_EQUAL_FIELDS, [
        pytest.param(HELLO, HELLO, True, id=ID_SAME_CASE),
        pytest.param(HELLO_UPPER, HELLO, True, id=ID_DIFF_CASE),
        pytest.param(STR_FOO, STR_BAR, False, id=ID_UNEQUAL),
    ])
    def test_case_insensitive_equal(self, vm, str1, str2, expected):
        """Must return True when str1 and str2 are case-insensitively equal, False otherwise."""
        assert vm.case_insensitive_equal(str1, str2) is expected


PIN_XML = '/fake/path/pin.xml'
MANIFEST_JSON = '/fake/path/manifest.json'
MANIFEST_XYZ = '/fake/path/manifest.xyz'
NODE_SOLO = 'Solo'
NODE_PARENT = 'Parent'
NODE_CHILD = 'Child'
NODE_KEY_TEXT = 'text'
NODE_KEY_TAIL = 'tail'
NODE_KEY_CHILDREN = 'children'
ELEMENT_ROOT_TAG = 'root'
ELEMENT_CHILD_TAG = 'child'
ELEMENT_TAG_PLACEHOLDER = 'placeholder'
ATTRIB_KEY = 'key'
ATTRIB_VAL = 'val'
TAIL_VALUE = ' world'
ORIGINAL_TEXT = 'original'
PARSE_ERROR_MSG = 'parse error'
INVALID_FILE_MSG = 'invalid file'
PRETTY_FORMAT_INDEX_FIELDS = 'index,{}'.format(PARAM_EXPECTED)
ID_INDEX_ZERO = 'index_zero'
ID_INDEX_NONZERO = 'index_nonzero'
INIT_SUCCESS_FIELDS = 'tag,fileref,xml_types'
ID_MANIFEST_TYPE = 'manifest_type'
ID_PIN_TYPE = 'pin_type'
INDENT_DEPTH_1 = '\n  '
INDENT_DEPTH_2 = '\n    '


class BaseTestBaseXmlHelper:

    manifest_module: str = None

    @pytest.fixture
    def mock_et_module(self):
        """Complete mock of the ET module to prevent any real operations."""
        with patch('{}.{}'.format(self.__class__.manifest_module, MODULE_ET)) as mock_et:
            mock_et.Element = MagicMock()
            mock_et.SubElement = MagicMock()
            mock_et.ElementTree = MagicMock()
            yield mock_et

    @pytest.fixture
    def mock_et(self):
        """Patch ET.ElementTree for the duration of a test; yields the mock class."""
        with patch('{}.{}'.format(self.__class__.manifest_module, METHOD_ET_ELEMENT_TREE)) as mock:
            yield mock

    @pytest.fixture
    def mock_load_tree(self):
        """Patch BaseXmlHelper._load_tree for the duration of a test; yields the mock."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        with patch.object(manifest_mod.BaseXmlHelper, FUNC_LOAD_TREE) as mock:
            yield mock

    @pytest.fixture
    def mock_json_open(self):
        """Patch builtins.open and json.load for the duration of a test; yields (mock_open, mock_json_load)."""
        with patch(BUILTIN_OPEN) as mock_open, \
             patch('{}.{}'.format(self.__class__.manifest_module, FUNC_JSON_LOAD)) as mock_json_load:
            yield mock_open, mock_json_load

    @pytest.fixture
    def bare_instance(self):
        """Return a bare BaseXmlHelper instance bypassing __init__."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        return object.__new__(manifest_mod.BaseXmlHelper)

    @staticmethod
    def _create_mock_element(tag, attrib=None, text=None):
        """Create a mock XML element with tag, attrib, and text support."""
        elem = MagicMock()
        elem.tag = tag
        elem.attrib = attrib if attrib is not None else {}
        elem.text = text
        elem.tail = None
        elem.__getitem__ = MagicMock(side_effect=lambda i: elem._children[i] if hasattr(elem, ATTR_CHILDREN) else MagicMock())
        elem.__len__ = MagicMock(side_effect=lambda: len(elem._children) if hasattr(elem, ATTR_CHILDREN) else ZERO_LENGTH)
        elem.__iter__ = MagicMock(side_effect=lambda: iter(elem._children) if hasattr(elem, ATTR_CHILDREN) else iter([]))
        elem._children = []
        return elem

    @staticmethod
    def _create_mock_subelement(parent, tag, attrib=None):
        """Create a mock SubElement and attach it to parent."""
        child = BaseTestBaseXmlHelper._create_mock_element(tag, attrib)
        if not hasattr(parent, ATTR_CHILDREN):
            parent._children = []
        parent._children.append(child)
        parent.__len__ = MagicMock(return_value=len(parent._children))
        parent.__getitem__ = MagicMock(side_effect=lambda i: parent._children[i])
        return child

    @staticmethod
    def _make_mock_tree(tag):
        """Return a mock ElementTree whose getroot().tag equals tag."""
        mock_tree = MagicMock()
        mock_tree.getroot.return_value.tag = tag
        return mock_tree

    def _build_node(self, current_dict):
        """Build an ET node from current_dict via _build_etree_node and return the first child of the parent."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        instance = object.__new__(manifest_mod.BaseXmlHelper)
        parent = self._create_mock_element(ELEMENT_ROOT_TAG)
        instance._build_etree_node(current_dict, parent)
        return parent[FIRST_ELEMENT_INDEX]

    def _assert_init_raises_typeerror(self, xml_types):
        """Assert that BaseXmlHelper(MANIFEST_FILE_PATH, xml_types) raises TypeError."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        with pytest.raises(TypeError):
            manifest_mod.BaseXmlHelper(MANIFEST_FILE_PATH, xml_types)

    def test_root_tag_not_in_xml_types_raises_typeerror(self, mock_load_tree):
        """When the root tag is not in xml_types, __init__ must raise TypeError."""
        mock_load_tree.return_value = self._make_mock_tree(UNKNOWN)
        self._assert_init_raises_typeerror([TAG_MANIFEST, TAG_PIN])

    def test_load_tree_raises_typeerror_propagates(self, mock_load_tree):
        """When _load_tree raises TypeError, the exception must propagate out of __init__ unchanged."""
        mock_load_tree.side_effect = TypeError(INVALID_FILE_MSG)
        self._assert_init_raises_typeerror([TAG_MANIFEST])

    def test_valid_json_returns_converted_element_tree(self, bare_instance, mock_json_open, mock_et_module):
        """When open and json.load succeed, _json_to_xml must return a tree whose root tag matches the JSON node name and call _pretty_format and _build_etree_node each exactly once."""
        mock_open, mock_json_load = mock_json_open
        mock_json_load.return_value = {ATTRIB_NAME: TAG_MANIFEST}

        # Configure ET mocks to return mock elements
        mock_root = self._create_mock_element(ELEMENT_TAG_PLACEHOLDER)
        mock_et_module.Element.return_value = mock_root
        mock_tree = MagicMock()
        mock_et_module.ElementTree.return_value = mock_tree

        def mock_build_node(d, p):
            return self._create_mock_subelement(p, TAG_MANIFEST)

        bare_instance._build_etree_node = MagicMock(side_effect=mock_build_node)
        bare_instance._pretty_format = MagicMock()

        # Configure getroot to return the child element that will be set by _setroot
        def mock_setroot(elem):
            mock_tree.getroot.return_value = elem
        mock_tree._setroot = mock_setroot

        result = bare_instance._json_to_xml(MANIFEST_JSON)

        assert result.getroot().tag == TAG_MANIFEST
        bare_instance._pretty_format.assert_called_once()
        bare_instance._build_etree_node.assert_called_once()

    def test_dict_with_all_optional_fields(self, mock_et_module):
        """When the dict contains name, attrib, text, tail, and children, _build_etree_node must set all fields and recurse."""
        # Configure ET.SubElement to return mock elements
        def create_subelement_mock(parent, tag, attrib=None):
            return self._create_mock_subelement(parent, tag, attrib)

        mock_et_module.SubElement.side_effect = create_subelement_mock

        node = self._build_node({
            ATTRIB_NAME: NODE_PARENT,
            FIELD_ATTRIB: {ATTRIB_KEY: ATTRIB_VAL},
            NODE_KEY_TEXT: HELLO,
            NODE_KEY_TAIL: TAIL_VALUE,
            NODE_KEY_CHILDREN: [{ATTRIB_NAME: NODE_CHILD}],
        })

        assert node.tag == NODE_PARENT
        assert node.attrib == {ATTRIB_KEY: ATTRIB_VAL}
        assert node.text == HELLO
        assert node.tail == TAIL_VALUE
        assert node[FIRST_ELEMENT_INDEX].tag == NODE_CHILD

    def test_dict_with_name_only(self, mock_et_module):
        """When the dict contains only the name key, _build_etree_node must create a SubElement with empty attrib, None text, None tail, and no children."""
        # Configure ET.SubElement to return mock elements
        def create_subelement_mock(parent, tag, attrib=None):
            return self._create_mock_subelement(parent, tag, attrib)

        mock_et_module.SubElement.side_effect = create_subelement_mock

        node = self._build_node({ATTRIB_NAME: NODE_SOLO})

        assert node.tag == NODE_SOLO
        assert node.attrib == {}
        assert node.text is None
        assert node.tail is None
        assert len(node) == ZERO_LENGTH

    def test_no_parent_completes_without_error(self, bare_instance):
        """When called without a parent argument, _pretty_format must complete without raising any exception."""
        root = self._create_mock_element(ELEMENT_ROOT_TAG)

        bare_instance._pretty_format(root)

    def test_pretty_format_recurses_into_children(self, bare_instance):
        """When current has nested children, _pretty_format must recursively set indentation on each ancestor's text."""
        root = self._create_mock_element(ELEMENT_ROOT_TAG)
        child = self._create_mock_subelement(root, NODE_CHILD)
        self._create_mock_subelement(child, NODE_CHILD)

        bare_instance._pretty_format(root)

        assert root.text == INDENT_DEPTH_1
        assert child.text == INDENT_DEPTH_2

    def test_xml_extension_returns_element_tree(self, bare_instance, mock_et):
        """When fileref has a .xml extension, _load_tree must call ET.ElementTree(file=fileref) and return the result."""
        mock_tree = MagicMock()
        mock_et.return_value = mock_tree

        result = bare_instance._load_tree(MANIFEST_FILE_PATH)

        mock_et.assert_called_once_with(file=MANIFEST_FILE_PATH)
        assert result is mock_tree

    def test_json_extension_delegates_to_json_to_xml(self, bare_instance):
        """When fileref has a .json extension, _load_tree must delegate to self._json_to_xml and return its result."""
        expected = MagicMock()
        bare_instance._json_to_xml = MagicMock(return_value=expected)

        result = bare_instance._load_tree(MANIFEST_JSON)

        bare_instance._json_to_xml.assert_called_once_with(MANIFEST_JSON)
        assert result is expected

    def test_unsupported_extension_raises_typeerror(self, bare_instance):
        """When fileref has an unsupported extension, _load_tree must raise TypeError."""
        with pytest.raises(TypeError):
            bare_instance._load_tree(MANIFEST_XYZ)

    def test_file_parse_error_raises_typeerror(self, bare_instance, mock_et):
        """When ET.ElementTree raises an exception during parsing, _load_tree must catch it and raise TypeError."""
        mock_et.side_effect = Exception(PARSE_ERROR_MSG)

        with pytest.raises(TypeError):
            bare_instance._load_tree(MANIFEST_FILE_PATH)

    def test_json_parse_error_raises_typeerror(self, bare_instance):
        """When _json_to_xml raises an exception during JSON parsing, _load_tree must catch it and raise TypeError."""
        bare_instance._json_to_xml = MagicMock(side_effect=Exception(PARSE_ERROR_MSG))

        with pytest.raises(TypeError):
            bare_instance._load_tree(MANIFEST_JSON)

    @pytest.mark.parametrize(PRETTY_FORMAT_INDEX_FIELDS, [
        pytest.param(FIRST_ELEMENT_INDEX, INDENT_DEPTH_2, id=ID_INDEX_ZERO),
        pytest.param(ONE_ITEM, ORIGINAL_TEXT, id=ID_INDEX_NONZERO),
    ])
    def test_pretty_format_parent_text_by_index(self, bare_instance, index, expected):
        """When called with a given index and depth=2, _pretty_format must set parent.text to the expected value."""
        parent = self._create_mock_element(ELEMENT_ROOT_TAG)
        parent.text = ORIGINAL_TEXT
        child = self._create_mock_subelement(parent, ELEMENT_CHILD_TAG)

        bare_instance._pretty_format(child, parent, index, INDENT_DEPTH_LEVEL_2)

        assert parent.text == expected

    @pytest.mark.parametrize(INIT_SUCCESS_FIELDS, [
        pytest.param(TAG_MANIFEST, MANIFEST_FILE_PATH, [TAG_MANIFEST, TAG_PIN], id=ID_MANIFEST_TYPE),
        pytest.param(TAG_PIN, PIN_XML, [TAG_PIN], id=ID_PIN_TYPE),
    ])
    def test_init_valid_root_tag_sets_attributes(self, mock_load_tree, tag, fileref, xml_types):
        """When _load_tree returns a tree whose root tag is in xml_types, __init__ must set _fileref, _tree, and _xml_type."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        mock_load_tree.return_value = self._make_mock_tree(tag)

        instance = manifest_mod.BaseXmlHelper(fileref, xml_types)

        assert instance._fileref == fileref
        assert instance._tree is mock_load_tree.return_value
        assert instance._xml_type == tag


PROJECT_XML_A = '{}/{}.xml'.format(PROJECT1_NAME, PROJECT1_NAME)
ELEMENT_TAG_CI_PROJECT_LIST = 'ProjectList'
CI_DEFAULT_XML_PATH = 'fake_path.xml'
CI_PARAMETRIZE_FIELDS = 'archived_a,archived_b,{}'.format(PARAM_EXPECTED)
ID_MIXED = 'mixed'
ID_ALL_ARCHIVED = 'all_archived'
ID_NONE_ARCHIVED = 'none_archived'


class BaseTestCiIndexXml:

    manifest_module: str = None

    @pytest.fixture(autouse=True)
    def mock_et(self):
        """Patch ET.ElementTree for every test to prevent real file I/O; yields the mock class."""
        with patch('{}.{}'.format(self.__class__.manifest_module, METHOD_ET_ELEMENT_TREE)) as mock_et_cls:
            mock_tree = MagicMock()
            mock_et_cls.return_value = mock_tree
            mock_tree.getroot.return_value.tag = ELEMENT_TAG_CI_PROJECT_LIST
            mock_tree.iter.return_value = []
            yield mock_et_cls

    @pytest.fixture
    def ci_instance(self):
        """Return a bare CiIndexXml instance with an empty _projects map ready for per-test configuration."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        return manifest_mod.CiIndexXml(CI_INDEX_PATH)

    @pytest.fixture
    def mock_project_cls(self):
        """Patch _Project for the duration of a test; yields the mock class with no default configuration."""
        with patch('{}.{}'.format(self.__class__.manifest_module, CLASS_PROJECT)) as mock:
            yield mock

    @staticmethod
    def _make_mock_project(name, archived, xml_path=None):
        """Build and return a mock _Project with the given name, archived flag, and xmlPath."""
        if xml_path is None:
            xml_path = CI_DEFAULT_XML_PATH
        proj = MagicMock()
        proj.name = name
        proj.archived = archived
        proj.xmlPath = xml_path
        return proj

    def _make_two_project_map(self, archived_a, archived_b):
        """Build a _projects dict with PROJECT1_NAME and PROJECT2_NAME using the given archived flags."""
        return {
            PROJECT1_NAME: self._make_mock_project(PROJECT1_NAME, archived_a),
            PROJECT2_NAME: self._make_mock_project(PROJECT2_NAME, archived_b),
        }

    def test_init_empty_tree_results_in_empty_project_map(self, mock_project_cls):
        """When the XML tree has no Project elements, _projects must be empty and _Project never called."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        ci = manifest_mod.CiIndexXml(CI_INDEX_PATH)

        assert ci._projects == {}
        mock_project_cls.assert_not_called()

    def test_init_single_project_populates_map_with_correct_key(self, mock_project_cls, mock_et):
        """When the tree has one Project element, _projects must contain exactly that entry keyed by name."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        mock_elem = MagicMock()
        mock_et.return_value.iter.return_value = [mock_elem]
        proj_a = self._make_mock_project(PROJECT1_NAME, False, PROJECT_XML_A)
        mock_project_cls.return_value = proj_a

        ci = manifest_mod.CiIndexXml(CI_INDEX_PATH)

        assert ci._projects == {PROJECT1_NAME: proj_a}
        mock_project_cls.assert_called_once_with(mock_elem)

    def test_init_multiple_projects_all_keyed_by_name(self, mock_project_cls, mock_et):
        """When the tree has multiple Project elements, _projects must contain one entry per project."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        mock_elem_a, mock_elem_b = MagicMock(), MagicMock()
        mock_et.return_value.iter.return_value = [mock_elem_a, mock_elem_b]
        proj_a = self._make_mock_project(PROJECT1_NAME, False)
        proj_b = self._make_mock_project(PROJECT2_NAME, True)
        mock_project_cls.side_effect = [proj_a, proj_b]

        ci = manifest_mod.CiIndexXml(CI_INDEX_PATH)

        assert ci._projects == {PROJECT1_NAME: proj_a, PROJECT2_NAME: proj_b}

    def test_get_project_xml_returns_path_when_project_found(self, ci_instance):
        """When the requested project exists in _projects, get_project_xml must return its xmlPath."""
        ci_instance._projects = {
            PROJECT1_NAME: self._make_mock_project(PROJECT1_NAME, False, PROJECT_XML_A),
        }

        assert ci_instance.get_project_xml(PROJECT1_NAME) == PROJECT_XML_A

    def test_get_project_xml_raises_value_error_when_not_found(self, ci_instance):
        """When the requested project is absent from _projects, get_project_xml must raise ValueError."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        with pytest.raises(ValueError) as exc_info:
            ci_instance.get_project_xml(UNKNOWN)
        assert str(exc_info.value) == manifest_mod.INVALID_PROJECTNAME_ERROR.format(UNKNOWN)

    @pytest.mark.parametrize(CI_PARAMETRIZE_FIELDS, [
        pytest.param(False, True, [PROJECT1_NAME], id=ID_MIXED),
        pytest.param(True, True, [], id=ID_ALL_ARCHIVED),
        pytest.param(False, False, [PROJECT1_NAME, PROJECT2_NAME], id=ID_NONE_ARCHIVED),
    ])
    def test_project_list(self, ci_instance, archived_a, archived_b, expected):
        """project_list must return only non-archived project names for each combination of archived flags."""
        ci_instance._projects = self._make_two_project_map(archived_a, archived_b)

        assert set(ci_instance.project_list) == set(expected)

    @pytest.mark.parametrize(CI_PARAMETRIZE_FIELDS, [
        pytest.param(False, True, [PROJECT2_NAME], id=ID_MIXED),
        pytest.param(False, False, [], id=ID_NONE_ARCHIVED),
        pytest.param(True, True, [PROJECT1_NAME, PROJECT2_NAME], id=ID_ALL_ARCHIVED),
    ])
    def test_archived_project_list(self, ci_instance, archived_a, archived_b, expected):
        """archived_project_list must return only archived project names for each combination of archived flags."""
        ci_instance._projects = self._make_two_project_map(archived_a, archived_b)

        assert set(ci_instance.archived_project_list) == set(expected)


ATTRIB_XML_PATH = 'xmlPath'
ELEMENT_TAG_PROJECT = 'Project'
TEST_PROJECT_NAME = 'MyProject'
PROJECT_XML_PATH = '{}/{}.xml'.format(TEST_PROJECT_NAME, TEST_PROJECT_NAME)
PROJECT_ARCHIVED_FLAG_FIELDS = 'archived_value,{}'.format(PARAM_EXPECTED)
ID_TRUE_LOWER = 'true_lower'
ID_FALSE_LOWER = 'false_lower'
ID_TRUE_UPPER = 'true_upper'


class BaseTestProject:

    manifest_module: str = None

    def _assert_required_attrib_key_error(self, attrib):
        """Call _parse_project_required_attribs with attrib and assert KeyError with the required-attrib message prefix."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element(attrib, tag=ELEMENT_TAG_PROJECT)
        with pytest.raises(KeyError) as exc_info:
            manifest_mod._parse_project_required_attribs(element)
        assert manifest_mod.REQUIRED_ATTRIB_ERROR_MSG.split(REQUIRED_ATTRIB_SPLIT_CHAR)[FIRST_ELEMENT_INDEX] in exc_info.value.args[FIRST_ELEMENT_INDEX]

    def test_parse_required_attribs_returns_name_and_xml_path_when_both_present(self):
        """When name and xmlPath are present, must return (name, xmlPath) without raising."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = self._make_full_element()

        name, xml_path = manifest_mod._parse_project_required_attribs(element)

        assert name == TEST_PROJECT_NAME
        assert xml_path == PROJECT_XML_PATH

    def test_parse_required_attribs_raises_key_error_when_name_missing(self):
        """When name is absent from the element, must raise KeyError with the required-attrib message."""
        self._assert_required_attrib_key_error({ATTRIB_XML_PATH: PROJECT_XML_PATH})

    def test_parse_required_attribs_raises_key_error_when_xml_path_missing(self):
        """When xmlPath is absent from the element, must raise KeyError with the required-attrib message."""
        self._assert_required_attrib_key_error({ATTRIB_NAME: TEST_PROJECT_NAME})

    def test_init_sets_name_and_xml_path_from_required_attribs(self):
        """When all required attributes are present, __init__ must set name and xmlPath correctly."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = self._make_full_element()

        proj = manifest_mod._Project(element)

        assert proj.name == TEST_PROJECT_NAME
        assert proj.xmlPath == PROJECT_XML_PATH

    @pytest.mark.parametrize(PROJECT_ARCHIVED_FLAG_FIELDS, [
        pytest.param(ATTRIB_BOOL_TRUE, True, id=ID_TRUE_LOWER),
        pytest.param(ATTRIB_BOOL_FALSE, False, id=ID_FALSE_LOWER),
        pytest.param(None, False, id=ID_MISSING),
        pytest.param(ARCHIVED_TRUE_UPPER, True, id=ID_TRUE_UPPER),
    ])
    def test_init_archived_flag(self, archived_value, expected):
        """Each archived_value must produce the expected boolean on self.archived."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = self._make_full_element(archived=archived_value)
        proj = manifest_mod._Project(element)
        assert proj.archived is expected


PARAM_IS_PIN_FILE = 'xml_type, {}'.format(PARAM_EXPECTED)
ID_XML_TYPE_PIN = 'xml_type_pin'
ID_XML_TYPE_MANIFEST = 'xml_type_manifest'
PARAM_SUBMODULE_ALTS = 'alt_remote, query_remote, expect_match'
ID_ALT_MATCHING = 'matching_remote'
PARAM_NESTED_REPO_RAISES = 'sources, path, expected_error'
ID_NON_NESTED_PATH = 'non_nested_path'
ID_NO_PARENT_FOUND = 'no_parent_found'
PARAM_COMBO_ARG = 'combo_arg'
ID_COMBO_NONE = 'combo_none'
ID_COMBO_SPECIFIED = 'combo_specified'
COMBO_NAME = 'default'
PIN_PREFIX_COMBO = '{}:{}'.format(TAG_PIN, BRANCH)
PARENT_REPO = 'parent'
NESTED_REPO = '{}/child'.format(PARENT_REPO)
INVALID_REPO_PATH = 'singlecomponent'
TAG_GENERAL_CONFIG = 'GeneralConfig'
TAG_BINARY_LIST = 'BinaryList'
TAG_SPARSE_CHECKOUT = 'SparseCheckout'
TAG_SUBMODULE_ALT_REMOTES = 'SubmoduleAlternateRemotes'
TAG_SELECTIVE_SUBMODULE_INIT = 'SelectiveSubmoduleInitList'
TAG_PATCH_SETS = 'PatchSets'
ROOT_PATH = 'platform/repo'
PARENT_SHA_ORPHAN = 'orphan'
METHOD_COPY_DEEPCOPY = 'copy.deepcopy'
METHOD_ET_ELEMENT_TREE = 'ET.ElementTree'
METHOD_ET_ELEMENT = 'ET.Element'
METHOD_ET_SUB_ELEMENT = 'ET.SubElement'
PIN_DESCRIPTION = 'Test pin description'
INVALID_COMBO = 'nonexistent_combo'
METHOD_GENERATE_PIN_ETREE = 'generate_pin_etree'
PIN_JSON_PATH = '/fake/pin.json'
KEY_CHILDREN = 'children'
FILE_MODE_WRITE = 'w'
METHOD_DFS_TRAVERSE = '_dfs_traverse_etree'
BUILTIN_OPEN = 'builtins.open'


class BaseTestManifestXml:

    manifest_module: str = None

    @pytest.fixture
    def mock_et(self):
        """Patch ET.ElementTree to prevent real file I/O; yields the mock class."""
        with patch('{}.{}'.format(self.__class__.manifest_module, METHOD_ET_ELEMENT_TREE)) as mock_et_cls:
            mock_tree = MagicMock()
            mock_et_cls.return_value = mock_tree
            mock_tree.getroot.return_value.tag = TAG_MANIFEST
            mock_tree.iter.return_value = []
            yield mock_et_cls

    @pytest.fixture
    def manifest_instance(self, mock_et):
        """Return a ManifestXml with cleared internal collections ready for per-test configuration."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        instance = manifest_mod.ManifestXml(MANIFEST_PATH)
        instance._combo_sources = {}
        instance._combinations = {}
        instance._remotes = {}
        instance._patch_sets = {}
        instance._patch_set_operations = {}
        instance._submodule_init_list = []
        instance._submodule_alternate_remotes = []
        instance._client_hook_list = []
        instance._xml_type = TAG_MANIFEST
        return instance

    @staticmethod
    def _make_mock_source(patch_set=None, remote_name=None):
        """Build and return a mock RepoSource-like object with configurable patch_set and remote_name."""
        src = MagicMock()
        src.patch_set = patch_set
        src.remote_name = remote_name if remote_name is not None else REMOTE_NAME
        return src

    @staticmethod
    def _make_mock_submodule_entry(remote_name, combo=None):
        """Build and return a mock _SubmoduleInitEntry-like object with remote_name and combo."""
        entry = MagicMock()
        entry.remote_name = remote_name
        entry.combo = combo
        return entry

    def _make_patchset_tuple(self, name, remote, parent_sha=PARENT_SHA_ORPHAN, fetch_branch=BRANCH):
        """Build and return a PatchSet namedtuple with the given fields."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        return manifest_mod.PatchSet(remote=remote, name=name, parent_sha=parent_sha, fetch_branch=fetch_branch)

    @staticmethod
    def _make_mock_remote(name=None, url=None):
        """Build and return a mock remote object; optionally set tuple.name and tuple.url."""
        remote = MagicMock()
        if name is not None:
            remote.tuple.name = name
        if url is not None:
            remote.tuple.url = url
        return remote

    @staticmethod
    def _make_mock_alt(remote_name):
        """Build and return a mock submodule alternate with the given remote_name."""
        alt = MagicMock()
        alt.remote_name = remote_name
        return alt

    @staticmethod
    def _make_combo_root(elements):
        """Build and return a mock combo root whose iter() yields the given elements."""
        combo_root = MagicMock()
        combo_root.iter.return_value = elements
        return combo_root

    def _setup_combo_with_patchset(self, manifest_instance):
        """Populate manifest_instance with one combo and one patchset; return the PatchSet tuple."""
        ps = self._make_patchset_tuple(PATCHSET_NAME, REMOTE_NAME)
        mock_src = self._make_mock_source(patch_set=PATCHSET_NAME, remote_name=REMOTE_NAME)
        manifest_instance._combo_sources = {COMBO_NAME: [mock_src]}
        manifest_instance._patch_sets = {(PATCHSET_NAME, REMOTE_NAME): ps}
        return ps

    def _setup_patchset_with_ops(self, manifest_instance, operations):
        """Populate manifest_instance with one patchset and given operations; return the PatchSet tuple."""
        ps = self._make_patchset_tuple(PATCHSET_NAME, REMOTE_NAME)
        manifest_instance._patch_sets = {(PATCHSET_NAME, REMOTE_NAME): ps}
        manifest_instance._patch_set_operations = {
            (PATCHSET_NAME, REMOTE_NAME): operations
        }
        return ps

    @staticmethod
    def _make_valid_repo_source(remote_name=None, root=None, remote_url=None, commit=None, branch=None):
        """Build and return a RepoSource-like mock with the given fields."""
        src = MagicMock()
        src.remote_name = remote_name or REMOTE_NAME
        src.root = root or ROOT_PATH
        src.remote_url = remote_url or REMOTE_URL
        src.commit = commit or COMMIT
        src.branch = branch or BRANCH
        src.tag = None
        src.patch_set = None
        src.sparse = False
        src.enable_submodule = False
        return src

    def test_validate_repo_local_root_raises_for_single_component_path(self):
        """When repo_local_root has only one path component, must raise ValueError."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        with pytest.raises(ValueError) as exc_info:
            manifest_mod._validate_repo_local_root_or_raise(INVALID_REPO_PATH)
        assert str(exc_info.value) == manifest_mod.INVALID_REPO_PATH_ERROR.format(INVALID_REPO_PATH)

    def test_validate_repo_local_root_does_not_raise_for_multi_component_path(self):
        """When repo_local_root has multiple path components, must not raise."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        manifest_mod._validate_repo_local_root_or_raise(NESTED_REPO)

    def test_get_remote_returns_remote_object_when_found(self, manifest_instance):
        """When remote_name exists in _remotes, must return the corresponding remote object."""
        mock_remote = self._make_mock_remote()
        manifest_instance._remotes = {REMOTE_NAME: mock_remote}
        assert manifest_instance.get_remote(REMOTE_NAME) is mock_remote

    def test_get_remote_returns_none_when_not_found(self, manifest_instance):
        """When remote_name is not in _remotes, must return None."""
        assert manifest_instance.get_remote(UPSTREAM) is None

    def test_get_repo_sources_returns_tuple_list_when_combo_found(self, manifest_instance):
        """When combo_name is in _combo_sources, must return tuples of that combo's sources."""
        mock_src = self._make_mock_source()
        manifest_instance._combo_sources = {COMBO_NAME: [mock_src]}
        result = manifest_instance.get_repo_sources(COMBO_NAME)
        assert result == [mock_src.tuple]

    def test_get_repo_sources_returns_default_combo_sources_for_pin_prefix(self, manifest_instance):
        """When combo_name starts with 'Pin:', must return sources of the default combo."""
        mock_src = self._make_mock_source()
        manifest_instance._combo_sources = {BRANCH: [mock_src]}
        manifest_instance._general_config = MagicMock()
        manifest_instance._general_config.tuple.default_combo = BRANCH
        result = manifest_instance.get_repo_sources(PIN_PREFIX_COMBO)
        assert result == [mock_src.tuple]

    def test_get_repo_sources_raises_value_error_when_combo_not_found(self, manifest_instance):
        """When combo_name is not in _combo_sources and not a Pin prefix, must raise ValueError."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        with pytest.raises(ValueError) as exc_info:
            manifest_instance.get_repo_sources(UNKNOWN)
        assert str(exc_info.value) == manifest_mod.COMBO_INVALIDINPUT_ERROR.format(UNKNOWN)

    def test_get_parent_of_nested_repo_returns_direct_parent(self, manifest_instance):
        """When a source matches the direct parent directory, must return that source."""
        mock_src = MagicMock()
        mock_src.root = PARENT_REPO
        result = manifest_instance.get_parent_of_nested_repo([mock_src], NESTED_REPO)
        assert result is mock_src

    def test_get_combo_element_returns_deepcopy_when_found(self, manifest_instance, mock_et):
        """When a Combination with the given name exists in the tree, must return a deepcopy."""
        mock_elem = MagicMock()
        mock_elem.attrib = {ATTRIB_NAME: COMBO_NAME}
        mock_et.return_value.find.return_value = self._make_combo_root([mock_elem])
        with patch('{}.{}'.format(self.__class__.manifest_module, METHOD_COPY_DEEPCOPY), return_value=mock_elem):
            result = manifest_instance.get_combo_element(COMBO_NAME)
        assert result is mock_elem

    def test_get_combo_element_raises_value_error_when_not_found(self, manifest_instance, mock_et):
        """When no Combination with the given name exists in the tree, must raise ValueError."""
        mock_et.return_value.find.return_value = self._make_combo_root([])
        with pytest.raises(ValueError) as exc_info:
            manifest_instance.get_combo_element(UNKNOWN)
        assert UNKNOWN in str(exc_info.value)

    def test_get_submodule_init_paths_returns_all_when_no_filters(self, manifest_instance):
        """When both remote_name and combo are None, must return tuples for all submodule entries."""
        e1 = self._make_mock_submodule_entry(REMOTE_NAME)
        manifest_instance._submodule_init_list = [e1]
        result = manifest_instance.get_submodule_init_paths()
        assert result == [e1.tuple]

    def test_get_submodule_init_paths_filters_by_remote_name(self, manifest_instance):
        """When only remote_name is given, must return tuples only for entries matching that remote."""
        e1 = self._make_mock_submodule_entry(REMOTE_NAME)
        e2 = self._make_mock_submodule_entry(UPSTREAM)
        manifest_instance._submodule_init_list = [e1, e2]
        result = manifest_instance.get_submodule_init_paths(remote_name=REMOTE_NAME)
        assert result == [e1.tuple]

    def test_get_submodule_init_paths_filters_by_combo(self, manifest_instance):
        """When only combo is given, must return tuples for entries matching that combo or with no combo."""
        e_match = self._make_mock_submodule_entry(REMOTE_NAME, combo=COMBO_NAME)
        e_no_combo = self._make_mock_submodule_entry(REMOTE_NAME, combo=None)
        e_other = self._make_mock_submodule_entry(REMOTE_NAME, combo=UNKNOWN)
        manifest_instance._submodule_init_list = [e_match, e_no_combo, e_other]
        result = manifest_instance.get_submodule_init_paths(combo=COMBO_NAME)
        assert e_match.tuple in result
        assert e_no_combo.tuple in result
        assert e_other.tuple not in result

    def test_get_submodule_init_paths_filters_by_remote_and_combo(self, manifest_instance):
        """When both remote_name and combo are given, must return entries matching both filters."""
        e_match = self._make_mock_submodule_entry(REMOTE_NAME, combo=COMBO_NAME)
        e_wrong_remote = self._make_mock_submodule_entry(UPSTREAM, combo=COMBO_NAME)
        manifest_instance._submodule_init_list = [e_match, e_wrong_remote]
        result = manifest_instance.get_submodule_init_paths(
            remote_name=REMOTE_NAME, combo=COMBO_NAME
        )
        assert result == [e_match.tuple]

    def test_get_patchset_returns_patchset_when_found(self, manifest_instance):
        """When (name, remote) exists in _patch_sets, must return the corresponding PatchSet."""
        ps = self._make_patchset_tuple(PATCHSET_NAME, REMOTE_NAME)
        manifest_instance._patch_sets = {(PATCHSET_NAME, REMOTE_NAME): ps}
        result = manifest_instance.get_patchset(PATCHSET_NAME, REMOTE_NAME)
        assert result == ps

    def test_get_patchset_raises_key_error_when_not_found(self, manifest_instance):
        """When (name, remote) does not exist in _patch_sets, must raise KeyError."""
        with pytest.raises(KeyError) as exc_info:
            manifest_instance.get_patchset(UNKNOWN, REMOTE_NAME)
        assert UNKNOWN in str(exc_info.value)

    def test_get_patchsets_for_combo_raises_key_error_when_no_patchsets_in_combo(self, manifest_instance):
        """When the specified combo has no sources with a patchset, must raise KeyError."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        mock_src = self._make_mock_source(patch_set=None)
        manifest_instance._combo_sources = {COMBO_NAME: [mock_src]}
        with pytest.raises(KeyError) as exc_info:
            manifest_instance.get_patchsets_for_combo(combo=COMBO_NAME)
        assert manifest_mod.NO_PATCHSET_IN_COMBO.format(COMBO_NAME) in str(exc_info.value)

    def test_get_patchset_operations_returns_list_when_patchset_found(self, manifest_instance):
        """When (name, remote) is in _patch_sets and there is no circular parent, must return a list containing the operations."""
        mock_ops = [MagicMock()]
        self._setup_patchset_with_ops(manifest_instance, mock_ops)
        result = manifest_instance.get_patchset_operations(PATCHSET_NAME, REMOTE_NAME)
        assert mock_ops in result

    def test_get_patchset_operations_raises_on_circular_dependency(self, manifest_instance):
        """When get_parent_patchset_operations raises RecursionError, must raise ValueError."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        self._setup_patchset_with_ops(manifest_instance, [])
        manifest_instance.get_parent_patchset_operations = MagicMock(side_effect=RecursionError)
        with pytest.raises(ValueError) as exc_info:
            manifest_instance.get_patchset_operations(PATCHSET_NAME, REMOTE_NAME)
        assert str(exc_info.value) == manifest_mod.PATCHSET_PARENT_CIRCULAR_DEPENDENCY

    def test_get_patchset_operations_raises_value_error_when_not_found(self, manifest_instance):
        """When (name, remote) is not in _patch_sets, must raise ValueError with the patchset name."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        with pytest.raises(ValueError) as exc_info:
            manifest_instance.get_patchset_operations(UNKNOWN, REMOTE_NAME)
        assert str(exc_info.value) == manifest_mod.PATCHSET_UNKNOWN_ERROR.format(UNKNOWN, MANIFEST_PATH)

    def test_init_common_collections_initialized(self, manifest_instance):
        """Common collections must be initialized to their empty defaults on construction."""
        assert manifest_instance._remotes == {}
        assert manifest_instance._combinations == {}
        assert manifest_instance._combo_sources == {}
        assert manifest_instance._patch_sets == {}
        assert manifest_instance._patch_set_operations == {}
        assert manifest_instance._submodule_init_list == []
        assert manifest_instance._submodule_alternate_remotes == []

    def test_generate_pin_json_writes_file_with_json_output(self, manifest_instance):
        """generate_pin_json must open the file and write the JSON string representation of the pin tree."""
        dummy_json = {ATTRIB_NAME: TAG_PIN, KEY_CHILDREN: []}
        with patch.object(manifest_instance, METHOD_GENERATE_PIN_ETREE) as mock_etree, \
             patch.object(manifest_instance, METHOD_DFS_TRAVERSE, return_value=dummy_json), \
             patch(BUILTIN_OPEN, mock_open()) as mocked_file:
            mock_root = MagicMock()
            mock_etree.return_value.getroot.return_value = mock_root
            manifest_instance.generate_pin_json(PIN_DESCRIPTION, COMBO_NAME, [], filename=PIN_JSON_PATH)
        mocked_file.assert_called_once_with(PIN_JSON_PATH, FILE_MODE_WRITE)
        mocked_file().write.assert_called_once_with(json.dumps(dummy_json, indent=TWO_ITEMS))

    @pytest.mark.parametrize(PARAM_IS_PIN_FILE, [
        pytest.param(TAG_PIN, True, id=ID_XML_TYPE_PIN),
        pytest.param(TAG_MANIFEST, False, id=ID_XML_TYPE_MANIFEST),
    ])
    def test_is_pin_file(self, manifest_instance, xml_type, expected):
        """When _xml_type is set to the given value, is_pin_file must return the expected boolean."""
        manifest_instance._xml_type = xml_type
        assert manifest_instance.is_pin_file() is expected

    @pytest.mark.parametrize(PARAM_NESTED_REPO_RAISES, [
        pytest.param([], INVALID_REPO_PATH, None, id=ID_NON_NESTED_PATH),
        pytest.param([], NESTED_REPO, None, id=ID_NO_PARENT_FOUND),
    ])
    def test_get_parent_of_nested_repo_raises(self, manifest_instance, sources, path, expected_error):
        """When path is non-nested or no parent source is found, must raise ValueError with the expected message."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        expected_msg = manifest_mod.INVALID_REPO_PATH_ERROR.format(path) if path == INVALID_REPO_PATH else manifest_mod.NO_PARENT_REPO_ERROR.format(path)
        with pytest.raises(ValueError) as exc_info:
            manifest_instance.get_parent_of_nested_repo(sources, path)
        assert str(exc_info.value) == expected_msg

    @pytest.mark.parametrize(PARAM_SUBMODULE_ALTS, [
        pytest.param(REMOTE_NAME, REMOTE_NAME, True, id=ID_ALT_MATCHING),
        pytest.param(UPSTREAM, REMOTE_NAME, False, id=ID_NO_MATCH),
    ])
    def test_get_submodule_alternates_for_remote(self, manifest_instance, alt_remote, query_remote, expect_match):
        """When an alternate's remote_name matches the query, its tuple is returned; otherwise an empty list."""
        mock_alt = self._make_mock_alt(alt_remote)
        manifest_instance._submodule_alternate_remotes = [mock_alt]
        result = manifest_instance.get_submodule_alternates_for_remote(query_remote)
        assert result == ([mock_alt.tuple] if expect_match else [])

    @pytest.mark.parametrize(PARAM_COMBO_ARG, [
        pytest.param(None, id=ID_COMBO_NONE),
        pytest.param(COMBO_NAME, id=ID_COMBO_SPECIFIED),
    ])
    def test_get_patchsets_for_combo_returns_patchset(self, manifest_instance, combo_arg):
        """When combo is None or a valid name, get_patchsets_for_combo must return the patchset for that combo."""
        ps = self._setup_combo_with_patchset(manifest_instance)
        result = manifest_instance.get_patchsets_for_combo(combo=combo_arg)
        assert result[COMBO_NAME] == ps


ATTRIB_PARENT_SHA = 'parentSha'
ATTRIB_FETCH_BRANCH = 'fetchBranch'
ELEMENT_TAG_PATCHSET = 'PatchSet'
OTHER_PATCHSET_NAME = 'other_ps'
ID_NAME_MISSING = 'name_missing'
ID_PARENT_SHA_MISSING = 'parent_sha_missing'
ID_FETCH_BRANCH_MISSING = 'fetch_branch_missing'


class BaseTestPatchSet:

    manifest_module: str = None

    @staticmethod
    def _make_full_element():
        """Build a mock element with all four required patchset attributes."""
        return make_mock_element({
            ATTRIB_REMOTE: REMOTE_NAME,
            ATTRIB_NAME: PATCHSET_NAME,
            ATTRIB_PARENT_SHA: COMMIT,
            ATTRIB_FETCH_BRANCH: BRANCH,
        }, tag=ELEMENT_TAG_PATCHSET)

    def test_parse_required_attribs_returns_all_four_when_all_present(self):
        """When all four required attributes are present, must return the four values."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = self._make_full_element()

        remote, name, parent_sha, fetch_branch = manifest_mod._parse_patchset_required_attribs(element)

        assert remote == REMOTE_NAME
        assert name == PATCHSET_NAME
        assert parent_sha == COMMIT
        assert fetch_branch == BRANCH

    def test_init_sets_all_fields_from_required_attribs(self):
        """When all required attributes are present, __init__ must set all four fields correctly."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = self._make_full_element()

        ps = manifest_mod._PatchSet(element)

        assert ps.remote == REMOTE_NAME
        assert ps.name == PATCHSET_NAME
        assert ps.parentSha == COMMIT
        assert ps.fetchBranch == BRANCH

    def test_eq_returns_true_for_equal_patchsets(self):
        """Two _PatchSet instances with identical attributes must compare as equal."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        ps1 = manifest_mod._PatchSet(self._make_full_element())
        ps2 = manifest_mod._PatchSet(self._make_full_element())

        assert ps1 == ps2

    def test_eq_returns_false_for_different_patchsets(self):
        """Two _PatchSet instances with different attributes must not compare as equal."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        ps1 = manifest_mod._PatchSet(self._make_full_element())
        ps2 = manifest_mod._PatchSet(make_mock_element({
            ATTRIB_REMOTE: REMOTE_NAME,
            ATTRIB_NAME: OTHER_PATCHSET_NAME,
            ATTRIB_PARENT_SHA: COMMIT,
            ATTRIB_FETCH_BRANCH: BRANCH,
        }, tag=ELEMENT_TAG_PATCHSET))

        assert ps1 != ps2

    def test_eq_returns_false_for_non_patchset_type(self):
        """Comparing a _PatchSet to a non-_PatchSet object must return False."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        ps = manifest_mod._PatchSet(self._make_full_element())

        assert ps.__eq__(object()) is False

    def test_tuple_returns_correct_patchset_namedtuple(self):
        """The tuple property must return a PatchSet namedtuple with the correct field values."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        ps = manifest_mod._PatchSet(self._make_full_element())

        result = ps.tuple

        assert result == manifest_mod.PatchSet(
            remote=REMOTE_NAME,
            name=PATCHSET_NAME,
            parent_sha=COMMIT,
            fetch_branch=BRANCH,
        )

    @pytest.mark.parametrize(PARAM_MISSING_ATTRIB, [
        pytest.param(ATTRIB_REMOTE, id=ID_REMOTE_MISSING),
        pytest.param(ATTRIB_NAME, id=ID_NAME_MISSING),
        pytest.param(ATTRIB_PARENT_SHA, id=ID_PARENT_SHA_MISSING),
        pytest.param(ATTRIB_FETCH_BRANCH, id=ID_FETCH_BRANCH_MISSING),
    ])
    def test_parse_required_attribs_raises_key_error_when_missing(self, missing_attrib):
        """When any required attribute is absent, must raise KeyError with the required-attrib message."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        full = {
            ATTRIB_REMOTE: REMOTE_NAME,
            ATTRIB_NAME: PATCHSET_NAME,
            ATTRIB_PARENT_SHA: COMMIT,
            ATTRIB_FETCH_BRANCH: BRANCH,
        }
        del full[missing_attrib]
        element = make_mock_element(full, tag=ELEMENT_TAG_PATCHSET)
        with pytest.raises(KeyError) as exc_info:
            manifest_mod._parse_patchset_required_attribs(element)
        assert manifest_mod.REQUIRED_ATTRIB_ERROR_MSG.split(REQUIRED_ATTRIB_SPLIT_CHAR)[FIRST_ELEMENT_INDEX] in exc_info.value.args[FIRST_ELEMENT_INDEX]


ELEMENT_TAG_CHERRY_PICK = 'CherryPick'
ATTRIB_SHA = 'sha'
ATTRIB_SOURCE_REMOTE = 'sourceRemote'
ATTRIB_SOURCE_BRANCH = 'sourceBranch'
ATTRIB_MERGE_STRATEGY = 'mergeStrategy'
OPS_FILE = 'some_file.patch'
OPS_SHA = 'aabbcc'
OPS_MERGE_STRATEGY = 'ours'
FIELD_SOURCE_REMOTE = 'source_remote'
FIELD_SOURCE_BRANCH = 'source_branch'
FIELD_MERGE_STRATEGY = 'merge_strategy'


class BaseTestPatchSetOperations:

    manifest_module: str = None

    @pytest.fixture
    def full_ops(self):
        """Return a _PatchSetOperations instance with all optional attributes present."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        return manifest_mod._PatchSetOperations(make_mock_element({
            ATTRIB_FILE: OPS_FILE,
            ATTRIB_SHA: OPS_SHA,
            ATTRIB_SOURCE_REMOTE: UPSTREAM,
            ATTRIB_SOURCE_BRANCH: DEV,
            ATTRIB_MERGE_STRATEGY: OPS_MERGE_STRATEGY,
        }, tag=ELEMENT_TAG_CHERRY_PICK))

    def test_init_sets_type_from_element_tag(self):
        """__init__ must set self.type to element.tag."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element({}, tag=ELEMENT_TAG_CHERRY_PICK)

        ops = manifest_mod._PatchSetOperations(element)

        assert ops.type == ELEMENT_TAG_CHERRY_PICK

    def test_init_sets_all_optional_attribs_when_present(self, full_ops):
        """When all optional attributes are present, __init__ must set each field to its value."""
        assert full_ops.file == OPS_FILE
        assert full_ops.sha == OPS_SHA
        assert full_ops.source_remote == UPSTREAM
        assert full_ops.source_branch == DEV
        assert full_ops.merge_strategy == OPS_MERGE_STRATEGY

    def test_tuple_returns_correct_patch_operation_namedtuple(self, full_ops):
        """The tuple property must return a PatchOperation namedtuple with the correct field values."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        assert full_ops.tuple == manifest_mod.PatchOperation(
            type=ELEMENT_TAG_CHERRY_PICK,
            file=OPS_FILE,
            sha=OPS_SHA,
            source_remote=UPSTREAM,
            source_branch=DEV,
            merge_strategy=OPS_MERGE_STRATEGY,
        )

    @pytest.mark.parametrize(PARAM_FIELD_NAME, [
        pytest.param(ATTRIB_FILE, id=ATTRIB_FILE),
        pytest.param(ATTRIB_SHA, id=ATTRIB_SHA),
        pytest.param(FIELD_SOURCE_REMOTE, id=FIELD_SOURCE_REMOTE),
        pytest.param(FIELD_SOURCE_BRANCH, id=FIELD_SOURCE_BRANCH),
        pytest.param(FIELD_MERGE_STRATEGY, id=FIELD_MERGE_STRATEGY),
    ])
    def test_init_optional_attrib_defaults_to_none_when_missing(self, field_name):
        """When any optional attribute is absent, __init__ must set the corresponding field to None."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        ops = manifest_mod._PatchSetOperations(make_mock_element({}, tag=ELEMENT_TAG_CHERRY_PICK))
        assert getattr(ops, field_name) is None


ELEMENT_TAG_PROJECT_INFO = 'ProjectInfo'
CHILD_CODE_NAME = 'CodeName'
CHILD_DESCRIPT = 'Description'
PROJECT_INFO_NAME = 'TestProject'
PROJECT_INFO_DESCRIPT = 'A test project.'
PARAM_REQUIRED_ABSENT = 'missing_child'
ID_CODE_NAME_ABSENT = 'code_name_absent'
ID_DESCRIPT_ABSENT = 'descript_absent'
CHILD_ORG = 'Org'
CHILD_SHORT_NAME = 'ShortName'
CHILD_LEAD_REVIEWERS = 'LeadReviewers'
LEAD = 'lead@example.com'
REVIEWER = 'reviewer@example.com'
ORG = 'Intel'
SHORT_NAME = 'TP'
ATTRIB_ORG = 'org'
ATTRIB_SHORT_NAME = 'short_name'
PARAM_OPTIONAL_PRESENT = 'child_key, value, attr'
PARAM_OPTIONAL_ABSENT = 'attr'
ID_ORG_PRESENT = 'org_present'
ID_SHORT_NAME_PRESENT = 'short_name_present'
ID_ORG_ABSENT = 'org_absent'
ID_SHORT_NAME_ABSENT = 'short_name_absent'
FIELD_CODENAME = 'codename'
FIELD_DEV_LEADS = 'dev_leads'
FIELD_REVIEWERS = 'reviewers'


class BaseTestProjectInfo:

    manifest_module: str = None

    @pytest.fixture
    def required_element(self):
        """Return a fresh mock element with only the required CodeName and Description children."""
        return make_find_map_element(
            find_map={
                CHILD_CODE_NAME: make_text_element(PROJECT_INFO_NAME),
                CHILD_DESCRIPT: make_text_element(PROJECT_INFO_DESCRIPT),
            },
            tag=ELEMENT_TAG_PROJECT_INFO,
        )

    @pytest.fixture
    def required_info(self, required_element):
        """Return a _ProjectInfo instance built from an element with only the required CodeName and Description children."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        return manifest_mod._ProjectInfo(required_element)

    def test_parse_required_fields_returns_codename_and_descript_when_both_present(self, required_element):
        """When CodeName and Description children are present, must return (codename, descript)."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)

        codename, descript = manifest_mod._parse_project_info_required_fields(required_element)

        assert codename == PROJECT_INFO_NAME
        assert descript == PROJECT_INFO_DESCRIPT

    def test_init_sets_codename_and_descript(self, required_info):
        """When required children are present, __init__ must set codename and descript correctly."""
        assert required_info.codename == PROJECT_INFO_NAME
        assert required_info.descript == PROJECT_INFO_DESCRIPT

    def test_init_builds_lead_list_from_dev_lead_children(self):
        """When DevLead child elements are present, __init__ must populate lead_list with their text values."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        lead_mock = make_text_element(LEAD)
        element = make_find_map_element(
            find_map={
                CHILD_CODE_NAME: make_text_element(PROJECT_INFO_NAME),
                CHILD_DESCRIPT: make_text_element(PROJECT_INFO_DESCRIPT),
            },
            dev_leads=[lead_mock],
            tag=ELEMENT_TAG_PROJECT_INFO,
        )

        info = manifest_mod._ProjectInfo(element)

        assert info.lead_list == [LEAD]

    def test_init_sets_lead_list_to_empty_when_no_dev_lead_children(self, required_info):
        """When no DevLead children exist, __init__ must set lead_list to an empty list."""
        assert required_info.lead_list == []

    def test_init_sets_reviewer_list_to_none_when_lead_reviewers_absent(self, required_info):
        """When no LeadReviewers child element exists, __init__ must set reviewer_list to None."""
        assert required_info.reviewer_list is None

    def test_init_sets_reviewer_list_from_lead_reviewers(self):
        """When LeadReviewers with Reviewer children is present, __init__ must populate reviewer_list."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        reviewer_mock = make_text_element(REVIEWER)
        lead_reviewers_mock = MagicMock()
        lead_reviewers_mock.iter.return_value = [reviewer_mock]
        element = make_find_map_element(find_map={
            CHILD_CODE_NAME: make_text_element(PROJECT_INFO_NAME),
            CHILD_DESCRIPT: make_text_element(PROJECT_INFO_DESCRIPT),
            CHILD_LEAD_REVIEWERS: lead_reviewers_mock,
        }, tag=ELEMENT_TAG_PROJECT_INFO)

        info = manifest_mod._ProjectInfo(element)

        assert info.reviewer_list == [REVIEWER]

    def test_tuple_returns_correct_project_info_namedtuple(self):
        """The tuple property must return a ProjectInfo namedtuple with the correct field values."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        lead_mock = make_text_element(LEAD)
        reviewer_mock = make_text_element(REVIEWER)
        lead_reviewers_mock = MagicMock()
        lead_reviewers_mock.iter.return_value = [reviewer_mock]
        find_map = {
            CHILD_CODE_NAME: make_text_element(PROJECT_INFO_NAME),
            CHILD_DESCRIPT: make_text_element(PROJECT_INFO_DESCRIPT),
            CHILD_ORG: make_text_element(ORG),
            CHILD_SHORT_NAME: make_text_element(SHORT_NAME),
            CHILD_LEAD_REVIEWERS: lead_reviewers_mock,
        }
        result = manifest_mod._ProjectInfo(make_find_map_element(find_map=find_map, dev_leads=[lead_mock], tag=ELEMENT_TAG_PROJECT_INFO)).tuple

        assert result == manifest_mod.ProjectInfo(
            codename=PROJECT_INFO_NAME,
            description=PROJECT_INFO_DESCRIPT,
            dev_leads=[LEAD],
            reviewers=[REVIEWER],
            org=ORG,
            short_name=SHORT_NAME,
        )

    @pytest.mark.parametrize(PARAM_REQUIRED_ABSENT, [
        pytest.param(CHILD_CODE_NAME, id=ID_CODE_NAME_ABSENT),
        pytest.param(CHILD_DESCRIPT, id=ID_DESCRIPT_ABSENT),
    ])
    def test_parse_required_fields_raises_when_required_child_absent(self, missing_child):
        """When a required child element is absent, must raise AttributeError."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        find_map = {
            CHILD_CODE_NAME: make_text_element(PROJECT_INFO_NAME),
            CHILD_DESCRIPT: make_text_element(PROJECT_INFO_DESCRIPT),
        }
        del find_map[missing_child]
        element = make_find_map_element(find_map=find_map, tag=ELEMENT_TAG_PROJECT_INFO)
        with pytest.raises(AttributeError):
            manifest_mod._parse_project_info_required_fields(element)

    @pytest.mark.parametrize(PARAM_OPTIONAL_PRESENT, [
        pytest.param(CHILD_ORG, ORG, ATTRIB_ORG, id=ID_ORG_PRESENT),
        pytest.param(CHILD_SHORT_NAME, SHORT_NAME, ATTRIB_SHORT_NAME, id=ID_SHORT_NAME_PRESENT),
    ])
    def test_init_sets_optional_field_when_present(self, child_key, value, attr):
        """When an optional child element is present, __init__ must set the field to its text value."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_find_map_element(find_map={
            CHILD_CODE_NAME: make_text_element(PROJECT_INFO_NAME),
            CHILD_DESCRIPT: make_text_element(PROJECT_INFO_DESCRIPT),
            child_key: make_text_element(value),
        }, tag=ELEMENT_TAG_PROJECT_INFO)

        info = manifest_mod._ProjectInfo(element)

        assert getattr(info, attr) == value

    @pytest.mark.parametrize(PARAM_OPTIONAL_ABSENT, [
        pytest.param(ATTRIB_ORG, id=ID_ORG_ABSENT),
        pytest.param(ATTRIB_SHORT_NAME, id=ID_SHORT_NAME_ABSENT),
    ])
    def test_init_sets_optional_field_to_none_when_absent(self, required_info, attr):
        """When an optional child element is absent, __init__ must set the field to None."""
        assert getattr(required_info, attr) is None


CHILD_PIN_PATH = 'PinPath'
CHILD_DEFAULT_COMBO = 'DefaultCombo'
CHILD_CURR_COMBO = 'CurrentClonedCombo'
CHILD_SOURCE_MANIFEST_REPO = 'SourceManifestRepository'
ATTRIB_MANIFEST_REPO = 'manifest_repo'
PIN_PATH = '/fake/pin.xml'
SOURCE_MANIFEST_REPO = 'edk2-manifest'
FIELD_PIN_PATH = 'pin_path'
FIELD_DEFAULT_COMBO = 'default_combo'
FIELD_CURR_COMBO = 'curr_combo'
FIELD_SOURCE_MANIFEST_REPO = 'source_manifest_repo'
ID_PIN_PATH_ABSENT = 'pin_path_absent'
ID_DEFAULT_COMBO_ABSENT = 'default_combo_absent'
ID_CURR_COMBO_ABSENT = 'curr_combo_absent'
ID_SOURCE_REPO_ABSENT = 'source_manifest_repo_absent'


class BaseTestGeneralConfig:

    manifest_module: str = None

    @pytest.fixture
    def empty_config(self):
        """Return a _GeneralConfig built from an element with no children so all fields default to None."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        return manifest_mod._GeneralConfig(self._make_mock_element({}))

    @staticmethod
    def _make_mock_element(find_map=None):
        """Build a mock XML element whose find() returns values from find_map, or None for absent keys."""
        return make_find_map_element(find_map)

    def _assert_field_present(self, find_map, field_name, expected):
        """Build a _GeneralConfig from an element containing find_map and assert field_name equals expected."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        config = manifest_mod._GeneralConfig(self._make_mock_element(find_map))
        assert getattr(config, field_name) == expected

    def test_init_sets_pin_path_when_present(self):
        """When the PinPath child element is present, __init__ must set self.pin_path to its text value."""
        self._assert_field_present(
            {CHILD_PIN_PATH: make_text_element(PIN_PATH)},
            FIELD_PIN_PATH,
            PIN_PATH,
        )

    def test_init_sets_default_combo_when_present(self):
        """When the DefaultCombo child element is present, __init__ must set self.default_combo to its combination attribute."""
        self._assert_field_present(
            {CHILD_DEFAULT_COMBO: make_attrib_element({ATTRIB_COMBINATION: BRANCH})},
            FIELD_DEFAULT_COMBO,
            BRANCH,
        )

    def test_init_sets_curr_combo_when_present(self):
        """When the CurrentClonedCombo child element is present, __init__ must set self.curr_combo to its combination attribute."""
        self._assert_field_present(
            {CHILD_CURR_COMBO: make_attrib_element({ATTRIB_COMBINATION: DEV})},
            FIELD_CURR_COMBO,
            DEV,
        )

    def test_init_sets_source_manifest_repo_when_present(self):
        """When the SourceManifestRepository child element is present, __init__ must set self.source_manifest_repo to its manifest_repo attribute."""
        self._assert_field_present(
            {CHILD_SOURCE_MANIFEST_REPO: make_attrib_element({ATTRIB_MANIFEST_REPO: SOURCE_MANIFEST_REPO})},
            FIELD_SOURCE_MANIFEST_REPO,
            SOURCE_MANIFEST_REPO,
        )

    def test_tuple_returns_correct_general_config_namedtuple(self):
        """The tuple property must return a GeneralConfig namedtuple with the correct field values."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        find_map = {
            CHILD_PIN_PATH: make_text_element(PIN_PATH),
            CHILD_DEFAULT_COMBO: make_attrib_element({ATTRIB_COMBINATION: BRANCH}),
            CHILD_CURR_COMBO: make_attrib_element({ATTRIB_COMBINATION: DEV}),
            CHILD_SOURCE_MANIFEST_REPO: make_attrib_element({ATTRIB_MANIFEST_REPO: SOURCE_MANIFEST_REPO}),
        }
        result = manifest_mod._GeneralConfig(self._make_mock_element(find_map)).tuple

        assert result == manifest_mod.GeneralConfig(
            default_combo=BRANCH,
            current_combo=DEV,
            pin_path=PIN_PATH,
            source_manifest_repo=SOURCE_MANIFEST_REPO,
        )

    @pytest.mark.parametrize(PARAM_FIELD_NAME, [
        pytest.param(FIELD_PIN_PATH, id=ID_PIN_PATH_ABSENT),
        pytest.param(FIELD_DEFAULT_COMBO, id=ID_DEFAULT_COMBO_ABSENT),
        pytest.param(FIELD_CURR_COMBO, id=ID_CURR_COMBO_ABSENT),
        pytest.param(FIELD_SOURCE_MANIFEST_REPO, id=ID_SOURCE_REPO_ABSENT),
    ])
    def test_init_field_defaults_to_none_when_absent(self, empty_config, field_name):
        """When any optional child element is absent, __init__ must set the corresponding field to None."""
        assert getattr(empty_config, field_name) is None


ATTRIB_OWNER = 'owner'
ATTRIB_REVIEW_TYPE = 'reviewType'
ATTRIB_PR_STRATEGY = 'prStrategy'
ELEMENT_TAG_REMOTE_REPO = 'RemoteRepo'
OWNER = 'Jane Doe'
REVIEW_TYPE = 'gerrit'
PR_STRATEGY = 'squash'
FIELD_REVIEW_TYPE = 'review_type'
FIELD_PR_STRATEGY = 'pr_strategy'
ID_OWNER_ABSENT = 'owner_absent'
ID_REVIEW_TYPE_ABSENT = 'review_type_absent'
ID_PR_STRATEGY_ABSENT = 'pr_strategy_absent'
ID_OWNER_PRESENT = 'owner_present'
ID_REVIEW_TYPE_PRESENT = 'review_type_present'
ID_PR_STRATEGY_PRESENT = 'pr_strategy_present'


class BaseTestRemoteRepo:

    manifest_module: str = None

    @pytest.fixture
    def full_remote_repo(self):
        """Return a _RemoteRepo built from a fully-populated element with all optional attributes set."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        return manifest_mod._RemoteRepo(make_mock_element_with_text(
            attrib={
                ATTRIB_NAME: REMOTE_NAME,
                ATTRIB_OWNER: OWNER,
                ATTRIB_REVIEW_TYPE: REVIEW_TYPE,
                ATTRIB_PR_STRATEGY: PR_STRATEGY,
            },
            text=REMOTE_URL,
            tag=ELEMENT_TAG_REMOTE_REPO,
        ))

    def test_parse_required_attribs_returns_name_and_url_when_name_present(self):
        """When name is present, _parse_remote_repo_required_attribs must return (name, url)."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element_with_text(
            attrib={ATTRIB_NAME: REMOTE_NAME},
            text=REMOTE_URL,
            tag=ELEMENT_TAG_REMOTE_REPO,
        )

        name, url = manifest_mod._parse_remote_repo_required_attribs(element)

        assert name == REMOTE_NAME
        assert url == REMOTE_URL

    def test_parse_required_attribs_raises_key_error_when_name_missing(self):
        """When name is absent, _parse_remote_repo_required_attribs must raise KeyError with the required-attrib message."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element_with_text(attrib={}, text=REMOTE_URL, tag=ELEMENT_TAG_REMOTE_REPO)

        with pytest.raises(KeyError) as exc_info:
            manifest_mod._parse_remote_repo_required_attribs(element)

        assert manifest_mod.REQUIRED_ATTRIB_ERROR_MSG.split(REQUIRED_ATTRIB_SPLIT_CHAR)[FIRST_ELEMENT_INDEX] in exc_info.value.args[FIRST_ELEMENT_INDEX]

    def test_init_sets_name_and_url_from_required_attribs(self):
        """When name is present, __init__ must set self.name and self.url correctly."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element_with_text(
            attrib={ATTRIB_NAME: REMOTE_NAME},
            text=REMOTE_URL,
            tag=ELEMENT_TAG_REMOTE_REPO,
        )

        repo = manifest_mod._RemoteRepo(element)

        assert repo.name == REMOTE_NAME
        assert repo.url == REMOTE_URL

    def test_tuple_returns_correct_remote_repo_namedtuple(self, full_remote_repo):
        """The tuple property must return a RemoteRepo namedtuple with all field values correct."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        result = full_remote_repo.tuple

        assert result == manifest_mod.RemoteRepo(
            name=REMOTE_NAME,
            url=REMOTE_URL,
            owner=OWNER,
            review_type=REVIEW_TYPE,
            pr_strategy=PR_STRATEGY,
        )

    @pytest.mark.parametrize(PARAM_FIELD_AND_EXPECTED, [
        pytest.param(ATTRIB_OWNER, OWNER, id=ID_OWNER_PRESENT),
        pytest.param(FIELD_REVIEW_TYPE, REVIEW_TYPE, id=ID_REVIEW_TYPE_PRESENT),
        pytest.param(FIELD_PR_STRATEGY, PR_STRATEGY, id=ID_PR_STRATEGY_PRESENT),
    ])
    def test_init_sets_optional_attrib_when_present(self, full_remote_repo, field_name, expected_value):
        """When any optional attribute is present, __init__ must set the corresponding field to its value."""
        assert getattr(full_remote_repo, field_name) == expected_value

    @pytest.mark.parametrize(PARAM_FIELD_NAME, [
        pytest.param(ATTRIB_OWNER, id=ID_OWNER_ABSENT),
        pytest.param(FIELD_REVIEW_TYPE, id=ID_REVIEW_TYPE_ABSENT),
        pytest.param(FIELD_PR_STRATEGY, id=ID_PR_STRATEGY_ABSENT),
    ])
    def test_init_optional_attrib_defaults_to_none_when_absent(self, field_name):
        """When any optional attribute is absent, __init__ must set the corresponding field to None."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element_with_text(
            attrib={ATTRIB_NAME: REMOTE_NAME}, text=REMOTE_URL, tag=ELEMENT_TAG_REMOTE_REPO,
        )
        repo = manifest_mod._RemoteRepo(element)
        assert getattr(repo, field_name) is None


ATTRIB_DESTINATION = 'destination'
ATTRIB_DEST_FILE = 'destination_file'
ELEMENT_TAG_CLIENT_GIT_HOOK = 'ClientGitHook'
HOOK_SOURCE = '/scripts/pre-commit.sh'
DEST_PATH = '.git/hooks'
DEST_FILE = 'pre-commit'
FIELD_REMOTE_URL = 'remote_url'
FIELD_DEST_FILE = 'dest_file'
ID_SOURCE_ABSENT = 'source_absent'
ID_DESTINATION_ABSENT = 'destination_absent'
ID_REMOTE_URL_FOUND = 'remote_url_found'
ID_DEST_FILE_PRESENT = 'dest_file_present'


class BaseTestRepoHook:

    manifest_module: str = None

    @pytest.fixture
    def default_remotes(self):
        """Return a remotes dict with a single entry using the class-level constants."""
        return make_mock_remotes()

    @pytest.fixture
    def full_hook(self, default_remotes):
        """Return a _RepoHook built from a full-attribute element and the default remotes."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element({
            ATTRIB_SOURCE: HOOK_SOURCE,
            ATTRIB_DESTINATION: DEST_PATH,
            ATTRIB_REMOTE: REMOTE_NAME,
            ATTRIB_DEST_FILE: DEST_FILE,
        }, tag=ELEMENT_TAG_CLIENT_GIT_HOOK)
        return manifest_mod._RepoHook(element, default_remotes)

    def test_parse_required_attribs_returns_source_and_dest_when_both_present(self):
        """When source and destination are present, must return (source, dest_path) without raising."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element({
            ATTRIB_SOURCE: HOOK_SOURCE,
            ATTRIB_DESTINATION: DEST_PATH,
        }, tag=ELEMENT_TAG_CLIENT_GIT_HOOK)

        source, dest_path = manifest_mod._parse_repo_hook_required_attribs(element)

        assert source == HOOK_SOURCE
        assert dest_path == DEST_PATH

    def test_init_sets_source_and_dest_path(self, full_hook):
        """When all required attributes are present, __init__ must set self.source and self.dest_path correctly."""
        assert full_hook.source == HOOK_SOURCE
        assert full_hook.dest_path == DEST_PATH

    def test_init_sets_remote_url_to_none_when_remote_absent(self):
        """When the remote attribute is absent from the element, __init__ must set self.remote_url to None."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element({
            ATTRIB_SOURCE: HOOK_SOURCE,
            ATTRIB_DESTINATION: DEST_PATH,
        }, tag=ELEMENT_TAG_CLIENT_GIT_HOOK)

        hook = manifest_mod._RepoHook(element, {})

        assert hook.remote_url is None

    def test_init_sets_dest_file_to_none_when_absent(self, default_remotes):
        """When the destination_file attribute is absent, __init__ must set self.dest_file to None."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element({
            ATTRIB_SOURCE: HOOK_SOURCE,
            ATTRIB_DESTINATION: DEST_PATH,
            ATTRIB_REMOTE: REMOTE_NAME,
        }, tag=ELEMENT_TAG_CLIENT_GIT_HOOK)

        hook = manifest_mod._RepoHook(element, default_remotes)

        assert hook.dest_file is None

    def test_tuple_returns_correct_repo_hook_namedtuple(self, full_hook):
        """The tuple property must return a RepoHook namedtuple with the correct field values."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        assert full_hook.tuple == manifest_mod.RepoHook(
            source=HOOK_SOURCE,
            dest_path=DEST_PATH,
            dest_file=DEST_FILE,
            remote_url=REMOTE_URL,
        )

    @pytest.mark.parametrize(PARAM_MISSING_ATTRIB, [
        pytest.param(ATTRIB_SOURCE, id=ID_SOURCE_ABSENT),
        pytest.param(ATTRIB_DESTINATION, id=ID_DESTINATION_ABSENT),
    ])
    def test_parse_required_attribs_raises_key_error_when_missing(self, missing_attrib):
        """When any required attribute is absent, must raise KeyError with the required-attrib message."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        full = {
            ATTRIB_SOURCE: HOOK_SOURCE,
            ATTRIB_DESTINATION: DEST_PATH,
        }
        del full[missing_attrib]
        element = make_mock_element(full, tag=ELEMENT_TAG_CLIENT_GIT_HOOK)
        with pytest.raises(KeyError) as exc_info:
            manifest_mod._parse_repo_hook_required_attribs(element)
        assert manifest_mod.REQUIRED_ATTRIB_ERROR_MSG.split(REQUIRED_ATTRIB_SPLIT_CHAR)[FIRST_ELEMENT_INDEX] in exc_info.value.args[FIRST_ELEMENT_INDEX]

    @pytest.mark.parametrize(PARAM_FIELD_AND_EXPECTED, [
        pytest.param(FIELD_REMOTE_URL, REMOTE_URL, id=ID_REMOTE_URL_FOUND),
        pytest.param(FIELD_DEST_FILE, DEST_FILE, id=ID_DEST_FILE_PRESENT),
    ])
    def test_init_sets_optional_field_when_present(self, full_hook, field_name, expected_value):
        """When the optional attribute is present and resolved, __init__ must set the corresponding field to its value."""
        assert getattr(full_hook, field_name) == expected_value


ATTRIB_VENV_ENABLE = 'venv_enable'
ELEMENT_TAG_COMBINATION = 'Combination'
COMBINATION_NAME = 'TestCombo'
COMBO_DESCRIPTION = 'A test combination'
PARAM_MINIMAL_FIELD = '{}, {}'.format(PARAM_FIELD_NAME, PARAM_EXPECTED)
PARAM_BOOL_FLAG = 'attrib_name, attrib_value, {}, {}'.format(PARAM_FIELD_NAME, PARAM_EXPECTED)
ID_NAME_SET = 'name_set'
ID_DESCRIPTION_ABSENT = 'description_absent'
ID_ARCHIVED_TRUE_LOWER = 'archived_true_lower'
ID_ARCHIVED_FALSE_LOWER = 'archived_false_lower'
ID_ARCHIVED_MISSING = 'archived_missing'
ID_ARCHIVED_TRUE_UPPER = 'archived_true_upper'
ID_VENV_TRUE = 'venv_true'
ID_VENV_FALSE = 'venv_false'
ID_VENV_MISSING = 'venv_missing'


class BaseTestCombination:

    manifest_module: str = None

    @pytest.fixture
    def required_element(self):
        """Return a fresh mock element with only the required name attribute."""
        return make_mock_element({ATTRIB_NAME: COMBINATION_NAME}, tag=ELEMENT_TAG_COMBINATION)

    def test_parse_required_attribs_returns_name_when_present(self, required_element):
        """When name is present, _parse_combination_required_attribs must return the name string."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        name = manifest_mod._parse_combination_required_attribs(required_element)

        assert name == COMBINATION_NAME

    def test_parse_required_attribs_raises_key_error_when_name_missing(self):
        """When name is absent, _parse_combination_required_attribs must raise KeyError with the required-attrib message."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element({}, tag=ELEMENT_TAG_COMBINATION)

        with pytest.raises(KeyError) as exc_info:
            manifest_mod._parse_combination_required_attribs(element)

        assert manifest_mod.REQUIRED_ATTRIB_ERROR_MSG.split(REQUIRED_ATTRIB_SPLIT_CHAR)[FIRST_ELEMENT_INDEX] in exc_info.value.args[FIRST_ELEMENT_INDEX]

    def test_init_sets_description_when_present(self):
        """When the description attribute is present, __init__ must set self.description to its value."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element({
            ATTRIB_NAME: COMBINATION_NAME,
            ATTRIB_DESCRIPTION: COMBO_DESCRIPTION,
        }, tag=ELEMENT_TAG_COMBINATION)

        combo = manifest_mod._Combination(element)

        assert combo.description == COMBO_DESCRIPTION

    def test_tuple_returns_correct_combination_namedtuple(self):
        """The tuple property must return a Combination namedtuple with name, description, and venv_enable."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element({
            ATTRIB_NAME: COMBINATION_NAME,
            ATTRIB_DESCRIPTION: COMBO_DESCRIPTION,
            ATTRIB_VENV_ENABLE: ATTRIB_BOOL_TRUE,
        }, tag=ELEMENT_TAG_COMBINATION)
        combo = manifest_mod._Combination(element)

        result = combo.tuple

        assert result == manifest_mod.Combination(
            name=COMBINATION_NAME,
            description=COMBO_DESCRIPTION,
            venv_enable=True,
        )

    @pytest.mark.parametrize(PARAM_MINIMAL_FIELD, [
        pytest.param(ATTRIB_NAME, COMBINATION_NAME, id=ID_NAME_SET),
        pytest.param(ATTRIB_DESCRIPTION, None, id=ID_DESCRIPTION_ABSENT),
    ])
    def test_init_sets_field_on_minimal_element(self, required_element, field_name, expected):
        """On an element with only the required name attribute, each field must equal the expected value after __init__."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        combo = manifest_mod._Combination(required_element)
        assert getattr(combo, field_name) == expected

    @pytest.mark.parametrize(PARAM_BOOL_FLAG, [
        pytest.param(ATTRIB_ARCHIVED, ATTRIB_BOOL_TRUE, ATTRIB_ARCHIVED, True, id=ID_ARCHIVED_TRUE_LOWER),
        pytest.param(ATTRIB_ARCHIVED, ATTRIB_BOOL_FALSE, ATTRIB_ARCHIVED, False, id=ID_ARCHIVED_FALSE_LOWER),
        pytest.param(ATTRIB_ARCHIVED, None, ATTRIB_ARCHIVED, False, id=ID_ARCHIVED_MISSING),
        pytest.param(ATTRIB_ARCHIVED, ARCHIVED_TRUE_UPPER, ATTRIB_ARCHIVED, True, id=ID_ARCHIVED_TRUE_UPPER),
        pytest.param(ATTRIB_VENV_ENABLE, ATTRIB_BOOL_TRUE, ATTRIB_VENV_ENABLE, True, id=ID_VENV_TRUE),
        pytest.param(ATTRIB_VENV_ENABLE, ATTRIB_BOOL_FALSE, ATTRIB_VENV_ENABLE, False, id=ID_VENV_FALSE),
        pytest.param(ATTRIB_VENV_ENABLE, None, ATTRIB_VENV_ENABLE, False, id=ID_VENV_MISSING),
    ])
    def test_init_sets_bool_flag(self, attrib_name, attrib_value, field_name, expected):
        """Each combination of attrib_name/attrib_value must produce the expected boolean on the named field."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        attrib = {ATTRIB_NAME: COMBINATION_NAME}
        if attrib_value is not None:
            attrib[attrib_name] = attrib_value
        element = make_mock_element(attrib, tag=ELEMENT_TAG_COMBINATION)
        combo = manifest_mod._Combination(element)
        assert getattr(combo, field_name) is expected


ATTRIB_LOCAL_ROOT = 'localRoot'
ELEMENT_TAG_SOURCE = 'Source'
LOCAL_ROOT = 'MyRepo'
ATTRIB_BRANCH = 'branch'
ATTRIB_COMMIT = 'commit'
ATTRIB_TAG = 'tag'
ATTRIB_PATCH_SET = 'patchSet'
ATTRIB_ENABLE_SUB_LEGACY = 'enable_submodule'
ATTRIB_VENV_CFG = 'venv_cfg'
TAG = 'v1.0.0'
PATCH_SET = 'ps-debug'
VENV_CFG = 'venv.cfg'
FIELD_PATCH_SET = 'patch_set'
FIELD_ENABLE_SUB = 'enableSub'
PARAM_PARSE_RAISES = 'attrib, remotes'
PARAM_PATCH_SET_COMBO = 'ref_attrib_key, ref_attrib_val'
ID_LOCAL_ROOT_MISSING = 'local_root_missing'
ID_REMOTE_ATTRIB_MISSING = 'remote_attrib_missing'
ID_REMOTE_NOT_IN_REMOTES = 'remote_not_in_remotes'
ID_COMMIT_PRESENT = 'commit_present'
ID_TAG_PRESENT = 'tag_present'
ID_ENABLE_SUB_LEGACY_COMPAT = 'enable_sub_legacy_compat'
ID_VENV_CFG_PRESENT = 'venv_cfg_present'
ID_COMMIT_ABSENT = 'commit_absent'
ID_TAG_ABSENT = 'tag_absent'
ID_PATCH_SET_ABSENT = 'patch_set_absent'
ID_VENV_CFG_ABSENT = 'venv_cfg_absent'
ID_PATCH_SET_WITH_BRANCH = 'patch_set_with_branch'
ID_PATCH_SET_WITH_COMMIT = 'patch_set_with_commit'
ID_PATCH_SET_WITH_TAG = 'patch_set_with_tag'
ATTRIB_SPARSE = 'sparseCheckout'
ATTRIB_ENABLE_SUB = 'enableSubmodule'
ATTRIB_BLOBLESS = 'blobless'
ATTRIB_TREELESS = 'treeless'
NESTED_LOCAL_ROOT = 'parent/{}'.format(LOCAL_ROOT)
FIELD_SPARSE = 'sparse'
FIELD_NESTED_REPO = 'nested_repo'
PARAM_BOOL_FIELD = 'extra, field_name, expected'
ID_SPARSE_MISSING = 'sparse_missing'
ID_SPARSE_TRUE = 'sparse_true'
ID_SPARSE_FALSE = 'sparse_false'
ID_ENABLE_SUB_MISSING = 'enable_sub_missing'
ID_ENABLE_SUB_TRUE = 'enable_sub_true'
ID_ENABLE_SUB_FALSE = 'enable_sub_false'
ID_BLOBLESS_MISSING = 'blobless_missing'
ID_BLOBLESS_TRUE = 'blobless_true'
ID_BLOBLESS_FALSE = 'blobless_false'
ID_TREELESS_MISSING = 'treeless_missing'
ID_TREELESS_TRUE = 'treeless_true'
ID_TREELESS_FALSE = 'treeless_false'
ID_NESTED_REPO_TRUE = 'nested_repo_true'
ID_NESTED_REPO_FALSE = 'nested_repo_false'


class BaseTestRepoSource:

    manifest_module: str = None

    @pytest.fixture
    def base_attrib(self):
        """Return minimum valid attributes dict (mutable - tests can modify as needed)."""
        return {
            ATTRIB_LOCAL_ROOT: LOCAL_ROOT,
            ATTRIB_REMOTE: REMOTE_NAME,
            ATTRIB_BRANCH: BRANCH,
        }

    @pytest.fixture
    def default_remotes(self):
        """Return a remotes dict with a single entry."""
        return make_mock_remotes()

    @pytest.fixture
    def base_source(self, base_attrib, default_remotes):
        """Return a _RepoSource built from minimum valid attributes."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element(base_attrib, tag=ELEMENT_TAG_SOURCE)
        return manifest_mod._RepoSource(element, default_remotes)

    @staticmethod
    def _make_single_ref_element(ref_key, ref_val):
        """Build a mock element with only the required fields (localRoot, remote) and one ref attribute."""
        return make_mock_element({
            ATTRIB_LOCAL_ROOT: LOCAL_ROOT,
            ATTRIB_REMOTE: REMOTE_NAME,
            ref_key: ref_val,
        }, tag=ELEMENT_TAG_SOURCE)

    def test_parse_required_attribs_returns_all_three_when_all_present(self, default_remotes):
        """When all required attributes and the remote key are present, must return (root, remote_name, remote_url)."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element({
            ATTRIB_LOCAL_ROOT: LOCAL_ROOT,
            ATTRIB_REMOTE: REMOTE_NAME,
        }, tag=ELEMENT_TAG_SOURCE)

        root, remote_name, remote_url = manifest_mod._parse_repo_source_required_attribs(element, default_remotes)

        assert root == LOCAL_ROOT
        assert remote_name == REMOTE_NAME
        assert remote_url == REMOTE_URL

    def test_init_sets_all_required_fields(self, base_source):
        """When all required attributes are present, __init__ must set root, remote_name, and remote_url correctly."""
        assert base_source.root == LOCAL_ROOT
        assert base_source.remote_name == REMOTE_NAME
        assert base_source.remote_url == REMOTE_URL

    def test_init_sets_branch_when_present(self, base_source):
        """When the branch attribute is present, __init__ must set self.branch to its value."""
        assert base_source.branch == BRANCH

    def test_init_sets_branch_to_none_when_absent(self):
        """When the branch attribute is absent, __init__ must set self.branch to None."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = self._make_single_ref_element(ATTRIB_COMMIT, COMMIT)
        assert manifest_mod._RepoSource(element, make_mock_remotes()).branch is None

    def test_init_sets_patch_set_when_present(self):
        """When the patchSet attribute is present and no other ref is given, __init__ must set self.patch_set to its value."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = self._make_single_ref_element(ATTRIB_PATCH_SET, PATCH_SET)
        assert manifest_mod._RepoSource(element, make_mock_remotes()).patch_set == PATCH_SET

    def test_init_raises_key_error_when_no_ref_specified(self):
        """When none of branch, commit, tag, or patchSet is specified, __init__ must raise KeyError."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element({ATTRIB_LOCAL_ROOT: LOCAL_ROOT, ATTRIB_REMOTE: REMOTE_NAME}, tag=ELEMENT_TAG_SOURCE)

        with pytest.raises(KeyError) as exc_info:
            manifest_mod._RepoSource(element, make_mock_remotes())

        assert exc_info.value.args[FIRST_ELEMENT_INDEX] == manifest_mod.ATTRIBUTE_MISSING_ERROR

    def test_tuple_returns_correct_repo_source_namedtuple(self, base_attrib, default_remotes):
        """The tuple property must return a RepoSource namedtuple with all field values correct."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        base_attrib.update({
            ATTRIB_COMMIT:      COMMIT,
            ATTRIB_SPARSE:      ATTRIB_BOOL_TRUE,
            ATTRIB_ENABLE_SUB:  ATTRIB_BOOL_FALSE,
            ATTRIB_VENV_CFG:    VENV_CFG,
            ATTRIB_BLOBLESS:    ATTRIB_BOOL_FALSE,
            ATTRIB_TREELESS:    ATTRIB_BOOL_FALSE,
        })
        element = make_mock_element(base_attrib, tag=ELEMENT_TAG_SOURCE)
        rs = manifest_mod._RepoSource(element, default_remotes)

        result = rs.tuple

        assert result == manifest_mod.RepoSource(
            root=LOCAL_ROOT,
            remote_name=REMOTE_NAME,
            remote_url=REMOTE_URL,
            branch=BRANCH,
            commit=COMMIT,
            sparse=True,
            enable_submodule=False,
            tag=None,
            venv_cfg=VENV_CFG,
            patch_set=None,
            blobless=False,
            treeless=False,
            nested_repo=False,
        )

    @pytest.mark.parametrize(PARAM_PARSE_RAISES, [
        pytest.param(
            {ATTRIB_REMOTE: REMOTE_NAME}, make_mock_remotes(),
            id=ID_LOCAL_ROOT_MISSING,
        ),
        pytest.param(
            {ATTRIB_LOCAL_ROOT: LOCAL_ROOT}, make_mock_remotes(),
            id=ID_REMOTE_ATTRIB_MISSING,
        ),
        pytest.param(
            {ATTRIB_LOCAL_ROOT: LOCAL_ROOT, ATTRIB_REMOTE: REMOTE_NAME}, {}, id=ID_REMOTE_NOT_IN_REMOTES, ),
    ])
    def test_parse_required_attribs_raises_key_error(self, attrib, remotes):
        """When any required attribute or remote lookup is missing, must raise KeyError with the required-attrib message."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element(attrib, tag=ELEMENT_TAG_SOURCE)

        with pytest.raises(KeyError) as exc_info:
            manifest_mod._parse_repo_source_required_attribs(element, remotes)

        assert manifest_mod.REQUIRED_ATTRIB_ERROR_MSG.split(REQUIRED_ATTRIB_SPLIT_CHAR)[FIRST_ELEMENT_INDEX] in exc_info.value.args[FIRST_ELEMENT_INDEX]

    @pytest.mark.parametrize(PARAM_ATTRIB_VAL_FIELD_EXPECTED, [
        pytest.param(ATTRIB_COMMIT, COMMIT, ATTRIB_COMMIT, COMMIT, id=ID_COMMIT_PRESENT),
        pytest.param(ATTRIB_TAG, TAG, ATTRIB_TAG, TAG, id=ID_TAG_PRESENT),
        pytest.param(ATTRIB_ENABLE_SUB_LEGACY, ATTRIB_BOOL_TRUE, FIELD_ENABLE_SUB, True, id=ID_ENABLE_SUB_LEGACY_COMPAT),
        pytest.param(ATTRIB_VENV_CFG, VENV_CFG, ATTRIB_VENV_CFG, VENV_CFG, id=ID_VENV_CFG_PRESENT),
    ])
    def test_init_sets_optional_field_when_present(self, base_attrib, default_remotes, attrib_key, attrib_val, field_name, expected):
        """When an optional attribute is present, __init__ must set the corresponding field to its value."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        base_attrib[attrib_key] = attrib_val
        element = make_mock_element(base_attrib, tag=ELEMENT_TAG_SOURCE)
        rs = manifest_mod._RepoSource(element, default_remotes)
        assert getattr(rs, field_name) == expected

    @pytest.mark.parametrize(PARAM_FIELD_NAME, [
        pytest.param(ATTRIB_COMMIT, id=ID_COMMIT_ABSENT),
        pytest.param(ATTRIB_TAG, id=ID_TAG_ABSENT),
        pytest.param(FIELD_PATCH_SET, id=ID_PATCH_SET_ABSENT),
        pytest.param(ATTRIB_VENV_CFG, id=ID_VENV_CFG_ABSENT),
    ])
    def test_init_sets_optional_field_to_none_when_absent(self, base_source, field_name):
        """When any optional attribute is absent, __init__ must set the corresponding field to None."""
        assert getattr(base_source, field_name) is None

    @pytest.mark.parametrize(PARAM_PATCH_SET_COMBO, [
        pytest.param(ATTRIB_BRANCH, BRANCH, id=ID_PATCH_SET_WITH_BRANCH),
        pytest.param(ATTRIB_COMMIT, COMMIT, id=ID_PATCH_SET_WITH_COMMIT),
        pytest.param(ATTRIB_TAG, TAG, id=ID_PATCH_SET_WITH_TAG),
    ])
    def test_init_raises_value_error_when_patch_set_combined_with_ref(self, default_remotes, ref_attrib_key, ref_attrib_val):
        """When patchSet is specified alongside any other ref attribute, __init__ must raise ValueError."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element({
            ATTRIB_LOCAL_ROOT: LOCAL_ROOT,
            ATTRIB_REMOTE: REMOTE_NAME,
            ATTRIB_PATCH_SET: PATCH_SET,
            ref_attrib_key: ref_attrib_val,
        }, tag=ELEMENT_TAG_SOURCE)

        with pytest.raises(ValueError) as exc_info:
            manifest_mod._RepoSource(element, default_remotes)

        assert str(exc_info.value) == manifest_mod.INVALID_COMBO_DEFINITION_ERROR

    @pytest.mark.parametrize(PARAM_BOOL_FIELD, [
        pytest.param({}, FIELD_SPARSE, False, id=ID_SPARSE_MISSING),
        pytest.param({ATTRIB_SPARSE: ATTRIB_BOOL_TRUE}, FIELD_SPARSE, True, id=ID_SPARSE_TRUE),
        pytest.param({ATTRIB_SPARSE: ATTRIB_BOOL_FALSE}, FIELD_SPARSE, False, id=ID_SPARSE_FALSE),
        pytest.param({}, FIELD_ENABLE_SUB, False, id=ID_ENABLE_SUB_MISSING),
        pytest.param({ATTRIB_ENABLE_SUB: ATTRIB_BOOL_TRUE}, FIELD_ENABLE_SUB, True, id=ID_ENABLE_SUB_TRUE),
        pytest.param({ATTRIB_ENABLE_SUB: ATTRIB_BOOL_FALSE}, FIELD_ENABLE_SUB, False, id=ID_ENABLE_SUB_FALSE),
        pytest.param({}, ATTRIB_BLOBLESS, False, id=ID_BLOBLESS_MISSING),
        pytest.param({ATTRIB_BLOBLESS: ATTRIB_BOOL_TRUE}, ATTRIB_BLOBLESS, True, id=ID_BLOBLESS_TRUE),
        pytest.param({ATTRIB_BLOBLESS: ATTRIB_BOOL_FALSE}, ATTRIB_BLOBLESS, False, id=ID_BLOBLESS_FALSE),
        pytest.param({}, ATTRIB_TREELESS, False, id=ID_TREELESS_MISSING),
        pytest.param({ATTRIB_TREELESS: ATTRIB_BOOL_TRUE}, ATTRIB_TREELESS, True, id=ID_TREELESS_TRUE),
        pytest.param({ATTRIB_TREELESS: ATTRIB_BOOL_FALSE}, ATTRIB_TREELESS, False, id=ID_TREELESS_FALSE),
        pytest.param({ATTRIB_LOCAL_ROOT: NESTED_LOCAL_ROOT}, FIELD_NESTED_REPO, True, id=ID_NESTED_REPO_TRUE),
        pytest.param({}, FIELD_NESTED_REPO, False, id=ID_NESTED_REPO_FALSE),
    ])
    def test_init_sets_bool_field(self, base_attrib, extra, field_name, expected):
        """Each boolean attribute must default to False when absent and map 'true'/'false' to True/False correctly."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        base_attrib.update(extra)
        element = make_mock_element(base_attrib, tag=ELEMENT_TAG_SOURCE)
        rs = manifest_mod._RepoSource(element, make_mock_remotes())
        assert getattr(rs, field_name) is expected


ATTRIB_SPARSE_BY_DEFAULT = 'sparseByDefault'
PARAM_SPARSE_BY_DEFAULT = 'attrib, expected'
ID_SPARSE_BY_DEFAULT_ABSENT = 'sparse_by_default_absent'
ID_SPARSE_BY_DEFAULT_TRUE = 'sparse_by_default_true'
ID_SPARSE_BY_DEFAULT_FALSE = 'sparse_by_default_false'


class BaseTestSparseSettings:

    manifest_module: str = None

    @pytest.mark.parametrize(PARAM_SPARSE_BY_DEFAULT, [
        pytest.param({}, False, id=ID_SPARSE_BY_DEFAULT_ABSENT),
        pytest.param({ATTRIB_SPARSE_BY_DEFAULT: ATTRIB_BOOL_TRUE}, True, id=ID_SPARSE_BY_DEFAULT_TRUE),
        pytest.param({ATTRIB_SPARSE_BY_DEFAULT: ATTRIB_BOOL_FALSE}, False, id=ID_SPARSE_BY_DEFAULT_FALSE),
    ])
    def test_init_sets_sparse_by_default(self, attrib, expected):
        """When sparseByDefault is absent, 'true', or 'false', __init__ must set self.sparse_by_default correctly."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element_with_iter(attrib)
        assert manifest_mod._SparseSettings(element).sparse_by_default is expected

    def test_tuple_returns_correct_sparse_settings_namedtuple(self):
        """The tuple property must return a SparseSettings namedtuple with the correct sparse_by_default value."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element_with_iter({ATTRIB_SPARSE_BY_DEFAULT: ATTRIB_BOOL_TRUE})
        ss = manifest_mod._SparseSettings(element)

        assert ss.tuple == manifest_mod.SparseSettings(sparse_by_default=True)


TAG_ALWAYS_INCLUDE = 'AlwaysInclude'
TAG_ALWAYS_EXCLUDE = 'AlwaysExclude'
COMBINATION = 'mycombo'
INCLUDE_VALUE = 'path/to/include'
EXCLUDE_VALUE = 'path/to/exclude'
INCLUDE_MULTI = 'path/a|path/b'
EXCLUDE_MULTI = 'path/c|path/d'
PIPE_SEPARATOR = '|'
FIELD_ALWAYS_INCLUDE = 'always_include'
FIELD_ALWAYS_EXCLUDE = 'always_exclude'
PARAM_LIST_FIELD = 'tag, text_value, {}, {}'.format(PARAM_FIELD_NAME, PARAM_EXPECTED)
ID_COMBINATION_PRESENT = 'combination_present'
ID_ALWAYS_INCLUDE_SPLIT = 'always_include_split'
ID_ALWAYS_EXCLUDE_SPLIT = 'always_exclude_split'


class BaseTestSparseData:

    manifest_module: str = None

    def _assert_child_list_field(self, tag, text_value, field_name, expected):
        """Build a _SparseData element with one child under tag and assert the named list field equals expected."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        child = make_text_element(text_value)
        element = make_mock_element_with_iter({}, {tag: [child]})
        sd = manifest_mod._SparseData(element)
        assert getattr(sd, field_name) == expected

    def test_all_fields_default_when_absent(self):
        """When all optional attributes and child elements are absent, __init__ must apply all defaults."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        sd = manifest_mod._SparseData(make_empty_element())

        assert sd.combination is None
        assert sd.remote_name is None
        assert sd.always_include == []
        assert sd.always_exclude == []

    def test_tuple_returns_correct_sparse_data_namedtuple(self):
        """The tuple property must return a SparseData namedtuple with all field values correct."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        include_elem = make_text_element(INCLUDE_VALUE)
        exclude_elem = make_text_element(EXCLUDE_VALUE)
        element = make_mock_element_with_iter(
            {ATTRIB_COMBINATION: COMBINATION, ATTRIB_REMOTE: REMOTE_NAME},
            {TAG_ALWAYS_INCLUDE: [include_elem], TAG_ALWAYS_EXCLUDE: [exclude_elem]},
        )
        result = manifest_mod._SparseData(element).tuple

        assert result == manifest_mod.SparseData(
            combination=COMBINATION,
            remote_name=REMOTE_NAME,
            always_include=[INCLUDE_VALUE],
            always_exclude=[EXCLUDE_VALUE],
        )

    @pytest.mark.parametrize(PARAM_ATTRIB_VAL_FIELD_EXPECTED, [
        pytest.param(ATTRIB_COMBINATION, COMBINATION, ATTRIB_COMBINATION, COMBINATION, id=ID_COMBINATION_PRESENT),
        pytest.param(ATTRIB_REMOTE, REMOTE_NAME, FIELD_REMOTE_NAME, REMOTE_NAME, id=ID_REMOTE_NAME_PRESENT),
    ])
    def test_init_sets_optional_attrib_when_present(self, attrib_key, attrib_val, field_name, expected):
        """When an optional attribute is present, __init__ must set the corresponding field to its value."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element_with_iter({attrib_key: attrib_val})
        sd = manifest_mod._SparseData(element)
        assert getattr(sd, field_name) == expected

    @pytest.mark.parametrize(PARAM_LIST_FIELD, [
        pytest.param(TAG_ALWAYS_INCLUDE, INCLUDE_VALUE, FIELD_ALWAYS_INCLUDE, [INCLUDE_VALUE], id=FIELD_ALWAYS_INCLUDE),
        pytest.param(TAG_ALWAYS_EXCLUDE, EXCLUDE_VALUE, FIELD_ALWAYS_EXCLUDE, [EXCLUDE_VALUE], id=FIELD_ALWAYS_EXCLUDE),
    ])
    def test_init_populates_list_field_from_single_child(self, tag, text_value, field_name, expected):
        """When one child element is present, __init__ must append its text to the corresponding list field."""
        self._assert_child_list_field(tag, text_value, field_name, expected)

    @pytest.mark.parametrize(PARAM_LIST_FIELD, [
        pytest.param(TAG_ALWAYS_INCLUDE, INCLUDE_MULTI, FIELD_ALWAYS_INCLUDE, INCLUDE_MULTI.split(PIPE_SEPARATOR), id=ID_ALWAYS_INCLUDE_SPLIT),
        pytest.param(TAG_ALWAYS_EXCLUDE, EXCLUDE_MULTI, FIELD_ALWAYS_EXCLUDE, EXCLUDE_MULTI.split(PIPE_SEPARATOR), id=ID_ALWAYS_EXCLUDE_SPLIT),
    ])
    def test_init_splits_pipe_separated_values(self, tag, text_value, field_name, expected):
        """When a child element contains pipe-separated paths, __init__ must add each path as a separate entry."""
        self._assert_child_list_field(tag, text_value, field_name, expected)


class BaseTestFolderToFolderMappingFolderExclude:

    manifest_module: str = None

    @pytest.fixture
    def full_folder_exclude(self):
        """Return a _FolderToFolderMappingFolderExclude built from an element with EXCLUDE_PATH set."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element_with_iter({ATTRIB_PATH: EXCLUDE_PATH})
        return manifest_mod._FolderToFolderMappingFolderExclude(element)

    def test_path_defaults_to_none_when_absent(self):
        """When the path attribute is absent, __init__ must set self.path to None."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        exc = manifest_mod._FolderToFolderMappingFolderExclude(make_empty_element())

        assert exc.path is None

    def test_path_when_present(self, full_folder_exclude):
        """When the path attribute is present, __init__ must set self.path to its value."""
        assert full_folder_exclude.path == EXCLUDE_PATH

    def test_tuple_returns_correct_folder_to_folder_mapping_folder_exclude_namedtuple(self, full_folder_exclude):
        """The tuple property must return a FolderToFolderMappingFolderExclude namedtuple with the correct path."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        assert full_folder_exclude.tuple == manifest_mod.FolderToFolderMappingFolderExclude(path=EXCLUDE_PATH)


FIELD_PROJECT1_FOLDER = 'project1_folder'
FIELD_PROJECT2_FOLDER = 'project2_folder'
ID_PROJECT1_FOLDER_PRESENT = 'project1_folder_present'
ID_PROJECT2_FOLDER_PRESENT = 'project2_folder_present'


class BaseTestFolderToFolderMappingFolder:

    manifest_module: str = None

    def test_all_fields_default_when_absent(self):
        """When all optional attributes and child elements are absent, __init__ must apply all defaults."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        folder = manifest_mod._FolderToFolderMappingFolder(make_empty_element())

        assert folder.project1_folder is None
        assert folder.project2_folder is None
        assert folder.excludes == []

    def test_init_populates_excludes_from_exclude_children(self):
        """When Exclude children are present, __init__ must create a _FolderToFolderMappingFolderExclude for each."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        exclude_elem = make_mock_element_with_iter({ATTRIB_PATH: EXCLUDE_PATH})
        element = make_mock_element_with_iter({}, {TAG_EXCLUDE: [exclude_elem]})
        folder = manifest_mod._FolderToFolderMappingFolder(element)

        assert len(folder.excludes) == ONE_ITEM
        assert folder.excludes[FIRST_ELEMENT_INDEX].path == EXCLUDE_PATH

    def test_tuple_returns_correct_folder_to_folder_mapping_folder_namedtuple(self):
        """The tuple property must return a FolderToFolderMappingFolder namedtuple with all field values correct."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        exclude_elem = make_mock_element_with_iter({ATTRIB_PATH: EXCLUDE_PATH})
        element = make_mock_element_with_iter(
            {ATTRIB_PROJECT1: PROJECT1_FOLDER, ATTRIB_PROJECT2: PROJECT2_FOLDER},
            {TAG_EXCLUDE: [exclude_elem]},
        )
        result = manifest_mod._FolderToFolderMappingFolder(element).tuple

        assert result.project1_folder == PROJECT1_FOLDER
        assert result.project2_folder == PROJECT2_FOLDER
        assert len(result.excludes) == ONE_ITEM
        assert result.excludes[FIRST_ELEMENT_INDEX].path == EXCLUDE_PATH

    @pytest.mark.parametrize(PARAM_ATTRIB_VALUE_FIELD, [
        pytest.param(ATTRIB_PROJECT1, PROJECT1_FOLDER, FIELD_PROJECT1_FOLDER, id=ID_PROJECT1_FOLDER_PRESENT),
        pytest.param(ATTRIB_PROJECT2, PROJECT2_FOLDER, FIELD_PROJECT2_FOLDER, id=ID_PROJECT2_FOLDER_PRESENT),
    ])
    def test_init_sets_project_folder_when_present(self, attrib_key, attrib_value, field_name):
        """When a project folder attribute is present, __init__ must set the corresponding field to its value."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element_with_iter(
            {attrib_key: attrib_value},
            {TAG_EXCLUDE: []},
        )
        folder = manifest_mod._FolderToFolderMappingFolder(element)
        assert getattr(folder, field_name) == attrib_value


TAG_FOLDER = 'Folder'
TAG_FILE = 'File'
ID_PROJECT1_PRESENT = 'project1_present'
ID_PROJECT2_PRESENT = 'project2_present'
PARAM_CHILD_SLOT = 'folder_children_count, file_children_count'
ID_FOLDER_CHILD = 'folder_child'
ID_FILE_CHILD = 'file_child'


class BaseTestFolderToFolderMapping:

    manifest_module: str = None

    def _make_folder_child_element(self, project1=None, project2=None):
        """Build a mock element suitable for use as a Folder/File child with optional project attribs and no Exclude children."""
        attrib = {}
        if project1 is not None:
            attrib[ATTRIB_PROJECT1] = project1
        if project2 is not None:
            attrib[ATTRIB_PROJECT2] = project2
        return make_mock_element_with_iter(attrib, {TAG_EXCLUDE: []})

    def _build_mapping_from_children(self, folder_children, file_children):
        """Build a _FolderToFolderMapping from explicit Folder and File child lists."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element_with_iter(
            {},
            {TAG_FOLDER: folder_children, TAG_FILE: file_children},
        )
        return manifest_mod._FolderToFolderMapping(element)

    def test_all_fields_default_when_absent(self):
        """When all optional attributes and child elements are absent, __init__ must apply all defaults."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        mapping = manifest_mod._FolderToFolderMapping(make_empty_element())

        assert mapping.project1 is None
        assert mapping.project2 is None
        assert mapping.remote_name is None
        assert mapping.folders == []

    def test_init_combines_folder_and_file_children(self):
        """When both Folder and File children are present, __init__ must create entries for all of them."""
        folder_child = self._make_folder_child_element(PROJECT1_FOLDER)
        file_child = self._make_folder_child_element(PROJECT2_FOLDER)
        mapping = self._build_mapping_from_children([folder_child], [file_child])

        assert len(mapping.folders) == TWO_ITEMS

    def test_tuple_returns_correct_folder_to_folder_mapping_namedtuple(self):
        """The tuple property must return a FolderToFolderMapping namedtuple with all field values correct."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        folder_child = self._make_folder_child_element(PROJECT1_FOLDER, PROJECT2_FOLDER)
        element = make_mock_element_with_iter(
            {ATTRIB_PROJECT1: PROJECT1_NAME, ATTRIB_PROJECT2: PROJECT2_NAME, ATTRIB_REMOTE: REMOTE_NAME},
            {TAG_FOLDER: [folder_child], TAG_FILE: []},
        )
        result = manifest_mod._FolderToFolderMapping(element).tuple

        assert result.project1 == PROJECT1_NAME
        assert result.project2 == PROJECT2_NAME
        assert result.remote_name == REMOTE_NAME
        assert len(result.folders) == ONE_ITEM

    @pytest.mark.parametrize(PARAM_ATTRIB_VALUE_FIELD, [
        pytest.param(ATTRIB_PROJECT1, PROJECT1_NAME, ATTRIB_PROJECT1, id=ID_PROJECT1_PRESENT),
        pytest.param(ATTRIB_PROJECT2, PROJECT2_NAME, ATTRIB_PROJECT2, id=ID_PROJECT2_PRESENT),
        pytest.param(ATTRIB_REMOTE, REMOTE_NAME, FIELD_REMOTE_NAME, id=ID_REMOTE_NAME_PRESENT),
    ])
    def test_init_sets_optional_attrib_when_present(self, attrib_key, attrib_value, field_name):
        """When an optional attribute is present, __init__ must set the corresponding field to its value."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element_with_iter({attrib_key: attrib_value})
        mapping = manifest_mod._FolderToFolderMapping(element)
        assert getattr(mapping, field_name) == attrib_value

    @pytest.mark.parametrize(PARAM_CHILD_SLOT, [
        pytest.param(ONE_ITEM, FIRST_ELEMENT_INDEX, id=ID_FOLDER_CHILD),
        pytest.param(FIRST_ELEMENT_INDEX, ONE_ITEM, id=ID_FILE_CHILD),
    ])
    def test_init_populates_folders_from_single_child_tag(self, folder_children_count, file_children_count):
        """When one child element is present under either the Folder or File tag, __init__ must add one _FolderToFolderMappingFolder with the correct project folder values."""
        child = self._make_folder_child_element(PROJECT1_FOLDER, PROJECT2_FOLDER)
        mapping = self._build_mapping_from_children(
            [child] * folder_children_count,
            [child] * file_children_count,
        )

        assert len(mapping.folders) == ONE_ITEM
        assert mapping.folders[FIRST_ELEMENT_INDEX].project1_folder == PROJECT1_FOLDER
        assert mapping.folders[FIRST_ELEMENT_INDEX].project2_folder == PROJECT2_FOLDER


ATTRIB_ORIGINAL_URL = 'originalUrl'
ELEMENT_TAG_SUBMODULE_ALT = 'edk_manifest.SubmoduleAlternateRemote'
ORIGINAL_URL = 'https://original.example.com/repo.git'
ALT_URL = 'https://alt.example.com/repo.git'
FIELD_ALT_URL = 'altUrl'
NO_REMOTE_SPLIT_CHAR = '{'
ID_ORIGINAL_URL_MISSING = 'original_url_missing'


class BaseTestSubmoduleAlternateRemote:

    manifest_module: str = None

    @pytest.fixture
    def default_remotes(self):
        """Return a remotes dict with a single entry using REMOTE_NAME."""
        return make_mock_remotes(REMOTE_NAME)

    @pytest.fixture
    def full_element(self):
        """Return a mock element with all required attributes set for a SubmoduleAlternateRemote."""
        return make_mock_element_with_text(
            {ATTRIB_REMOTE: REMOTE_NAME, ATTRIB_ORIGINAL_URL: ORIGINAL_URL},
            text=ALT_URL,
            tag=ELEMENT_TAG_SUBMODULE_ALT,
        )

    @pytest.fixture
    def full_sar(self, full_element, default_remotes):
        """Return a _SubmoduleAlternateRemote built from an element with all required attributes set."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        return manifest_mod._SubmoduleAlternateRemote(full_element, default_remotes)

    def test_parse_returns_all_fields_when_all_present(self, full_element, default_remotes):
        """When all required attributes are present and the remote is in remotes, must return (remote_name, original_url, alt_url)."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        remote_name, original_url, alt_url = manifest_mod._parse_submodule_alternate_remote_attribs(full_element, default_remotes)

        assert remote_name == REMOTE_NAME
        assert original_url == ORIGINAL_URL
        assert alt_url == ALT_URL

    def test_parse_raises_when_remote_not_in_remotes(self, full_element):
        """When the remote attribute value is not a key in the remotes dict, must raise KeyError with the no-remote message."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        with pytest.raises(KeyError) as exc_info:
            manifest_mod._parse_submodule_alternate_remote_attribs(full_element, {})

        assert manifest_mod.NO_REMOTE_EXISTS_WITH_NAME.split(NO_REMOTE_SPLIT_CHAR)[FIRST_ELEMENT_INDEX] in exc_info.value.args[FIRST_ELEMENT_INDEX]

    def test_init_sets_all_fields(self, full_sar):
        """When all required attributes are valid, __init__ must correctly set remote_name, originalUrl, and altUrl."""
        assert getattr(full_sar, FIELD_REMOTE_NAME) == REMOTE_NAME
        assert getattr(full_sar, ATTRIB_ORIGINAL_URL) == ORIGINAL_URL
        assert getattr(full_sar, FIELD_ALT_URL) == ALT_URL

    def test_tuple_returns_correct_submodule_alternate_remote_namedtuple(self, full_sar):
        """The tuple property must return a SubmoduleAlternateRemote namedtuple with all field values correct."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        assert full_sar.tuple == manifest_mod.SubmoduleAlternateRemote(
            remote_name=REMOTE_NAME,
            original_url=ORIGINAL_URL,
            alternate_url=ALT_URL,
        )

    @pytest.mark.parametrize(FIELD_ATTRIB, [
        pytest.param({ATTRIB_ORIGINAL_URL: ORIGINAL_URL}, id=ID_REMOTE_MISSING),
        pytest.param({ATTRIB_REMOTE: REMOTE_NAME}, id=ID_ORIGINAL_URL_MISSING),
    ])
    def test_parse_raises_when_required_attrib_missing(self, default_remotes, attrib):
        """When any required attribute is absent, must raise KeyError with the required-attrib message."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element_with_text(attrib, tag=ELEMENT_TAG_SUBMODULE_ALT)
        with pytest.raises(KeyError) as exc_info:
            manifest_mod._parse_submodule_alternate_remote_attribs(element, default_remotes)
        assert manifest_mod.REQUIRED_ATTRIB_ERROR_MSG.split(REQUIRED_ATTRIB_SPLIT_CHAR)[FIRST_ELEMENT_INDEX] in exc_info.value.args[FIRST_ELEMENT_INDEX]


ATTRIB_COMBO = 'combo'
ATTRIB_RECURSIVE = 'recursive'
ELEMENT_TAG_SUBMODULE_INIT = 'SubmoduleInitEntry'
SUBMODULE_PATH_VALUE = 'some/submodule/path'
SUBMODULE_COMBO = 'combo_a'
PARAM_RECURSIVE_FLAG = 'attrib_val, {}'.format(PARAM_EXPECTED)
ID_RECURSIVE_TRUE = 'recursive_true'
ID_RECURSIVE_FALSE = 'recursive_false'


class BaseTestSubmoduleInitEntry:

    manifest_module: str = None

    @pytest.fixture
    def full_sie(self):
        """Return a _SubmoduleInitEntry built from an element with required fields only and no optional fields."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        return manifest_mod._SubmoduleInitEntry(self._make_required_element())

    def _make_required_element(self, **extra):
        """Build a mock element with the required remote attrib and SUBMODULE_PATH_VALUE text, plus any extra attribs."""
        attrib = {ATTRIB_REMOTE: REMOTE_NAME}
        attrib.update(extra)
        return make_mock_element_with_text(attrib, text=SUBMODULE_PATH_VALUE, tag=ELEMENT_TAG_SUBMODULE_INIT)

    def test_parse_returns_all_fields_when_all_present(self):
        """When the required remote attribute is present, must return (remote_name, path) with the correct values."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = self._make_required_element()

        remote_name, path = manifest_mod._parse_submodule_init_required_attribs(element)

        assert remote_name == REMOTE_NAME
        assert path == SUBMODULE_PATH_VALUE

    def test_parse_raises_when_remote_missing(self):
        """When the remote attribute is absent, must raise KeyError with the required-attrib message."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = make_mock_element_with_text({}, text=SUBMODULE_PATH_VALUE, tag=ELEMENT_TAG_SUBMODULE_INIT)

        with pytest.raises(KeyError) as exc_info:
            manifest_mod._parse_submodule_init_required_attribs(element)

        assert manifest_mod.REQUIRED_ATTRIB_ERROR_MSG.split(REQUIRED_ATTRIB_SPLIT_CHAR)[FIRST_ELEMENT_INDEX] in exc_info.value.args[FIRST_ELEMENT_INDEX]

    def test_init_sets_all_required_fields(self, full_sie):
        """When all required attributes are present, __init__ must correctly set remote_name and path."""
        assert getattr(full_sie, FIELD_REMOTE_NAME) == REMOTE_NAME
        assert getattr(full_sie, ATTRIB_PATH) == SUBMODULE_PATH_VALUE

    def test_all_optional_fields_default_when_absent(self, full_sie):
        """When all optional attributes are absent, __init__ must set combo to None and recursive to False."""
        assert full_sie.combo is None
        assert full_sie.recursive is False

    def test_combo_when_present(self):
        """When the combo attribute is present, __init__ must set self.combo to its value."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = self._make_required_element(**{ATTRIB_COMBO: SUBMODULE_COMBO})
        sie = manifest_mod._SubmoduleInitEntry(element)
        assert sie.combo == SUBMODULE_COMBO

    def test_tuple_returns_correct_submodule_init_path_namedtuple(self, full_sie):
        """The tuple property must return a SubmoduleInitPath namedtuple with all field values correct."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        assert full_sie.tuple == manifest_mod.SubmoduleInitPath(
            remote_name=REMOTE_NAME,
            combo=None,
            recursive=False,
            path=SUBMODULE_PATH_VALUE,
        )

    @pytest.mark.parametrize(PARAM_RECURSIVE_FLAG, [
        pytest.param(ATTRIB_BOOL_TRUE, True, id=ID_RECURSIVE_TRUE),
        pytest.param(ATTRIB_BOOL_FALSE, False, id=ID_RECURSIVE_FALSE),
    ])
    def test_init_sets_recursive_flag(self, attrib_val, expected):
        """When recursive is 'true' or 'false', __init__ must set self.recursive to the expected boolean."""
        manifest_mod = importlib.import_module(self.__class__.manifest_module)
        element = self._make_required_element(**{ATTRIB_RECURSIVE: attrib_val})
        sie = manifest_mod._SubmoduleInitEntry(element)
        assert sie.recursive is expected
