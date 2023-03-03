import python

string getQualifiedName(Function f) {
    if exists(string s | s = f.getQualifiedName()) then
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
    if a instanceof BooleanLiteral then
        result = a.(BooleanLiteral).toString()
    else if a instanceof IntegerLiteral then
        result = a.(IntegerLiteral).toString()
    else if a instanceof FloatLiteral then
        result = a.(FloatLiteral).toString()
    else if a instanceof ImaginaryLiteral then
        result = a.(ImaginaryLiteral).toString()
    else if a instanceof None then
        result = a.(None).toString()
    else if a instanceof ImmutableLiteral then
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
    if exists(Expr e | e = p.getDefault()) then
        result = "=" + getString(p.getDefault())
    else
        result = ""
}

string getParamAnnotation(Parameter p) {
    if exists(Expr e | e = p.getAnnotation()) then
        result = ": " + getString(p.getAnnotation())
    else
        result = ""
}

string getParam(Parameter p) {
    result = p.getName() + getDefault(p) + getParamAnnotation(p)
}

string getPosParams(Function f) {
    result = concat(int i |  | getParam(f.getArg(i)), ", " order by i)
}

string getKwParams(Function f) {
    result = concat(int i |  | getParam(f.getKwonlyarg(i)), ", " order by i)
}

string getParams(Function f) {
    if getPosParams(f) != "" and getKwParams(f) != "" then
        result = getPosParams(f) + ", *, " + getKwParams(f)
    else if getPosParams(f) != "" then
        result = getPosParams(f)
    else if getKwParams(f) != "" then
        result = getKwParams(f)
    else
        result = ""
}

string getReturnAnnotation(Function f) {
    if exists(Expr e | e = f.getDefinition().(FunctionExpr).getReturns()) then
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
        result = f.getMetrics().getDocString().getText().trim().regexpReplaceAll("\\s+", " ")
    else
        result = ""
}

string getFunctionContext(Function f) {
    result = getFunctionHeader(f) + getDocString(f)
}