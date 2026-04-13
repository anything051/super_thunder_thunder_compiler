# Final Check

对照 `AGENTS.md` 完成标准的最终验收结果如下。

| 完成标准 | 结论 | 对应证据 |
| --- | --- | --- |
| 词法：能正确识别所有 token 类型，注释跳过 | 已达成 | `tests/test_task3_lexer.py` 覆盖关键字、标识符、整数常量、字符常量、运算符/分隔符、非法字符、未闭合注释、注释跳过；`tests/test_task9_sample_programs.py` 再次验证 `test/lexer_cases/comments.snl` 可正确词法分析。 |
| 语法：能构建 AST 并层次输出 | 已达成 | `tests/test_task2_ast_and_tokens.py` 验证 AST 节点与 `pretty_print_ast`；`tests/test_task4_parser.py` 覆盖最小程序、声明、过程、控制流、调用、表达式优先级；`tests/test_task5_cli_and_parser_diagnostics.py` 验证 `--dump-ast` 输出。 |
| 语义：能检测 12 类语义错误 | 已达成 | `tests/test_task6_semantic.py` 明确校验 `SEMANTIC_ERROR_TYPES` 共 12 类，并覆盖重复定义、未定义标识符、未定义类型、赋值类型不匹配、数组相关错误、记录相关错误、调用参数个数/类型错误、非法返回、非法 IO 操作数。 |
| 代码生成：MARS 仿真器能跑通测试程序 | 已达成 | `tests/test_task7_codegen.py` 与 `tests/test_task8_control_flow_codegen.py` 覆盖表达式、IO、selector、控制流、过程调用、基础栈帧；`tests/test_task11_mars_runtime.py` 使用真实 `Mars.jar` 运行 `test/hello.snl`、`test/codegen_cases/multi_param.snl`、`test/codegen_cases/multi_locals.snl`、`test/codegen_cases/local_selector.snl`、`test/codegen_cases/read_write_selector.snl`、`test/codegen_cases/recursive_countdown.snl`；`HANDOFF.md` 记录了 `selectors.asm`、`procedure_frame.asm` 等样例的 MARS 实跑结果。 |

## 验收汇总

- 当前自动化测试总数：`47`
- 最新验证命令：`python -m unittest discover -s tests -p 'test_*.py' -v`
- 最新验证结果：`47` 项全部通过
- 真实 MARS 运行时回归：已通过

## 结论

项目已满足 `AGENTS.md` 中列出的四项完成标准，可作为课程设计验收版本。
