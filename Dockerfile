from ubuntu:latest

RUN apt-get update
RUN apt-get -y install imagemagick tesseract-ocr xsltproc

COPY docker-run.sh /docker-run.sh
COPY to-json.xslt /to-json.xslt
RUN chmod +x /docker-run.sh

# Tweak security policy to allow ImageMagick to open PDFs
RUN sed -i 's~^</policymap>$~<policy domain="coder" rights="read | write" pattern="PDF" />\n</policymap>~' /etc/ImageMagick-6/policy.xml

ENTRYPOINT ["/docker-run.sh"]