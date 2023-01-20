import python
import utils

string memberNames(Class c) {
    result = concat(AssignStmt a, Expr target, FunctionDef f|
        f.getDefinedFunction() = c.getAMethod() and 
        // not engulfs(f, file, startLine, startColumn, endLine, endColumn) and
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
    if c.getDocString().getText() != "" then
        result = c.getDocString().getText().regexpReplaceAll("\n", "<NL>") + "\n"
    else
        result = ""
}

string getHeritage(Class c) {
    if count( |  | c.getABase()) = 0 then
        result = ""
    else
        result = concat(Expr e | e = c.getABase() | getString(e), ", ")
}

predicate filtered(Function f) {
    f.getName().regexpMatch("__.+__")
}

string functionsContext(Class c) {
    if count( |  | c.getAMethod()) = 0 then
        result = ""
    else
        result = "functions:\n" +
        concat(Function f | f = c.getAMethod() and not filtered(f) | getFunctionContext(f), "\n") + "\n"
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