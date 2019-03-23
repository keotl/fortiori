import re
from typing import List

from jivago_streams import Stream

from dialect.edits import CodeEdit, apply_edits, remove_unused_whitespace

VALID_BLOCK_NAMES = ("function", "subroutine", "module", "do", "if", "program")


def strip_comments(text: str) -> str:
    lines = text.split("\n")
    result = []
    for line in lines:
        if "!" in line:
            comment_markers = re.finditer("!", line)
            first_comment_marker_index = Stream(comment_markers) \
                .map(lambda matcher: matcher.regs[0][0]) \
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
        start_pos, end_pos = bracket_match.regs[0]
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
    pass


def _is_inside_string_block(position: int, text: str) -> bool:
    for quote_symbol in ('"', "'"):
        quotes = re.finditer(f"\\{quote_symbol}", text[:position])
        quotes_count = Stream(quotes).count()
        if quotes_count % 2 == 1:
            return True
    return False
