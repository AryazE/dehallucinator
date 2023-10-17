from typing import Tuple, List, Set, Dict
from sklearn.preprocessing import normalize
import time
from .utils import clip_prompt, embeddings, cos_sim
from pathlib import Path
import re
import logging
import json
import pickle
from .utils import embeddings, postprocess, get_completion_safely, get_indentation, merge, parse_results_into_context

logger = logging.getLogger(__name__)

class RetrievalCompletion:
    def __init__(self, project_root: str, model: str = "Codex", func: str = '', location: Dict = {}, c: int = 5, mode: str = ''):
        self.project_root = Path(project_root)
        self.context_size = c
        self.mode = mode
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
        saved_path = self.project_root/'..'/'..'/'..'/'..'
        with open(saved_path/'tree.pkl', 'rb') as f:
            self.ball_tree = pickle.load(f)
        with open(saved_path/'all.json', 'r') as f:
            self.additional_context = json.load(f)
        self.model = model
        
        self.artifacts = self.project_root/'..'/'..'/'artifacts.md'

    def get_context(self, prompt: str) -> List[Tuple[float, str]]:
        code = prompt
        lines = code.splitlines()
        line_embeddings = normalize(embeddings(lines))
        dist, res = self.ball_tree.query(line_embeddings, k=self.context_size)
        bests = {}
        for i in range(len(res)):
            for j in range(len(res[i])):
                if res[i][j] not in bests:
                    bests[res[i][j]] = dist[i][j]
                else:
                    bests[res[i][j]] = min(bests[res[i][j]], dist[i][j])
        indices = sorted([(dis, ind) for ind, dis in bests.items()], key=lambda x: x[0])
        contexts = [(dis, self.additional_context[ind]) for dis, ind in indices]
        return contexts
    
    def format_context(self, context: List[Tuple[float, str]]) -> str:
        if len(context) == 0:
            return ''
        context = ['# API Reference:'] + [i[1] for i in context[:self.context_size]]
        return '\n# '.join(context)

    def generate_new_prompt(self, prompt: str) -> Tuple[str, Set[str]]:
        new_context = self.get_context(prompt)
        full_context = self.format_context(new_context)
        if self.model == 'GPT3.5':
            prompt_size = 3500
        else:
            prompt_size = 1750
        new_prompt = full_context + '\n' + clip_prompt(prompt, prompt_size - len(full_context)//2)
        return new_prompt, new_context

    def modify_prompt(self, prompt: str) -> str:
        return prompt

    def completion(self, completor, prompt: str, k=4) -> Tuple[str, List[str]]:
        prompt = self.modify_prompt(prompt)
        new_prompt, context = self.generate_new_prompt(prompt)
        attempts = 0
        self.used = set()
        prev_completion = ''
        context = []
        artifact = ''
        self.indent_style, self.indent_count = get_indentation(prompt)
        logger.info(f'indent_style: {self.indent_style}, indent_count: {self.indent_count}')
        completion = get_completion_safely(self.model, completor, new_prompt, k=1)[0]
        logger.info(f'completion w/o postprocessing:\n{completion}\n')
        completion = postprocess(completion, self.indent_style, self.indent_count, self.mode)
        completions = [completion]
        logger.info(f'Initial prompt with retrieved APIs: \n{new_prompt}\n')
        logger.info(f'Initial completion:\n{completion}\n')
        artifact += f'prompt {attempts}:\n```python\n{new_prompt}\n```\ncompletion {attempts}:\n```python\n{completion}\n```\n'
        with open(self.artifacts, 'w') as f:
            f.write(artifact)
        return new_prompt, completions
