# Codegen Gaps Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fill the remaining code generation gaps for selector addressing, procedure stack frames, and MARS-oriented validation in the SNL compiler.

**Architecture:** Extend `codegen.py` with explicit storage layout metadata instead of label-only storage resolution. Selector codegen will compute addresses from a global label or frame-pointer-relative base. Procedure calls will switch from static data-backed locals to per-call stack frames using `$sp/$fp`, while globals remain in `.data`. Validation will add sample SNL programs and regression tests that assert the generated assembly follows the expected MIPS conventions.

**Tech Stack:** Python 3, `unittest`, existing compiler modules (`lexer.py`, `parser.py`, `semantic.py`, `codegen.py`)

---

### Task 1: Selector Addressing

**Files:**
- Modify: `codegen.py`
- Modify: `tests/test_task7_codegen.py`
- Modify: `HANDOFF.md`

- [ ] **Step 1: Write the failing test**

```python
    def test_generate_selector_addressing_for_array_and_record(self):
        from codegen import generate

        ast, semantic_result = compile_semantic_result(
            """
PROGRAM demo
TYPE pair = RECORD
  left, right : INTEGER;
END;
VAR nums : ARRAY [1..3] OF INTEGER;
VAR item : pair;
BEGIN
  nums[2] := 7;
  item.right := nums[2];
  WRITE(item.right);
END
"""
        )

        assembly = generate(ast, semantic_result)

        self.assertIn("nums: .space 12", assembly)
        self.assertIn("item: .space 8", assembly)
        self.assertIn("la $t1, nums", assembly)
        self.assertIn("addi $t2, $t0, -1", assembly)
        self.assertIn("mul $t2, $t2, 4", assembly)
        self.assertIn("add $t1, $t1, $t2", assembly)
        self.assertIn("sw $t0, 0($t1)", assembly)
        self.assertIn("la $t1, item", assembly)
        self.assertIn("addi $t1, $t1, 4", assembly)
        self.assertIn("lw $a0, 0($t1)", assembly)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_task7_codegen.CodegenTests.test_generate_selector_addressing_for_array_and_record -v`
Expected: FAIL with `CodegenError` about selector-based assignments or missing selector address generation.

- [ ] **Step 3: Write minimal implementation**

```python
def _emit_var_address(self, var_ref: VarRefNode, current_scope: str | None, target_register: str = "$t1") -> Any:
    storage = self._resolve_storage(var_ref.name, current_scope)
    self._emit_storage_address(storage, target_register)
    current_type = storage.type_info
    for selector in var_ref.selectors:
        if selector["kind"] == "index":
            ...
        elif selector["kind"] == "field":
            ...
    return current_type
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_task7_codegen.CodegenTests.test_generate_selector_addressing_for_array_and_record -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add codegen.py tests/test_task7_codegen.py HANDOFF.md docs/superpowers/plans/2026-04-13-codegen-gaps.md
git commit -m "feat: add selector address codegen"
```

### Task 2: Procedure Stack Frames

**Files:**
- Modify: `codegen.py`
- Modify: `tests/test_task8_control_flow_codegen.py`
- Modify: `HANDOFF.md`

- [ ] **Step 1: Write the failing test**

```python
    def test_generate_procedure_stack_frame_and_argument_passing(self):
        from codegen import generate

        ast, semantic_result = compile_semantic_result(
            """
PROGRAM demo
VAR x : INTEGER;
PROCEDURE show(a : INTEGER);
VAR temp : INTEGER;
BEGIN
  temp := a;
  WRITE(temp);
  RETURN;
END
BEGIN
  x := 7;
  show(x);
END
"""
        )

        assembly = generate(ast, semantic_result)

        self.assertIn("addi $sp, $sp, -4", assembly)
        self.assertIn("sw $ra, 0($sp)", assembly)
        self.assertIn("sw $fp, 4($sp)", assembly)
        self.assertIn("move $fp, $sp", assembly)
        self.assertIn("lw $t0, 8($fp)", assembly)
        self.assertIn("sw $t0, -4($fp)", assembly)
        self.assertIn("lw $ra, 0($fp)", assembly)
        self.assertIn("lw $fp, 4($fp)", assembly)
        self.assertIn("jal show", assembly)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_task8_control_flow_codegen.ControlFlowCodegenTests.test_generate_procedure_stack_frame_and_argument_passing -v`
Expected: FAIL because current code stores params/locals in `.data` labels and does not emit a stack frame.

- [ ] **Step 3: Write minimal implementation**

```python
@dataclass(frozen=True)
class FrameLayout:
    size: int
    param_offsets: dict[str, int]
    local_offsets: dict[str, int]

def _emit_procedure_prologue(self, procedure_name: str) -> None:
    frame = self.frame_layouts[procedure_name]
    self.emitter.emit_text(f"addi $sp, $sp, -{frame.size}")
    self.emitter.emit_text("sw $ra, 0($sp)")
    self.emitter.emit_text("sw $fp, 4($sp)")
    self.emitter.emit_text("move $fp, $sp")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_task8_control_flow_codegen.ControlFlowCodegenTests.test_generate_procedure_stack_frame_and_argument_passing -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add codegen.py tests/test_task8_control_flow_codegen.py HANDOFF.md
git commit -m "feat: use stack frames for procedure calls"
```

### Task 3: MARS Validation Samples

**Files:**
- Create: `test/codegen_cases/selectors.snl`
- Create: `test/codegen_cases/procedure_frame.snl`
- Modify: `tests/test_task9_sample_programs.py`
- Modify: `README.md`
- Modify: `HANDOFF.md`

- [ ] **Step 1: Write the failing test**

```python
    def test_mars_validation_samples_exist_and_compile(self):
        import main

        sample_paths = [
            "test/codegen_cases/selectors.snl",
            "test/codegen_cases/procedure_frame.snl",
        ]

        for sample_path in sample_paths:
            with self.subTest(sample_path=sample_path):
                exit_code = main.compile_file(sample_path)
                self.assertEqual(exit_code, 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_task9_sample_programs.SampleProgramRegressionTests.test_mars_validation_samples_exist_and_compile -v`
Expected: FAIL because the files and regression do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```snl
PROGRAM selectors
TYPE pair = RECORD
  left, right : INTEGER;
END;
VAR nums : ARRAY [1..3] OF INTEGER;
VAR item : pair;
BEGIN
  nums[2] := 7;
  item.right := nums[2];
  WRITE(item.right);
END
```

```snl
PROGRAM procframe
VAR x : INTEGER;
PROCEDURE show(a : INTEGER);
VAR temp : INTEGER;
BEGIN
  temp := a + 1;
  WRITE(temp);
  RETURN;
END
BEGIN
  x := 7;
  show(x);
END
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_task9_sample_programs.SampleProgramRegressionTests.test_mars_validation_samples_exist_and_compile -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add test/codegen_cases/selectors.snl test/codegen_cases/procedure_frame.snl tests/test_task9_sample_programs.py README.md HANDOFF.md
git commit -m "test: add MARS validation samples"
```
