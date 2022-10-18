from typing import Collection, List
from coder.backend import get_completion
import libcst as cst
from libcst.metadata import FullRepoManager, FullyQualifiedNameProvider
from libcst.metadata import QualifiedNameSource

class SimpleCompletion:
    def __init__(self, project_root: str, important_files: Collection[str]):
        self.project_root = project_root
        self.manager = FullRepoManager(project_root, important_files, {FullyQualifiedNameProvider})

    def add_to_context(self, context: str, completion: str, file: str) -> str:
        wrapper = self.manager.get_metadata_wrapper_for_path(file)
        fqnames = wrapper.resolve(FullyQualifiedNameProvider)
        for k, v in fqnames.items():
            for i in v:
                if i.source == QualifiedNameSource.IMPORT:
                    print(k, i)
        return context

    def completion(self, context: str, file: str) -> str:
        BUDGET = 10
        attempts = 0
        prev_completion = "<Empty>"
        completion = ""
        while attempts < BUDGET and prev_completion != completion:
            prev_completion = completion
            context = self.add_to_context(context, completion, file)
            completion = get_completion(context)
            attempts += 1
        return completion

