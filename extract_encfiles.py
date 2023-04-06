#!/usr/bin/env python3

import sys
import os
import struct
import getopt
import getpass
import base64
import sqlite3

from iOSbackup import iOSbackup

def db_ok(dbfile):
    conn=sqlite3.connect("file:"+dbfile+"?immutable=1",uri=True)
    cursor=conn.cursor()
    dbok=1
    try:
        res=cursor.execute("select name from sqlite_master")
        res.fetchone()
    except sqlite3.DatabaseError as e:
        print(dbfile+": "+str(e),file=sys.stderr)
        dbok=0
        pass
    conn.close()
    return dbok

def fix_db(dbfile):
    # handle corrupt db file
    clonedb = dbfile+".clone.db"
    try:
        os.unlink(clonedb)
    except:
        pass
    os.system("echo '.clone "+clonedb+"' | sqlite3 "+dbfile+" >/dev/null 2>&1")
    os.system("mv "+clonedb+" "+dbfile)
    if (os.path.exists(dbfile+"-wal")):
        os.unlink(dbfile+"-wal")
        pass
    if (os.path.exists(dbfile+"-shm")):
        os.unlink(dbfile+"-shm")
        pass
    print(dbfile+": fixed",file=sys.stderr)
    pass

def main():
    key = ""
    keyfile = ""
    backuproot = ""
    udid = ""
    destdir = "sms"
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
                                           targetFolder=destdir,
                                           targetName=targetName)
        fullpath = destdir+"/"+targetName
        if (fullpath.endswith(".db") and
            not db_ok(fullpath)):
            fix_db(fullpath)
            pass
        pass
                

if __name__ == "__main__":
    main()
        
