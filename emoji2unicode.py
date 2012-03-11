#!/usr/bin/python

import sys
import StringIO
import xml.sax
import xml.sax.handler

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
                map={}
                map["name"]=attrs["name"]
                if attrs.has_key("unicode"):
                    try:
                        map["unicode"]=unichr(int(attrs["unicode"],16))
                    except:
                        try:
                            map["unicode"]=eval("u\"\\U"+str.rjust(str("%X"%int(attrs["unicode"],16)),8,"0")+"\"")
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
                        if encoding=='unicode':
                            try:
                                key=eval("u\"\\U"+str.rjust(str("%X"%int(key,16)),8,"0")+"\"")
                            except:
                                continue
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
        self.mappings=handler.mappings
        pass
    def translate(self,input):
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
            for encoding in ['softbank','unicode']:
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
    pass
