# SNL Compiler

Python 3 实现的 SNL（Small Nested Language）课程编译器，覆盖词法分析、递归下降语法分析、AST 构建、语义检查和 MIPS 汇编生成。

## 运行方式

主流程命令：

```bash
python main.py test/hello.snl
```

调试输出：

```bash
python main.py test/hello.snl --dump-tokens --dump-ast
```

成功时会在源文件同目录生成同名 `.asm` 文件，例如 `test/hello.asm`。

## 模块结构

- `lexer.py`：词法分析，输出带行列位置的 `Token` 序列
- `parser.py`：递归下降语法分析，构建 AST
- `ast_node.py`：AST 节点定义和树形输出
- `semantic.py`：语义分析、符号表、作用域与类型检查
- `codegen.py`：MIPS 汇编生成
- `main.py`：CLI 入口，串联编译流程
- `test/`：正向样例、词法样例、语法样例、语义错误样例
- `tests/`：单元测试和回归测试

## 当前支持范围

词法：
- 关键字、标识符、整数常量、字符常量
- 常见运算符与分隔符
- 花括号注释跳过
- EOF token 和非法字符报错

语法：
- `PROGRAM`
- `TYPE`、`VAR`、`PROCEDURE`
- `BEGIN ... END`
- 赋值、`IF THEN ELSE FI`、`WHILE DO ENDWH`
- `READ`、`WRITE`、`RETURN`
- 过程调用
- 表达式优先级
- 数组下标和记录字段访问的 AST 表达

语义：
- 符号表与嵌套作用域
- 类型别名、数组、记录、过程参数
- 12 类语义错误检测

代码生成：
- 全局变量静态存储
- 表达式、赋值、`READ`、`WRITE`
- `IF/ELSE`、`WHILE`
- 数组下标和记录字段 selector 地址计算
- 过程调用与返回的基础完整栈帧约定（caller 压实参，callee 保存 `$ra/$fp`）
- 输出 MIPS 汇编，目标运行环境为 MARS

## 测试样例

正向样例：
- `test/hello.snl`
- `test/parser_cases/if_while.snl`
- `test/codegen_cases/selectors.snl`
- `test/codegen_cases/procedure_frame.snl`
- `test/codegen_cases/multi_param.snl`
- `test/codegen_cases/multi_locals.snl`
- `test/codegen_cases/local_selector.snl`
- `test/codegen_cases/read_write_selector.snl`
- `test/codegen_cases/recursive_countdown.snl`

词法样例：
- `test/lexer_cases/basic.snl`
- `test/lexer_cases/comments.snl`

语义反向样例：
- `test/semantic_errors/undefined_identifier.snl`
- `test/semantic_errors/type_mismatch.snl`
- `test/semantic_errors/duplicate_decl.snl`

## 已实现的 12 类语义错误

- `DUPLICATE_DECLARATION`
- `UNDEFINED_IDENTIFIER`
- `UNDEFINED_TYPE`
- `ASSIGNMENT_TYPE_MISMATCH`
- `INVALID_ARRAY_INDEX_TYPE`
- `NON_ARRAY_INDEXED`
- `INVALID_RECORD_FIELD`
- `NON_RECORD_FIELD_ACCESS`
- `CALL_ARGUMENT_COUNT_MISMATCH`
- `CALL_ARGUMENT_TYPE_MISMATCH`
- `INVALID_RETURN`
- `INVALID_IO_OPERAND`

## 已知限制

- `RETURN expr` 形式未实现返回值协议
- 未实现静态链或 display，嵌套过程只依赖全局变量与当前过程私有栈帧
- 暂未实现更完整的运行时协议，例如返回值寄存器约定、静态链访问和更丰富的数据布局优化

## MARS 验证建议

先运行真实 MARS 回归：

```bash
python -m unittest tests.test_task11_mars_runtime -v
```

也可以手动生成并运行单个样例：

```bash
python main.py test/codegen_cases/selectors.snl
java -Djava.awt.headless=true -jar Mars.jar nc sm test/codegen_cases/selectors.asm
```

当前已通过真实 MARS 验证的样例包括：
- `test/hello.snl`
- `test/codegen_cases/selectors.snl`
- `test/codegen_cases/procedure_frame.snl`
- `test/codegen_cases/multi_param.snl`
- `test/codegen_cases/multi_locals.snl`
- `test/codegen_cases/local_selector.snl`
- `test/codegen_cases/read_write_selector.snl`
- `test/codegen_cases/recursive_countdown.snl`

说明：
- 在当前无图形环境下运行 MARS 需要加 `-Djava.awt.headless=true`
- Java 可能输出 `preferences` 或 `hsperfdata` 告警，但不影响程序运行结果

## 完成标准对照

### 词法

- 已实现所有 AGENTS.md 列出的关键字识别
- 已支持注释跳过和非法字符报错

### 语法

- 已实现递归下降 parser
- 已支持 AST 构建和层次输出

### 语义

- 已实现符号表和作用域管理
- 已覆盖 12 类语义错误

### 代码生成

- 已生成可执行的 MIPS 汇编输出
- `python main.py test/hello.snl` 已可生成 `test/hello.asm`
- 已通过真实 `Mars.jar` 跑通 `hello`、selector、多参数过程、多个局部变量、过程内 selector、selector IO 和递归样例

## 验收文件

- `HANDOFF.md`：当前实现、测试和 MARS 运行结果汇总
- `FINAL_CHECK.md`：对照 `AGENTS.md` 完成标准的最终验收对照表
