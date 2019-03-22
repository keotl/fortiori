import re
from typing import List

from jivago_streams import Stream


class CodeEdit(object):

    def __init__(self, start_pos: int, end_pos: int, inserted_text: str):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.inserted_text = inserted_text


def apply_edits(text: str, edits: List[CodeEdit]) -> str:
    edited = text
    for edit in reversed(edits):
        edited = edited[:edit.start_pos] + edit.inserted_text + edited[edit.end_pos:]
    return edited


def remove_unused_whitespace(text: str) -> str:
    return "\n".join(Stream(" ".join(Stream(text.split(" ")).filter(lambda x: x != "").toList()) \
                            .split("\n")).filter(lambda x: x != "").toList())
