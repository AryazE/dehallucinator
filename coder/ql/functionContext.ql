import python

string params(Function f) {
    result = concat(f.getAnArg().getName(), ", ") + ""
}

from Function f
select f.getName(), f.getEnclosingModule().getPath().toString(), f.getName() + "(" + params(f) + ")"