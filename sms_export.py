#!/usr/bin/python
import base64, os, commands, sys, getopt
from sgmllib import SGMLParser

import sqlite3
import glob
import time
import stat
import StringIO
import hashlib
import calendar

#import ManifestMBDB
import emoji2unicode

emoji=emoji2unicode.Emoji()

class bplist_converter:
    def decode_bplist(self, plist_filename):
        decode_command = "plutil -convert xml1 \"%(plist_filename)s\"" % locals()
        status=os.system(decode_command)
        if not status == 0:
            print "Error converting from binary plist using plutil."
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
            print "No text to output."
            print "path " + self.path
            return
		
        print "the file:" + thefile	 
				
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
        print "----------here"
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
        if self.dict.has_key("path"):
            data=data_section()
            data.path=self.dict["path"]
            if data.path==None:
                data.path=""
                pass
            data.domain=self.dict["domain"]
            return data
        elif self.dict.has_key("metadata"):
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
        print "----------here"
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
        
class plist_processor(SGMLParser):
    def reset(self):
        SGMLParser.reset(self)
        self.inkey = 0
        self.indata = 0
        self.sections = []
        self.currentkey = ""
        self.currentdata=data_section()
        
    def start_key(self, attrs):
        print "start key"
        self.inkey = 1
		
    def end_key(self):
        self.inkey = 0
		
    def start_string(self, attrs):
        self.start_data(attrs)
    def end_string(self):
        self.end_data()
	
    def start_data(self, attrs):
        self.indata = 1	
    def end_data(self):
        self.indata = 0

    def unknown_starttag(self, tag, attrs):
        #strattrs = "".join([' %s="%s"' % (key, value) for key, value in attrs])
        #self.handle_data("<%(tag)s%(strattrs)s>" % locals())
        return None

    def unknown_endtag(self, tag):
        print "unk:"+tag
        #self.handle_data("</%(tag)s>" % locals())
        return None
    
    def do_false(self, tag):
        return None

    def do_true(self, tag):
        return None          
		
    def process_key_path(self, text):
        self.currentdata.path = text
	
    def process_key_data(self, text):
        self.currentdata.data.append(text)

    def process_key_string(self,text):
        self.process_key_data(text)	   
	
    def process_key_greylist(self,text):       
        #print "Inkey: " + str(self.inkey) + " key: " + str(self.currentkey)
        self.currentdata.path = text
        return None
	                            
    def process_key_version(self, text):
        # We don't need to do anything with the version key.
        return None

    def process_key_domain(self,text):
        self.currentdata.domain=text
        return None

    def handle_data(self, text):
        # called for each block of plain text, i.e. outside of any tag and
        # not containing any character or entity references
        # Store the original text verbatim.             
        if self.inkey == 1:
            self.currentkey = text.lower()
            #print "In key: %(text)s" % locals()
        elif self.indata == 1:
            print self.currentkey
            #print text
            try: 
                key_function = getattr(self,"process_key_%s" % self.currentkey )
                key_function(text)
            except AttributeError:
                #print "Warning: No function exists to handle key: %s.  It will be ignored." % self.currentkey
                pass

    def write(self):
        self.currentdata.write()
    def output(self):
        print "Path: %s \n" % self.currentdata.path
        print "Data: %s \n" % self.currentdata.decode()
    def getData(self):
        return self.currentdata



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
        self.phonenumbers.append(number)

class Addresses:
    def __init__(self,addressdb):
        self.numbers={}
        self.people={}
        self.readDB(addressdb)
        return
    def readDB(self,addressdb):
        conn=sqlite3.connect(addressdb)
        c=conn.cursor()
        c.execute("select ROWID,First,Middle,Last from ABPerson")
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
            
            person.setName(name)
            self.people[person.id]=person
            pass
        c.execute("select record_id,value from ABMultiValue where property=3")
        rows=fetchall_dict(c)
        for row in rows:
            self.people[row["record_id"]].addPhoneNumber(row["value"])
            self.numbers[row["value"]]=self.people[row["record_id"]]
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
    f=open(filename,"a")
    buf+="----\n"
    buf+=str(timestamp)+"\n"
    buf+=time.ctime(timestamp)+"\n"
    message_type = 'sms'
    if row['service'] == 'iMessage':
        message_type = 'iMessage'
        pass
    if flags==2 or row['date_read']:
        buf+="Received ("+message_type+"):\n"
        pass
    else:
        buf+="Sent ("+message_type+"):\n"
        pass
    buf+=text+"\n"
    f.write(buf.encode("utf-8"))
    f.close()

def madrid_ts_to_unix(ts):
    return calendar.timegm(time.strptime("2001-01-01 00:00","%Y-%m-%d %H:%M"))+ts

def message_sort_key(row):
    return row['date']

def processSMSDB(smsdir,addressdb,smsdb,lastTimeStamps):
    addresses=Addresses(addressdb)
    conn=sqlite3.connect(smsdb)
    c=conn.cursor()
    c.execute("select * from message order by date")
    rows=fetchall_dict(c)
    
    rows.sort(key=message_sort_key)
    for row in rows:
        numbers=[]
        c.execute("select chat_identifier from chat,chat_message_join where chat.rowid=chat_message_join.chat_id and chat_message_join.message_id="+str(row['rowid']))
        recipients=fetchall_dict(c)
        for recp in recipients:
            numbers.append(recp['chat_identifier'])
            pass
        for number in numbers:
            if len(number)==11 and number[0]=="1":
                # assume USA number
                number=number[1:4]+"-"+number[4:7]+"-"+number[7:11]
                pass
            elif len(number)==14 and number[0]=="(":
                # assume USA number (123) 456-7890
                number=number[1:4]+"-"+number[6:9]+"-"+number[10:14]
                pass
            elif len(number)==12 and number.startswith("+1"):
                # assume USA number +11234567890
                number=number[2:5]+"-"+number[5:8]+"-"+number[8:]
                pass
            person=None
            if addresses.numbers.has_key(number):
                person=addresses.numbers[number]
                pass

            if person!=None:
                filename=generateFilenameFromName(person.name)
            else:
                filename=generateFilenameFromName(number)
                pass

            filename=smsdir+"/"+filename+"-sms.txt"
            # store the timestamps in a dictionary and use it since we want to make sure we catch all the new messages
            # since the last run
            if lastTimeStamps.has_key(filename):
                timestamp=lastTimeStamps[filename]
            else:
                timestamp=getLastTimestamp(filename)
                lastTimeStamps[filename]=timestamp
                pass
            smstimestamp=int(madrid_ts_to_unix(row["date"]))
            if (smstimestamp>timestamp):
                text=row["text"]
                if text==None:
                    text=""
                    pass
                if (0):
                    c.execute("select * from msg_pieces where message_id=?",[row["rowid"]])
                    pieces_rows=fetchall_dict(c)
                    for prow in pieces_rows:
                        if prow["content_type"].startswith("text") or prow["content_type"].startswith("application/smil"):
                            if prow["data"]!=None:
                                text+=unicode(prow["data"],"utf-8","xmlcharrefreplace")+"\n"
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
    xmlparser.parse(StringIO.StringIO(text))
    return

def verifySMSDB(filename):
    conn=sqlite3.connect(filename)
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
    conn=sqlite3.connect(filename)
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

def main(argv):    
    try:
        opts, args = getopt.getopt(argv[1:], "",[])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
        
    if args.__len__() == 0:
        usage()
        sys.exit(2)
        
    converter = bplist_converter()

    directory=args[0]
    filenames=glob.glob(directory+"/*.mdinfo")

    datafilenames=[]
    try:
        file=open("datafiles.txt")
        filenames=[]
        for line in file.readlines():
            filenames.append(line.strip())
            pass
        file.close()
    except:
        pass
    
    smsdir="sms"

    smsdbs=[]
    addressdb=None
    filenames=[]
    for filename in filenames:
        print "Processing: " + filename
        #parser = plist_processor()
        if filename.endswith(".mdinfo"):
            plist_file = open(filename, 'r')
            plist_text = plist_file.read()
            if plist_text[0:6] == "bplist":
                plist_file.close()
                converter.decode_bplist(plist_name)
                plist_file = open(plist_name, 'r')
                plist_text = plist_file.read()
                pass

            xmlhandler=plist_XMLHandler()
            parseXML(xmlhandler,plist_text)
            
            data=xmlhandler.getData()
            if data==None:
                pass
            elif (data.path=="Library/SMS/sms.db" and data.domain=="HomeDomain"):
                datafilenames.append(filename)
                #print filename
                print data.path
                #print "domain="+str(data.domain)
                output_text=getDataFromInfo(filename)
                #output_text = base64.b64decode("".join(data.data))
                smsdb=smsdir+"/sms-"+str(len(smsdbs)+1)+".db"
                smsdbs.append(smsdb)
                output_file = open(smsdb, 'wb') 
                output_file.write(output_text)
                output_file.close()
                pass
            elif  (data.path=="Library/AddressBook/AddressBook.sqlitedb" and data.domain=="HomeDomain"):
                datafilenames.append(filename)
                print data.path
                #output_text = base64.b64decode("".join(data.data))
                output_text=getDataFromInfo(filename)
                addressdb=smsdir+"/addresses.db"
                output_file = open(addressdb, 'wb') 
                output_file.write(output_text)
                output_file.close()
                print addressdb
                pass
            #if smsdb!=None and addressdb!=None:
            #    break
            pass
        elif 0:
            # try to read raw file
            conn=sqlite3.connect(filename)
            c=conn.cursor();
            c.execute("select name from sqlite_master")
            rows=fetchall_dict(c)
            tables=[]
            for row in rows:
                tables.append(row["name"])
                pass
            if "ABPerson" in tables:
                addressdb=smsdir+"/addresses.db"
                os.system("cp -p "+filename+" "+addressdb)
                pass
            if (("message" in tables) and
                ("msg_group" in tables) and
                ("msg_pieces" in tables)):
                smsdb=smsdir+"/sms-"+str(len(smsdbs)+1)+".db"
                smsdbs.append(smsdb)
                os.system("cp -p "+filename+" "+smsdb)
            pass
        pass

    useManifest=0
    useSHA=1
    if useManifest or useSHA:
        if useManifest:
            filename=ManifestMBDB.get_filename_from_db(directory,"Library/SMS/sms.db")
            pass
        if useSHA:
            filename=hashlib.sha1("HomeDomain-"+"Library/SMS/sms.db").hexdigest()
            pass
        filename=directory+"/"+filename
        if os.path.exists(filename) and verifySMSDB(filename):
            print "Processing "+filename
            smsdb=smsdir+"/sms-"+str(len(smsdbs)+1)+".db"
            smsdbs.append(smsdb)
            os.system("cp -p "+filename+" "+smsdb)
            pass
        else:
            print "Couldn't find sms.db"
            sys.exit(1)
            pass
        if useManifest:
            filename=ManifestMBDB.get_filename_from_db(directory,"Library/AddressBook/AddressBook.sqlitedb")
        if useSHA:
            filename=hashlib.sha1("HomeDomain-"+"Library/AddressBook/AddressBook.sqlitedb").hexdigest()
            pass
        filename=directory+"/"+filename
        if os.path.exists(filename) and verifyAddressDB(filename):
            print "Processing "+filename
            addressdb=smsdir+"/addresses.db"
            os.system("cp -p "+filename+" "+addressdb)
            pass
        else:
            print "Couldn't find address.db"
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
