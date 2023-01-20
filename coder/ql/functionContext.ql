import python
import utils

from FunctionDef fd, Function f
where f = fd.getDefinedFunction() and f.inSource() and okayToLook(fd)
select f.getName() as name, 
    f.getQualifiedName() as qualifiedName, 
    fd.getLocation().getFile().getAbsolutePath() as file,
    fd.getLocation().getStartLine() as start_line,
    fd.getLocation().getStartColumn() as start_column,
    fd.getLocation().getEndLine() as end_line,
    fd.getLocation().getEndColumn() as end_column, 
    getFunctionContext(f) as context