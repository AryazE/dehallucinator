from typing import Tuple, List, Set, Dict
from pathlib import Path
import re
import logging
import json
import pickle
from .utils import embeddings, postprocess, get_completion_safely, get_indentation, merge, parse_results_into_context

logger = logging.getLogger(__name__)

class BaseDiCompletion:
    def __init__(self, project_root: str, model: str = "Codex", func: str = '', location: Dict = {}, mode: str = ''):
        self.project_root = Path(project_root)
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

    def get_context(self, prompt: str, completion: str) -> List[str]:
        pass
    
    def format_context(self, context: List[str]) -> str:
        pass

    def generate_new_prompt(self, prompt: str, context: Set[str], completion: str) -> Tuple[str, Set[str]]:
        pass

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
        completion = postprocess(completion, self.indent_style, self.indent_count, self.mode)
        completions = [completion]
        logger.info(f'Initial prompt: \n{prompt}\n')
        logger.info(f'Initial completion:\n{completion}\n')
        artifact += f'prompt {attempts}:\n```python\n{prompt}\n```\ncompletion {attempts}:\n```python\n{completion}\n```\n'
        while attempts == 0 or attempts < k-1:
            prev_completion = completion
            new_prompt, context = self.generate_new_prompt(prompt, context, completion)
            completion = get_completion_safely(self.model, completor, new_prompt, k=1)[0]
            logger.info(f'completion w/o postprocessing:\n{completion}\n')
            completion = postprocess(completion, self.indent_style, self.indent_count, self.mode)
            completions.append(completion)
            logger.info(f'For prompt:\n{new_prompt}\n, got completion:\n{completion}\n')
            attempts += 1
            artifact += f'prompt {attempts}:\n```python\n{new_prompt}\n```\ncompletion {attempts}:\n```python\n{completion}\n```\n'
        with open(self.artifacts, 'w') as f:
            f.write(artifact)
        return new_prompt, completions
