import python

string params(Function f) {
    result = concat(f.getAnArg().getName(), ", ") + ""
}

from FunctionDef f
select f.getDefinedFunction().getName(), f.getEnclosingModule().getPath().toString(), f.getDefinedFunction().getName() + "(" + params(f.getDefinedFunction()) + ")"