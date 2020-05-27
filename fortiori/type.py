import re

from jivago_streams import Stream

from fortiori.exceptions import InvalidSymbolTypeDeclarationException


class VariableDeclaration(object):

    def __init__(self, type: str, identifier: str):
        self.type = type
        self.identifier = identifier


class FunctionBlock(object):

    def __init__(self, function_name: str, block_start: str, block_end: str, block_content: str):
        """block start/end : Opening and closing curly brackets."""
        self.block_content = block_content
        self.function_name = function_name
        self.block_start = block_start
        self.block_end = block_end


class CodeBlock(object):

    def __init__(self, block_type: str, block_start: str, block_end: str, block_content: str):
        """block start/end : Opening and closing curly brackets."""
        self.block_type = block_type
        self.block_content = block_content
        self.block_start = block_start
        self.block_end = block_end


class SymbolDeclaration(object):

    def __init__(self, symbol_name: str, line: str):
        self.symbol_name = symbol_name
        self.line = line.strip("\n \t")

    def is_gc_object(self) -> bool:
        return bool(re.search(r"object\s*(,\w+)*::", self.line))

    def get_object_declared_type(self) -> str:
        return Stream(re.finditer(r"(\w+)", self.line)) \
            .first() \
            .map(lambda x: x.group(1)) \
            .map(lambda x: x if not "type" in x else re.search(r"type\((w+)\)", x).group(1)) \
            .orElseThrow(InvalidSymbolTypeDeclarationException(self.symbol_name))
