from typing import List

from jivago_streams import Stream


class CodeEdit(object):

    def __init__(self, start_pos: int, end_pos: int, inserted_text: str):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.inserted_text = inserted_text

    def _apply(self, text: str) -> str:
        return text[:self.start_pos] + self.inserted_text + text[self.end_pos:]


def apply_edits(text: str, edits: List[CodeEdit]) -> str:
    edited = text
    for edit in sorted(edits, key=lambda edit: edit.start_pos, reverse=True):
        edited = edit._apply(edited)
    return edited


def remove_unused_whitespace(text: str) -> str:
    return "\n".join(Stream(" ".join(Stream(text.split(" ")).filter(lambda x: x != "").toList()) \
                            .split("\n")).filter(lambda x: x != "").toList())
