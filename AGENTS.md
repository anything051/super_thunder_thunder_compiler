cat > AGENTS.md << 'EOF'
# SNL Compiler - 编译原理课程设计

## 项目目标
实现 SNL 语言完整编译器，语言：Python 3

## 模块结构
- lexer.py      词法分析，输出 Token 列表
- parser.py     递归下降语法分析，构建 AST
- ast_node.py   AST 节点定义
- semantic.py   语义分析 + 符号表
- codegen.py    MIPS 汇编代码生成
- main.py       入口，串联所有模块

## 测试命令
python main.py test/hello.snl

## SNL 关键字
PROGRAM VAR TYPE PROCEDURE BEGIN END IF THEN ELSE FI
WHILE DO ENDWH READ WRITE RETURN INTEGER CHAR ARRAY RECORD OF

## 完成标准
- 词法：能正确识别所有 token 类型，注释跳过
- 语法：能构建 AST 并层次输出
- 语义：能检测 12 类语义错误
- 代码生成：MARS 仿真器能跑通测试程序
EOF
