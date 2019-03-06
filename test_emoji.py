#!/usr/bin/python

import sys
import emoji2unicode

emoji=emoji2unicode.Emoji()

for line in sys.stdin:
    line = line.decode('utf-8')
    print emoji.translate(line)
    
