from typing import Tuple
from os import path
import subprocess
import tempfile
from coder.backend import get_completion
import libcst as cst
from libcst.metadata import PositionProvider
import libcst.matchers as m
# import fasttext
# import fasttext.util
# from scipy import spatial
import Levenshtein

class SimpleCompletion:
    def __init__(self, project_root: str, model: str = "Codex"):
        self.project_root = path.abspath(project_root)
        self.tmp_dir = tempfile.mkdtemp()
        self.database = path.join(self.tmp_dir, 'database')
        subprocess.run(['codeql', 'database', 'create',
                        '--language=python',
                        f'--source-root={self.project_root}',
                        '--', self.database])
        subprocess.run(['codeql', 'query', 'run',
            f'--database={self.database}',
            # f'--external=names={path.join(self.tmp_dir, "names.csv")}',
            f'--output={path.join(self.tmp_dir, "functionRes.bqrs")}',
            '--', f'{path.join(path.dirname(__file__), "ql", "functionContext.ql")}'])
        subprocess.run(['codeql', 'bqrs', 'decode',
            '--format=csv',
            '--no-titles',
            f'--output={path.join(self.tmp_dir, "functionRes.csv")}',
            '--', f'{path.join(self.tmp_dir, "functionRes.bqrs")}'])
        subprocess.run(['codeql', 'query', 'run',
            f'--database={self.database}',
            # f'--external=names={path.join(self.tmp_dir, "names.csv")}',
            f'--output={path.join(self.tmp_dir, "classRes.bqrs")}',
            '--', f'{path.join(path.dirname(__file__), "ql", "classContext.ql")}'])
        subprocess.run(['codeql', 'bqrs', 'decode',
            '--format=csv',
            '--no-titles',
            f'--output={path.join(self.tmp_dir, "classRes.csv")}',
            '--result-set=#select',
            '--', f'{path.join(self.tmp_dir, "classRes.bqrs")}'])
        
        self.additional_context = dict()
        with open(path.join(self.tmp_dir, 'functionRes.csv'), 'r') as f:
            functionRes = f.read().replace('"', '').splitlines()
        with open(path.join(self.tmp_dir, 'classRes.csv'), 'r') as f:
            classRes = f.read().replace('"', '').splitlines()
        print(functionRes)
        print(classRes)
        for line in functionRes:
            ind = line.find(',')
            name = line[:ind]
            ind2 = line[ind + 2:].find(',')
            module = line[ind + 2:ind + 2 + ind2]
            module = '.' + module[len(self.project_root):].replace('/', '.')[:-3]
            if name not in self.additional_context:
                self.additional_context[name] = []
            self.additional_context[name].append((module, line[ind + 2 + ind2 + 1:]))
        for line in classRes:
            ind = line.find(',')
            name = line[:ind]
            ind2 = line[ind + 2:].find(',')
            module = line[ind + 2:ind + 2 + ind2 + 1]
            module = '.' + module[len(self.project_root):].replace('/', '.')[:-3]
            if name not in self.additional_context:
                self.additional_context[name] = []
            self.additional_context[name].append((module, line[ind + 2 + ind2 + 1:]))
        print(self.additional_context)
        self.model = model
        # fasttext.util.download_model('en', if_exists='ignore')
        # self.ft = fasttext.util.reduce_model(fasttext.load_model('cc.en.300.bin'), 100)
    
    def context_for(self, name: str) -> Tuple[str, str]:
        if name in self.additional_context and name not in self.used:
            result = ''
            imps = ''
            self.used.add(name)
            for m, c in self.additional_context[name]:
                result += '\n# ' + c
                imps += 'from ' + m + ' import ' + name + '\n'
            return imps, result
        else:
            result = ''
            imps = ''
            for k, v in self.additional_context.items():
                if Levenshtein.ratio(name, k) > 0.5 and k not in self.used:
                    self.used.add(k)
                    for m, c in v:
                        result += '\n# ' + c
                        imps += 'from ' + m + ' import ' + k + '\n'
            return imps, result

    def get_context(self, context: str, completion: str) -> str:
        code = context + completion
        ast = None
        while ast is None:
            try:
                ast = cst.parse_module(code)
            except:
                ast = None
                if '\n' not in code:
                    return context
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
                    new_context = ctx + new_context
                    new_imports = imps + new_imports
        if len(new_context) > 0:
            new_context = '# API reference:' + new_context + '\n\n'
        return new_imports, new_context

    def completion(self, prompt: str) -> str:
        BUDGET = 3
        attempts = 0
        self.used = set()
        prev_completion = ''
        context = ''
        completion = get_completion(self.model, prompt)
        print(f'Initial completion:\n{completion}\n')
        while attempts < BUDGET and prev_completion != completion:
            prev_completion = completion
            new_imports, new_context = self.get_context(context, completion)
            context = new_imports + '\n' + new_context + context
            completion = get_completion(self.model, context + prompt)
            print(f'For prompt:\n{context + prompt}\n, got completion:\n{completion}\n')
            attempts += 1
        return completion

