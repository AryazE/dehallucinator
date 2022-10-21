from os import path
from typing import Optional
import libcst as cst
from libcst.metadata import QualifiedNameProvider, PositionProvider
import libcst.matchers as m

class CodeVisitor(cst.CSTVisitor):
    METADATA_DEPENDENCIES = (QualifiedNameProvider, PositionProvider,)

    def __init__(self, root: str, filepath: str):
        self.contents = {}
        self.filepath = filepath
        with open(path.join(root, filepath + '.py'), 'r') as f:
            self.content = f.read().splitlines()
        self.parent = []
        self.signatures = []
    
    @m.call_if_not_inside(m.ClassDef)
    def visit_ClassDef(self, node: cst.ClassDef) -> Optional[bool]:
        self.parent.append(node.name.value)
    
    @m.call_if_not_inside(m.ClassDef)
    def leave_ClassDef(self, node: cst.ClassDef) -> None:
        self.parent.pop()
        members = '\n# '.join(self.signatures)
        self.signatures = []
        pos = self.get_metadata(PositionProvider, node)
        signature = self.content[pos.start.line - 1]
        my_names = self.get_metadata(QualifiedNameProvider, node.name).pop().name
        name_prefix = self.filepath.replace('/', '.')
        self.contents[name_prefix + '.' + my_names] = '# ' + signature + '\n# ' + members
        self.signatures.append(signature)
    
    @m.call_if_not_inside(m.FunctionDef)
    def visit_FunctionDef(self, node: cst.FunctionDef) -> Optional[bool]:
        self.parent.append(node.name.value)
    
    @m.call_if_not_inside(m.FunctionDef)
    def leave_FunctionDef(self, node: cst.FunctionDef) -> None:
        self.parent.pop()
        pos = self.get_metadata(PositionProvider, node)
        signature = self.content[pos.start.line - 1]
        my_names = self.get_metadata(QualifiedNameProvider, node.name).pop().name
        name_prefix = self.filepath.replace('/', '.')
        self.contents[name_prefix + '.' + my_names] = '# ' + signature
        self.signatures.append(signature)
    
