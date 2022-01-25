# What is this?
An extractor for PDF files which converts to:
* PNG files (one per page)
* Alto XML files (this is the native format of Tesseract)
* JSON files - a direct conversion of the Tesseract XML

# How does this work?
It uses some shell tools to do the hard lifting:
* ImageMagic for PDF to PNG conversion
* Tesseract OCR for PNG to Alto XML conversion
* Xsltpoc and a stylesheet for XML to JSON conversion

# How do I run this?
You can either install and configure dependencies on your machine, or you can use the -d flag to transparently pull and run a Docker image which has the prerequisites installed.