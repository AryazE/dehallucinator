import python
import utils

string memberNames(Class c) {
    result = concat(AssignStmt a, Expr target | 
        a = c.getAMethod().getBody().getAnItem() and a.getATarget() = target and target.(Attribute).getObject() instanceof Name and target.(Attribute).getObject().(Name).toString() = "self" | 
        c.getQualifiedName() + "." + target.(Attribute).getAttr(), "\n\t\t")
}

string memberContext(Class c) {
    if memberNames(c) = "" then
        result = ""
    else
        result = "\tvariables:\n" + "\t\t" + memberNames(c)
}

string docStringContext(Class c) {
    if c.getDocString().getText() != "" then
        result = "\t" + c.getDocString().getText() + "\n"
    else
        result = ""
}

string getHeritage(Class c) {
    if count( |  | c.getABase()) = 0 then
        result = ""
    else
        result = concat(Expr e | e = c.getABase() | getString(e), ", ")
}

string functionsContext(Class c) {
    if count( |  | c.getAMethod()) = 0 then
        result = ""
    else
        result = "\tfunctions:\n" +
        "\t\t" + concat(Function f | f = c.getAMethod() | getFunctionContext(f), "\n\t\t") + "\n"
}

string classContext(Class c) {
    result = "class " + c.getQualifiedName() + "(" + getHeritage(c) + "):\n" +
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