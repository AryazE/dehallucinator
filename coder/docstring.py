from typing import Tuple, List, Set, Dict
import logging
import re
import time
from .utils import clip_prompt, embeddings, cos_sim
from .BaseDiCompletion import BaseDiCompletion

logger = logging.getLogger(__name__)

class DocstringCompletion(BaseDiCompletion):
    def __init__(self, project_root: str, model: str = "Codex", func: str = '', location: Dict = {}, c: int = 5, t: float = 0.5):
        super().__init__(project_root, model, func, location)
        self.context_size = c
        self.similarity_threshold = t

    def get_context(self, prompt: str, completion: str) -> List[Tuple[float, str]]:
        code = prompt[prompt.rfind(f'def {self.func}'):] + completion #prompt + completion
        lines = code.splitlines()
        new_context = []
        tmp = []
        tmp.extend(self.additional_context.keys())
        line_embeddings = embeddings(lines)
        for i in tmp:
            for l in range(len(lines)):
                for j in range(len(self.embeddings[i])):
                    if j >= len(self.additional_context[i]):
                        jj = 0
                    else:
                        jj = j
                    similarity = cos_sim(self.embeddings[i][j], line_embeddings[l])
                    if similarity > self.similarity_threshold:
                        found = False
                        for m in range(len(new_context)):
                            if new_context[m][1] == self.additional_context[i][jj]:
                                found = True
                                if new_context[m][0] < similarity:
                                    new_context[m] = (similarity, self.additional_context[i][jj])
                                break
                        if not found:
                            new_context.append((similarity, self.additional_context[i][jj]))
        return sorted(new_context, key=lambda x: x[0], reverse=True)
    
    def format_context(self, context: List[Tuple[float, str]]) -> str:
        if len(context) == 0:
            return ''
        # for i in range(len(context)):
        #     tmp = context[i][1]
        #     open_bracket = 0
        #     ann = False
        #     res = ''
        #     for j in range(len(tmp)):
        #         if tmp[j] == ':':
        #             ann = True
        #         elif tmp[j] == '[':
        #             open_bracket += 1
        #         elif tmp[j] == ']':
        #             open_bracket -= 1
        #         elif tmp[j] == '-' and j+1 < len(tmp) and tmp[j+1] == '>':
        #             res += tmp[j:]
        #             break
        #         elif tmp[j] ==',' and open_bracket == 0:
        #             ann = False
        #             res += tmp[j]
        #         elif open_bracket == 0 and not ann:
        #             res += tmp[j]
        #     context[i] = (context[i][0], res)
        context = ['Uses:'] + [i[1] for i in context]
        return self.indent_style*(self.indent_count+1) + f'\n{self.indent_style*(self.indent_count+1)}'.join(context[:self.context_size])

    def generate_new_prompt(self, prompt: str, context: Set[str], completion: str) -> Tuple[str, Set[str]]:
        start = time.process_time_ns()
        new_context = self.get_context(prompt, completion)
        end = time.process_time_ns()
        if not (self.project_root/'..'/'..'/'retrieval_time.txt').exists():
            with open(self.project_root/'..'/'..'/'retrieval_time.txt', 'w') as f:
                f.write(f'{end-start} 1')
        with open(self.project_root/'..'/'..'/'retrieval_time.txt', 'r') as f:
            rt, n = f.read().split(' ')
        with open(self.project_root/'..'/'..'/'retrieval_time.txt', 'w') as f:
            f.write(f'{(float(rt)*int(n)+end-start)/(int(n)+1)} {int(n)+1}')
        # new_context = new_context.union(context)
        full_context = self.format_context(new_context)
        prompt_lines = prompt.splitlines(keepends=True)
        i = 1
        while i < len(prompt_lines) and (prompt_lines[-i].strip().startswith('#') or len(prompt_lines[-i].strip()) == 0):
            i += 1
        logger.info(f'Indent count: {self.indent_count}, Indent style: <{self.indent_style}>')
        logger.info(f'Found {i} lines of comments')
        logger.info(f'Last line: {"".join(prompt_lines[:-i])}')
        if prompt_lines[-i].strip().endswith('"""') or prompt_lines[-i].strip().endswith("'''"):
            new_prompt = ''.join(prompt_lines[:-i]) + prompt_lines[-i].rstrip()[:-3]
            new_prompt += '\n' + full_context + '\n' + self.indent_style*(self.indent_count+1) + '"""\n' + ''.join(prompt_lines[-i+1:])
        else:
            new_prompt = ''.join(prompt_lines[:-i]) + prompt_lines[-i]
            new_prompt += self.indent_style*(self.indent_count+1) + '"""\n'
            new_prompt += '\n' + full_context + '\n' + self.indent_style*(self.indent_count+1) + '"""\n' + ''.join(prompt_lines[-i+1:])
        if self.model == 'GPT3.5':
            prompt_size = 3500
        else:
            prompt_size = 1500
        new_prompt = clip_prompt(new_prompt, prompt_size)
        return new_prompt, new_context