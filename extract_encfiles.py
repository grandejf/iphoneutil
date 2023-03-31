#!/usr/bin/env python3

import sys
import os
import struct
import getopt
import getpass
import base64

from iOSbackup import iOSbackup


def main():
    key = ""
    keyfile = ""
    backuproot = ""
    udid = ""
    getkey = 0
    opts,args = getopt.getopt(sys.argv[1:],"",["keyfile=","getkey"]);
    for o,a in opts:
        if o in ("--keyfile"):
            keyfile=a
            pass
        elif o in ("--getkey"):
            getkey=1
        pass
    args.insert(0,sys.argv[0])
    sys.argv=args
    if len(sys.argv)!=3:
        print("Usage: extract_encfiles.py (--keyfile keyfile) (--getkey) udid backupdir")
        sys.exit(0)
        pass
    udid = sys.argv[1]
    backuproot = sys.argv[2]
    if not keyfile or getkey:
        password=getpass.getpass()
    else:
        password = ''
    if password:
        backup = iOSbackup(backuproot=backuproot,
                           udid=udid,
                           cleartextpassword=password)
        key = backup.getDecryptionKey()
        if getkey:
            if (len(key)==64):
                if keyfile:
                    f=open(keyfile,"w")
                    f.write(key)
                    f.close()
                else:
                    print(key)
                    pass
            else:
                print("There was a problem extracting the key.")
                pass
            sys.exit(0)
        pass
    f=open(keyfile,"r")
    key=f.read()
    key=key[0:64];
    backup = iOSbackup(backuproot=backuproot,
                       udid=udid,
                       derivedkey=key)

    for path in ("Library/SMS/sms.db","Library/AddressBook/AddressBook.sqlitedb"):
        fname = os.path.basename(path)
        targetName = fname
        if (fname=="sms.db"):
            targetName = "sms-1.db"
            pass
        elif (fname=="AddressBook.sqlitedb"):
            targetName="addresses.db"
            pass
        file = backup.getFileDecryptedCopy(relativePath=path,
                                           targetFolder="sms",
                                           targetName=targetName)
        pass
                

if __name__ == "__main__":
    main()
        
