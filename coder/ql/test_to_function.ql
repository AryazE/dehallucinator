import python

predicate callPath(FunctionDef source, FunctionDef target) {
    callGraphEdge(source, target)
    or
    exists(FunctionDef callee |
        callGraphEdge(source, callee) and
        callPath(callee, target)
    )
}

predicate callGraphEdge(FunctionDef caller, FunctionDef callee) {
    callee.getDefinedFunction().getFunctionObject().getACall().getScope().(Function) = caller.getDefinedFunction()
}

from FunctionDef f1, FunctionDef f2
where 
    f1.getLocation().getFile().getAbsolutePath().matches("%tests%") and
    //f2.getDefinition().getLocation().getFile().getAbsolutePath().matches("%UltraDict%") and
    callPath(f1, f2)
select f1.getDefinedFunction().getName(), f2.getDefinedFunction().getName()