import Foundation

import func Darwin.fputs
import var Darwin.stderr


struct StderrOutputStream: TextOutputStream {
  mutating func write(_ string: String) {
    fputs(string, stderr)
  }
}
var stdErr = StderrOutputStream()

let filename=CommandLine.arguments[1]

getAttributedBody(filename);

func getAttributedBody(_ filename:String) {
  var possibleObject:NSAttributedString
  if let data = NSData(contentsOfFile: filename) {
    possibleObject = NSUnarchiver.unarchiveObject(with:data as Data) as! NSAttributedString;
    // print(possibleObject, to: &stdErr)
    // print(possibleObject.string, to: &stdErr)
    
    let text = possibleObject.string
    var outtext = ""
    
    possibleObject.enumerateAttributes(in: NSRange(0..<possibleObject.length)) {
      dict, range, stop in
      let srange = Range(range, in:text)
      var stext = text[srange as! Range]
      if (false) {
        for (key, value) in dict {
          print(key.rawValue, to: &stdErr)
          print(value,to: &stdErr)
        }
      }
      if (dict[NSAttributedString.Key("__kIMEmojiImageAttributeName")] != nil) {
        let guid = dict[NSAttributedString.Key("__kIMFileTransferGUIDAttributeName")]
        if (guid != nil) {
          stext = "[emoji_guid="+(guid as! String)+"]"
        }
      }
      outtext += stext     
    }
    print(outtext)
  }
}



