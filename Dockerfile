from ubuntu:latest

RUN apt-get update
RUN apt-get -y install imagemagick tesseract-ocr xsltproc

COPY run.sh /run.sh
COPY to-json.xslt /to-json.xslt
RUN chmod +x /run.sh

# Tweak security policy to allow ImageMagick to open PDFs
RUN sed -i 's~^</policymap>$~<policy domain="coder" rights="read | write" pattern="PDF" />\n</policymap>~' /etc/ImageMagick-6/policy.xml

ENTRYPOINT ["/run.sh"]