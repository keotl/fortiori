import re
import unittest

from jivago_streams import Stream

from dialect.simple_operations import remove_curly_brackets, strip_comments


class SimpleOperationsTest(unittest.TestCase):


    def test_curlyBrackets(self):
        input = """function foobar {
        do i=1,10 {
        some stuff !}
        "!" ! "foobar!!
        stuff
        }}"""
        expected = """function foobar
        do i=1,10
        some stuff
        "!"
        stuff
        end do
        end function"""

        actual = remove_curly_brackets(strip_comments(input))

        self.assertEqualIgnoreWhitespace(expected, actual)

    def test_removeLineBreaksInBlocks(self):
        input = """print(10,
        11,
        13
        ,14);"""

    def assertEqualIgnoreWhitespace(self, expected: str, actual: str) -> None:
        self.assertEqual(
            Stream(re.split(r" |\n|\t", expected)).filter(lambda x: x != "").toList(),
            Stream(re.split(r" |\n|\t", actual)).filter(lambda x: x != "").toList()
        )
