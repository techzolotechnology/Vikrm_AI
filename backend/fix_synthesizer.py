import ast
with open('app/services/project/code_synthesizer.py', encoding='utf-8') as f:
    src = f.read()
try:
    ast.parse(src)
    print('SYNTAX OK')
except SyntaxError as e:
    print('SyntaxError line ' + str(e.lineno) + ' : ' + str(e.msg))
    lines = src.splitlines()
    for i in range(max(0, e.lineno-4), min(len(lines), e.lineno+4)):
        print(str(i+1) + ': ' + repr(lines[i]))
