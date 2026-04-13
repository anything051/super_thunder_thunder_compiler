# HANDOFF

## 1. 已实现模块和功能清单

- `lexer.py`
  - 识别 SNL 关键字、标识符、整数常量、字符常量
  - 识别常见运算符、分隔符、赋值符 `:=`、区间符 `..`
  - 跳过花括号注释和空白符
  - 输出带行列位置的 `Token` 序列和 `EOF`

- `parser.py`
  - 递归下降语法分析
  - 构建程序、声明、过程、语句、表达式 AST
  - 支持 `PROGRAM`、`TYPE`、`VAR`、`PROCEDURE`
  - 支持赋值、`IF/THEN/ELSE/FI`、`WHILE/DO/ENDWH`
  - 支持 `READ`、`WRITE`、`RETURN`、过程调用
  - 支持表达式优先级、数组下标和记录字段的 AST 表达

- `ast_node.py`
  - 定义编译器使用的核心 AST 节点
  - 提供 AST 层次化打印 `pretty_print_ast`

- `semantic.py`
  - 实现符号表、嵌套作用域和类型系统
  - 支持基本类型、类型别名、数组类型、记录类型、过程参数
  - 支持 12 类语义错误检测

- `codegen.py`
  - 生成 MIPS 汇编文本
  - 支持全局变量静态存储
  - 支持表达式、赋值、`READ`、`WRITE`
  - 支持 `IF/ELSE`、`WHILE`
  - 支持过程调用与返回的简化代码生成

- `main.py`
  - 串联 lexer -> parser -> semantic -> codegen
  - 支持 `--dump-tokens` 和 `--dump-ast`
  - 成功时输出 `.asm` 文件
  - 失败时输出统一阶段错误格式

- 测试与样例
  - `test/` 下已有正向、词法、语法、语义错误样例
  - `tests/` 下已有 38 个自动化测试覆盖当前实现

## 2. 每个文件的作用

- `lexer.py`
  - 词法分析器，实现字符流到 Token 流的转换

- `parser.py`
  - 递归下降 parser，实现 Token 流到 AST 的转换

- `ast_node.py`
  - AST 数据结构定义和树形打印

- `semantic.py`
  - 语义分析、符号表、作用域管理、类型检查、语义错误定义

- `codegen.py`
  - MIPS emitter 和目标代码生成逻辑

- `main.py`
  - 命令行入口，负责调试输出、错误收口、汇编文件写出

- `README.md`
  - 项目说明、运行方式、完成标准对照、已知限制

- `HANDOFF.md`
  - 当前交接说明

- `test/hello.snl`
  - 主正向样例，当前演示主流程使用的输入程序

- `test/lexer_cases/basic.snl`
  - 基础词法样例

- `test/lexer_cases/comments.snl`
  - 注释处理词法样例

- `test/parser_cases/minimal_program.snl`
  - 最小可解析程序样例

- `test/parser_cases/if_while.snl`
  - 条件与循环语法样例

- `test/semantic_errors/undefined_identifier.snl`
  - 未定义标识符语义错误样例

- `test/semantic_errors/type_mismatch.snl`
  - 类型不匹配语义错误样例

- `test/semantic_errors/duplicate_decl.snl`
  - 重复定义语义错误样例

- `tests/test_task1_pipeline.py`
  - 主流程串联和阶段失败行为测试

- `tests/test_task2_ast_and_tokens.py`
  - Token/SourcePosition 契约和 AST 结构测试

- `tests/test_task3_lexer.py`
  - lexer 功能测试

- `tests/test_task4_parser.py`
  - parser 功能测试

- `tests/test_task5_cli_and_parser_diagnostics.py`
  - CLI dump 和 parser 错误诊断测试

- `tests/test_task6_semantic.py`
  - 语义分析和 12 类错误测试

- `tests/test_task7_codegen.py`
  - 表达式/IO 代码生成测试

- `tests/test_task8_control_flow_codegen.py`
  - 控制流和过程调用代码生成测试

- `tests/test_task9_sample_programs.py`
  - 样例文件存在性和基本行为回归测试

- `tests/test_task10_readme.py`
  - README 关键信息覆盖测试

## 3. 三个已知缺口

- 数组/记录 selector codegen 已完成
  - 当前 codegen 已支持一维数组元素和一级记录字段的地址计算与读写生成
  - selector 统一走“先求地址、再读写”的 MIPS 生成路径

- 过程调用已改为完整基础栈帧
  - 当前过程调用采用 caller 压实参、callee 保存 `$ra/$fp`、建立 `$fp` 栈帧、返回时恢复现场
  - 过程形参和局部变量已迁移到过程私有栈帧，支持递归和重入场景下的独立存储
  - 仍未实现返回值协议、静态链或 display

- 未经 MARS 实测
  - 当前已能生成 MIPS 汇编并通过本地测试
  - 但还没有用真实 MARS 仿真器做最终运行验证

## 4. 如何运行和测试

- 运行主流程

```bash
python main.py test/hello.snl
```

- 运行主流程并打印 token 和 AST

```bash
python main.py test/hello.snl --dump-tokens --dump-ast
```

- 运行全部自动化测试

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

- 运行单个阶段样例

```bash
python main.py test/semantic_errors/type_mismatch.snl
python main.py test/semantic_errors/duplicate_decl.snl
python main.py test/semantic_errors/undefined_identifier.snl
```

- 当前成功运行后会在源文件同目录生成 `.asm` 文件，例如：

```bash
test/hello.asm
```

## 5. 下一步建议

- 第一优先级
  - 完成一维数组元素和一级记录字段的 selector codegen

- 第二优先级
  - 把过程调用从简化静态模型升级为完整栈帧模型

- 第三优先级
  - 用真实 MARS 仿真器跑通 `test/hello.snl` 和至少一个包含 selector/过程调用的样例

- 做完以上三项后
  - 更新 README 的已知限制
  - 增补对应测试和样例
  - 再进行一次完整验收
