import re
from typing import List

from jivago_streams import Stream

from dialect.edits import CodeEdit, apply_edits, remove_unused_whitespace
from dialect.type import VariableDeclaration

VALID_BLOCK_NAMES = ("function", "subroutine", "module", "do", "if", "program")


def strip_comments(text: str) -> str:
    lines = text.split("\n")
    result = []
    for line in lines:
        if "!" in line:
            comment_markers = re.finditer("!", line)
            first_comment_marker_index = Stream(comment_markers) \
                .map(lambda matcher: matcher.start()) \
                .filter(lambda pos: not _is_inside_string_block(pos, line)) \
                .first()
            if first_comment_marker_index.isPresent():
                result.append(line[:first_comment_marker_index.get()])
            else:
                result.append(line)
        else:
            result.append(line)

    return "\n".join(result)


def remove_curly_brackets(text: str) -> str:
    code_block_stack = []
    brackets = re.finditer(r"\{|\}", text)
    code_edits: List[CodeEdit] = []

    for bracket_match in brackets:
        start_pos, end_pos = bracket_match.start(), bracket_match.end()
        if _is_inside_string_block(start_pos, text):
            continue
        if text[start_pos] == '{':
            code_block_stack.append(_previous_keyword(text, start_pos))
            code_edits.append(CodeEdit(start_pos, end_pos, "\n"))
        else:
            ending_block = code_block_stack.pop()
            code_edits.append(CodeEdit(start_pos, end_pos, f"\nend {ending_block}"))

    return remove_unused_whitespace(apply_edits(text, code_edits))


def _previous_keyword(text: str, bracket_position: int) -> str:
    return Stream(VALID_BLOCK_NAMES) \
        .filter(lambda block: block in text[:bracket_position]) \
        .map(lambda block: (block, text.rindex(block, 0, bracket_position))) \
        .reduce(("", -1), lambda acc, e: acc if acc[1] > e[1] else e)[0]


def remove_line_splits_inside_blocks(text: str) -> str:
    depth = 0
    result = ""
    for line in text.split("\n"):
        depth += line.count("(") - line.count(")")
        if depth > 0:
            result += line
        else:
            result += line + "\n"
    return result


def _is_inside_string_block(position: int, text: str) -> bool:
    for quote_symbol in ('"', "'"):
        quotes = re.finditer(f"\\{quote_symbol}", text[:position])
        quotes_count = Stream(quotes).count()
        if quotes_count % 2 == 1:
            return True
    return False


def move_function_parameter_type_declaration_to_body(text: str) -> str:
    edits: List[CodeEdit] = []
    for function_declaration in re.finditer(r"^\s*\S+( |\n)+function( |\n)+.+( |\n)*\(", text):
        if _is_inside_string_block(function_declaration.start(), text):
            continue

        depth = 1
        declaration_closing_parenthesis = None
        for parenthesis in re.finditer(r"(\(|\))", text[function_declaration.end():]):
            if text[parenthesis.start()] == '(':
                depth += 1
            else:
                depth -= 1
            if depth == 0:
                declaration_closing_parenthesis = parenthesis.start() + function_declaration.end()

        function_opening_curly_bracket = text.index("{", function_declaration.end())
        parameter_str = text[function_declaration.end():declaration_closing_parenthesis]

        parameter_declarations: List[VariableDeclaration] = []
        parameter = re.search(r"::( |\n)*[^,\) \n]+", parameter_str)
        while parameter:
            identifier = parameter_str[parameter.start() + 2:parameter.end()].strip(" \n\t")
            declared_type = parameter_str[:parameter.start()].strip(", \n\t")
            parameter_declarations.append(VariableDeclaration(declared_type, identifier))

            parameter_str = parameter_str[parameter.end():]
            parameter = re.search(r"::( |\n)*[^,\) \n]+", parameter_str)

        edits.append(CodeEdit(function_declaration.start(),
                              declaration_closing_parenthesis + 1,
                              text[function_declaration.start():function_declaration.end()] + ",".join(
                                  Stream(parameter_declarations).map(lambda x: x.identifier)) + ")"))
        edits.append(CodeEdit(function_opening_curly_bracket,
                              function_opening_curly_bracket + 1,
                              "{\n" + "\n".join(
                                  Stream(parameter_declarations).map(lambda x: f"{x.type}::{x.identifier}"))))
    return apply_edits(text, edits)


BLOCKS_WHICH_DECLARE_VARIABLES = ("function", "procedure", "program")


def move_variable_declaration_to_start_of_block(text: str) -> str:
    edits: List[CodeEdit] = []
    for block_name in BLOCKS_WHICH_DECLARE_VARIABLES:
        for declaration in re.finditer(r"^.*" + block_name + r".*(\(.*\))?.*$", text, flags=re.M):
            block_start = text.index("{", declaration.start()) + 1
            block_end = -1
            depth = 0
            for bracket in re.finditer(r"(\{|\})", text[declaration.start():]):
                if text[bracket.start()] == "{":
                    depth += 1
                else:
                    depth -= 1

                if depth == 0:
                    block_end = bracket.start()
                    break

            code_block_str = text[block_start:block_end].strip("\n \t")
            variable_declaration_statements = []
            other_statements = []

            for statement in code_block_str.split("\n"):
                inline_assignation_operator = re.search(r"((.|\s)+::(.|\s)+)(=[^=])", statement)
                if inline_assignation_operator:
                    variable_declaration_statements.append(inline_assignation_operator.group(1).strip(" \n\t") + ";\n")
                    assignation_substatement = statement[statement.index("::")+2:]
                    other_statements.append(assignation_substatement)
                else:
                    other_statements.append(statement)

            edits.append(CodeEdit(block_start,
                                  block_end,
                                  "\n" + "\n".join(variable_declaration_statements) +
                                  "\n".join(other_statements) + "\n"))
    return apply_edits(text, edits)
