import textwrap
from typing import Tuple, List, Set, Dict
import csv
from pathlib import Path
import re
import logging
import pkgutil
from .utils import clip_prompt, same_location, embeddings, postprocess, get_completion_safely, get_indentation, merge, cos_sim
from .BaseDiCompletion import BaseDiCompletion

logger = logging.getLogger(__name__)

similarity_threshold = 0.7

class ExplicitCompletion(BaseDiCompletion):
    def __init__(self, project_root: str, model: str = "Codex", location: Dict[str, int] = {}):
        super().__init__(project_root, model, location)

    def get_context(self, prompt: str, completion: str) -> List[str]:
        code = completion #prompt + completion
        lines = code.splitlines()
        new_context = []
        tmp = []
        tmp.extend(self.additional_context.keys())
        line_embeddings = embeddings(lines)
        for i in tmp:
            ctx = False
            for l in range(len(lines)):
                if '# need context for' in lines[l]:
                    ctx = True
                elif ctx and not lines[l].strip().startswith('#'):
                    break
                elif not ctx:
                    continue
                for j in range(len(self.embeddings[i])):
                    if j >= len(self.additional_context[i]):
                        jj = 0
                    else:
                        jj = j
                    similarity = cos_sim(self.embeddings[i][j], line_embeddings[l])
                    if similarity > similarity_threshold:
                        found = False
                        for m in range(len(new_context)):
                            if new_context[m][1] == self.additional_context[i][jj]:
                                found = True
                                if new_context[m][0] < similarity:
                                    new_context[m] = (similarity, self.additional_context[i][jj])
                                break
                        if not found:
                            new_context.append((similarity, self.additional_context[i][jj]))
        return [i[1] for i in sorted(new_context, key=lambda x: x[0], reverse=True)]
    
    def format_context(self, context: List[str]) -> str:
        instructions = '''
        # Example for requesting extra context when completing a function:
        # prompt:
        # def get_credit_scores():
        # """
        # Reads personal data from the data.csv file, calculates credit scores, and returns the list of scores
        # """
        #
        # completion:
        # # need context for
        # # read_csv
        # data = pd.read_csv('data.csv')
        # credit_scores = data['income'] * 0.4 + data['age'] * 0.3 + data['loan'] * 0.3
        # return credit_scores
        # 
        # Now complete the function below and add a commented line at the beginning for each function you use.
        '''
        instructions = textwrap.dedent(instructions)
        commented_context = ['# ' + '\n#'.join(i.split('\n')) for i in context]
        if len(commented_context) == 0:
            return instructions + ''
        if max([len(i) for i in commented_context]) < 3:
            return instructions + ''
        return instructions + '# API REFERENCE:\n' + '\n'.join(commented_context[:5]) + '\n'

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
        new_prompt = clip_prompt(prompt_1 + full_context, 1500 - int(len(prompt_2)/3)) + prompt_2
        return new_prompt, new_context