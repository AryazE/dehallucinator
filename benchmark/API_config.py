from typing import Optional
import argparse
from pathlib import Path
import libcst as cst
import libcst.matchers as m
from typing import NamedTuple
import json
import random

FunctionInfo = NamedTuple('FunctionInfo', [('function', str), ('start_line', int), ('start_column', int), ('end_line', int), ('end_column', int)])

class APIFinder(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (cst.metadata.PositionProvider, cst.metadata.QualifiedNameProvider, cst.metadata.ParentNodeProvider,)
    def __init__(self, package_name):
        self.function = ['']
        self.apis = []
        self.package_name = package_name

    def visit_FunctionDef(self, node):
        if len(self.apis) > 40:
            return False
        self.function.append(node.name.value)
    
    def leave_FunctionDef(self, node):
        self.function.pop()

    def visit_Call(self, node: cst.Call) -> Optional[bool]:
        if len(self.apis) > 40:
            return False
        qnames = self.get_metadata(cst.metadata.QualifiedNameProvider, node)
        for qname in qnames:
            if qname.source == cst.metadata.QualifiedNameSource.IMPORT:
                if self.package_name in qname.name or qname.name.startswith('.'):
                    par = self.get_metadata(cst.metadata.ParentNodeProvider, node)
                    while par and not (isinstance(par, cst.BaseSmallStatement) or isinstance(par, cst.BaseCompoundStatement)):
                        par = self.get_metadata(cst.metadata.ParentNodeProvider, par)
                    pos = self.get_metadata(cst.metadata.PositionProvider, par)
                    start = pos.start
                    end = pos.end
                    self.apis.append(FunctionInfo(self.function[-1], start.line, start.column, end.line, end.column))
                    return False

def extract_evaluations(file, package_name):
    with open(file, 'r') as f:
        code = f.read()
    wrapper = cst.metadata.MetadataWrapper(cst.parse_module(code))
    finder = APIFinder(package_name)
    wrapper.visit(finder)
    print('.', end='', flush=True)
    return finder.apis


def make_config(project, tests, package_name):
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
    if len(python_files) > 30:
        python_files = random.sample(python_files, 30)
    print(len(python_files))
    for f in python_files:
        try:
            e = extract_evaluations(f, package_name)
        except:
            print('x', end='', flush=True)
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
    if len(evaluations) == 1:
        print(f'No APIs found in {package_name}')
        return
    if len(evaluations) > 10:
        evaluations = [evaluations[0]] + random.sample(evaluations[1:], 10)
    project_name = project_path.as_posix().split('/')[-1]
    benchmark_dir = Path(__file__).resolve().parent
    config = {
        'name': project_name,
        'project_root': project_path.as_posix().lstrip(benchmark_dir.as_posix()),
        'tests_path': tests[len(project):].strip('/'),
        'evaluations': evaluations
    }
    
    with open(Path(__file__).parent/'benchmark_configs'/f'{project_name}-apis.json', 'w') as f:
        json.dump(config, f, indent=4)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', type=str, required=True)
    parser.add_argument('--tests', type=str, required=True)
    parser.add_argument('--packageName', type=str, required=True)
    args = parser.parse_args()
    make_config(args.project, args.tests, args.packageName)