import python
import utils

string memberNames(Class c) {
    result = concat(AssignStmt a, Expr target | 
        a = c.getInitMethod().getBody().getAnItem() and a.getATarget() = target and target.(Attribute).getObject() instanceof Name and target.(Attribute).getObject().(Name).toString() = "self" | 
        target.(Attribute).getAttr(),
        "\n\t"
    )
}

string memberContext(Class c) {
    if count( |  | memberNames(c)) = 0 then
        result = ""
    else
        result = memberNames(c)
}

string docStringContext(Class c) {
    if c.getDocString().getText() != "" then
        result = c.getDocString().getText()
    else
        result = ""
}

string getHeritage(Class c) {
    if count( |  | c.getABase()) = 0 then
        result = ""
    else
        result = concat(Expr e | e = c.getABase() | getString(e), ", ")
}

string classContext(Class c) {
    result = "class " + c.getQualifiedName() + "(" + getHeritage(c) + "):\n" +
        "\t" + docStringContext(c) + "\n" +
        "\tfunctions:\n" +
        "\t" + concat(Function f | f = c.getAMethod() | getFunctionContext(f), "\n\t") + "\n" +
        "\tvariables:\n" +
        "\t" + memberContext(c)
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