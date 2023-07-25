from typing import Optional
import argparse
from pathlib import Path
import libcst as cst
import libcst.matchers as m
from typing import NamedTuple
import json
import random
from coverage import Coverage
from coverage.data import CoverageData

FunctionInfo = NamedTuple('FunctionInfo', [('function', str), ('start_line', int), ('start_column', int), ('end_line', int), ('end_column', int)])

class APIFinder(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (cst.metadata.PositionProvider, cst.metadata.QualifiedNameProvider, cst.metadata.ParentNodeProvider,)
    def __init__(self, package_name, tests_per_line):
        self.function = ['']
        self.apis = []
        self.package_name = package_name
        self.tests_per_line = tests_per_line

    def visit_Decorator(self, node) -> Optional[bool]:
        return False
    
    def visit_FunctionDef(self, node):
        if len(self.apis) > 100:
            return False
        self.function.append(node.name.value)
    
    def leave_FunctionDef(self, node):
        self.function.pop()

    def visit_Call(self, node: cst.Call) -> Optional[bool]:
        if len(self.apis) > 100:
            return False
        qnames = self.get_metadata(cst.metadata.QualifiedNameProvider, node)
        for qname in qnames:
            if qname.source == cst.metadata.QualifiedNameSource.IMPORT:
                if self.package_name in qname.name or qname.name.startswith('.'):
                    par = self.get_metadata(cst.metadata.ParentNodeProvider, node)
                    # while par and not (isinstance(par, cst.BaseSmallStatement) or isinstance(par, cst.BaseCompoundStatement)):
                    #     par = self.get_metadata(cst.metadata.ParentNodeProvider, par)
                    pos = self.get_metadata(cst.metadata.PositionProvider, par)
                    start = pos.start
                    end = pos.end
                    covered = False
                    if self.tests_per_line is None:
                        covered = True
                    else:
                        for i in range(start.line, end.line):
                            if i in self.tests_per_line and len(self.tests_per_line[i]) > 0 and any(self.tests_per_line[i]):
                                covered = True
                                break
                    if covered:
                        self.apis.append(FunctionInfo(self.function[-1], start.line, start.column, end.line, end.column))
                    return False

def extract_evaluations(file, package_name, tests_per_line):
    with open(file, 'r') as f:
        code = f.read()
    wrapper = cst.metadata.MetadataWrapper(cst.parse_module(code))
    finder = APIFinder(package_name, tests_per_line)
    wrapper.visit(finder)
    print('.', end='', flush=True)
    return finder.apis


def make_config(project, tests, package_name, with_tests=False):
    project_path = Path(project).resolve()
    tests_path = Path(tests).resolve()
    project_name = project_path.as_posix().split('/')[-1]
    here = Path(__file__).parent.resolve()
    if with_tests and (here/'temp_conf'/project_name).exists():
        cov = Coverage(data_file=str(here/'temp_conf'/project_name/'.coverage'))
        cov.load()
        cov_data = cov.get_data()
    else:
        return

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
    if len(python_files) > 200:
        python_files = random.sample(python_files, 200)
    print(len(python_files))
    for f in python_files:
        if with_tests:
            proj_file = str(f).replace("GitHubProjects", "temp_conf")
            tests_per_line = cov_data.contexts_by_lineno(proj_file)
            if tests_per_line is None or tests_per_line == {}:
                continue
        else:
            tests_per_line = None
        try:
            e = extract_evaluations(f, package_name, tests_per_line)
        except:
            print('x', end='', flush=True)
            continue
        for i in e:
            if i.function == '__init__':
                continue
            new_e = {
                'id': id, 
                'file': f.relative_to(project_path).as_posix(), 
                'function': i.function, 
                'remove': [{
                    'description': 'code',
                    'start_line': i.start_line,
                    'start_column': 0,#i.start_column,
                    'end_line': i.end_line+1,
                    'end_column': 0#i.end_column
                }]
            }
            duplicate = False
            for j in evaluations:
                if new_e["file"] == j["file"] and new_e["remove"][0] == j["remove"][0]:
                    duplicate = True
                    break
            if not duplicate:
                evaluations.append(new_e)
                id += 1
    if len(evaluations) == 1:
        print(f'No APIs found in {package_name}')
        return
    if len(evaluations) > 100:
        evaluations = [evaluations[0]] + random.sample(evaluations[1:], 100)
    
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