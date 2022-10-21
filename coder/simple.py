from os import path
from typing import Collection, List
from coder.backend import get_completion
import libcst as cst
from libcst.metadata import FullRepoManager, FullyQualifiedNameProvider
from libcst.metadata import QualifiedNameProvider, PositionProvider
import libcst.matchers as m
from importlib.machinery import PathFinder
from coder.CodeVisitor import CodeVisitor

class SimpleCompletion:
    def __init__(self, project_root: str, important_files: Collection[str], model: str = "Codex"):
        self.project_root = path.abspath(project_root)
        self.important_files = important_files
        self.fqn_to_context = {}
        for file in important_files:
            filepath = path.join(self.project_root, file)
            with open(filepath, 'r') as f:
                content = f.read()
                ast = cst.parse_module(content)
                visitor = CodeVisitor(self.project_root, file[:-3])
                cst.MetadataWrapper(ast).visit(visitor)
                self.fqn_to_context.update(visitor.contents)

        self.manager = FullRepoManager(project_root, paths=important_files, providers={FullyQualifiedNameProvider})
        self.model = model
    
    def closest_fqn(self, name: str) -> str:
        res = ''
        for k, v in self.fqn_to_context.items():
            if name in k and len(v) > 0:
                res += v + '\n'
        return res

    def add_to_context(self, file: str, context: str, completion: str) -> str:
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
        # qnames_in_completion = cst.MetadataWrapper(ast).resolve(QualifiedNameProvider)
        position = {k.value: v for k, v in cst.MetadataWrapper(ast).resolve(PositionProvider).items() if m.matches(k, m.Name())}
        # wrapper = self.manager.get_metadata_wrapper_for_path(file)
        # fqnames = wrapper.resolve(FullyQualifiedNameProvider)
        new_context = context
        # for k, v in {k.value: v for k, v in qnames_in_completion.items() if m.matches(k, m.Name())}.items():
        #     if k in position.keys() and position[k].start.line >= len(context.splitlines()):
        #         if k in fqnames.keys():
        #             fqn = fqnames[k]
        #         else:
        #             fqn = v() if callable(v) else v
        #         for i in fqn:
        #             if i.name not in self.used:
        #                 self.used.add(i.name)
        #                 new_context = self.closest_fqn(i.name) + '\n' + new_context
        for k, v in position.items():
            if v.start.line >= len(context.splitlines()):
                ctx = self.closest_fqn(k)
                if len(ctx) > 0:
                    new_context += '\n' + ctx
        return new_context

    def completion(self, context: str, file: str) -> str:
        BUDGET = 3
        attempts = 0
        self.used = set()
        prev_completion = ''
        completion = get_completion(self.model, context)
        while attempts < BUDGET:# and prev_completion != completion:
            prev_completion = completion
            context = self.add_to_context(file, context, completion)
            completion = get_completion(self.model, context)
            print(f'For context: {context}, got completion: {completion}')
            attempts += 1
        return completion

