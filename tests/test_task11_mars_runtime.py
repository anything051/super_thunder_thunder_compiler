import subprocess
import unittest
from pathlib import Path


def compile_sample(source_path: str) -> Path:
    import main

    exit_code = main.compile_file(source_path)
    if exit_code != 0:
        raise AssertionError(f"failed to compile {source_path}")
    return Path(source_path).with_suffix(".asm")


def run_mars(asm_path: Path, input_data: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "java",
            "-Djava.awt.headless=true",
            "-jar",
            "Mars.jar",
            "nc",
            "sm",
            str(asm_path),
        ],
        cwd=Path(__file__).resolve().parent.parent,
        input=input_data,
        text=True,
        capture_output=True,
        check=False,
    )


def program_stdout(raw_stdout: str) -> str:
    lines = [line.strip() for line in raw_stdout.splitlines() if line.strip()]
    filtered = [line for line in lines if not line.startswith("[")]
    return "".join(filtered)


class MarsRuntimeTests(unittest.TestCase):
    def assert_mars_output(self, source_path: str, expected_output: str, input_data: str = "") -> None:
        self.assertTrue(Path(source_path).exists(), source_path)
        asm_path = compile_sample(source_path)
        result = run_mars(asm_path, input_data=input_data)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(program_stdout(result.stdout), expected_output)

    def test_hello_sample_runs_in_mars(self):
        self.assert_mars_output("test/hello.snl", "7")

    def test_multi_parameter_procedure_runs_in_mars(self):
        self.assert_mars_output("test/codegen_cases/multi_param.snl", "7")

    def test_multiple_locals_do_not_overlap_in_mars(self):
        self.assert_mars_output("test/codegen_cases/multi_locals.snl", "23")

    def test_procedure_local_selector_runs_in_mars(self):
        self.assert_mars_output("test/codegen_cases/local_selector.snl", "6")

    def test_read_write_selector_runs_in_mars(self):
        self.assert_mars_output("test/codegen_cases/read_write_selector.snl", "9", input_data="9\n")

    def test_recursive_call_runs_in_mars(self):
        self.assert_mars_output("test/codegen_cases/recursive_countdown.snl", "210")


if __name__ == "__main__":
    unittest.main()
