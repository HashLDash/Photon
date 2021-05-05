#!/usr/bin/env python3
print("# This is a REPL just for testing!")
import os
cmd = ""
while True:
    cmd += input("> ")    
    cmd += "\r\n"
    temp = open("temp.w", "w")
    temp.write(cmd)
    temp.close()
    print(os.popen(f'photon temp.w').read())
