import python

external predicate dontLook(string file, int startLine, int startColumn, int endLine, int endColumn);

string getQualifiedName(Function f) {
    if f.getQualifiedName() != "" then
        result = f.getQualifiedName()
    else
        result = f.getName()
}

language[monotonicAggregates]
string tupleToString(Tuple t) {
    if t.isParenthesized() then
        result = "(" + concat(int i | i = [0 .. count(|| t.getAnElt())] | getString(t.getElt(i)), ", " order by i) + ")"
    else
        result = concat(int i | i = [0 .. count(|| t.getAnElt())] | getString(t.getElt(i)), ", " order by i)
}

string getString(Expr a) {
    if a instanceof ImmutableLiteral then
        result = a.(ImmutableLiteral).getLiteralValue().toString()
    else if a instanceof Name then
        result = a.(Name).toString()
    else if a instanceof Subscript then
        result = getString(a.(Subscript).getValue()) + "[" + getString(a.(Subscript).getIndex()) + "]"
    else if a instanceof Str then
        result = a.(Str).getText()
    else if a instanceof Tuple then
        result = tupleToString(a.(Tuple))
    else if a instanceof Ellipsis then
        result = "..."
    else if a instanceof Attribute then
        result = getString(a.(Attribute).getObject()) + "." + a.(Attribute).getAttr()
    else
        result = a.toString()
}

string getDefault(Parameter p) {
    if p.getDefault().toString() != "" then
        result = "=" + getString(p.getDefault())
    else
        result = ""
}

string getParamAnnotation(Parameter p) {
    if p.getAnnotation().toString() != "" then
        result = ": " + getString(p.getAnnotation())
    else
        result = ""
}

string getParam(Parameter p) {
    result = p.getName() + getDefault(p) + getParamAnnotation(p)
}

string getParams(Function f) {
    result = concat(int i |  | getParam(f.getArg(i)), ", " order by i)
}

string getReturnAnnotation(Function f) {
    if f.getDefinition().(FunctionExpr).getReturns().toString() != "" then
        result = " -> " + getString(f.getDefinition().(FunctionExpr).getReturns())
    else
        result = ""
}

string getFunctionHeader(Function f) {
    if getReturnAnnotation(f) != "" then
        result = getQualifiedName(f) + "(" + getParams(f) + ")" + getReturnAnnotation(f)
    else
        result = getQualifiedName(f) + "(" + getParams(f) + ")"
}

string getDocString(Function f) {
    if f.getMetrics().getDocString().getText() != "" then
        result = " - " + f.getMetrics().getDocString().getText().regexpFind("^[^\r\n]+", _, _).trim()
    else
        result = ""
}

string getFunctionContext(Function f) {
    result = getFunctionHeader(f) + getDocString(f)
}

predicate okayToLook(FunctionDef f) {
    not exists(string file, int startLine, int startColumn, int endLine, int endColumn |
        dontLook(file, startLine, startColumn, endLine, endColumn) and
        f.getLocation().getFile().getRelativePath() = file and
        f.getLocation().getStartLine() <= startLine and
        f.getLocation().getStartColumn() <= startColumn and
        f.getLocation().getEndLine() >= endLine and
        f.getLocation().getEndColumn() >= endColumn
    )
}