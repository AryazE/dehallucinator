from typing import Tuple, List, Set, Dict
from collections import Counter
import os
import csv
from pathlib import Path
import re
from numpy import dot
from numpy.linalg import norm
import logging
import subprocess
import pkgutil
import pydoc
import importlib
from sentence_transformers import SentenceTransformer
from .utils import clip_prompt, run_query, same_location

logger = logging.getLogger(__name__)

similarity_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def cos_sim(emb_a: List[float], emb_b: List[float]) -> float:
    return dot(emb_a, emb_b) / (norm(emb_a) * norm(emb_b))

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
            logger.info(os.getcwd())
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
        self.embeddings = dict()
        for k, v in self.additional_context.items():
            self.embeddings[k] = similarity_model.encode(v)
        self.modules = set(i.name for i in pkgutil.iter_modules())
    
    def parse_results_into_context(self, file):
        with open(file, newline='') as csvfile:
            csv_reader = csv.DictReader(csvfile)
            for line in csv_reader:
                if same_location(line, self.location):
                    continue
                if line['qualifiedName'] not in self.additional_context:
                    self.additional_context[line['qualifiedName']] = []
                tmp_context = line['context'].split('\n')
                ctx = []
                for i in range(len(tmp_context)):
                    if tmp_context[i] not in tmp_context[:i]:
                        ctx.append(tmp_context[i])
                self.additional_context[line['qualifiedName']].append(ctx)

    def context_for(self, name: str) -> List[str]:
        result = []
        name_embedding = similarity_model.encode([name])[0]
        for k, v in self.additional_context.items():
            for i in v:
                if k not in self.used and cos_sim(name_embedding, self.embeddings[i]) > 0.6:
                    self.used.add(k)
                    c = v[0]
                    for c in v:
                        result.append(c)
        for i in self.modules:
            if i not in self.used and cos_sim(name_embedding, self.embeddings[i]) > 0.6:
                self.used.add(i)
                result.append('import ' + i)
        return result

    def get_context(self, prompt: str, completion: str) -> Set[str]:
        code = prompt + completion
        # last_line = code.rfind('\n')
        # if last_line != -1:
        #     code = code[:last_line]

        # tokens = Counter(re.split('[^a-zA-Z0-9]+', code))
        # if tokens['self'] > 0:
        #     tokens[self.self_name] += tokens['self']
        #     del tokens['self']
        # new_context = set()
        # for k, _ in tokens.most_common():
        #     if len(k) > 0 and k not in self.used:
        #         if k == 'self':
        #             logger.info(f'self is {self.self_name}')
        #         ctx = self.context_for(k)
        #         if k == 'self':
        #             logger.info(f'context for self is {ctx}')
        #         if len(ctx) > 0:
        #             dont_add = False
        #             for c in ctx:
        #                 if c.strip().split('.')[0] in tokens:
        #                     dont_add = True
        #             if dont_add:
        #                 continue
        #             new_context  = new_context.union(ctx)
        lines = code.splitlines()
        new_context = set()

        return new_context
    
    def format_context(self, context: Set[str]) -> str:
        commented_context = ['# ' + '\n#'.join(i.split('\n')) for i in context]
        return '# API REFERENCE:\n' + '\n'.join(commented_context)[:2000] + '\n'

    def generate_new_prompt(self, prompt: str, context: Set[str], completion: str) -> Tuple[str, Set[str]]:
        new_context = self.get_context(prompt, completion)
        new_context = new_context.union(context)
        full_context = self.format_context(new_context)
        new_prompt = clip_prompt(full_context, prompt, 1500)
        return new_prompt, new_context

    def modify_prompt(self, prompt: str) -> str:
        return prompt

    def completion(self, completor, prompt: str, budget=3) -> Tuple[str, str]:
        prompt = self.modify_prompt(prompt)
        attempts = 0
        self.used = set()
        prev_completion = ''
        context = []
        # indentation = re.match('\s*', prompt.split('\n')[-1]).group(0)
        completion = completor.get_completion(self.model, prompt)
        logger.info(f'Initial prompt: \n{prompt}\n')
        logger.info(f'Initial completion:\n{completion}\n')
        while attempts < budget and prev_completion != completion:
            prev_completion = completion
            new_prompt, context = self.generate_new_prompt(prompt, context, completion)
            completion = completor.get_completion(self.model, new_prompt)
            logger.info(f'For prompt:\n{new_prompt}\n, got completion:\n{completion}\n')
            attempts += 1
        return new_prompt, completion
