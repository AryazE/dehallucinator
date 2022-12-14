import python
import utils

query string members(Class c) {
    exists(AssignStmt a, Expr target | 
        a = c.getInitMethod().getBody().getAnItem() and a.getATarget() = target and target.(Attribute).getObject() instanceof Name and target.(Attribute).getObject().(Name).toString() = "self" | 
        result = target.(Attribute).getAttr()
    )
}

string classContext(Class c) {
    result = getFunctionContext(c.getAMethod())
    or
    result = members(c)
    or
    result = c.getDocString().toString()
}

from ClassDef c
where c.getDefinedClass().inSource()
select c.getDefinedClass().getName() as name, c.getDefinedClass().getQualifiedName() as qualifiedName, c.getEnclosingModule().getPath().toString() as path, classContext(c.getDefinedClass()) as context