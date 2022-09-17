import Foundation
let filename=CommandLine.arguments[1]

getAttributedBody(filename);

func getAttributedBody(_ filename:String) {
  var possibleObject:NSAttributedString
  if let data = NSData(contentsOfFile: filename) {
    possibleObject = NSUnarchiver.unarchiveObject(with:data as Data) as! NSAttributedString;
    print(possibleObject.string)
  }
}


