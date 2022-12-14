from typing import Tuple, List
import os
import csv
from pathlib import Path
import re
import logging
import subprocess
import pkgutil
import tempfile
import libcst as cst
from libcst.metadata import PositionProvider
import libcst.matchers as m
import Levenshtein
from .utils import clip_prompt, run_query

class SimpleCompletion:
    def __init__(self, project_root: str, model: str = "Codex"):
        self.project_root = Path(project_root)
        print(f'Project root: {self.project_root.as_posix()}')
        self.tmp_dir = tempfile.mkdtemp()
        self.database = os.path.join(self.tmp_dir, 'database')
        working_dir = os.getcwd()
        os.chdir(self.project_root)
        subprocess.run(['codeql', 'database', 'create',
                        '--language=python',
                        '--overwrite',
                        '--threads=0',
                        # f'--source-root={str(self.project_root)}',
                        '--', self.database], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.chdir(working_dir)
        run_query(self.database, 'functionContext.ql', 'functionRes.csv', str(self.project_root))
        run_query(self.database, 'classContext.ql', 'classRes.csv', str(self.project_root))
        self.additional_context = dict()
        
        def parse_results_into_context(self, file):
            with open(file, newline='') as csvfile:
                csv_reader = csv.DictReader(csvfile)
                for line in csv_reader:
                    if line['name'] not in self.additional_context:
                        self.additional_context[line['name']] = []
                    self.additional_context[line['name']].append((line['qualifiedName'], line['context']))
        
        parse_results_into_context(self, self.project_root/'functionRes.csv')
        parse_results_into_context(self, self.project_root/'classRes.csv')
        self.model = model
        # self.modules = { i.name for i in pkgutil.iter_modules() }
    
    def context_for(self, name: str) -> Tuple[List[str], List[str]]:
        # TODO Which import to choose?
        result = []
        imps = []
        if name in self.additional_context:
            self.used.add(name)
            m, c = self.additional_context[name][0]
            imps.append('from ' + m + ' import ' + name)
            for m, c in self.additional_context[name]:
                result.append(c)
            return imps, result
        # elif name in self.modules:
        #     return f'import {name}\n', ''
        else:
            for k, v in self.additional_context.items():
                if len(name) > 4 and Levenshtein.ratio(name, k) > 0.5 and k not in self.used:
                    self.used.add(k)
                    m, c = v[0]
                    imps.append('from ' + m + ' import ' + k)
                    for m, c in v:
                        result.append(c)
            return imps, result

    def get_context(self, context: str, completion: str) -> Tuple[str, str]:
        code = context + completion
        ast = None
        while ast is None:
            try:
                ast = cst.parse_module(code)
            except:
                ast = None
                if '\n' not in code:
                    return '', ''
                code = code[:code.rfind('\n')]
        new_code_start = len(context.splitlines())
        position = {
            k.value: v 
                for k, v in cst.MetadataWrapper(ast).resolve(PositionProvider).items() 
                if m.matches(k, m.Name()) and v.start.line >= new_code_start
        }

        new_context = ''
        new_imports = ''
        for k, v in position.items():
            if k not in self.used:
                imps, ctx = self.context_for(k)
                if len(ctx) > 0:
                    new_context = '# ' + '\n# '.join(ctx) + '\n' + new_context
                    new_imports = '\n'.join(imps) + new_imports
        if len(new_context) > 0:
            new_context = '# API reference:\n' + new_context + '\n'
        logging.info(f'New context:\n{new_context}\n')
        return new_imports, new_context

    def completion(self, completor, prompt: str) -> Tuple[str, str]:
        BUDGET = 3
        attempts = 0
        self.used = set()
        prev_completion = ''
        context = ''
        imports = ''
        # indentation = re.match('\s*', prompt.split('\n')[-1]).group(0)
        completion = completor.get_completion(self.model, prompt)
        logging.info(f'Initial prompt: \n{prompt}\n')
        logging.info(f'Initial completion:\n{completion}\n')
        while attempts < BUDGET and prev_completion != completion:
            prev_completion = completion
            new_imports, new_context = self.get_context(context + prompt, completion)
            #imports += new_imports
            context += new_context# + '\n' + new_imports
            context = clip_prompt(context, 1000)
            completion = completor.get_completion(self.model, context + prompt)
            logging.info(f'For prompt:\n{context + prompt}\n, got completion:\n{completion}\n')
            attempts += 1
        return imports, completion
