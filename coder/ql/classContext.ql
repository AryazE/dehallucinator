import python
import utils

string memberNames(Class c) {
    result = concat(AssignStmt a, Expr target, FunctionDef f|
        f.getDefinedFunction() = c.getAMethod() and 
        a = f.getDefinedFunction().getBody().getAnItem() and 
        a.getATarget() = target and 
        target.(Attribute).getObject() instanceof Name and 
        target.(Attribute).getObject().(Name).toString() = "self" | 
        c.getQualifiedName() + "." + target.(Attribute).getAttr(), "\n")
}

string memberContext(Class c) {
    if memberNames(c) = "" then
        result = ""
    else
        result = "variables:\n" + memberNames(c)
}

string docStringContext(Class c) {
    if exists(StrConst s | s = c.getDocString()) then
        result = c.getDocString().getText().trim().regexpCapture("^([^\r\n]+)", 1) + "\n"
    else
        result = ""
}

string getHeritage(Class c) {
    if not exists(Expr e | e = c.getABase()) then
        result = ""
    else
        result = concat(Expr e | e = c.getABase() | getString(e), ", ")
}

string functionsContext(Class c) {
    if not exists(Function f | f = c.getAMethod()) then
        result = ""
    else
        result = "functions:\n" +
        concat(
            Function f | 
            f = c.getAMethod() and not c.getLocation().getFile().getShortName().matches("%test%") | 
            getFunctionContext(f), "\n"
        ) + "\n"
}

string classContext(Class c) {
    result = "class " + c.getQualifiedName() + "(" + getHeritage(c) + "): " +
        docStringContext(c) +
        functionsContext(c) +
        memberContext(c)
}

from ClassDef cd, Class c
where cd.getDefinedClass() = c and c.inSource()
select c.getName() as name,
    c.getQualifiedName() as qualifiedName, 
    cd.getLocation().getFile().getAbsolutePath() as file,
    cd.getLocation().getStartLine() as start_line,
    cd.getLocation().getStartColumn() as start_column,
    cd.getLocation().getEndLine() as end_line,
    cd.getLocation().getEndColumn() as end_column,
    classContext(c) as context