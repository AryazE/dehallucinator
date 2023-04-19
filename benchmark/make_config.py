import argparse
from pathlib import Path
import libcst as cst
import libcst.matchers as m
from typing import NamedTuple
import json

FunctionInfo = NamedTuple('FunctionInfo', [('function', str), ('start_line', int), ('start_column', int), ('end_line', int), ('end_column', int)])

class FunctionFinder(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (cst.metadata.PositionProvider,)
    def __init__(self):
        self.functions = []
    def visit_FunctionDef(self, node):
        pos = self.get_metadata(cst.metadata.PositionProvider, node.body)
        start = pos.start
        end = pos.end
        if end.line - start.line > 25:
            return
        if m.matches(node.body.body[0], m.SimpleStatementLine(body=[m.Expr(value=m.SimpleString())])) and len(node.body.body) > 1:
            start = self.get_metadata(cst.metadata.PositionProvider, node.body.body[1]).start
        self.functions.append(FunctionInfo(node.name.value, start.line, start.column, end.line, end.column))
        return False
        

def extract_evaluations(file):
    with open(file, 'r') as f:
        code = f.read()
    wrapper = cst.metadata.MetadataWrapper(cst.parse_module(code))
    finder = FunctionFinder()
    wrapper.visit(finder)
    return finder.functions


def make_config(project, tests):
    project_path = Path(project).resolve()
    tests_path = Path(tests).resolve()
    files_to_ignore = set(tests_path.glob('**/*.py'))
    files_to_ignore.add(project_path/'setup.py')
    files_to_ignore.add(project_path/'__init__.py')
    files_to_ignore.update(project_path.glob('**/__init__.py'))
    files_to_ignore.update(project_path.glob('.*/**/*.py'))
    files_to_ignore.update(project_path.glob('docs*/**/*.py'))
    files_to_ignore.update(project_path.glob('examples*/**/*.py'))
    python_files = [f for f in project_path.glob('**/*.py') if f not in files_to_ignore]
    evaluations = [{
        'id': 0,
        'file': '',
        'function': '',
        'remove': []
    }]
    id = 1
    print(len(python_files))
    for f in python_files:
        try:
            e = extract_evaluations(f)
        except:
            continue
        for i in e:
            if i.function == '__init__':
                continue
            evaluations.append({
                'id': id, 
                'file': f.relative_to(project_path).as_posix(), 
                'function': i.function, 
                'remove': [{
                    'description': 'code',
                    'start_line': i.start_line,
                    'start_column': i.start_column,
                    'end_line': i.end_line,
                    'end_column': i.end_column
                }]
            })
            id += 1
            print('-', end='', flush=True)
    project_name = project_path.as_posix().split('/')[-1]
    benchmark_dir = Path(__file__).resolve().parent
    config = {
        'name': project_name,
        'project_root': project_path.as_posix().lstrip(benchmark_dir.as_posix()),
        'tests_path': tests[len(project):].strip('/'),
        'evaluations': evaluations
    }
    with open(Path(__file__).parent/'benchmark_configs'/f'{project_name}.json', 'w') as f:
        json.dump(config, f, indent=4)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', type=str, required=True)
    parser.add_argument('--tests', type=str, required=True)
    args = parser.parse_args()
    make_config(args.project, args.tests)