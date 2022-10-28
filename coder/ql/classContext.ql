import python

string params(Function f) {
    result = concat(f.getAnArg().getName(), ", ")
}

query string signatures(Class c) {
    exists(Function f | f = c.getAMethod() |
        result = f.getName() + "(" + params(f) + ")"
    )
}

query string members(Class c) {
    exists(AssignStmt a | 
        a = c.getInitMethod().getBody().getAnItem() | 
        result = a.getATarget().(Attribute).getName()
    )
}

string classContext(Class c) {
    result = signatures(c)
    or
    result = members(c)
}

from Class c
select c.getName(), c.getEnclosingModule().getPath().toString(), classContext(c)