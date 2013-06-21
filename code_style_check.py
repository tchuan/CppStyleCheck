# -*- coding:utf-8 -*-

# 根据GoogleCodeStyle修改.cpp文件的编码规范，主要有以下几点
# 删除行尾空格
# Tab->4 Spaces
# if, while, for, switch等语句的规范:keyword (condition)
# ' == ', ', ','for (con; con; con)'
# > < >= <= == >> <<

import os
import sys
import re

_regexp_compile_cache = {}


def _Substitute(pattern, s, sub):
    if not pattern in _regexp_compile_cache:
        _regexp_compile_cache[pattern] = re.compile(pattern)
    return _regexp_compile_cache[pattern].sub(sub, s)


def _Search(pattern, s):
    if not pattern in _regexp_compile_cache:
        _regexp_compile_cache[pattern] = re.compile(pattern)
    return _regexp_compile_cache[pattern].search(s)


def _Findall(pattern, s):
    if not pattern in _regexp_compile_cache:
        _regexp_compile_cache[pattern] = re.compile(pattern)
    return _regexp_compile_cache[pattern].findall(s)


def _Split(pattern, s):
    if not pattern in _regexp_compile_cache:
        _regexp_compile_cache[pattern] = re.compile(pattern)
    return _regexp_compile_cache[pattern].split(s)


def _IsBlankLine(line):
    return not line or line.isspace()


#TODO: need to handle all the following
#function(abc
#function(abc, [def], "string("
#function(abc, [def], "string(", ghi(
def _FindUnmatchedLeftBracket(line):
    """搜索不匹配的("""
    index = [-1]
    count = 0
    for ch in line:
        count += 1
        if ch == '(':
            index.append(count)
        if ch == ')':
            index.pop()
    return index[len(index) - 1]


def _FindUnmatchedRightBracket(line):
    """搜索不匹配的)"""
    index = [-1]
    count = len(line) - 1
    for count in xrange(count, -1, -1):
        ch = line[count]
        if ch == ')':
            index.append(count)
        if ch == '(':
            index.pop()
    return index[len(index) - 1]


def _ProcessSpaces(line):
    """ 规范操作符左右的空格
    单运算符->双运算符->关键字"""
    if _IsBlankLine(line):
        return line
    line = _Substitute(r'\s!(?!=)\s', line, '!')
    # && || == != >= <= ->
    line = _Substitute(r'\s*&&\s*', line, ' && ')
    line = _Substitute(r'\s*\|\|\s*', line, ' || ')
    line = _Substitute(r'\s*==\s*', line, ' == ')
    line = _Substitute(r'\s*!=\s*', line, ' != ')
    line = _Substitute(r'\s*>=\s*', line, ' >= ')
    line = _Substitute(r'\s*<=\s*', line, ' <= ')
    line = _Substitute(r'\s*->\s*', line, '->')
    line = _Substitute(r'::\s*', line, '::')
    # ++ -- += -= *= /= %= &= ^= |= + - = * / % > < & | ~ !
    line = _Substitute(r'\s*\+\+\s*', line, '++')
    line = _Substitute(r'\s*--\s*', line, '--')
    line = _Substitute(r'\s*\+=\s*', line, ' += ')
    line = _Substitute(r'\s*\-=\s*', line, ' -= ')
    line = _Substitute(r'\s*(?<!/)\*=\s*', line, ' *= ')
    line = _Substitute(r'\s*\/=\s*', line, ' /= ')
    line = _Substitute(r'\s*\|=\s*', line, ' |= ')
    line = _Substitute(r'(?<=\w)\s*\+\s*(?=\w)', line, ' + ')
    line = _Substitute(r'(?<=\w)\s*\-\s*(?=\w)', line, ' - ')
    line = _Substitute(r'(?<![\-\+\*\|%&!\^><=])\s*=\s*(?!=)', line, ' = ')
    line = _Substitute(r'(?<=\w)/(?=\w)', line, ' / ')
    line = _Substitute(r'\s*%\s*', line, ' % ')
    line = _Substitute(r'(?<![->])\s*\>\s*(?![=>])', line, ' > ')
    line = _Substitute(r'(?<!<)\s*\<\s*(?![<=])', line, ' < ')
    line = _Substitute(r'(?<!\|)\s*\|\s*(?![\|=])', line, ' | ')
    #TODO, how to identify &/*/~ ?
    # , ; ? :
    line = _Substitute(r'\s*;\s*', line, '; ')
    line = _Substitute(r'\s*,\s*', line, ', ')
    line = _Substitute(r'\s*\?\s*', line, ' ? ')
    line = _Substitute(r'(?<!:)\s*:\s*(?!:)', line, ' : ')
    # () []
    line = _Substitute(r'\(\s', line, '(')
    line = _Substitute(r'\s+\)', line, ')')
    line = _Substitute(r'\[\s', line, '[')
    line = _Substitute(r'\s\]', line, ']')
    # if else_if while for switch
    line = _Substitute(r'if\s*\(\s*', line, 'if (')
    line = _Substitute(r'else\s+ if', line, 'else if')
    line = _Substitute(r'while\s*\(\s*', line, 'while (')
    line = _Substitute(r'switch\s*\(\s*', line, 'switch (')
    line = _Substitute(r'for\s*\(\s*', line, 'for (')
    # 去除可能引入的空格
    return line.strip()


def _ProcessBreaklines(lines, line, line_num):
    """ 正确处理断行 """
    if line.startswith('&&'):
        lines[line_num - 1] += ' &&'
        line = line[2:]
    elif line.startswith('||'):
        lines[line_num - 1] += ' ||'
        line = line[2:]
    elif line.startswith(','):
        lines[line_num - 1] += ','
        line = line[2:]

    return line


def _ProcessScope(lines, line, line_num):
    """ 处理同行的{ } ;"""
    if line == '{' or line == '}':
        return line
    if line.find('{') > 0:
        lines.pop(line_num)
        new_lines = [l for l in line.partition('{') if l != '']
        lines[line_num:line_num] = new_lines
        return lines[line_num]
    if line.find('}') > 0:
        lines.pop(line_num)
        new_lines = [l for l in line.partition('}') if l != '']
        lines[line_num:line_num] = new_lines
        return lines[line_num]
    return line


def _CalIndentPos(indent, lines, line_num):
    """ indent_pos保存代码行的缩进，最后一个元素表示下一行的缩进
    返回当前行缩进"""
    pos = indent[-1]
    preline = lines[line_num - 1].strip()
    curline = lines[line_num].strip()
    if curline.startswith('#'):
        return 0
    if _Search(r'(\w+)::\1', preline) and curline.startswith(':'):
        indent.append(pos + 4)
        return pos + 4
    if preline.endswith(',') or preline.endswith('('):
        idx = _FindUnmatchedLeftBracket(preline)
        if idx > -1:
            pos += idx
            indent.append(pos)
        if (_FindUnmatchedRightBracket(curline) > -1 or
                (not curline.endswith(','))):
            indent.pop()
        return pos
    if curline.startswith(r'//'):
        return pos
    if curline.startswith('case ') or curline.startswith('default '):
        return pos - 4
    if ((curline.find('{') > -1 and preline.find('namespace ') < 0) or
            curline[0:17] == 'BEGIN_MESSAGE_MAP'):
        indent.append(pos + 4)
        return pos
    if curline.find('}') > -1 or curline[0:15] == 'END_MESSAGE_MAP':
        return indent.pop() - 4
    if (_Search(r'^(for|while|if|else|else if)(?!\w)', preline) and
            (not preline.endswith(';')) and (not preline.endswith('}')) and
            curline != '{'):
        return pos + 4
    return pos


def _CheckCodeStyle(lines):
    line_num = 1
    lines.insert(0, '\n')
    lines.extend(['\n'])
    while line_num < len(lines) - 1:
        line = lines[line_num].strip()
        if line.startswith(r'//'):
            #TODO:注释行暂不处理
            None
        else:
            # 规范{}
            line = _ProcessScope(lines, line, line_num)
            # 删除多于两行或与{/}相邻的的空行
            next_line = lines[line_num + 1].strip()
            if (_IsBlankLine(line) and
                    (_IsBlankLine(next_line) or next_line == '}')):
                lines.pop(line_num)
                continue
            if line == '{' and _IsBlankLine(next_line):
                lines.pop(line_num + 1)
                continue
            if line:
                # 1.后续处理之前先保存原行字符串，避免对字符串的修改
                string_pattern = r'"[^"]*"'
                strings = _Findall(string_pattern, line)
                # 规范语句中的空格
                line = _ProcessSpaces(line)
                line = _ProcessBreaklines(lines, line, line_num)
                # 2.恢复原有字符串
                for match in _Findall(string_pattern, line):
                    line = line.replace(match, strings.pop(0))

        lines[line_num] = line
        line_num += 1

    indent = [0, 0]
    for line_num in range(0, len(lines) - 1):
        pos = _CalIndentPos(indent, lines, line_num)
        lines[line_num] = (' ' * pos + lines[line_num]).rstrip() + '\n'
    lines.pop(0)
    lines.pop()


def _DirWalk(dir, extension):
    """ return ALL SPECIFIED file in dir and subdir """
    files = sum([[os.path.join(path_name, file_name) for file_name in files]
                for path_name, dir_name, files in os.walk(dir)], [])
    cpp_files = []
    for file_name in files:
        file_extension = file_name[file_name.rfind('.') + 1:]
        if file_extension == extension:
            cpp_files.append(file_name)

    return cpp_files


def main():
    filenames = sys.argv[1:]
    if not filenames:
        print 'Invalid Filename'
        return False
    for filename in filenames:
        if os.path.isdir(filename):
            files_list = _DirWalk(filename, 'cpp')
        elif os.path.isfile(filename):
            files_list = [filename]
        for file_name in files_list:
            with open(file_name, u'r') as f:
                lines = f.readlines()
                _CheckCodeStyle(lines)

            # TODO:
            with open(file_name, u'w') as f:
                f.writelines(lines)


if __name__ == "__main__":
    main()
