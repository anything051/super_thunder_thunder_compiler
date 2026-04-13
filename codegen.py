class CodegenError(Exception):
    """Raised when code generation fails."""


def generate(ast, semantic_result):
    raise NotImplementedError("codegen stage is not implemented yet")
