#!/usr/bin/python

import sys
sys.path.append("pycrypto")
sys.path.append("iphone-dataprotection")

from backups.backup10 import ManifestDB
from keystore.keybag import Keybag
from util import readPlist
import os
import struct
import getopt
import getpass
import base64

def main():
    key = ""
    keyfile = ""
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
    if len(sys.argv)!=2:
        print "Usage: extract_encfiles.py (--keyfile keyfile) (--getkey) backupdir"
        sys.exit(0)
    backup_path = sys.argv[1]
    manifest = readPlist(backup_path + "/Manifest.plist")
    kb = Keybag(manifest["BackupKeyBag"].data)
    if not keyfile or getkey:
        password=getpass.getpass()
    else:
        password = ''
    if password:
        key=kb.getPasscodekeyFromPasscode(password,ios102=True)
        if getkey:
            if (len(key)==32):
                if keyfile:
                    f=open(keyfile,"w")
                    f.write(base64.b64encode(key))
                    f.close()
                else:
                    print base64.b64encode(key)
                    pass
            else:
                print "There was a problem extracting the key."
                pass
            sys.exit(0)
        pass
    f=open(keyfile,"r")
    key=base64.b64decode(f.read())
    key=key[0:32];
    kb.unlockWithPasscodeKey(key)
    manifest["password"] = password
    manifest_key = None
    if 'ManifestKey' in manifest:
        clas = struct.unpack('<L', manifest['ManifestKey'].data[:4])[0]
        wkey = manifest['ManifestKey'].data[4:]
        manifest_key = kb.unwrapKeyForClass(clas, wkey)
    manifest_db = ManifestDB(backup_path, key=manifest_key)
    manifest_db.keybag = kb
    for filename, mbfile in manifest_db.files.iteritems():
        if (mbfile.domain=="HomeDomain"):
            if mbfile.relative_path in ("Library/SMS/sms.db","Library/AddressBook/AddressBook.sqlitedb"):
                mbfile.domain="."
                mbfile.relative_path=os.path.basename(mbfile.relative_path)
                if mbfile.relative_path=="sms.db":
                    mbfile.relative_path="sms-1.db"
                    pass
                if mbfile.relative_path=="AddressBook.sqlitedb":
                    mbfile.relative_path="addresses.db"
                    pass
                manifest_db._extract_file(filename,mbfile,"sms")
                

if __name__ == "__main__":
    main()
        
