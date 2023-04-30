from typing import Tuple, List, Set, Dict
import logging
from sklearn.preprocessing import normalize
import time
from .utils import clip_prompt, embeddings, cos_sim
from .BaseDiCompletion import BaseDiCompletion

logger = logging.getLogger(__name__)

class CommentCompletion(BaseDiCompletion):
    def __init__(self, project_root: str, model: str = "Codex", func: str = '', location: Dict = {}, c: int = 5, t: float = 0.5, mode: str = ''):
        super().__init__(project_root, model, func, location, mode)
        self.context_size = c
        self.similarity_threshold = t

    def get_context(self, prompt: str, completion: str) -> List[Tuple[float, str]]:
        code = completion #prompt[prompt.rfind(f'def {self.func}'):] + completion #prompt + completion
        lines = code.splitlines()
        line_embeddings = normalize(embeddings(lines))
        dist, res = self.ball_tree.query(line_embeddings, k=self.context_size)
        bests = {}
        for i in range(len(res)):
            for j in range(len(res[i])):
                if dist[i][j] < 1 - self.similarity_threshold:
                    if res[i][j] not in bests:
                        bests[res[i][j]] = dist[i][j]
                    else:
                        bests[res[i][j]] = min(bests[res[i][j]], dist[i][j])
        indices = sorted([(dis, ind) for ind, dis in bests.items()], key=lambda x: x[0])
        contexts = [(dis, self.additional_context[ind]) for dis, ind in indices]
        ignore = set()
        used = set()
        for i in range(len(contexts)):
            if contexts[i][1] in used:
                ignore.add(i)
            else:
                used.add(contexts[i][1])
        return [contexts[i] for i in range(len(contexts)) if i not in ignore]
    
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
        context = ['# API Reference:'] + [i[1] for i in context[:self.context_size]]
        return '\n# '.join(context)

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
        full_context = self.format_context(new_context)
        if self.model == 'GPT3.5':
            prompt_size = 3500
        else:
            prompt_size = 1750
        new_prompt = full_context + '\n' + clip_prompt(prompt, prompt_size - len(full_context)//2)
        return new_prompt, new_context