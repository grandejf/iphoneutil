#!/usr/bin/python

import sys
import StringIO
import xml.sax
import xml.sax.handler
import re

class emoji_XMLHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.encodings=["google","docomo","softbank","kddi","unicode"]
        self.mappings={}
        for encoding in self.encodings:
            self.mappings[encoding]={}
            pass
        pass
    def startElement(self,name,attrs):
        if name=='e':
            for encoding in self.encodings:
                hash={}
                hash["name"]=attrs["name"]
                if attrs.has_key("unicode"):
                    try:
                        mappper["unicode"]=unichr(int(attrs["unicode"],16))
                    except:
                        try:
                            hash["unicode"]=eval("u\"\\U"+str.rjust(str("%X"%int(attrs["unicode"],16)),8,"0")+"\"")
                        except:
                            hash["unicode"]=None
                    pass
                else:
                    hash["unicode"]=None
                    pass
                if attrs.has_key(encoding):
                    key=attrs[encoding]
                    if key[0]=='>':
                        # combo emoji... just skip
                        continue
                    #print hash,attrs[encoding]
                    if len(key)<=4:
                        key=unichr(int(key,16))
                        pass
                    else:
                        if encoding=='unicode':
                            try:
                                key=eval("u\"\\U"+str.rjust(str("%X"%int(key,16)),8,"0")+"\"")
                            except:
                                continue
                        else:
                            key=eval("u\"\\U"+str.rjust(str(key),8,"0")+"\"")
                        pass
                    self.mappings[encoding][key]=hash
                    pass
                pass
            pass
        pass
    pass

def parseXML(xmlhandler,text):
    xmlparser=xml.sax.make_parser()
    xmlparser.setFeature(xml.sax.handler.feature_namespaces,0)
    xmlparser.setFeature(xml.sax.handler.feature_external_ges,0)
    xmlparser.setFeature(xml.sax.handler.feature_external_pes,0)
    xmlparser.setContentHandler(xmlhandler)
    xmlparser.parse(StringIO.StringIO(text))
    return


class Emoji:
    def __init__(self):
        file=open("emoji/emoji4unicode.xml","r")
        emojixml=file.read()
        file.close()
        handler=emoji_XMLHandler()
        parseXML(handler,emojixml)
        self.mappings=handler.mappings
        self.mappings["e"]={}
        file=open("emoji/emoji-test.txt","r")
        while 1:
            line=file.readline()
            if line=="":
                break
            line=line.strip()
            if line=="" or line[0]=="#":
                continue
            m = re.match('(.+?) +; (.*?) +# ([^\x20-\x7E]+) ?([a-zA-Z0-9].+)',line)
            if m:
                codes=m.group(1).split(' ')
                key = u"".join(map(lambda x: eval("u\"\\U"+x.zfill(8)+"\""), codes))                
                emoji=m.group(3)
                desc=m.group(4)
                hash={}
                hash["name"]=desc
                hash["unicode"]=emoji
                self.mappings["e"][key]=hash
                pass
            pass
        # create regex
        arr = []
        for key in sorted(self.mappings["e"],key=len,reverse=True):
            arr.append(key)
            pass
        self.emojiPattern="("+("|".join(arr))+")"
        self.emojiRE = re.compile(self.emojiPattern,re.UNICODE)
        pass
    def translate(self,input):

        def emojiReplace(m):
            s = m.group(1)
            desc = None
            if self.mappings["e"][s]!=None:
                desc = self.mappings["e"][s]["name"]
            if desc!=None:
                s=s+ " [ALT="+desc+"]"
            return s
        input = self.emojiRE.sub(emojiReplace,input)
        
        output=[]
        import codecs
        bytestr, _ = codecs.getencoder("utf_32_be")(input)
        for i in xrange(0,len(bytestr),4):
            code = 0
            for b in bytestr[i:i + 4]:
                code = (code << 8) + ord(b)
                pass
            code = "%X" % code
            char=eval("u\"\\U"+str.rjust(str(code),8,"0")+"\"")
            foundIt=0
            for encoding in ['softbank']:
                map=self.mappings[encoding]
                if map.has_key(char):
                    if map[char]["unicode"]!=None:
                        output.append(map[char]["unicode"])
                        output.append(" [ALT="+map[char]["name"]+"]")
                    else:
                        output.append(" ["+map[char]["name"]+"]")
                        pass
                    foundIt=1
                    break
                pass
            if not foundIt:
                if (char== u'\ufffc'):
                    char=''
                if (char==u'\xa0'):
                    char=' '
                    pass
                output.append(char)
                pass
            pass
        return "".join(output)

if __name__=="__main__":
    emoji=Emoji()
    print emoji.translate("this is a test")
    print emoji.translate(u"unicode test\ue159")
    print emoji.translate(u"unicode test hand\U0001F596")
    print emoji.translate(u"unicode test italy flag \U0001F1EE\U0001F1F9")
    pass
