import re
from typing import List, Iterable

from jivago_streams import Stream

from fortiori.edits import CodeEdit, apply_edits, remove_unused_whitespace
from fortiori.exceptions import TranslationException, CannotFindSymbolDeclarationException
from fortiori.type import VariableDeclaration, FunctionBlock, SymbolDeclaration

VALID_BLOCK_NAMES = ("function", "subroutine", "module", "do", "program")


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
            code_edits.append(CodeEdit(start_pos, end_pos, f"\nend {ending_block};\n"))

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


BLOCKS_WHICH_DECLARE_VARIABLES = ("function", "subroutine", "program")


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
                    if inline_assignation_operator.group(1).strip(" \n\t").startswith("do"):
                        variable_declaration_statements.append(
                            inline_assignation_operator.group(1).strip(" \n\t")[2:] + ";\n")
                        assignation_substatement = "do " + statement[statement.index("::") + 2:]
                    else:
                        variable_declaration_statements.append(
                            inline_assignation_operator.group(1).strip(" \n\t") + ";\n")
                        assignation_substatement = statement[statement.index("::") + 2:]
                    other_statements.append(assignation_substatement)
                else:
                    other_statements.append(statement)

            edits.append(CodeEdit(block_start,
                                  block_end,
                                  "\n" + "\n".join(variable_declaration_statements) +
                                  "\n".join(other_statements) + "\n"))
    return apply_edits(text, edits)


def _find_function_blocks(text: str, block_name: str = "function") -> Iterable[FunctionBlock]:
    for declaration in re.finditer(r"^.*" + block_name + r"([^\(]+)(\(.*\))?.*$", text, flags=re.M):
        if _is_inside_string_block(declaration.start(), text):
            continue
        block_start = text.index("{", declaration.start()) + 1
        block_end = -1
        depth = 0
        function_name = declaration.group(1)
        for bracket in re.finditer(r"(\{|\})", text[declaration.start():]):
            if text[bracket.start()] == "{":
                depth += 1
            else:
                depth -= 1

            if depth == 0:
                block_end = bracket.start()
                break

        yield FunctionBlock(function_name, block_start, block_end, text[block_start:block_end].strip("\n \t"))


def translate_return_statement(text: str) -> str:
    edits: List[CodeEdit] = []
    for function_block in _find_function_blocks(text):
        content = text[function_block.block_start:function_block.block_end]
        if "return" not in content:
            continue

        for return_statement in re.finditer(r"return\s+(.+);", content):
            if _is_inside_string_block(return_statement.start(), text):
                continue
            returned_value = return_statement.group(1)
            edits.append(CodeEdit(function_block.block_start + return_statement.start(),
                                  function_block.block_start + return_statement.end(),
                                  f"{function_block.function_name} = {returned_value};\n"
                                  "return;"))

    return apply_edits(text, edits)


def declare_invoked_function_return_types(text: str) -> str:
    edits: List[CodeEdit] = []
    for block_name in BLOCKS_WHICH_DECLARE_VARIABLES:
        for block in _find_function_blocks(text, block_name=block_name):
            declaration_statements = []
            content = text[block.block_start:block.block_end]
            for function_call in re.finditer(r"(new\s)?([^ \n\t]+)\(.*\)", content):
                if function_call.group(1):
                    continue  # new was found
                invoked_function_name = function_call.group(2)
                invoked_function_declaration = re.search(
                    r"([^ \n\t]+)\s+function\s+" + invoked_function_name + r"\(.*\)",
                    text)
                if not invoked_function_name:
                    raise TranslationException(f"Function {invoked_function_name} is never declared.")

                function_declared_type = invoked_function_declaration.group(1)
                declaration_statements.append(f"{function_declared_type}::{invoked_function_name};")

            edits.append(
                CodeEdit(block.block_start, block.block_start, "\n" + "\n".join(declaration_statements) + "\n"))

    return apply_edits(text, edits)


def add_implicit_none(text: str) -> str:
    edits: List[CodeEdit] = []
    for block_name in BLOCKS_WHICH_DECLARE_VARIABLES:
        for block in _find_function_blocks(text, block_name):
            edits.append(CodeEdit(block.block_start, block.block_start, "\nimplicit none;\n"))

    return apply_edits(text, edits)


def add_name_to_unnamed_program_blocks(text: str) -> str:
    edits: List[CodeEdit] = []
    for program_declaration in re.finditer(r"[^\w\d]program\s*\{", text):
        if _is_inside_string_block(program_declaration.start(), text):
            continue
        edits.append(CodeEdit(program_declaration.start(), program_declaration.end(), "\nprogram main {\n"))

    return apply_edits(text, edits)


def translate_case_sensitive_identifier(text: str) -> str:
    edits: List[CodeEdit] = []
    for word in re.finditer("\w+", text):
        if _is_inside_string_block(word.start(), text):
            continue
        if word.group(0).lower() != word.group(0):
            edits.append(CodeEdit(word.start(), word.end(), _encode_character_case(word.group(0))))

    return apply_edits(text, edits)


def _encode_character_case(word: str) -> str:
    character_wise_encoding = Stream(word) \
        .map(lambda x: [x] if not x.isupper() else [x.lower(), "$"]) \
        .flat() \
        .reduce("", lambda a, e: a + e)

    caps_lock_state, caps_lock_encoding = Stream(word) \
        .reduce((False, ""), lambda state, el:
    (state[0], state[1] + el.lower())
    if (state[0] is False and el.islower()) or (state[0] is True and el.isupper())
    else (not state[0], f"{state[1]}{el.lower()}$$"))

    if caps_lock_state is True:
        caps_lock_encoding += "$$"

    return character_wise_encoding \
        if len(character_wise_encoding) <= len(caps_lock_encoding) \
        else caps_lock_encoding


def _next_word(text: str, start_position: int) -> str:
    return Stream(re.finditer(r"\s*(\w+)", text[start_position:])) \
        .firstMatch(lambda match: not _is_inside_string_block(match.start(), text)) \
        .map(lambda match: match.group(1)) \
        .orElse("")


def _previous_word(text: str, search_end_position: int) -> str:
    return Stream(reversed(list(re.finditer(r"(w+)\s*", text[:search_end_position])))) \
        .firstMatch(lambda match: not _is_inside_string_block(match.start(), text)) \
        .map(lambda match: match.group(1)) \
        .orElse("")


def _block_end(text: str, inside_first_bracket_position: int) -> int:
    block_end = -1
    depth = 1
    for bracket in re.finditer(r"(\{|\})", text[inside_first_bracket_position:]):
        if bracket.group(0) == "{":
            depth += 1
        else:
            depth -= 1
        if depth == 0:
            block_end = bracket.start() + inside_first_bracket_position
            break
    return block_end


def convert_conditional_blocks(text: str) -> str:
    edits: List[CodeEdit] = []

    for if_declaration in re.finditer(r"if\s*(\(.*\))\s*\{", text):
        if_condition = if_declaration.group(1)

        block_end = _block_end(text, if_declaration.end())

        next_word = _next_word(text, block_end)

        edits.append(CodeEdit(if_declaration.start(), if_declaration.end(), f"if {if_condition} then\n"))
        edits.append(CodeEdit(block_end, block_end + 1, ""))

        if next_word != "else":
            edits.append(CodeEdit(block_end, block_end + 1, "end if;"))

    for else_declaration in re.finditer(r"else\s*\{", text):
        block_start = else_declaration.end()
        block_end = _block_end(text, block_start)

        edits.append(CodeEdit(else_declaration.start(), else_declaration.end(), "else\n"))
        edits.append(CodeEdit(block_end, block_end + 1, "end if;\n"))

    return apply_edits(text, edits)


def replace_object_reference_type_declaration(text: str) -> str:
    edits: List[CodeEdit] = []
    for declaration in re.finditer(r"(\w+),\s*object\s*::\s*(.+)$", text, flags=re.M):
        if _is_inside_string_block(declaration.start(), text):
            continue

        edits.append(CodeEdit(declaration.start(),
                              declaration.end(),
                              f"type({declaration.group(1)}),pointer::{declaration.group(2).strip(',')}"))

    return apply_edits(text, edits)


def _find_symbol_declaration(symbol_name: str, text: str, usage_position: int) -> SymbolDeclaration:
    return Stream(reversed(list(
        re.finditer(r"[^:\n;]*::\s*(\w+,)*" + symbol_name + r".*$", text[:usage_position], flags=re.M)))) \
        .firstMatch(lambda x: not _is_inside_string_block(x.start(), text)) \
        .map(lambda x: SymbolDeclaration(symbol_name, text[x.start(): x.end()])) \
        .orElseThrow(CannotFindSymbolDeclarationException(symbol_name))


def inline_pointer_cast_function(text: str) -> str:
    edits: List[CodeEdit] = []
    for cast_call in re.finditer(r"(\w+)\s*=\s*cast\((\w+)\)", text):
        if _is_inside_string_block(cast_call.start(), text):
            continue
        destination_variable = cast_call.group(1)
        source_pointer = cast_call.group(2)

        target_symbol_declaration = _find_symbol_declaration(destination_variable, text, cast_call.start())
        if target_symbol_declaration.is_gc_object():
            edits.append(CodeEdit(cast_call.start(), cast_call.end(), f"""select type(a => {source_pointer})
            class is ({target_symbol_declaration.get_object_declared_type()})
            {destination_variable} => a
            end select"""))
    return apply_edits(text, edits)
