#!/usr/bin/env python
import sys
for i, line in enumerate(sys.stdin.readlines()):
    print "%d : %s" %(i, line.strip())
