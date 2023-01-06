#!/usr/bin/env python3

from typedstream import stream
from typedstream import archiving
from typedstream import advanced_repr
import re
import sys

from ast import literal_eval
import ast

def main(argv):
    ts=stream.TypedStreamReader.open(argv[1])
    for obj in ts:
        r = repr(obj)
        if (re.match(r"b['\"]",r)):
            print(literal_eval(r).decode("utf8"))
            break
    sys.exit(0)
                  

if __name__ == "__main__":
        main(sys.argv)
