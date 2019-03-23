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
