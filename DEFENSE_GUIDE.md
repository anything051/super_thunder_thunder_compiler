# Defense Guide

这份文档给“做过这个编译器，但对代码细节不够熟”的同学用。目标不是把源码背下来，而是保证答辩时能讲清楚、演示顺、遇到临时样例也不慌。

## 1. 模块核心逻辑大白话解释

### `lexer.py`

`lexer` 干的事最像“切词”。它从头到尾扫描源程序，把一长串字符切成编译器后面能理解的最小单位，也就是 `Token`。比如 `PROGRAM` 会被认成关键字，`x` 会被认成标识符，`123` 会被认成整数常量，`:=`、`;`、`..` 这些也都会被认出来。注释和空白会被跳过，不会进入后续阶段。这个模块的输出不是字符串，而是一串带有行列位置的 token，所以后面 parser 和报错信息都能知道“错在第几行第几列”。

### `parser.py`

`parser` 干的事像“按语法把句子搭成树”。它读取 lexer 给的 token 序列，按 SNL 语言的语法规则做递归下降分析。比如程序最外层要先有 `PROGRAM`，声明区里可能有 `TYPE`、`VAR`、`PROCEDURE`，语句区里可能有赋值、`IF`、`WHILE`、`READ`、`WRITE`、调用过程等等。它最后生成的不是文本，而是一棵 AST，也就是抽象语法树。你可以把 AST 理解成“程序结构图”，后面的语义检查和代码生成都不是直接看原始源码，而是看这棵树。

### `semantic.py`

`semantic` 做的是“语法没错，但意思对不对”的检查。比如变量有没有先声明再使用，类型名是不是真的存在，`INTEGER` 能不能赋值给 `CHAR`，数组下标是不是整数，记录字段名是不是合法，过程调用时参数个数和类型对不对。这一层会维护符号表和作用域，也就是记录“当前有哪些名字、每个名字是什么类型、属于哪个过程作用域”。所以它不只是报错，还顺便把很多类型信息整理好，给 `codegen` 用。

### `codegen.py`

`codegen` 就是把 AST 变成 MIPS 汇编。它会把全局变量放到 `.data`，把主程序和过程体变成 `.text` 里的指令。赋值、表达式、`READ/WRITE`、`IF/WHILE`、过程调用都会在这里翻译成具体的 MIPS 指令。数组下标和记录字段访问是通过“先算地址，再读写内存”来实现的；过程调用则用了基础栈帧模型，也就是 caller 压参数，callee 保存 `$ra/$fp`，再给局部变量和参数分配自己的栈空间。最后生成的 `.asm` 可以直接交给 MARS 跑。

## 2. 老师最可能问的 10 个问题和回答思路

### 1. 你的编译器整体流程是什么？

回答思路：
- 先词法分析，把源码切成 token
- 再语法分析，构建 AST
- 再语义分析，做类型和作用域检查
- 最后代码生成，输出 MIPS 汇编
- `main.py` 把这四步串起来

### 2. 为什么要先构建 AST，不能直接生成代码吗？

回答思路：
- 可以直接生成，但会让语义检查和后续扩展很难做
- AST 把“程序结构”和“源码文本”分开了
- 后面无论做语义分析还是代码生成，都是在统一的数据结构上工作，更清晰

### 3. lexer 怎么区分关键字和普通标识符？

回答思路：
- 都先按“字母开头的一段串”读出来
- 再查关键字表
- 如果在关键字表里，就是关键字；否则就是普通标识符

### 4. parser 为什么用递归下降？

回答思路：
- SNL 语法规模适中，递归下降实现直接、清楚
- 每个语法规则基本对应一个函数，便于调试和展示
- 对课程设计来说，可读性比更复杂的自动生成 parser 更合适

### 5. 语义分析和语法分析的区别是什么？

回答思路：
- 语法分析只看“写法像不像合法句子”
- 语义分析看“意思对不对”
- 例如 `x := y` 这种写法语法上可能没错，但如果 `y` 没定义或类型不匹配，就是语义错误

### 6. 你们怎么处理作用域？

回答思路：
- 用嵌套作用域符号表
- 全局作用域里放全局变量、类型、过程
- 进入过程时新建子作用域
- 查名字时先查当前作用域，再逐层向上找

### 7. 数组和记录字段是怎么生成 MIPS 地址的？

回答思路：
- 先找到基地址
- 数组下标用 `(index - lower) * element_size` 算偏移
- 记录字段按前面字段累计大小算偏移
- 基地址加偏移后得到真正内存地址
- 然后再 `lw` 或 `sw`

### 8. 过程调用为什么要用栈帧？

回答思路：
- 如果参数和局部变量都放静态区，递归和重入会互相覆盖
- 栈帧能保证每次调用都有自己独立的参数和局部变量空间
- 进入过程保存 `$ra/$fp`，返回时恢复，这样调用关系稳定

### 9. 你们现在支持到了什么程度，还有什么限制？

回答思路：
- 已支持词法、语法、12 类语义错误、MIPS 代码生成、真实 MARS 运行
- 支持数组/记录 selector、过程调用栈帧、递归样例
- 还没做 `RETURN expr` 返回值协议，也没做静态链或 display

### 10. 你怎么证明不是“只能过固定样例”？

回答思路：
- 有 47 个自动化测试，不只是一个 hello world
- 有词法、语法、语义、代码生成分层测试
- 还有真实 `Mars.jar` 运行时回归
- 新增了多参数、多个局部变量、selector IO、递归样例

## 3. 现场演示步骤

建议按这个顺序，最稳。

### 第一步：展示项目结构

```bash
ls
```

重点说：
- `lexer.py` / `parser.py` / `semantic.py` / `codegen.py` / `main.py`
- `test/` 里有样例
- `tests/` 里有自动化测试

### 第二步：跑主流程 hello

```bash
python main.py test/hello.snl
```

展示点：
- 编译成功信息
- 生成了 `test/hello.asm`

### 第三步：展示 token 和 AST

```bash
python main.py test/hello.snl --dump-tokens --dump-ast
```

展示点：
- token 序列长什么样
- AST 分层输出长什么样
- 顺便说明“前端阶段已经把程序结构化了”

### 第四步：展示语义错误

```bash
python main.py test/semantic_errors/undefined_identifier.snl
python main.py test/semantic_errors/type_mismatch.snl
```

展示点：
- 编译器不是只会成功，也能在语义阶段卡住错误
- 报错有阶段名和位置信息

### 第五步：展示真实 MARS 运行时回归

```bash
python -m unittest tests.test_task11_mars_runtime -v
```

展示点：
- `hello`
- 多参数过程调用
- 多局部变量
- 过程内部 selector
- `READ/WRITE` 对 selector
- 递归调用

如果时间不够，就单独跑两三个最有代表性的：

```bash
python main.py test/codegen_cases/multi_param.snl
java -Djava.awt.headless=true -jar Mars.jar nc sm test/codegen_cases/multi_param.asm

python main.py test/codegen_cases/recursive_countdown.snl
java -Djava.awt.headless=true -jar Mars.jar nc sm test/codegen_cases/recursive_countdown.asm
```

### 第六步：展示最终验收表

```bash
cat FINAL_CHECK.md
```

展示点：
- 四项完成标准都能对应到测试和运行证据

## 4. 如果老师给一个新的 SNL 程序，如何现场编译和运行

最稳的做法是四步。

### 1. 先把程序保存成一个新文件

假设老师给的程序叫 `demo.snl`，保存到 `test/demo.snl`。

### 2. 先编译，看前端和语义能不能过

```bash
python main.py test/demo.snl
```

如果失败：
- 看报错前缀是 `LEXER`、`PARSER`、`SEMANTIC` 还是 `CODEGEN`
- 再根据行列位置解释问题出在哪

### 3. 如果老师想看 token 或 AST

```bash
python main.py test/demo.snl --dump-tokens --dump-ast
```

这样可以现场说明：
- lexer 切出来了哪些 token
- parser 构建出的 AST 结构是什么

### 4. 如果编译成功，就运行生成的汇编

```bash
java -Djava.awt.headless=true -jar Mars.jar nc sm test/demo.asm
```

如果程序里有 `READ(...)`，可以直接在命令后等待输入，或者用重定向/管道提供输入。

例如：

```bash
printf '9\n' | java -Djava.awt.headless=true -jar Mars.jar nc sm test/demo.asm
```

## 临场提醒

- 不要上来就讲代码细节，先讲“整体流程”
- 老师问实现时，优先用“输入是什么、输出是什么、中间做了什么”来答
- 如果被追问某个函数名，承认“具体函数名记不牢”，但要把逻辑讲对
- 真正最有说服力的不是背源码，而是把新程序编译出来并在 MARS 跑通
