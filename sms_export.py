#!/usr/bin/env python3
import base64, os, subprocess, sys, argparse

import sqlite3
import glob
import time
import stat
import io
import hashlib
import calendar
import re

#import ManifestMBDB
import emoji2unicode

emoji=emoji2unicode.Emoji()

sqlite_connect_options="immutable=1"

debug=0

class bplist_converter:
    def decode_bplist(self, plist_filename):
        decode_command = "plutil -convert xml1 \"%(plist_filename)s\"" % locals()
        status=os.system(decode_command)
        if not status == 0:
            print("Error converting from binary plist using plutil.")
            sys.exit(2)
            pass
        return

class data_section:
    def __init__(self):
        self.data = []
        self.path = ""
        self.domain=None
    def decode(self):
        return base64.b64decode("".join(self.data))
    def write(self):
        self.path = os.path.join("MobileSyncExport",self.path)
        thepath, thefile = os.path.split(self.path)       
        
        #if the folders don't exists, make 'em
        if not os.path.exists(thepath):
            os.makedirs(thepath) 
		
       	# convert from base64
        if (sys.version[:1] > (2,4)):	
            output_text = base64.b64decode("".join(self.data))
       	else:
            output_text = base64.decodestring("".join(self.data))		

        if output_text == "":
            print("No text to output.")
            print("path " + self.path)
            return
		
        print("the file:" + thefile)	 
				
        output_file = open(self.path, 'wb') 
        
        output_file.write(output_text)
        output_file.close()
		
        # check here if it's a plist and decode it using plutil
        if output_text[0:6] == "bplist":
            c = bplist_converter()
            c.decode_bplist(self.path)

import xml.sax
import xml.sax.handler

class plist_XMLHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        xml.sax.handler.ContentHandler.__init__(self)
        self.inkey=0
        self.indata=0
        self.currentkey=""
        self.currentdata=""
        self.dict={}
        pass
    def getRecommendedFeatures(self):
        """The recommended features (which clients should pass along to the
        SAX parser) disable namespace parsing and external entities.
        
        If external_ges aren't disabled, xml.sax.handler may try to load the DTD
        from Apple's web server, which prevents parsing when there's no Internet
        connection."""
        print("----------here")
        return {feature_namespaces: 0, feature_external_ges: 0, feature_external_pes: 0}

    def startElement(self,name,attrs):
        if name=="key":
            self.inkey=1
            pass
        elif (name=="string" or
              name=="false" or
              name=="data"):
            self.indata=1
            pass
        pass
    def endElement(self,name):
        if name=="key":
            self.inkey=0
            pass
        elif (name=="string" or
              name=="false" or
              name=="data"):
            self.indata=0
            self.dict[self.currentkey.lower()]=self.currentdata
            self.currentkey=""
            self.currentdata=""
            pass
        pass
    def characters(self,content):
        if self.inkey:
            self.currentkey+=content
            pass
        if self.indata:
            self.currentdata+=content
            pass
        pass
    def getData(self):
        if "path" in self.dict:
            data=data_section()
            data.path=self.dict["path"]
            if data.path==None:
                data.path=""
                pass
            data.domain=self.dict["domain"]
            return data
        elif "metadata" in self.dict:
            metadata=self.dict["metadata"]
            buf=base64.b64decode(metadata)
            tempfilename="sms_export.tmp"
            file=open(tempfilename,"w")
            file.write(buf)
            file.close()
            bplist_converter().decode_bplist(tempfilename)
            file=open(tempfilename,"r")
            buf=file.read()
            file.close()
            xmlhandler=plist_XMLHandler()
            xml.sax.parseString(buf,xmlhandler)
            data=xmlhandler.getData()
            return data
        return None
    

class recipient_plist_XMLHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        xml.sax.handler.ContentHandler.__init__(self)
        self.inArray=0
        self.currentString=None
        self.array=[]
        pass
    def getRecommendedFeatures(self):
        """The recommended features (which clients should pass along to the
        SAX parser) disable namespace parsing and external entities.
        
        If external_ges aren't disabled, xml.sax.handler may try to load the DTD
        from Apple's web server, which prevents parsing when there's no Internet
        connection."""
        print("----------here")
        return {feature_namespaces: 0, feature_external_ges: 0, feature_external_pes: 0}
    def startElement(self,name,attrs):
        if name=="array":
            self.inArray=1
            pass
        elif name=="string":
            self.currentString=""
            pass
        pass
    def endElement(self,name):
        if name=="string":
            self.array.append(self.currentString)
            self.currentString=None
            pass
        pass
    def characters(self,content):
        if self.currentString!=None:
            self.currentString+=content
            pass
        pass
    def getArray(self):
        return self.array
        
def get_columnnames_from_cursor(cursor,lowercase=1):
    column_names=[]
    for curcol in range(0,len(cursor.description)):
        name=cursor.description[curcol][0]
        if lowercase:
            name=name.lower()
            pass
        column_names.append(name)
        pass
    return column_names


def sequence_to_dict(column_names,seq):
    dict={}
    for curcol in range(0,len(column_names)):
        dict[column_names[curcol]] = seq[curcol]
        pass
    return dict
    
def fetchall_dict(cursor,lowercase=1):
    """
    NOTE: the keys are converted to lowercase
    """
    result=[]
    column_names=get_columnnames_from_cursor(cursor,lowercase)
    rows=cursor.fetchall()
    for currow in rows:
        rowdict = sequence_to_dict(column_names,currow)
        result.append(rowdict)
        pass
    return result


class Person:
    def __init__(self,id):
        self.id=id
        self.name=None
        self.phonenumbers=[]
        pass
    def setName(self,name):
        self.name=name
        pass
    def addPhoneNumber(self,number):
        number=normalizeNumber(number)
        self.phonenumbers.append(number)

class Addresses:
    def __init__(self,addressdb):
        self.numbers={}
        self.emails={}
        self.people={}
        self.readDB(addressdb)
        return
    def readDB(self,addressdb):
        conn=sqlite3.connect("file:"+addressdb+"?"+sqlite_connect_options)
        c=conn.cursor()
        c.execute("select ROWID,First,Middle,Last,Organization from ABPerson")
        rows=fetchall_dict(c)
        for row in rows:
            person=Person(row["rowid"])
            name=""
            if row["first"]!=None:
                name=name.strip()+" "+row["first"]
                pass
            if row["middle"]!=None:
                name=name.strip()+" "+row["middle"]
                pass
            if row["last"]!=None:
                name=name.strip()+" "+row["last"]
                pass
            if name=='':
                name=row["organization"]
                pass
            person.setName(name)
            self.people[person.id]=person
            pass
        c.execute("select record_id,value from ABMultiValue where property=3")
        rows=fetchall_dict(c)
        for row in rows:
            number = normalizeNumber(row["value"])
            self.people[row["record_id"]].addPhoneNumber(number)
            self.numbers[number]=self.people[row["record_id"]]
            pass
        c.execute("select record_id,value from ABMultiValue where property=4")
        rows=fetchall_dict(c)
        for row in rows:
            email = row["value"]
            self.emails[email]=self.people[row["record_id"]]
            pass
        return


def generateFilenameFromName(name):
    arr=list(name)
    narr=[]
    for c in arr:
        if c.isalnum():
            narr.append(c)
            pass
        pass
    return "".join(narr)

def getLastTimestamp(filename):
    """
    ----
    timestamp
    ctimestamp
    message
    """
    timestamp=0
    try:
        f=open(filename,"r")
        while 1:
            line=f.readline()
            if line=="":
                break
            line=line.strip()
            if line=="----":
                line=f.readline()
                timestamp=int(line)
                pass
            pass
        f.close()
    except:
        return 0
    return timestamp

def exportSMS(filename,timestamp,text,flags,row):
    text=emoji.translate(text)
    buf=""    
    buf+="----\n"
    buf+=str(timestamp)+"\n"
    buf+=time.ctime(timestamp)+"\n"
    message_type = 'sms'
    if row['service'] == 'iMessage':
        message_type = 'iMessage'
        pass
    if flags==2:
        buf+="Received from "+row["handle_from"]+" ("+message_type+"):\n"
        pass
    else:
        buf+="Sent ("+message_type+"):\n"
        pass
    buf+=text+"\n"
    if (debug):
        sys.stdout.write(buf)
        return
    f=open(filename,"a")
    # f.write(buf.encode("utf-8"))
    f.write(buf)
    f.close()

def madrid_ts_to_unix(ts):
    # iOS 11: divide ts by 1000000000
    return calendar.timegm(time.strptime("2001-01-01 00:00","%Y-%m-%d %H:%M"))+ts/1000000000

def message_sort_key(row):
    return row['date']

def normalizeNumber(number):
    number=number.encode('ascii', 'ignore').decode("utf-8");
    number=re.sub(r'\s+',' ',number)
    match=re.match(r'\+1 (\(\d+\) \d+-\d+)',number)
    if (match):
        number=match[1]
        pass
    matched=0
    match=re.match(r'^1(\d{3})(\d{3})(\d{4})$',number)
    if (match):
        # assume USA number 16192223610
        number=match[1]+"-"+match[2]+"-"+match[3]
        matched=1
        pass
    match=re.match(r'^\s*\((\d{3})\) (\d{3})-(\d{4})$',number)
    if not matched	and match:
        # assume USA number (123) 456-7890
        number=match[1]+"-"+match[2]+"-"+match[3]
        matched=1
        pass
    match=re.match(r'^\+1(\d{3})(\d{3})(\d{4})$',number)
    if not matched and match:
        # assume USA number +11234567890 
        number=match[1]+"-"+match[2]+"-"+match[3]
        matched=1
        pass
    match=re.match(r'^\+1\s*\((\d{3})\)\s*(\d{3})-?(\d{4})$',number)
    if not matched and match:
        # assume USA number +1(123) 456-7890 
        number=match[1]+"-"+match[2]+"-"+match[3]
        matched=1
        pass
    match=re.match(r'^\+1\-(\d{3})-(\d{3})-(\d{4})$',number)
    if not matched and match:
        # assume USA number +1-123-456-7890 
        number=match[1]+"-"+match[2]+"-"+match[3]
        matched=1
        pass
    return number

def replace_memoji(text,attachment_rows):
    guid_to_emoji = {}
    for row in attachment_rows:
        desc = row['emoji_image_short_description']
        desc = desc.strip()
        guid_to_emoji[row['guid']] = desc
        pass
    def emoji_guid(match):
        guid = match[1]
        desc = guid_to_emoji[guid]
        if (desc):
            desc = "[EMOJI="+desc+"]"
        return desc
    text = re.sub(r'\[emoji_guid=(.+?)\]',emoji_guid,text)
    return text

def processSMSDB(smsdir,addressdb,smsdb,lastTimeStamps):
    updated = {}
    addresses=Addresses(addressdb)
    conn=sqlite3.connect("file:"+smsdb+"?"+sqlite_connect_options)
    c=conn.cursor()
    c.execute("select * from message order by date")
    rows=fetchall_dict(c)
    rows.sort(key=message_sort_key)
    for row in rows:
        numbers=[]
        display_names={}
        # chat.is_filtered=2 appears to signify messages in the Spam filter
        c.execute("select chat_identifier,display_name from chat,chat_message_join where chat.rowid=chat_message_join.chat_id and chat_message_join.message_id="+str(row['rowid'])+" and chat.is_filtered!=2")
        recipients=fetchall_dict(c)
        for recp in recipients:
            numbers.append(recp['chat_identifier'])
            if recp['display_name']!='':
                display_names[recp['chat_identifier']]=recp['display_name']
                pass
            pass
        for number in numbers:
            chat_identifier = number
            number = normalizeNumber(number)
            person=None
            if number in addresses.numbers:
                person=addresses.numbers[number]
                pass
            if person==None and chat_identifier in addresses.emails:
                person=addresses.emails[chat_identifier]
                pass
            if person==None and chat_identifier in display_names:
                number=display_names[chat_identifier]
                pass

            if person!=None:
                filename=generateFilenameFromName(person.name)
            else:
                filename=generateFilenameFromName(number)
                pass

            filename=smsdir+"/"+filename+"-sms.txt"
            # store the timestamps in a dictionary and use it since we want to make sure we catch all the new messages
            # since the last run
            if filename in lastTimeStamps:
                timestamp=lastTimeStamps[filename]
            else:
                timestamp=getLastTimestamp(filename)
                lastTimeStamps[filename]=timestamp
                pass
            smstimestamp=int(madrid_ts_to_unix(row["date"]))
            if (smstimestamp>timestamp):
                if filename not in updated:
                    print("Updating "+filename)
                    updated[filename]=1
                    pass
                c.execute("""select message_id,attachment_id,attachment.guid,emoji_image_short_description
                from message_attachment_join 
                left join attachment on attachment.ROWID = message_attachment_join.attachment_id
                where emoji_image_content_identifier is not NULL and message_attachment_join.message_id=?""",[row["rowid"]])
                attachment_rows = fetchall_dict(c)
                text=row["text"]
                if text==None:
                    attributedBody = row["attributedbody"];
                    if (attributedBody != None):
                        text = abody2txt_swift(attributedBody)
                        text = replace_memoji(text,attachment_rows)
                    else:
                        text=""
                        pass
                    if text==None:
                        text=""
                        pass
                    pass
                if (0):
                    c.execute("select * from msg_pieces where message_id=?",[row["rowid"]])
                    pieces_rows=fetchall_dict(c)
                    for prow in pieces_rows:
                        if prow["content_type"].startswith("text") or prow["content_type"].startswith("application/smil"):
                            if prow["data"]!=None:
                                text+=str(prow["data"],"utf-8","xmlcharrefreplace")+"\n"
                                pass
                            pass
                        else:
                            if prow["content_loc"]!=None:
                                text+=prow["content_loc"]+"\n"
                                pass
                            pass
                        pass
                    pass
                flags = 2
                if (row['is_from_me']):
                    flags = 0
                    pass
                c.execute("select * from handle where rowid=?",[row["handle_id"]])
                handle = fetchall_dict(c);
                if (len(handle)==1):
                    fromnumber = handle[0]["id"]
                    fromnumber = normalizeNumber(fromnumber)
                    fromperson=None
                    if fromnumber in addresses.numbers:
                        fromperson=addresses.numbers[fromnumber]
                        pass
                    if (fromperson):
                        row["handle_from"] = fromperson.name or fromnumber
                        pass
                    else:
                        row["handle_from"] = fromnumber
                        pass
                    pass
                else:
                    row["handle_from"] = ''
                    pass
                exportSMS(filename,smstimestamp,text,flags,row)
                pass
            pass
        pass
    return


def getDataFromInfo(info_filename):
    # gets the data from the data file (data used to be in the data blob in the mdbackup file)
    filename=info_filename.replace("mdinfo","mddata")
    file=open(filename,"rb")
    data=file.read()
    file.close()
    return data

def parseXML(xmlhandler,text):
    xmlparser=xml.sax.make_parser()
    xmlparser.setFeature(xml.sax.handler.feature_namespaces,0)
    xmlparser.setFeature(xml.sax.handler.feature_external_ges,0)
    xmlparser.setFeature(xml.sax.handler.feature_external_pes,0)
    xmlparser.setContentHandler(xmlhandler)
    xmlparser.parse(io.StringIO(text))
    return

def verifySMSDB(filename):
    conn=sqlite3.connect("file:"+filename+"?"+sqlite_connect_options)
    c=conn.cursor();
    c.execute("select name from sqlite_master")
    rows=fetchall_dict(c)
    tables=[]
    for row in rows:
        tables.append(row["name"])
        pass
    if ("message" in tables):
        return 1
    return 0

def verifyAddressDB(filename):
    conn=sqlite3.connect("file:"+filename+"?"+sqlite_connect_options)
    c=conn.cursor();
    c.execute("select name from sqlite_master")
    rows=fetchall_dict(c)
    tables=[]
    for row in rows:
        tables.append(row["name"])
        pass
    
    if "ABPerson" in tables:
        return 1
    return 0

def abody2txt_swift(attributedBody):
    tfile = open("attributedbody.tmp","wb")
    tfile.write(attributedBody)
    tfile.close()
    buf=os.popen("swift abody2txt.swift attributedbody.tmp 2>abody2txt.errors").read()
    if (buf):
        return buf
    return None

def abody2txt(attributedBody):
    tfile = open("attributedbody.tmp","wb")
    tfile.write(attributedBody)
    tfile.close()
    buf=os.popen("./abody2txt.py attributedbody.tmp 2>abody2txt.errors").read()
    if (buf):
        return buf
    return None

def main(argv):
    global debug

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--debug', action='store_true', help="debug: don't write files")
    arg_parser.add_argument('directory',nargs='?')
    args = arg_parser.parse_args()
    debug = args.debug

    skipcopy=0
    if (args.directory):
        directory = args.directory
    else:
        skipcopy=1
        pass
        
    converter = bplist_converter()

    smsdir="sms"

    smsdbs=[]
    addressdb=None

    useManifest=0
    useSHA=1
    if skipcopy:
        smsdb=smsdir+"/sms-1.db"
        if not verifySMSDB(smsdb):
            print("Problem with sms-1.db")
            sys.exit(1)
            pass
        else:
            smsdbs.append(smsdb)
            pass
        addressdb=smsdir+"/addresses.db"
        if not verifyAddressDB(addressdb):
            print("Problem with addresses.db")
            sys.exit(1)
            pass
        pass
    elif (useManifest or useSHA):
        if useManifest:
            filename=ManifestMBDB.get_filename_from_db(directory,"Library/SMS/sms.db")
            pass
        if useSHA:
            filename=hashlib.sha1(str("HomeDomain-"+"Library/SMS/sms.db").encode("utf-8")).hexdigest()
            filename=filename[:2]+"/"+filename
            pass
        filename=directory+"/"+filename
        if os.path.exists(filename) and verifySMSDB(filename):
            print("Processing "+filename)
            smsdb=smsdir+"/sms-"+str(len(smsdbs)+1)+".db"
            smsdbs.append(smsdb)
            os.system("cp -p "+filename+" "+smsdb)
            pass
        else:
            print(filename)
            print("Couldn't find sms.db")
            sys.exit(1)
            pass
        if useManifest:
            filename=ManifestMBDB.get_filename_from_db(directory,"Library/AddressBook/AddressBook.sqlitedb")
        if useSHA:
            filename=hashlib.sha1(str("HomeDomain-"+"Library/AddressBook/AddressBook.sqlitedb").encode("utf-8")).hexdigest()
            filename=filename[:2]+"/"+filename
            pass
        filename=directory+"/"+filename
        if os.path.exists(filename) and verifyAddressDB(filename):
            print("Processing "+filename)
            addressdb=smsdir+"/addresses.db"
            os.system("cp -p "+filename+" "+addressdb)
            pass
        else:
            print("Couldn't find address.db")
            sys.exit(1)
            pass
        pass
        
    lastTimeStamps={}
    for smsdb in smsdbs:
        processSMSDB(smsdir,addressdb,smsdb,lastTimeStamps)
        pass
    pass

if __name__ == "__main__":
    main(sys.argv)
