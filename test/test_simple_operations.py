import re
import unittest

from jivago_streams import Stream

from dialect.simple_operations import remove_curly_brackets


class SimpleOperationsTest(unittest.TestCase):

    def test_curlyBrackets(self):
        input = """function {
        do i=1,10 {
        stuff
        }}"""
        expected = """function
        do i=1,10
        stuff
        end do
        end function"""

        actual = remove_curly_brackets(input)

        self.assertEqualIgnoreWhitespace(expected, actual)

    def assertEqualIgnoreWhitespace(self, expected: str, actual: str) -> None:
        self.assertEqual(
            Stream(re.split(r" |\n|\t", expected)).filter(lambda x: x != "").toList(),
            Stream(re.split(r" |\n|\t", actual)).filter(lambda x: x != "").toList()
        )
