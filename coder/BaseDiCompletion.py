from typing import Tuple, List, Set, Dict
import csv
from pathlib import Path
import re
import logging
import pkgutil
from .utils import same_location, embeddings, postprocess, get_completion_safely, get_indentation, merge

logger = logging.getLogger(__name__)

class BaseDiCompletion:
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

        # self.modules = set(i.name for i in pkgutil.iter_modules())
        # for i in self.modules:
        #     if i not in self.additional_context:
        #         self.additional_context[i] = []
        #     self.additional_context[i].append('package ' + i)
        
        self.embeddings = dict()
        for k, v in self.additional_context.items():
            self.embeddings[k] = embeddings(v + [k])
        
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
        pass
    
    def format_context(self, context: List[str]) -> str:
        pass

    def generate_new_prompt(self, prompt: str, context: Set[str], completion: str) -> Tuple[str, Set[str]]:
        pass

    def modify_prompt(self, prompt: str) -> str:
        return prompt

    def completion(self, completor, prompt: str, budget=3, k=4) -> Tuple[str, List[str]]:
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
        while attempts == 0 or (attempts < min(budget, k-1) and prev_completion != completion):
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