from typing import Tuple, List, Set, Dict
import csv
from pathlib import Path
import re
from numpy import dot
from numpy.linalg import norm
import logging
import pkgutil
from .utils import clip_prompt, same_location, embeddings, postprocess, get_completion_safely

logger = logging.getLogger(__name__)

similarity_threshold = 0.6

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
        self.location = location
        with open(merge(project_root, self.location["file"]), 'r') as f:
            code = f.read()
            lines = code.splitlines()
            for i in range(self.location["start_line"] - 1, -1, -1):
                cls = re.match('class (?P<class>[a-zA-Z0-9_]+)', lines[i])
                if cls:
                    self.self_name = cls.group('class')
                    break

        self.additional_context = dict()
        self.parse_results_into_context(self.project_root/'..'/'..'/'functionRes.csv')
        self.parse_results_into_context(self.project_root/'..'/'..'/'classRes.csv')
        self.model = model

        self.modules = set(i.name for i in pkgutil.iter_modules())
        for i in self.modules:
            if i not in self.additional_context:
                self.additional_context[i] = []
            self.additional_context[i].append('package ' + i)
        
        self.embeddings = dict()
        for k, v in self.additional_context.items():
            self.embeddings[k] = embeddings(v)
        
        self.artifacts = self.project_root/'..'/'..'/'artifacts.md'
    
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
                    if tmp_context[i] not in ctx:
                        ctx.append(tmp_context[i])
                self.additional_context[line['qualifiedName']].extend(ctx)

    def get_context(self, prompt: str, completion: str) -> List[str]:
        code = prompt + completion
        lines = code.splitlines()
        new_context = []
        tmp = []
        tmp.extend(self.additional_context.keys())
        line_embeddings = embeddings(lines)
        for i in tmp:
            for l in range(len(lines)):
                for j in range(len(self.embeddings[i])):
                    similarity = cos_sim(self.embeddings[i][j], line_embeddings[l])
                    if similarity > similarity_threshold:
                        found = False
                        for m in range(len(new_context)):
                            if new_context[m][1] == self.additional_context[i][j]:
                                found = True
                                if new_context[m][0] < similarity:
                                    new_context[m] = (similarity, self.additional_context[i][j])
                                break
                        if not found:
                            new_context.append((similarity, self.additional_context[i][j]))
        return [i[1] for i in sorted(new_context, key=lambda x: x[0], reverse=True)]
    
    def format_context(self, context: List[str]) -> str:
        commented_context = ['# ' + '\n#'.join(i.split('\n')) for i in context]
        if len(commented_context) == 0:
            return ''
        if max([len(i) for i in commented_context]) < 3:
            return ''
        return '# API REFERENCE:\n' + '\n'.join(commented_context)[:2000] + '\n'

    def generate_new_prompt(self, prompt: str, context: Set[str], completion: str) -> Tuple[str, Set[str]]:
        new_context = self.get_context(prompt, completion)
        # new_context = new_context.union(context)
        full_context = self.format_context(new_context)
        def_start = prompt.rfind('def ')
        while True:
            func_start = prompt.rfind('\n', 0, def_start)
            if prompt[func_start + 1: def_start].strip().startswith('#') or \
                prompt[func_start + 1: def_start].strip().startswith('\'\'\'') or \
                prompt[func_start + 1: def_start].strip().startswith('\"\"\"'):
                def_start = prompt.rfind('def ', 0, def_start)
            else:
                break
        prompt_1 = prompt[:func_start] + '\n'
        prompt_2 = prompt[func_start:]
        new_prompt = clip_prompt(full_context, prompt_1, 1500 - int(len(prompt_2)/3)) + prompt_2
        return new_prompt, new_context

    def modify_prompt(self, prompt: str) -> str:
        return prompt

    def completion(self, completor, prompt: str, budget=3) -> Tuple[str, str]:
        prompt = self.modify_prompt(prompt)
        attempts = 0
        self.used = set()
        prev_completion = ''
        context = []
        artifact = ''
        # indentation = re.match('\s*', prompt.split('\n')[-1]).group(0)
        completion = get_completion_safely(self.model, completor, '', prompt)
        logger.info(f'Initial prompt: \n{prompt}\n')
        logger.info(f'Initial completion:\n{completion}\n')
        artifact += f'prompt {attempts}:\n```python\n{prompt}\n```\ncompletion {attempts}:\n```python\n{completion}\n```\n'
        while attempts < budget and prev_completion != completion:
            prev_completion = completion
            new_prompt, context = self.generate_new_prompt(prompt, context, completion)
            completion = get_completion_safely(self.model, completor, '', new_prompt)
            completion = postprocess(completion)
            logger.info(f'For prompt:\n{new_prompt}\n, got completion:\n{completion}\n')
            attempts += 1
            artifact += f'prompt {attempts}:\n```python\n{new_prompt}\n```\ncompletion {attempts}:\n```python\n{completion}\n```\n'
        with open(self.artifacts, 'w') as f:
            f.write(artifact)
        return new_prompt, completion
