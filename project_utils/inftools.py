#!/usr/bin/env python3
#
## @file
# inftools.py
#
# Copyright (c) 2015- 2019, Intel Corporation. All rights reserved.<BR>
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
import copy

#
# Shared functions to help clean up lines in an INF style file.  This function is
# only intended to clean up lines for parsing as indentation will be lost.
#
def clean_line(line):
    #
    # remove comments
    #
    ret_line = line.strip()
    find_loc = ret_line.find('#')
    if find_loc >= 0:
        ret_line = ret_line[:find_loc].strip()
    if ret_line == '':
        return ret_line

    #
    # Normalize spaces to help when comparing strings
    #
    ret_line = ' '.join(ret_line.split())

    return ret_line

#
# Takes a list of lines and cleans them removing extra spaces and comments
#
def clean_lines(lines):
    ret_lines = []

    #
    # Check to make sure parameters are good
    #
    if not isinstance(lines, list):
        raise ValueError('Input value not a list.')

    #
    # Clean each line and only append the ones with data in them
    #
    for line in lines:
        new_line = clean_line(line)
        if not new_line == '':
            ret_lines.append(new_line)

    return ret_lines

#
# Defines a class for basic processing of any of our EDKII package files
#
# APIs return types list(Success, Failure):
#   Object:  (Object, None)
#   Boolean: (True, False)
#
class BaseInf:
    def __init__(self):
        self.__file_header = []      # All data prior to the firs section
        self.__section_list = []     # Ordered list of sections of the file
        self.__section_dict = {}     # A dictionary sections where the data is the lines of the section

    #
    # Initializes the class with provided file information
    #
    def init_data(self, file_lines):
        #
        # Start a new dictionary and section list assuming that it will have a header
        #
        self.__file_header = []
        self.__section_list = []
        self.__section_dict = {}
        section = None

        #
        # Process all the lines in the file and initialize the dictionary
        #
        for line in file_lines:
            #
            # Clean up line endings and trailing white spaces.
            #
            line = line.rstrip()

            #
            # Create a clean copy of the line for parsing.  The real version will be added to the
            # list if it is not a section
            #
            tmp_line = clean_line(line)

            #
            # Find and add new sections
            #
            if tmp_line.startswith('[') and tmp_line.endswith(']'):
                section = tmp_line.strip('[]').strip()
                if section not in self.__section_dict.keys():
                    self.__section_list.append(section)
                    self.__section_dict[section] = []
                continue
            elif len(self.__section_list) == 0:
                self.__file_header.append(line)
                continue

            #
            # Add line to the section
            #
            self.__section_dict[section].append(line)

    #
    # Returns the header information
    #
    def get_header(self):
        return copy.deepcopy(self.__file_header)

    #
    # Sets the header content
    #
    def set_header(self, Header):
        self.__file_header = copy.deepcopy(Header)

    #
    # Returns an ordered list of sections found in the file.
    #
    def get_sections(self):
        return copy.deepcopy(self.__section_list)

    #
    # Allows a section to be moved to a new relative location in the file
    # - Removes the entry from the current position and inserts it in the new location
    #
    def move_section(self, current_index, new_index):
        if current_index < 0 or new_index < 0:
            raise ValueError('Invalid index provided.')
        if current_index >= len(self.__section_list) or new_index >= len(self.__section_list):
            raise ValueError('Invalid index range provided.')

        #
        # Remove the entry first and then insert it at the new index
        #
        tmp_section = self.__section_list.pop(current_index)
        self.__section_list.insert(new_index, tmp_section)

    #
    # Returns the lines of the specified section
    #
    def get_section_lines(self, section):
        if section not in self.__section_dict.keys():
            raise ValueError('Invalid section name: {}'.format(section))
        return copy.deepcopy(self.__section_dict[section])

    #
    # Adds a new section to the file and any lines specified.
    #
    def add_section(self, section, lines=[]):
        if section in self.__section_dict.keys():
            raise ValueError('Invalid section name: {}'.format(section))
        if not isinstance(lines, list):
            raise ValueError('Invalid parameter type.')
        self.__section_dict[section] = copy.deepcopy(lines)
        self.__section_list.append(section)

    #
    # Removes a section and all associated lines from the file
    #
    def remove_section(self, section):
        if section not in self.__section_dict.keys():
            raise ValueError('Invalid section name: {}'.format(section))
        self.__section_dict.pop(section, [])
        self.__section_list.remove(section)

    #
    # Appends lines to a section
    #
    def append_lines(self, section, lines):
        if section not in self.__section_dict.key():
            raise ValueError('Invalid section name: {}'.format(section))
        if not isinstance(lines, list):
            raise ValueError('Invalid parameter type.')
        self.__section_dict[section].extend(lines)

    #
    # Inserts one or more lines into a section
    #
    def insert_lines(self, section, index, lines):
        #
        # Check input parameters
        #
        if section not in self.__section_dict.keys():
            raise ValueError('Invalid section name: {}'.format(section))
        if not isinstance(lines, list):
            raise ValueError('Invalid parameter type.')
        if index < 0 or index > len(self.__section_dict[section]):
            raise ValueError('Index out of range.')

        #
        # Create a copy of the list and reverse it.  This makes it easier to insert the list.
        #
        tmp_lines = copy.deepcopy(lines)
        tmp_lines.reverse()
        for line in tmp_lines:
            self.__section_dict[section].insert(index, line)

    #
    # Removes some number of lines starting at a given index
    #
    def remove_lines(self, section, index, count):
        #
        # Check input parameters
        #
        if section not in self.__section_dict.keys():
            raise ValueError('Invalid section name: {}'.format(section))
        if index < 0 or index >= len(self.__section_dict[section]):
            raise ValueError('Invalid index.')
        if index + count > len(self.__section_dict[section]):
            raise ValueError('Invalid data range.')

        #
        # Just delete the line at the specified index until the
        # specified number of lines are removed.
        #
        for num in range(count):
            self.__section_dict[section].pop(index)

    #
    # Replaces a given number of lines with the provided new lines.
    # Functionally the same as remove_lines followed by insert_lines.
    #
    def replace_lines(self, section, index, remove_count, new_lines):
        raise NotImplementedError('The function replace_lines has not been implemented.')

    #
    # Gets all the file lines based on the current order of the section list.
    #
    def get_lines(self):
        ret_lines = []

        #
        # Put the file header in place
        #
        ret_lines.extend(self.__file_header)

        #
        # Now add all the sections
        #
        for section in self.__section_list:
            ret_lines.append('[{0}]'.format(section))
            ret_lines.extend(self.__section_dict[section])

        return ret_lines

#
# Data structure to process EDKII build files
# - Targets DSC and FDF file formats.
#
class BuildFileInfo:
    def __init__(self):
        self.__file_data = BaseInf()
        self.__defines_dict = {}
        self.__use_comments = False

    #
    # Initialize the data structure
    #
    def init_data(self, file_lines, import_defines=None, use_comments=False):
        #
        # Just check to make sure the list has some data in it.
        #
        if len(file_lines) == 0:
            raise ValueError('Invalid file data provided.')

        #
        # Set line removal mode
        #
        self.__use_comments = use_comments

        #
        # If a defines dictionary is passed in we will seed our defines dictionary
        #
        if isinstance(import_defines, dict):
            self.__defines_dict = copy.deepcopy(import_defines)

        #
        # Initialize the data structure to hold file content
        #
        self.__file_data.init_data(file_lines)

        #
        # Extract any defines and put them in a dictionary
        #
        self.__update_defines()

    #
    # Returns a copy of the defines dictionary
    #
    def get_defines(self):
        return copy.deepcopy(self.__defines_dict)

    #
    # Returns the raw lines
    #
    def get_file_lines(self):
        return self.__file_data.get_lines()

    #
    # Returns a list of include paths
    #
    def find_includes(self):
        #
        # Search for include entries
        #
        return self.__find_key_with_path('!include', self.__file_data.get_lines())

    #
    # Replaces an include statement with the contents of the line buffer.
    #
    # Returns True on success
    #
    def replace_include(self, inc_path, file_lines):
        include_line_num = -1
        section_lines = []

        #
        # Check the header
        #
        include_line_num = self.__find_key_path_index('!include', inc_path, self.__file_data.get_header())
        if include_line_num < 0:
            #
            # Now check all the sections
            #
            for section in self.__file_data.get_sections():
                section_lines = self.__file_data.get_section_lines(section)
                include_line_num = self.__find_key_path_index('!include', inc_path, section_lines)
                if include_line_num >= 0:
                    break
        if include_line_num < 0:
            raise RuntimeError('Include value not found: {}'.format(inc_path))

        #
        # include_line_num is now the index of the include statement so start by removing it
        #
        self.__file_data.remove_lines(section, include_line_num, 1)
        if self.__use_comments:
            self.__file_data.insert_lines(
                    section,
                    include_line_num,
                    ['#### Discard #### {0}'.format(section_lines[include_line_num].strip())]
                    )

        #
        # Copy the file lines and add a header / Footer comment to make included sections
        # easy to find.
        #
        inc_lines = []
        inc_lines.append('####============================================================================')
        inc_lines.append('#### Start: {0}'.format(inc_path))
        inc_lines.append('####============================================================================')
        inc_lines.extend(copy.copy(file_lines))
        inc_lines.append('####============================================================================')
        inc_lines.append('#### End: {0}'.format(inc_path))
        inc_lines.append('####============================================================================')

        #
        # Insert file lines
        #
        self.__file_data.insert_lines(section, include_line_num, inc_lines)

        #
        # Reinitialize data after processing an include.  Need to make sure that new sections are handled.
        #
        self.__file_data.init_data(self.get_file_lines())

        #
        # Update the other storage items
        #
        self.__update_defines()

        return True

    #
    # Finds a Key/Value pair within the defines section
    #
    def find_key_value(self, key):
        if key in self.__defines_dict.keys():
            return self.__defines_dict[key]
        raise RuntimeError('Key not found: {}'.format(key))

    #
    # Sets the value of a Key/Value pair
    #
    def set_key_value(self, key, new_value):
        #
        # Check to see if the value exists in the defines DB and get the current value
        #
        if key not in self.__defines_dict.keys():
            raise RuntimeError('Key not found: {}'.format(key))

        #
        # Search the all sections for the key and value
        #
        for section in self.__file_data.get_sections():
            index = -1
            entry_found = False
            for line in self.__file_data.get_section_lines(section):
                index += 1
                tmp_line = clean_line(line)
                if tmp_line == '':
                    continue
                if tmp_line.find(key) >= 0:
                    entry_found = True
                    cur_value = tmp_line.split('=')[1].strip()
                    break
            if entry_found:
                break
        if not entry_found:
            raise RuntimeError('Unable to find key in file lines: {}'.format(key))

        #
        # Update the file line with the new value
        #
        new_line = self.__file_data.get_section_lines(section)[index].replace(cur_value, new_value)
        self.__file_data.remove_lines(section, index, 1)
        self.__file_data.insert_lines(section, index, [new_line])

        #
        # Update dictionaries
        #
        self.__update_defines()

    #
    # Replace all macros in the current file.
    #
    def replace_macros(self):
        file_lines = self.__file_data.get_lines()

        tmp_lines = []
        for line in file_lines:
            tmp_lines.append(self.__replace_macros(line))

        self.init_data(tmp_lines, None, self.__use_comments)

    #
    # Gets the Name portion of a statement if possible.  Otherwise returns the original line.
    # Formats:
    # - NAME | Value
    #
    def __get_name_only(self, line):
        index = line.find('|')
        if index < 0:
            return line.strip()
        return line[:index].strip()

    #
    # Processes file lines used with !merge statements
    # - Currently not sure if this is goind to be needed in the future.  It is specifically to work
    #   around a specific syntax.
    #
    def __process_raw_merge_lines(self, lines):
        ret_lines = []
        stack = []
        section_found = False
        skip_endif_count = 0

        #
        # Process !if statements that start before the first statement
        #
        for line in lines:
            tmp_line = clean_line(line)
            if not section_found and tmp_line.startswith('['):
                section_found = True
                if len(stack) > 0:
                    skip_endif_count = len(stack)
            elif tmp_line.startswith('!if'):
                stack.insert(0, '!endif')
            elif len(stack) > 0:
                if tmp_line.startswith(stack[0]):
                    stack.pop()
                    if len(stack) < skip_endif_count:
                        skip_endif_count -= 1
                        continue

            #
            # Append the line
            #
            if section_found:
                ret_lines.append(line)

        return ret_lines

    #
    # Find a key word that is followed by a path.  Return a list of all the items found.
    #
    def __find_key_with_path(self, key, lines):
        ret_list = []

        #
        # Just search the file lines and return every include entry
        #
        for line in lines:
            #
            # Remove any comments
            #
            line = clean_line(line)
            if line == '':
                continue

            #
            # Check to see if this is an include statement
            #
            if line.lower().startswith(key):
                inc_parts = line.split()
                if len(inc_parts) == 2:
                    #
                    # Attempt to create a macro free include path
                    #
                    inc_path = self.__replace_macros(inc_parts[1])

                    #
                    # Check to see if a define is still being used in the path.  If so, skip it for now.
                    #
                    if inc_path.find('$(') >= 0:
                        continue

                    #
                    # This is a processable path so return it
                    #
                    ret_list.append(inc_path)

        return ret_list

    #
    # Gets the index of the first key/path entry that matches the input parametes
    #
    def __find_key_path_index(self, key, path, lines):
        key_line_num = -1
        line_found = False

        #
        # Loop through the lines and find the first matching entry
        #
        for line in lines:
            key_line_num += 1
            tmp_line = clean_line(line)
            if tmp_line == '':
                continue
            if not tmp_line.lower().startswith(key):
                continue
            tmp_line = self.__replace_macros(tmp_line)
            if tmp_line.find(path) >= 0:
                line_found = True
                break

        #
        # Double check that the line was found
        #
        if not line_found:
            key_line_num = -1

        return key_line_num

    #
    # Processes any defines in the DSC file so they can be used for substitution
    #
    def __update_defines(self):
        tag_stack = []

        #
        # Search defines section of dictionary of Key / Value pairs
        # Format: DEFINE Key = Value(User Defined)
        # Format: Key = Value(Spec Defined)
        #
        # TODO: Expand defines search to entire file
        #
        try:
            for line in self.__file_data.get_section_lines('Defines'):
                #
                # Ignore comments
                #
                tmp_line = clean_line(line)
                if tmp_line == '':
                    continue

                #
                # Skip ! tags
                #
                if tmp_line.lower().find('!include') >= 0:
                    continue
                elif tmp_line.lower().find('!if') >= 0:
                    tag_stack.insert(0, '!endif')
                    continue
                elif len(tag_stack) > 0:
                    if tmp_line.lower().find(tag_stack[0]) >= 0:
                        tag_stack.pop(0)
                    continue

                #
                # Line must have a define of some sort on it.  Check both formats.
                #
                if tmp_line.find('=') < 0:
                    continue
                if tmp_line.startswith('DEFINE '):
                    tmp_line = tmp_line.replace('DEFINE ', '', 1).strip()
                define_parts = tmp_line.split('=')
                if len(define_parts) != 2:
                    continue

                #
                # Add the define to the dictionary
                #
                self.__defines_dict[define_parts[0].strip()] = define_parts[1].strip()
        except:
            pass

        #
        # Once all defines are processed replace any define Macros with real values
        #
        for key in self.__defines_dict.keys():
            self.__defines_dict[key] = self.__replace_macros(self.__defines_dict[key])

    #
    # Removes macros from the input string if possible based on the Defines dictionary
    #
    def __replace_macros(self, in_str):
        ret_str = ''
        macro_list = []

        #
        # First see if the string even has a macro
        #
        if in_str.find('$(') < 0:
            return in_str

        #
        # Replace all macros in the string.
        #
        ret_str = in_str
        while ret_str.find('$(') >= 0:
            #
            # Extract the macro name
            #
            macro_start = ret_str.find('$(')
            macro_end = ret_str.find(')')
            if macro_start < 0 or macro_end < 0:
                break
            macro = ret_str[macro_start:macro_end+1]
            macro_name = ret_str[macro_start+2:macro_end]

            #
            # Attempt to replace the macro with a real value
            #
            if macro_name in self.__defines_dict.keys():
                ret_str = ret_str.replace(macro, self.__defines_dict[macro_name])
            else:
                break

        return ret_str

    #
    # Builds a new SectionDict from RawLines
    #
    def __UpdateSectionDict(self, raw_lines):
        section_list = []
        section_dict = {}

        #
        # Start by clearing out the existing data
        #
        current_section = section_list[0]
        section_dict[current_section] = []

        #
        # Start processing lines
        #
        for line in raw_lines:
            #
            # Create a temp string for destructive processing and remove comments
            #
            tmp_line = clean_line(line)

            #
            # Check to see if this line is a section definition
            #
            if tmp_line.startswith('[') and tmp_line.endswith(']'):
                current_section = tmp_line.strip('[]').strip()
                section_list.append(current_section)
                section_dict[current_section] = []
                continue

            #
            # Add the line to the current section
            #
            section_dict[current_section].append(line.rstrip())

        #
        # Once done processing double check that the first key had anything in it
        #
        if section_list[0] not in section_dict.keys():
            section_list.pop(0)

        #
        # Return the section list and dictionary to the caller
        #
        return(section_list, section_dict)
