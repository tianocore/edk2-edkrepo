#!/usr/bin/env python3
#
## @file
# test_base_xml_helper.py
#
# Copyright (c) 2026, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#

import sys
import os
import xml.etree.ElementTree as ET
import pytest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
import edkrepo_manifest_parser.edk_manifest as edk_manifest
import edkrepo_manifest_parser.manifest_parser_unit_test_helpers.helpers as helpers

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
ATTRIB_KEY = 'key'
ATTRIB_VAL = 'val'
TAIL_VALUE = ' world'
ORIGINAL_TEXT = 'original'
PARSE_ERROR_MSG = 'parse error'
INVALID_FILE_MSG = 'invalid file'
PRETTY_FORMAT_INDEX_FIELDS = 'index,expected'
ID_INDEX_ZERO = 'index_zero'
ID_INDEX_NONZERO = 'index_nonzero'
INIT_SUCCESS_FIELDS = 'tag,fileref,xml_types'
ID_MANIFEST_TYPE = 'manifest_type'
ID_PIN_TYPE = 'pin_type'
INDENT_DEPTH_1 = '\n  '
INDENT_DEPTH_2 = '\n    '


class TestBaseXmlHelper:

    @staticmethod
    def _make_mock_tree(tag):
        """Return a mock ElementTree whose getroot().tag equals tag."""
        mock_tree = MagicMock()
        mock_tree.getroot.return_value.tag = tag
        return mock_tree

    @staticmethod
    def _build_node(current_dict):
        """Build an ET node from current_dict via _build_etree_node and return the first child of the parent."""
        instance = object.__new__(edk_manifest.BaseXmlHelper)
        parent = ET.Element(ELEMENT_ROOT_TAG)
        instance._build_etree_node(current_dict, parent)
        return parent[0]

    @staticmethod
    def _assert_init_raises_typeerror(xml_types):
        """Assert that edk_manifest.BaseXmlHelper(MANIFEST_FILE_PATH, xml_types) raises TypeError."""
        with pytest.raises(TypeError):
            edk_manifest.BaseXmlHelper(helpers.MANIFEST_FILE_PATH, xml_types)

    @pytest.fixture
    def mock_et(self):
        """Patch ET.ElementTree for the duration of a test; yields the mock class."""
        with patch('edkrepo_manifest_parser.edk_manifest.ET.ElementTree') as mock:
            yield mock

    @pytest.fixture
    def mock_load_tree(self):
        """Patch edk_manifest.BaseXmlHelper._load_tree for the duration of a test; yields the mock."""
        with patch.object(edk_manifest.BaseXmlHelper, '_load_tree') as mock:
            yield mock

    @pytest.fixture
    def mock_json_open(self):
        """Patch builtins.open and json.load for the duration of a test; yields (mock_open, mock_json_load)."""
        with patch('builtins.open') as mock_open, \
             patch('edkrepo_manifest_parser.edk_manifest.json.load') as mock_json_load:
            yield mock_open, mock_json_load

    @pytest.fixture
    def bare_instance(self):
        """Return a bare edk_manifest.BaseXmlHelper instance bypassing __init__."""
        return object.__new__(edk_manifest.BaseXmlHelper)

    @pytest.mark.parametrize(INIT_SUCCESS_FIELDS, [
        pytest.param(helpers.TAG_MANIFEST, helpers.MANIFEST_FILE_PATH, [helpers.TAG_MANIFEST, helpers.TAG_PIN], id=ID_MANIFEST_TYPE),
        pytest.param(helpers.TAG_PIN, PIN_XML, [helpers.TAG_PIN], id=ID_PIN_TYPE),
    ])
    def test_init_valid_root_tag_sets_attributes(self, mock_load_tree, tag, fileref, xml_types):
        """When _load_tree returns a tree whose root tag is in xml_types, __init__ must set _fileref, _tree, and _xml_type."""
        mock_load_tree.return_value = self._make_mock_tree(tag)

        instance = edk_manifest.BaseXmlHelper(fileref, xml_types)

        assert instance._fileref == fileref
        assert instance._tree is mock_load_tree.return_value
        assert instance._xml_type == tag

    def test_root_tag_not_in_xml_types_raises_typeerror(self, mock_load_tree):
        """When the root tag is not in xml_types, __init__ must raise TypeError."""
        mock_load_tree.return_value = self._make_mock_tree(helpers.UNKNOWN)
        self._assert_init_raises_typeerror([helpers.TAG_MANIFEST, helpers.TAG_PIN])

    def test_load_tree_raises_typeerror_propagates(self, mock_load_tree):
        """When _load_tree raises TypeError, the exception must propagate out of __init__ unchanged."""
        mock_load_tree.side_effect = TypeError(INVALID_FILE_MSG)
        self._assert_init_raises_typeerror([helpers.TAG_MANIFEST])

    def test_valid_json_returns_converted_element_tree(self, bare_instance, mock_json_open):
        """When open and json.load succeed, _json_to_xml must return a tree whose root tag matches the JSON node name and call _pretty_format and _build_etree_node each exactly once."""
        mock_open, mock_json_load = mock_json_open
        mock_json_load.return_value = {helpers.ATTRIB_NAME: helpers.TAG_MANIFEST}

        def mock_build_node(d, p):
            return ET.SubElement(p, helpers.TAG_MANIFEST)

        bare_instance._build_etree_node = MagicMock(side_effect=mock_build_node)
        bare_instance._pretty_format = MagicMock()

        result = bare_instance._json_to_xml(MANIFEST_JSON)

        assert result.getroot().tag == helpers.TAG_MANIFEST
        bare_instance._pretty_format.assert_called_once()
        bare_instance._build_etree_node.assert_called_once()

    def test_dict_with_all_optional_fields(self):
        """When the dict contains name, attrib, text, tail, and children, _build_etree_node must set all fields and recurse."""
        node = self._build_node({
            helpers.ATTRIB_NAME: NODE_PARENT,
            helpers.FIELD_ATTRIB: {ATTRIB_KEY: ATTRIB_VAL},
            NODE_KEY_TEXT: helpers.HELLO,
            NODE_KEY_TAIL: TAIL_VALUE,
            NODE_KEY_CHILDREN: [{helpers.ATTRIB_NAME: NODE_CHILD}],
        })

        assert node.tag == NODE_PARENT
        assert node.attrib == {ATTRIB_KEY: ATTRIB_VAL}
        assert node.text == helpers.HELLO
        assert node.tail == TAIL_VALUE
        assert node[0].tag == NODE_CHILD

    def test_dict_with_name_only(self):
        """When the dict contains only the name key, _build_etree_node must create a SubElement with empty attrib, None text, None tail, and no children."""
        node = self._build_node({helpers.ATTRIB_NAME: NODE_SOLO})

        assert node.tag == NODE_SOLO
        assert node.attrib == {}
        assert node.text is None
        assert node.tail is None
        assert len(node) == 0

    @pytest.mark.parametrize(PRETTY_FORMAT_INDEX_FIELDS, [
        pytest.param(0, INDENT_DEPTH_2, id=ID_INDEX_ZERO),
        pytest.param(1, ORIGINAL_TEXT, id=ID_INDEX_NONZERO),
    ])
    def test_pretty_format_parent_text_by_index(self, bare_instance, index, expected):
        """When called with a given index and depth=2, _pretty_format must set parent.text to the expected value."""
        parent = ET.Element(ELEMENT_ROOT_TAG)
        parent.text = ORIGINAL_TEXT
        child = ET.SubElement(parent, ELEMENT_CHILD_TAG)

        bare_instance._pretty_format(child, parent, index, 2)

        assert parent.text == expected

    def test_no_parent_completes_without_error(self, bare_instance):
        """When called without a parent argument, _pretty_format must complete without raising any exception."""
        root = ET.Element(ELEMENT_ROOT_TAG)

        bare_instance._pretty_format(root)

    def test_pretty_format_recurses_into_children(self, bare_instance):
        """When current has nested children, _pretty_format must recursively set indentation on each ancestor's text."""
        root = ET.Element(ELEMENT_ROOT_TAG)
        child = ET.SubElement(root, NODE_CHILD)
        ET.SubElement(child, NODE_CHILD)

        bare_instance._pretty_format(root)

        assert root.text == INDENT_DEPTH_1
        assert child.text == INDENT_DEPTH_2

    def test_xml_extension_returns_element_tree(self, bare_instance, mock_et):
        """When fileref has a .xml extension, _load_tree must call ET.ElementTree(file=fileref) and return the result."""
        mock_tree = MagicMock()
        mock_et.return_value = mock_tree

        result = bare_instance._load_tree(helpers.MANIFEST_FILE_PATH)

        mock_et.assert_called_once_with(file=helpers.MANIFEST_FILE_PATH)
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
            bare_instance._load_tree(helpers.MANIFEST_FILE_PATH)

    def test_json_parse_error_raises_typeerror(self, bare_instance):
        """When _json_to_xml raises an exception during JSON parsing, _load_tree must catch it and raise TypeError."""
        bare_instance._json_to_xml = MagicMock(side_effect=Exception(PARSE_ERROR_MSG))

        with pytest.raises(TypeError):
            bare_instance._load_tree(MANIFEST_JSON)
