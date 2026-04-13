# SNL Compiler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete SNL compiler in Python 3 that performs lexical analysis, recursive-descent parsing, AST construction, semantic checking, and MIPS code generation, runnable via `python main.py test/hello.snl`.

**Architecture:** The compiler is organized as a linear pipeline: `lexer.py` converts source text into tokens, `parser.py` builds AST nodes defined in `ast_node.py`, `semantic.py` validates symbols and types, and `codegen.py` emits MIPS assembly. `main.py` is the single CLI entry that orchestrates the pipeline, surfaces errors consistently, and writes output artifacts for debugging and MARS execution.

**Tech Stack:** Python 3, standard library only, optional `pytest` for local tests, MIPS assembly targeting MARS.

---

## File Map

- Create: `lexer.py`
- Create: `parser.py`
- Create: `ast_node.py`
- Create: `semantic.py`
- Create: `codegen.py`
- Create: `main.py`
- Create: `test/hello.snl`
- Create: `test/semantic_errors/`
- Create: `test/parser_cases/`
- Create: `test/lexer_cases/`
- Create: `README.md`

## Delivery Rules

- Keep module boundaries aligned with `AGENTS.md`.
- Prefer Python dataclasses for structured compiler data.
- All compiler errors must include stage name and source position.
- Every task below must end with a runnable verification command.
- Do not start codegen until parser and semantic outputs are stable.

### Task 1: Scaffold the compiler entry and shared data contracts

**Files:**
- Create: `main.py`
- Create: `lexer.py`
- Create: `parser.py`
- Create: `semantic.py`
- Create: `codegen.py`

- [ ] **Step 1: Create module stubs and a shared pipeline contract**

Add module-level public entrypoints with these names:

```python
# lexer.py
def tokenize(source_code: str):
    raise NotImplementedError

# parser.py
def parse(tokens):
    raise NotImplementedError

# semantic.py
def analyze(ast):
    raise NotImplementedError

# codegen.py
def generate(ast, semantic_result):
    raise NotImplementedError
```

- [ ] **Step 2: Create the main compile pipeline**

Implement `main.py` with:

```python
def compile_file(source_path: str) -> int:
    ...

def main() -> int:
    ...

if __name__ == "__main__":
    raise SystemExit(main())
```

Behavior:
- Read source file
- Call `tokenize`, `parse`, `analyze`, `generate` in order
- Print a success summary
- Return `0` on success and non-zero on failure

- [ ] **Step 3: Add initial stage error handling**

Define a common error format in each stage:

```text
[LEXER] line 3, col 5: unexpected character '@'
[PARSER] line 8, col 1: expected END, got ELSE
[SEMANTIC] line 12, col 9: undefined identifier 'x'
```

- [ ] **Step 4: Verify the CLI wiring**

Run: `python main.py test/hello.snl`

Expected:
- Command runs through the pipeline entrypoints
- It may fail with `FileNotFoundError` or `NotImplementedError` before later tasks
- The failure location should be obvious

- [ ] **Step 5: Commit**

Run:

```bash
git add main.py lexer.py parser.py semantic.py codegen.py
git commit -m "feat: scaffold compiler pipeline entrypoints"
```

### Task 2: Build AST node definitions and token contracts

**Files:**
- Create: `ast_node.py`
- Modify: `lexer.py`
- Modify: `parser.py`

- [ ] **Step 1: Define token and source position dataclasses**

Add to `lexer.py` or a shared section:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class SourcePosition:
    line: int
    column: int

@dataclass(frozen=True)
class Token:
    kind: str
    lexeme: str
    position: SourcePosition
```

- [ ] **Step 2: Define AST dataclasses**

Create `ast_node.py` with at least:
- `ProgramNode`
- `TypeDeclNode`
- `VarDeclNode`
- `ProcedureDeclNode`
- `CompoundStmtNode`
- `AssignStmtNode`
- `IfStmtNode`
- `WhileStmtNode`
- `ReadStmtNode`
- `WriteStmtNode`
- `ReturnStmtNode`
- `CallStmtNode`
- `BinaryExprNode`
- `ConstNode`
- `VarRefNode`

- [ ] **Step 3: Add AST pretty-print support**

Expose one of:

```python
def pretty_print_ast(node, indent: int = 0) -> str:
    ...
```

or instance methods with equivalent output.

- [ ] **Step 4: Verify AST formatting**

Run:

```bash
python - <<'PY'
from ast_node import ProgramNode
print(ProgramNode)
PY
```

Expected:
- Import succeeds
- AST module has no syntax errors

- [ ] **Step 5: Commit**

Run:

```bash
git add ast_node.py lexer.py parser.py
git commit -m "feat: add token contracts and ast node definitions"
```

### Task 3: Implement the lexer for core tokens and keywords

**Files:**
- Modify: `lexer.py`
- Create: `test/lexer_cases/basic.snl`

- [ ] **Step 1: Implement scanning for basic token classes**

Support:
- identifiers
- integer literals
- char literals
- operators
- delimiters
- assignment
- range and punctuation used by SNL declarations

- [ ] **Step 2: Add keyword recognition**

Recognize these keywords exactly:

```text
PROGRAM VAR TYPE PROCEDURE BEGIN END IF THEN ELSE FI
WHILE DO ENDWH READ WRITE RETURN INTEGER CHAR ARRAY RECORD OF
```

- [ ] **Step 3: Skip whitespace and comments**

Requirements:
- comments do not produce tokens
- line and column tracking remains correct
- unclosed comments raise lexer errors

- [ ] **Step 4: Return an EOF token**

Append a terminal token:

```python
Token("EOF", "", SourcePosition(...))
```

- [ ] **Step 5: Verify lexer behavior**

Run:

```bash
python - <<'PY'
from lexer import tokenize
code = "PROGRAM p VAR x : INTEGER ; BEGIN x := 1 ; END"
tokens = tokenize(code)
print([t.kind for t in tokens[:8]])
PY
```

Expected:
- output begins with `PROGRAM`
- token list ends with `EOF`

- [ ] **Step 6: Commit**

Run:

```bash
git add lexer.py test/lexer_cases/basic.snl
git commit -m "feat: implement core snl lexer"
```

### Task 4: Implement parser support for declarations and statements

**Files:**
- Modify: `parser.py`
- Modify: `ast_node.py`
- Create: `test/parser_cases/minimal_program.snl`

- [ ] **Step 1: Add a token stream helper**

Implement parser helpers:

```python
class Parser:
    def current(self): ...
    def advance(self): ...
    def expect(self, kind: str): ...
```

- [ ] **Step 2: Parse top-level program structure**

Support:
- `PROGRAM`
- type declarations
- variable declarations
- procedure declarations
- program body

- [ ] **Step 3: Parse executable statements**

Support:
- assignment
- `IF THEN ELSE FI`
- `WHILE DO ENDWH`
- `READ`
- `WRITE`
- `RETURN`
- procedure call

- [ ] **Step 4: Parse expressions with precedence**

Support:
- literals
- identifiers
- grouped expressions
- binary operators with precedence
- array indexing and record field access

- [ ] **Step 5: Verify parser output**

Run:

```bash
python - <<'PY'
from lexer import tokenize
from parser import parse
ast = parse(tokenize("PROGRAM p BEGIN WRITE(1); END"))
print(type(ast).__name__)
PY
```

Expected:
- parse succeeds
- top-level node is `ProgramNode` or equivalent

- [ ] **Step 6: Commit**

Run:

```bash
git add parser.py ast_node.py test/parser_cases/minimal_program.snl
git commit -m "feat: implement recursive descent parser"
```

### Task 5: Wire AST output and parser error reporting into the CLI

**Files:**
- Modify: `main.py`
- Modify: `parser.py`

- [ ] **Step 1: Improve parser errors**

Include:
- stage name
- line and column
- expected token
- actual token

- [ ] **Step 2: Print AST on successful parse**

`main.py` should:
- print a short token summary optionally
- always print AST summary or tree before semantic analysis in debug mode

- [ ] **Step 3: Add a debug flag**

Support:

```text
python main.py test/hello.snl --dump-tokens --dump-ast
```

- [ ] **Step 4: Verify parser diagnostics**

Run:

```bash
python main.py test/parser_cases/minimal_program.snl --dump-ast
```

Expected:
- AST appears in stdout
- syntax errors are readable if input is malformed

- [ ] **Step 5: Commit**

Run:

```bash
git add main.py parser.py
git commit -m "feat: expose ast output and parser diagnostics"
```

### Task 6: Implement symbol tables and semantic analysis

**Files:**
- Modify: `semantic.py`
- Modify: `ast_node.py`
- Create: `test/semantic_errors/undefined_identifier.snl`

- [ ] **Step 1: Build symbol and scope models**

Implement:

```python
class Symbol: ...
class Scope: ...
class SymbolTable: ...
```

Symbols must cover:
- types
- variables
- parameters
- procedures
- record fields

- [ ] **Step 2: Implement definition and lookup rules**

Requirements:
- nested scope lookup
- duplicate definition detection
- procedure-local scopes

- [ ] **Step 3: Traverse AST and infer expression types**

Validate:
- declarations before use
- assignment compatibility
- array indexing on array values only
- record field access on record values only
- procedure argument count and type checks

- [ ] **Step 4: Define and detect 12 semantic error classes**

Create a stable list such as:
- duplicate declaration
- undefined identifier
- undefined type
- assignment type mismatch
- invalid array index type
- non-array indexed
- invalid record field
- non-record field access
- call argument count mismatch
- call argument type mismatch
- invalid return placement or type
- invalid read/write operand

- [ ] **Step 5: Verify semantic failure handling**

Run:

```bash
python main.py test/semantic_errors/undefined_identifier.snl
```

Expected:
- semantic stage fails
- error includes source position and semantic class

- [ ] **Step 6: Commit**

Run:

```bash
git add semantic.py ast_node.py test/semantic_errors/undefined_identifier.snl
git commit -m "feat: add symbol table and semantic analysis"
```

### Task 7: Implement MIPS code generation for expressions and I/O

**Files:**
- Modify: `codegen.py`
- Modify: `main.py`

- [ ] **Step 1: Create a MIPS emitter**

Implement:

```python
class MipsEmitter:
    def emit_data(self, line: str): ...
    def emit_text(self, line: str): ...
    def new_label(self, prefix: str) -> str: ...
    def render(self) -> str: ...
```

- [ ] **Step 2: Generate assembly for literals, variables, assignments, READ, and WRITE**

Support:
- integer literal loading
- variable storage and load
- simple arithmetic
- syscall-based read
- syscall-based write

- [ ] **Step 3: Write `.asm` output from `main.py`**

On success:
- write output beside source file or to a deterministic output path
- print generated assembly file path

- [ ] **Step 4: Verify assembly generation**

Run:

```bash
python main.py test/hello.snl
```

Expected:
- `.asm` file is created
- output contains `.data` and `.text`

- [ ] **Step 5: Commit**

Run:

```bash
git add codegen.py main.py
git commit -m "feat: generate mips for expressions and io"
```

### Task 8: Implement control flow and procedure call code generation

**Files:**
- Modify: `codegen.py`
- Modify: `semantic.py`

- [ ] **Step 1: Generate conditional and loop labels**

Support:
- `IF/ELSE/FI`
- `WHILE/DO/ENDWH`

- [ ] **Step 2: Add a calling convention**

At minimum define:
- how arguments are passed
- how return flow works
- how temporaries are preserved

- [ ] **Step 3: Generate procedure calls and returns**

Support:
- call setup
- jump and return
- local procedure body emission

- [ ] **Step 4: Verify control flow generation**

Run:

```bash
python main.py test/hello.snl
```

Expected:
- resulting assembly contains branch or jump labels for flow control
- generated assembly remains syntactically valid MIPS

- [ ] **Step 5: Commit**

Run:

```bash
git add codegen.py semantic.py
git commit -m "feat: add control flow and procedure call codegen"
```

### Task 9: Add sample programs and regression cases

**Files:**
- Create: `test/hello.snl`
- Create: `test/lexer_cases/comments.snl`
- Create: `test/parser_cases/if_while.snl`
- Create: `test/semantic_errors/type_mismatch.snl`
- Create: `test/semantic_errors/duplicate_decl.snl`

- [ ] **Step 1: Create one end-to-end passing sample**

`test/hello.snl` must include:
- `PROGRAM`
- variable declaration
- assignment
- `WRITE`

- [ ] **Step 2: Create focused lexer and parser samples**

Add:
- one comment-heavy lexer sample
- one parser sample using `IF` and `WHILE`

- [ ] **Step 3: Create semantic negative samples**

Add at least:
- undefined identifier
- duplicate declaration
- type mismatch

- [ ] **Step 4: Verify all sample entrypoints**

Run:

```bash
python main.py test/hello.snl
python main.py test/semantic_errors/type_mismatch.snl
python main.py test/semantic_errors/duplicate_decl.snl
```

Expected:
- positive case reaches code generation
- negative cases fail in semantic stage with distinct diagnostics

- [ ] **Step 5: Commit**

Run:

```bash
git add test
git commit -m "test: add sample snl programs and regression cases"
```

### Task 10: Final integration, documentation, and acceptance mapping

**Files:**
- Create: `README.md`
- Modify: `main.py`

- [ ] **Step 1: Document project usage**

Include:
- project structure
- run command
- output files
- supported language features
- known limitations

- [ ] **Step 2: Add acceptance checklist mapping**

Map README sections to AGENTS.md completion criteria:
- lexical support
- AST construction
- 12 semantic errors
- MARS-compatible output

- [ ] **Step 3: Verify the final demo path**

Run:

```bash
python main.py test/hello.snl
```

Expected:
- command completes without Python exceptions
- success output states where assembly was written

- [ ] **Step 4: Commit**

Run:

```bash
git add README.md main.py
git commit -m "docs: add usage guide and acceptance checklist"
```

## Self-Review

- Spec coverage: the plan covers pipeline scaffolding, lexer, AST, parser, semantic analysis, 12 semantic errors, MIPS codegen, integration samples, and final acceptance mapping from `AGENTS.md`.
- Placeholder scan: no `TODO` or `TBD` markers remain.
- Type consistency: shared names across tasks are `tokenize`, `parse`, `analyze`, `generate`, `ProgramNode`, and `compile_file`.
