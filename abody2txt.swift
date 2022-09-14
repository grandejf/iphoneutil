import Foundation
let filename=CommandLine.arguments[1]

getAttributedBody(filename);

func getAttributedBody(_ filename:String) {
  var possibleObject:NSMutableAttributedString
  if let data = NSData(contentsOfFile: filename) {
    possibleObject = NSUnarchiver.unarchiveObject(with:data as Data) as! NSMutableAttributedString;
    print(possibleObject.string)
  }
}


