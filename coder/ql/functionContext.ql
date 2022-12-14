import python
import utils

from FunctionDef fd, Function f
where f = fd.getDefinedFunction() and f.inSource()
select f.getName() as name, f.getQualifiedName() as qualifiedName, fd.getEnclosingModule().getPath().toString() as path, getFunctionContext(f) as context