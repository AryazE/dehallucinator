from typing import Tuple, List, Set, Dict
import os
import csv
from pathlib import Path
import re
import logging
import subprocess
import pkgutil
import Levenshtein
from .utils import clip_prompt, run_query, same_location

logger = logging.getLogger(__name__)

def merge(project_root: str, file: str) -> str:
    p_r = project_root.split('/')
    f = file.split('/')
    max_common = 0
    for i in range(1, min(len(p_r), len(f))):
        if '/'.join(p_r[-i:]) == '/'.join(f[:i]):
            max_common = i
    return '/'.join(p_r[:-max_common] + f)

class SimpleCompletion:
    def __init__(self, project_root: str, model: str = "Codex", location: Dict[str, int] = {}):
        self.project_root = Path(project_root)
        print(f'Project root: {self.project_root.as_posix()}')
        self.database = self.project_root/'..'/'..'/'..'/'codeqldb'
        self.location = location
        with open(merge(project_root, self.location["file"]), 'r') as f:
            code = f.read()
            lines = code.splitlines()
            for i in range(self.location["start_line"] - 1, -1, -1):
                cls = re.match('class (?P<class>[a-zA-Z0-9_]+)', lines[i])
                if cls:
                    self.self_name = cls.group('class')
                    break
        if not self.database.exists():
            working_dir = os.getcwd()
            os.chdir(self.project_root)
            subprocess.run(['codeql', 'database', 'create',
                            '--language=python',
                            '--overwrite',
                            '--threads=0',
                            '--', self.database], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.chdir(working_dir)
            run_query(self.database, 'functionContext.ql', 'functionRes.csv', str(self.database/'..'))
            run_query(self.database, 'classContext.ql', 'classRes.csv', str(self.database/'..'))
        self.additional_context = dict()
        self.parse_results_into_context(self.database/'..'/'functionRes.csv')
        self.parse_results_into_context(self.database/'..'/'classRes.csv')
        self.model = model
        # self.modules = { i.name for i in pkgutil.iter_modules() }
    
    def parse_results_into_context(self, file):
        with open(file, newline='') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for line in csv_reader:
                if same_location(line, self.location):
                    continue
                if line['name'] not in self.additional_context:
                    self.additional_context[line['name']] = []
                self.additional_context[line['name']].append((line['qualifiedName'], line['context']))

    def context_for(self, name: str) -> Tuple[Set[str], Set[str]]:
        # TODO Which import to choose?
        result = set()
        imps = set()
        if name == 'self':
            name = self.self_name
        if name in self.additional_context:
            self.used.add(name)
            m, c = self.additional_context[name][0]
            imps.add('from ' + m + ' import ' + name)
            for m, c in self.additional_context[name]:
                result.add(c)
            return imps, result
        # elif name in self.modules:
        #     return f'import {name}\n', ''
        else:
            for k, v in self.additional_context.items():
                if len(name) > 4 and Levenshtein.ratio(name, k) > 0.5 and k not in self.used:
                    self.used.add(k)
                    m, c = v[0]
                    imps.add('from ' + m + ' import ' + k)
                    for m, c in v:
                        result.add(c)
            return imps, result

    def get_context(self, prompt: str, completion: str) -> Tuple[str, Set[str]]:
        code = prompt + completion
        last_line = code.rfind('\n')
        if last_line != -1:
            code = code[:last_line]
        tokens = re.split('\W+', code)
        new_context = set()
        new_imports = ''
        for k in tokens:
            if k not in self.used:
                imps, ctx = self.context_for(k)
                if len(ctx) > 0:
                    new_context  = new_context.union(ctx)
                    new_imports = '\n'.join(imps) + new_imports
        return new_imports, new_context
    
    def format_context(self, context: Set[str]) -> str:
        commented_context = ['# ' + '\n#'.join(i.split('\n')) for i in context]
        return '# API REFERENCE:\n' + '\n'.join(commented_context) + '\n'

    def generate_new_prompt(self, prompt: str, context: Set[str], completion: str) -> Tuple[str, Set[str]]:
        new_imports, new_context = self.get_context(prompt, completion)
        new_context = new_context.union(context)
        full_context = self.format_context(new_context)
        new_prompt = clip_prompt(full_context, prompt, 1500)
        return new_prompt, new_context

    def modify_prompt(self, prompt: str) -> str:
        return prompt

    def completion(self, completor, prompt: str) -> Tuple[str, str]:
        prompt = self.modify_prompt(prompt)
        BUDGET = 3
        attempts = 0
        self.used = set()
        prev_completion = ''
        context = []
        imports = ''
        # indentation = re.match('\s*', prompt.split('\n')[-1]).group(0)
        completion = completor.get_completion(self.model, prompt)
        logger.info(f'Initial prompt: \n{prompt}\n')
        logger.info(f'Initial completion:\n{completion}\n')
        while attempts < BUDGET and prev_completion != completion:
            prev_completion = completion
            new_prompt, context = self.generate_new_prompt(prompt, context, completion)
            completion = completor.get_completion(self.model, new_prompt)
            logger.info(f'For prompt:\n{new_prompt}\n, got completion:\n{completion}\n')
            attempts += 1
        return new_prompt, imports, completion
