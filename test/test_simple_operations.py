import re
import unittest

from jivago_streams import Stream

from fortiori.simple_operations import remove_curly_brackets, strip_comments, remove_line_splits_inside_blocks, \
    move_function_parameter_type_declaration_to_body, move_variable_declaration_to_start_of_block, \
    translate_return_statement, declare_invoked_function_return_types, add_implicit_none, \
    add_name_to_unnamed_program_blocks, translate_case_sensitive_identifier, convert_conditional_blocks, \
    replace_object_reference_type_declaration, inline_pointer_cast_function


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
        end do;
        end function;"""

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
        do integer::n = 1,10 {
        }
        }"""
        expected = """void function myFunction() {
        integer::a;
        print("hello");
        a = 30;
        }
        program {
        integer::aNumber;
        integer::n;
        stuff;
        aNumber = 40;
        do n = 1,10 {
        }
        }
        """

        actual = move_variable_declaration_to_start_of_block(input)

        self.assertEqualIgnoreWhitespace(expected, actual)

    def test_return_statement(self):
        input = """integer function myFunction() {
        return 5;
        }"""
        expected = """integer function myFunction() {
        myFunction = 5;
        return;
        }"""

        actual = translate_return_statement(input)

        self.assertEqualIgnoreWhitespace(expected, actual)

    def test_declareUsedFunctionReturnTypes(self):
        input = """integer function myFunction() {
        }
        program {
        myFunction();
        new foobar();
        }
        """
        expected = """integer function myFunction() {
        }
        program {
        integer::myFunction;
        myFunction();
        new foobar();
        }"""

        actual = declare_invoked_function_return_types(input)

        self.assertEqualIgnoreWhitespace(expected, actual)

    def test_addImplicitNoneToEveryCodeBlock(self):
        input = """integer function myFunction() {
        }"""
        expected = """integer function myFunction() {
        implicit none;
        }"""

        actual = add_implicit_none(input)

        self.assertEqualIgnoreWhitespace(expected, actual)

    def test_addProgramNameToUnnamedPrograms(self):
        input = """integer function myFunction() {
        }
        program 
        {
        stuff;
        }"""
        expected = """integer function myFunction() {
        }
        program main {
        stuff;
        }"""

        actual = add_name_to_unnamed_program_blocks(input)

        self.assertEqualIgnoreWhitespace(expected, actual)

    def test_translateCaseSensitiveIdentifier(self):
        input = """integer function myFunction() {
        integer::aVariable1;
        integer::AVARIABLE1;
        
        aVariable = 5;
        AVARIABLE = 10;
        myFunction(aVariable1, "fooBar");
        }"""

        expected = """integer function myf$unction() {
        integer::av$ariable1;
        integer::a$$variable1$$;
        
        av$ariable = 5;
        a$$variable$$ = 10;
        myf$unction(av$ariable1, "fooBar");
        }"""

        actual = translate_case_sensitive_identifier(input)

        self.assertEqualIgnoreWhitespace(expected, actual)

    def test_ifElseBlocks(self):
        input = """integer function myFunction() {
        if (a == 2) {
        stuff_if;
        } else if (a == 3) {
        stuff_else_if;
        } else {
        stuff_else;
        }
        }"""

        expected = """integer function myFunction() {
        if (a == 2) then
        stuff_if;
        else if (a == 3) then
        stuff_else_if;
        else
        stuff_else;
        end if;
        }"""

        actual = convert_conditional_blocks(input)

        self.assertEqualIgnoreWhitespace(expected, actual)

    def test_replaceObjectReferenceDeclaration(self):
        input = """integer function myFunction() {
        myType, object :: myInstance;
        }"""
        expected = """integer function myFunction() {
        type(myType),pointer::myInstance;
        }"""

        actual = replace_object_reference_type_declaration(input)

        self.assertEqualIgnoreWhitespace(expected, actual)

    def test_replaceCastFunctionWithInlineBlock(self):
        input = """integer function myFunction() {
        myType, object :: myInstance;
        myInstance = cast(a_pointer);
        }"""
        expected = """integer function myFunction() {
        myType, object :: myInstance;
        select type(a => a_pointer)
        class is (myType)
        myInstance => a
        end select;
        }"""

        actual = inline_pointer_cast_function(input)

        self.assertEqualIgnoreWhitespace(expected, actual)

    def assertEqualIgnoreWhitespace(self, expected: str, actual: str) -> None:
        expected = re.sub(" *, *", ",", expected)
        actual = re.sub(" *, *", ",", actual)
        self.assertEqual(
            Stream(re.split(r" |\n|\t", expected)).filter(lambda x: x.strip() != "").toList(),
            Stream(re.split(r" |\n|\t", actual)).filter(lambda x: x.strip() != "").toList()
        )
