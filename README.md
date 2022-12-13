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
The wrapper script can either run the local commands using packages you installed on your machine, or act as a front-end to using a Docker image which has all the required packages pre-installed.
```bash
./run.sh -h
```