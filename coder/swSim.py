import time
from typing import Tuple, List, Set, Dict
import csv
from pathlib import Path
import re
import logging
import pkgutil
from .utils import same_location, embeddings, postprocess, get_completion_safely, get_indentation, merge, clip_prompt
import pickle
import numpy as np
from sklearn.neighbors import BallTree

logger = logging.getLogger(__name__)

class SWSim:
    def __init__(self, project_root: str, model: str = "Codex", func: str = '', location: Dict = {}, similarity_threshold: float = 0.5):
        self.project_root = Path(project_root)
        self.similarity_threshold = similarity_threshold
        self.model = model
        print(f'Project root: {self.project_root.as_posix()}')
        self.location = location
        self.func = func
        with open(merge(project_root, self.location["file"]), 'r') as f:
            code = f.read()
            lines = code.splitlines()
            for i in range(self.location["start_line"] - 1, -1, -1):
                cls = re.match('class (?P<class>[a-zA-Z0-9_]+)', lines[i])
                if cls:
                    self.self_name = cls.group('class')
                    break

        with open(self.project_root/'tree.pkl', 'rb') as f:
            self.ball_tree = pickle.load(f)
        with open(self.project_root/'all.py', 'r') as f:
            self.code_lines = f.read().splitlines(keepends=True)
        
        self.artifacts = self.project_root/'..'/'..'/'artifacts.md'

    def generate_new_prompt(self, prompt: str, context: Set[str], completion: str) -> Tuple[str, Set[str]]:
        if len(completion) > 0:
            start = time.process_time_ns()
            comp_embd = np.array(embeddings(completion.splitlines(keepends=True)))
            dist, res = self.ball_tree.query(comp_embd)
            end = time.process_time_ns()
            if not (self.project_root/'..'/'..'/'retrieval_time.txt').exists():
                with open(self.project_root/'..'/'..'/'retrieval_time.txt', 'w') as f:
                    f.write(f'{end-start} 1')
            with open(self.project_root/'..'/'..'/'retrieval_time.txt', 'r') as f:
                rt, n = f.read().split(' ')
            with open(self.project_root/'..'/'..'/'retrieval_time.txt', 'w') as f:
                f.write(f'{(float(rt)*int(n)+end-start)/(int(n)+1)} {int(n)+1}')
            new_context = set()
            for r in res:
                new_context.add('# '.join(self.code_lines[r[0]:r[0]+5]))
            text_context = '# '.join(new_context)
            new_prompt = clip_prompt(prompt, 3500 - len(text_context) - 20)
            new_prompt = f'# These are lines of code from other files that are relevant to the last function\n# {text_context}\n{new_prompt}'
        else:
            new_prompt = f'# These are lines of code from other files that are relevant to the last function\n# {"# ".join(context)}\n{clip_prompt(prompt, 3500 - 20)}'
            new_context = context
        return new_prompt, new_context

    def modify_prompt(self, prompt: str) -> str:
        return prompt

    def completion(self, completor, prompt: str, k=4) -> Tuple[str, List[str]]:
        prompt = self.modify_prompt(prompt)
        attempts = 0
        self.used = set()
        prev_completion = ''
        context = []
        artifact = ''
        self.indent_style, self.indent_count = get_indentation(prompt)
        logger.info(f'indent_style: {self.indent_style}, indent_count: {self.indent_count}')
        completion = get_completion_safely(self.model, completor, prompt, k=1)[0]
        logger.info(f'completion w/o postprocessing:\n{completion}\n')
        completion = postprocess(completion, self.indent_style, self.indent_count)
        completions = [completion]
        logger.info(f'Initial prompt: \n{prompt}\n')
        logger.info(f'Initial completion:\n{completion}\n')
        artifact += f'prompt {attempts}:\n```python\n{prompt}\n```\ncompletion {attempts}:\n```python\n{completion}\n```\n'
        while attempts == 0 or attempts < k-1:
            prev_completion = completion
            new_prompt, context = self.generate_new_prompt(prompt, context, completion)
            completion = get_completion_safely(self.model, completor, new_prompt, k=1)[0]
            logger.info(f'completion w/o postprocessing:\n{completion}\n')
            completion = postprocess(completion, self.indent_style, self.indent_count)
            completions.append(completion)
            logger.info(f'For prompt:\n{new_prompt}\n, got completion:\n{completion}\n')
            attempts += 1
            artifact += f'prompt {attempts}:\n```python\n{new_prompt}\n```\ncompletion {attempts}:\n```python\n{completion}\n```\n'
        with open(self.artifacts, 'w') as f:
            f.write(artifact)
        return new_prompt, completions
