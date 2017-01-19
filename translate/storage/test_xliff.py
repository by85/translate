import pytest
import six
from lxml import etree

from translate.misc.xml_helpers import setXMLspace
from translate.storage import test_base, xliff
from translate.storage.placeables import StringElem
from translate.storage.placeables.xliff import G, X


class TestXLIFFUnit(test_base.TestTranslationUnit):
    UnitClass = xliff.xliffunit

    def test_markreview(self):
        """Tests if we can mark the unit to need review."""
        unit = self.unit
        # We have to explicitly set the target to nothing, otherwise xliff
        # tests will fail.
        # Can we make it default behavior for the UnitClass?
        unit.target = ""

        unit.addnote("Test note 1", origin="translator")
        unit.addnote("Test note 2", origin="translator")
        original_notes = unit.getnotes(origin="translator")

        assert not unit.isreview()
        unit.markreviewneeded()
        assert unit.isreview()
        unit.markreviewneeded(False)
        assert not unit.isreview()
        assert unit.getnotes(origin="translator") == original_notes
        unit.markreviewneeded(explanation="Double check spelling.")
        assert unit.isreview()
        notes = unit.getnotes(origin="translator")
        assert notes.count("Double check spelling.") == 1

    def test_errors(self):
        """Tests that we can add and retrieve error messages for a unit."""
        unit = self.unit

        assert len(unit.geterrors()) == 0
        unit.adderror(errorname='test1', errortext='Test error message 1.')
        unit.adderror(errorname='test2', errortext='Test error message 2.')
        unit.adderror(errorname='test3', errortext='Test error message 3.')
        assert len(unit.geterrors()) == 3
        assert unit.geterrors()['test1'] == 'Test error message 1.'
        assert unit.geterrors()['test2'] == 'Test error message 2.'
        assert unit.geterrors()['test3'] == 'Test error message 3.'
        unit.adderror(errorname='test1', errortext='New error 1.')
        assert unit.geterrors()['test1'] == 'New error 1.'

    def test_accepted_control_chars(self):
        """Tests we can assign the accepted control chars.

        Source: https://en.wikipedia.org/wiki/Valid_characters_in_XML#XML_1.0
        """
        # Unicode Character 'CHARACTER TABULATION' (U+0009)
        self.unit.target = u'Een\t'

        # Unicode Character 'LINE FEED (LF)' (U+000A)
        self.unit.target = u'Een\n'

        # Unicode Character 'CARRIAGE RETURN (CR)' (U+000D)
        self.unit.target = u'Een\r'

    def test_unaccepted_control_chars(self):
        """Tests we cannot assign the unaccepted control chars.

        Source: https://en.wikipedia.org/wiki/Valid_characters_in_XML#XML_1.0
        """
        ascii_control_codes = [
            '0000',  # Unicode Character 'NULL' (U+0000)
            '0001',  # Unicode Character 'START OF HEADING' (U+0001)
            '0002',  # Unicode Character 'START OF TEXT' (U+0002)
            '0003',  # Unicode Character 'END OF TEXT' (U+0003)
            '0004',  # Unicode Character 'END OF TRANSMISSION' (U+0004)
            '0005',  # Unicode Character 'ENQUIRY' (U+0005)
            '0006',  # Unicode Character 'ACKNOWLEDGE' (U+0006)
            '0007',  # Unicode Character 'BELL' (U+0007), "\a" in Python
            '0008',  # Unicode Character 'BACKSPACE' (U+0008), "\b" in Python
            '000b',  # Unicode Character 'LINE TABULATION' (U+000B), "\v" in Python
            '000c',  # Unicode Character 'FORM FEED (FF)' (U+000C), "\f" in Python
            '000e',  # Unicode Character 'SHIFT OUT' (U+000E)
            '000f',  # Unicode Character 'SHIFT IN' (U+000F)
            '0010',  # Unicode Character 'DATA LINK ESCAPE' (U+0010)
            '0011',  # Unicode Character 'DEVICE CONTROL ONE' (U+0011)
            '0012',  # Unicode Character 'DEVICE CONTROL TWO' (U+0012)
            '0013',  # Unicode Character 'DEVICE CONTROL THREE' (U+0013)
            '0014',  # Unicode Character 'DEVICE CONTROL FOUR' (U+0014)
            '0015',  # Unicode Character 'NEGATIVE ACKNOWLEDGE' (U+0015)
            '0016',  # Unicode Character 'SYNCHRONOUS IDLE' (U+0016)
            '0017',  # Unicode Character 'END OF TRANSMISSION BLOCK' (U+0017)
            '0018',  # Unicode Character 'CANCEL' (U+0018)
            '0019',  # Unicode Character 'END OF MEDIUM' (U+0019)
            '001a',  # Unicode Character 'SUBSTITUTE' (U+001A)
            '001b',  # Unicode Character 'ESCAPE' (U+001B)
            '001c',  # Unicode Character 'INFORMATION SEPARATOR FOUR' (U+001C)
            '001d',  # Unicode Character 'INFORMATION SEPARATOR THREE' (U+001D)
            '001e',  # Unicode Character 'INFORMATION SEPARATOR TWO' (U+001E)
            '001f',  # Unicode Character 'INFORMATION SEPARATOR ONE' (U+001F)
        ]
        exc_msg = ("All strings must be XML compatible: Unicode or ASCII, no "
                   "NULL bytes or control characters")
        for code in ascii_control_codes:
            self.unit.target = u'Een&#x%s;' % code.lstrip('0') or '0'
            with pytest.raises(ValueError) as excinfo:
                self.unit.target = u'Een%s' % six.unichr(int(code, 16))
            assert exc_msg in excinfo.value


class TestXLIFFfile(test_base.TestTranslationStore):
    StoreClass = xliff.xlifffile
    skeleton = '''<?xml version="1.0" encoding="utf-8"?>
<xliff version="1.1" xmlns="urn:oasis:names:tc:xliff:document:1.1">
        <file original="doc.txt" source-language="en-US">
                <body>
                        %s
                </body>
        </file>
</xliff>'''

    def test_basic(self):
        xlifffile = xliff.xlifffile()
        assert xlifffile.units == []
        xlifffile.addsourceunit("Bla")
        assert len(xlifffile.units) == 1
        newfile = xliff.xlifffile.parsestring(bytes(xlifffile))
        print(bytes(xlifffile))
        assert len(newfile.units) == 1
        assert newfile.units[0].source == "Bla"
        assert newfile.findunit("Bla").source == "Bla"
        assert newfile.findunit("dit") is None

    def test_namespace(self):
        """Check that we handle namespaces other than the default correctly."""
        xlfsource = '''<?xml version="1.0" encoding="utf-8"?>
<xliff:xliff version="1.2" xmlns:xliff="urn:oasis:names:tc:xliff:document:1.2">
    <xliff:file original="doc.txt" source-language="en-US">
        <xliff:body>
            <xliff:trans-unit id="1">
                <xliff:source>File 1</xliff:source>
            </xliff:trans-unit>
        </xliff:body>
    </xliff:file>
</xliff:xliff>'''
        xlifffile = xliff.xlifffile.parsestring(xlfsource)
        print(bytes(xlifffile))
        assert xlifffile.units[0].source == "File 1"

    def test_rich_source(self):
        xlifffile = xliff.xlifffile()
        xliffunit = xlifffile.addsourceunit(u'')

        # Test 1
        xliffunit.rich_source = [StringElem([u'foo', X(id='bar'), u'baz'])]
        source_dom_node = xliffunit.getlanguageNode(None, 0)
        x_placeable = source_dom_node[0]

        assert source_dom_node.text == 'foo'

        assert x_placeable.tag == u'x'
        assert x_placeable.attrib['id'] == 'bar'
        assert x_placeable.tail == 'baz'

        xliffunit.rich_source[0].print_tree(2)
        print(xliffunit.rich_source)
        assert xliffunit.rich_source == [StringElem([StringElem(u'foo'), X(id='bar'), StringElem(u'baz')])]

        # Test 2
        xliffunit.rich_source = [StringElem([u'foo', u'baz', G(id='oof', sub=[G(id='zab', sub=[u'bar', u'rab'])])])]
        source_dom_node = xliffunit.getlanguageNode(None, 0)
        g_placeable = source_dom_node[0]
        nested_g_placeable = g_placeable[0]

        assert source_dom_node.text == u'foobaz'

        assert g_placeable.tag == u'g'
        assert g_placeable.text is None
        assert g_placeable.attrib[u'id'] == u'oof'
        assert g_placeable.tail is None

        assert nested_g_placeable.tag == u'g'
        assert nested_g_placeable.text == u'barrab'
        assert nested_g_placeable.attrib[u'id'] == u'zab'
        assert nested_g_placeable.tail is None

        rich_source = xliffunit.rich_source
        rich_source[0].print_tree(2)
        assert rich_source == [StringElem([u'foobaz', G(id='oof', sub=[G(id='zab', sub=[u'barrab'])])])]

    def test_rich_target(self):
        xlifffile = xliff.xlifffile()
        xliffunit = xlifffile.addsourceunit(u'')

        # Test 1
        xliffunit.set_rich_target([StringElem([u'foo', X(id='bar'), u'baz'])], u'fr')
        target_dom_node = xliffunit.getlanguageNode(None, 1)
        x_placeable = target_dom_node[0]

        assert target_dom_node.text == 'foo'
        assert x_placeable.tag == u'x'
        assert x_placeable.attrib['id'] == 'bar'
        assert x_placeable.tail == 'baz'

        # Test 2
        xliffunit.set_rich_target([StringElem([u'foo', u'baz', G(id='oof', sub=[G(id='zab', sub=[u'bar', u'rab'])])])], u'fr')
        target_dom_node = xliffunit.getlanguageNode(None, 1)
        g_placeable = target_dom_node[0]
        nested_g_placeable = g_placeable[0]

        assert target_dom_node.text == u'foobaz'

        assert g_placeable.tag == u'g'
        print('g_placeable.text: %s (%s)' % (g_placeable.text, type(g_placeable.text)))
        assert g_placeable.text is None
        assert g_placeable.attrib[u'id'] == u'oof'
        assert g_placeable.tail is None

        assert nested_g_placeable.tag == u'g'
        assert nested_g_placeable.text == u'barrab'
        assert nested_g_placeable.attrib[u'id'] == u'zab'
        assert nested_g_placeable.tail is None

        xliffunit.rich_target[0].print_tree(2)
        assert xliffunit.rich_target == [StringElem([u'foobaz', G(id='oof', sub=[G(id='zab', sub=[u'barrab'])])])]

    def test_source(self):
        xlifffile = xliff.xlifffile()
        xliffunit = xlifffile.addsourceunit("Concept")
        xliffunit.source = "Term"
        newfile = xliff.xlifffile.parsestring(bytes(xlifffile))
        print(bytes(xlifffile))
        assert newfile.findunit("Concept") is None
        assert newfile.findunit("Term") is not None

    def test_target(self):
        xlifffile = xliff.xlifffile()
        xliffunit = xlifffile.addsourceunit("Concept")
        xliffunit.target = "Konsep"
        newfile = xliff.xlifffile.parsestring(bytes(xlifffile))
        print(bytes(xlifffile))
        assert newfile.findunit("Concept").target == "Konsep"

    def test_sourcelanguage(self):
        xlifffile = xliff.xlifffile(sourcelanguage="xh")
        xmltext = bytes(xlifffile).decode('utf-8')
        print(xmltext)
        assert xmltext.find('source-language="xh"') > 0
        #TODO: test that it also works for new files.

    def test_targetlanguage(self):
        xlifffile = xliff.xlifffile(sourcelanguage="zu", targetlanguage="af")
        xmltext = bytes(xlifffile).decode('utf-8')
        print(xmltext)
        assert xmltext.find('source-language="zu"') > 0
        assert xmltext.find('target-language="af"') > 0

    def test_notes(self):
        xlifffile = xliff.xlifffile()
        unit = xlifffile.addsourceunit("Concept")
        # We don't want to add unnecessary notes
        assert "note" not in bytes(xlifffile).decode('utf-8')
        unit.addnote(None)
        assert "note" not in bytes(xlifffile).decode('utf-8')
        unit.addnote("")
        assert "note" not in bytes(xlifffile).decode('utf-8')

        unit.addnote("Please buy bread")
        assert unit.getnotes() == "Please buy bread"
        notenodes = unit.xmlelement.findall(".//%s" % unit.namespaced("note"))
        assert len(notenodes) == 1

        unit.addnote("Please buy milk", origin="Mom")
        notenodes = unit.xmlelement.findall(".//%s" % unit.namespaced("note"))
        assert len(notenodes) == 2
        assert "from" not in notenodes[0].attrib
        assert notenodes[1].get("from") == "Mom"
        assert unit.getnotes(origin="Mom") == "Please buy milk"

        unit.addnote("Don't forget the beer", origin="Dad")
        notenodes = unit.xmlelement.findall(".//%s" % unit.namespaced("note"))
        assert len(notenodes) == 3
        assert notenodes[1].get("from") == "Mom"
        assert notenodes[2].get("from") == "Dad"
        assert unit.getnotes(origin="Dad") == "Don't forget the beer"

        assert not unit.getnotes(origin="Bob") == "Please buy bread\nPlease buy milk\nDon't forget the beer"
        assert not notenodes[2].get("from") == "Mom"
        assert "from" not in notenodes[0].attrib
        assert unit.getnotes() == "Please buy bread\nPlease buy milk\nDon't forget the beer"
        assert unit.correctorigin(notenodes[2], "ad")
        assert not unit.correctorigin(notenodes[2], "om")

    def test_alttrans(self):
        """Test xliff <alt-trans> accessors"""
        xlifffile = xliff.xlifffile()
        unit = xlifffile.addsourceunit("Testing")

        unit.addalttrans("ginmi")
        unit.addalttrans("shikenki")
        alternatives = unit.getalttrans()
        assert alternatives[0].source == "Testing"
        assert alternatives[0].target == "ginmi"
        assert alternatives[1].target == "shikenki"

        assert not unit.target

        unit.addalttrans("Tasting", origin="bob", lang="eng")
        alternatives = unit.getalttrans()
        assert alternatives[2].target == "Tasting"

        alternatives = unit.getalttrans(origin="bob")
        assert alternatives[0].target == "Tasting"

        unit.delalttrans(alternatives[0])
        assert len(unit.getalttrans(origin="bob")) == 0
        alternatives = unit.getalttrans()
        assert len(alternatives) == 2
        assert alternatives[0].target == "ginmi"
        assert alternatives[1].target == "shikenki"

        #clean up:
        alternatives = unit.getalttrans()
        for alt in alternatives:
            unit.delalttrans(alt)
        unit.addalttrans("targetx", sourcetxt="sourcex")
        # test that the source node is before the target node:
        alt = unit.getalttrans()[0]
        altformat = etree.tostring(alt.xmlelement).decode('utf-8')
        print(altformat)
        assert altformat.find("<source") < altformat.find("<target")

        # test that a new target is still before alt-trans (bug 1098)
        unit.target = u"newester target"
        unitformat = str(unit)
        print(unitformat)
        assert unitformat.find("<source") < unitformat.find("<target") < unitformat.find("<alt-trans")

    def test_fuzzy(self):
        xlifffile = xliff.xlifffile()
        unit = xlifffile.addsourceunit("Concept")
        unit.markfuzzy()
        assert not unit.isfuzzy()  # untranslated
        unit.target = "Konsep"
        assert unit.isfuzzy()
        unit.markfuzzy()
        assert unit.isfuzzy()
        unit.markfuzzy(False)
        assert not unit.isfuzzy()
        unit.markfuzzy(True)
        assert unit.isfuzzy()

        #If there is no target, we can't really indicate fuzzyness, so we set
        #approved to "no". If we want isfuzzy() to reflect that, the line can
        #be uncommented
        unit.target = None
        assert unit.target is None
        print(unit)
        unit.markfuzzy(True)
        assert 'approved="no"' in str(unit)
        #assert unit.isfuzzy()

    def test_xml_space(self):
        """Test for the correct handling of xml:space attributes."""
        xlfsource = self.skeleton % (
            '''<trans-unit id="1" xml:space="preserve">
                   <source> File  1 </source>
               </trans-unit>''')
        xlifffile = xliff.xlifffile.parsestring(xlfsource)
        assert xlifffile.units[0].source == " File  1 "
        root_node = xlifffile.document.getroot()
        setXMLspace(root_node, "preserve")
        assert xlifffile.units[0].source == " File  1 "
        setXMLspace(root_node, "default")
        assert xlifffile.units[0].source == " File  1 "

        xlfsource = self.skeleton % (
            '''<trans-unit id="1" xml:space="default">
                   <source> File  1 </source>
               </trans-unit>''')
        xlifffile = xliff.xlifffile.parsestring(xlfsource)
        assert xlifffile.units[0].source == "File 1"
        root_node = xlifffile.document.getroot()
        setXMLspace(root_node, "preserve")
        assert xlifffile.units[0].source == "File 1"
        setXMLspace(root_node, "default")
        assert xlifffile.units[0].source == "File 1"

        xlfsource = self.skeleton % (
            '''<trans-unit id="1">
                   <source> File  1 </source>
               </trans-unit>''')
        # we currently always normalize as default behaviour for xliff
        xlifffile = xliff.xlifffile.parsestring(xlfsource)
        assert xlifffile.units[0].source == "File 1"
        root_node = xlifffile.document.getroot()
        setXMLspace(root_node, "preserve")
        assert xlifffile.units[0].source == "File 1"
        setXMLspace(root_node, "default")
        assert xlifffile.units[0].source == "File 1"

        xlfsource = self.skeleton % (
            '''<trans-unit id="1">
                   <source> File  1
</source>
               </trans-unit>''')
        # we currently always normalize as default behaviour for xliff
        xlifffile = xliff.xlifffile.parsestring(xlfsource)
        assert xlifffile.units[0].source == "File 1"
        root_node = xlifffile.document.getroot()
        setXMLspace(root_node, "preserve")
        assert xlifffile.units[0].source == "File 1"
        setXMLspace(root_node, "default")
        assert xlifffile.units[0].source == "File 1"

    def test_parsing(self):
        xlfsource = self.skeleton \
            % '''<trans-unit id="1" xml:space="preserve">
                     <source>File</source>
                     <target/>
                 </trans-unit>'''
        xlifffile = xliff.xlifffile.parsestring(xlfsource)
        assert xlifffile.units[0].istranslatable()

        xlfsource = self.skeleton \
            % '''<trans-unit id="1" xml:space="preserve" translate="no">
                     <source>File</source>
                     <target/>
                 </trans-unit>'''
        xlifffile = xliff.xlifffile.parsestring(xlfsource)
        assert not xlifffile.units[0].istranslatable()

        xlfsource = self.skeleton \
            % '''<trans-unit id="1" xml:space="preserve" translate="yes">
                     <source>File</source>
                     <target/>
                 </trans-unit>'''
        xlifffile = xliff.xlifffile.parsestring(xlfsource)
        assert xlifffile.units[0].istranslatable()
