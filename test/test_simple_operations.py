import re
import unittest

from jivago_streams import Stream

from dialect.simple_operations import remove_curly_brackets, strip_comments, remove_line_splits_inside_blocks, \
    move_function_parameter_type_declaration_to_body, move_variable_declaration_to_start_of_block


class SimpleOperationsTest(unittest.TestCase):

    def test_curlyBrackets(self):
        input = """function foobar() {
        do i=1,10 {
        some stuff !}
        "!" ! "foobar!!
        
        stuff
        }}"""
        expected = """function foobar()
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

        expected = """print(10,11,13,14);"""

        actual = remove_line_splits_inside_blocks(input)

        self.assertEqualIgnoreWhitespace(expected, actual)

    def test_inlineParameterDeclaration(self):
        input = """integer function myFunction(integer::a, integer,pointer :: b) 
        {
        }"""
        expected = """integer function myFunction(a,b) {
        integer::a
        integer,pointer::b
        }"""

        actual = move_function_parameter_type_declaration_to_body(input)

        self.assertEqualIgnoreWhitespace(expected, actual)

    def test_moveVariableDeclarationToStartOfFunction(self):
        input = """void function myFunction() {
        print("hello");
        integer::a = 30;
        }
        program {
        stuff;
        integer::aNumber = 40;
        }"""
        expected = """void function myFunction() {
        integer::a;
        print("hello");
        a = 30;
        }
        program {
        integer::aNumber;
        stuff;
        aNumber = 40;
        }
        """

        actual = move_variable_declaration_to_start_of_block(input)

        self.assertEqualIgnoreWhitespace(expected, actual)

    def assertEqualIgnoreWhitespace(self, expected: str, actual: str) -> None:
        expected = re.sub(" *, *", ",", expected)
        actual = re.sub(" *, *", ",", actual)
        self.assertEqual(
            Stream(re.split(r" |\n|\t", expected)).filter(lambda x: x != "").toList(),
            Stream(re.split(r" |\n|\t", actual)).filter(lambda x: x != "").toList()
        )
