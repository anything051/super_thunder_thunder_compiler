# SNL Compiler Project

## 项目目标
实现 SNL（Small Nested Language）编译器，包含以下模块：
1. 词法分析（Lexer）
2. 语法分析（Parser，递归下降）
3. 语义分析（Semantic Analyzer）
4. 目标代码生成（MIPS 汇编，可选）

## 语言要求
Python 3.x，不依赖第三方编译器生成工具

## 测试方法
python main.py test.snl

## SNL 关键词
PROGRAM, VAR, TYPE, PROCEDURE, BEGIN, END, IF, THEN, ELSE, FI,
WHILE, DO, ENDWH, READ, WRITE, RETURN, INTEGER, CHAR, ARRAY, RECORD, OF
