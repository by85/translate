# -*- coding: utf-8 -*-

import pytest

from translate.convert import po2l20n, test_convert
from translate.misc import wStringIO


class TestPO2L20n(object):

    ConverterClass = po2l20n.po2l20n

    def _convert(self, input_string, template_string=None, include_fuzzy=False,
                 output_threshold=None, success_expected=True):
        """Helper that converts to target format without using files."""
        input_file = wStringIO.StringIO(input_string)
        output_file = wStringIO.StringIO()
        template_file = None
        if template_string:
            template_file = wStringIO.StringIO(template_string)
        expected_result = 1 if success_expected else 0
        converter = self.ConverterClass(input_file, output_file, template_file,
                                        include_fuzzy, output_threshold)
        assert converter.run() == expected_result
        return None, output_file

    def _convert_to_string(self, *args, **kwargs):
        """Helper that converts to target format string without using files."""
        return self._convert(*args, **kwargs)[1].getvalue().decode('utf-8')

    def test_convert_no_templates(self):
        """Check converter doesn't allow to pass no templates."""
        with pytest.raises(ValueError):
            self._convert_to_string('')

    def test_merging_simple(self):
        """Check the simplest case of merging a translation."""
        input_string = """#: l20n
msgid "value"
msgstr "waarde"
"""
        template_string = """l20n = value
"""
        expected_output = """l20n = waarde
"""
        assert expected_output == self._convert_to_string(input_string,
                                                          template_string)

    def test_merging_untranslated(self):
        """check the simplest case of merging an untranslated unit"""
        input_string = """#: l20n
msgid "value"
msgstr ""
"""
        template_string = """l20n = value
"""
        expected_output = template_string
        assert expected_output == self._convert_to_string(input_string,
                                                          template_string)


class TestPO2L20nCommand(test_convert.TestConvertCommand, TestPO2L20n):
    """Tests running actual po2prop commands on files"""
    convertmodule = po2l20n
    defaultoptions = {"progress": "none"}

    def test_help(self):
        """tests getting help"""
        options = test_convert.TestConvertCommand.test_help(self)
        options = self.help_check(options, "-t TEMPLATE, --template=TEMPLATE")
        options = self.help_check(options, "--fuzzy")
        options = self.help_check(options, "--threshold=PERCENT")
        options = self.help_check(options, "--nofuzzy", last=True)
