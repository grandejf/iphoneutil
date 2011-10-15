#!/usr/bin/python

import sys
import StringIO
import xml.sax
import xml.sax.handler

class emoji_XMLHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.encodings=["google","docomo","softbank","kddi"]
        self.mappings={}
        for encoding in self.encodings:
            self.mappings[encoding]={}
            pass
        pass
    def startElement(self,name,attrs):
        if name=='e':
            for encoding in self.encodings:
                map={}
                map["name"]=attrs["name"]
                if attrs.has_key("unicode"):
                    try:
                        map["unicode"]=unichr(int(attrs["unicode"],16))
                    except:
                        map["unicode"]=None
                    pass
                else:
                    map["unicode"]=None
                    pass
                if attrs.has_key(encoding):
                    key=attrs[encoding]
                    if key[0]=='>':
                        # combo emoji... just skip
                        continue
                    #print map,attrs[encoding]
                    if len(key)<=4:
                        key=unichr(int(key,16))
                        pass
                    else:
                        key=eval("u\"\\U"+str.rjust(str(key),8,"0")+"\"")
                        pass
                    self.mappings[encoding][key]=map
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
        self.mappings=handler.mappings["softbank"]
        pass
    def translate(self,input):
        output=[]
        for i in xrange(len(input)):
            char=input[i]
            if self.mappings.has_key(char):
                if self.mappings[char]["unicode"]!=None:
                    output.append(self.mappings[char]["unicode"])
                    output.append("[ALT="+self.mappings[char]["name"]+"]")
                else:
                    output.append("["+self.mappings[char]["name"]+"]")
                    pass
                pass
            else:
                output.append(char)
                pass
            pass
        return "".join(output)





if __name__=="__main__":
    emoji=Emoji()
    print emoji.translate("this is a test")
    print emoji.translate(u"unicode test\ue159")
    pass
