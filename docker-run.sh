#!/bin/bash

function err_exit {
    echo  "[FATAL] "$*
    exit 1
}

XSLT=to-json.xslt
NUM_PROCS=4

HELP="$(cat <<EOF
Usage: $0 <options>:
    -h              show this message
    -i  <pdf file>  the source pdf file
    -j  <directory> the directory for outputs
EOF
)"

opts="hi:o:"
PDF=
OUT_DIR=
while getopts $opts opt; do
    case $opt in
        h)
            echo "$HELP"
            exit 4
            ;;
        i)  PDF=$OPTARG ;;
        o)  OUT_DIR=$OPTARG ;;
        *)
            echo "Unknown arg $opt"
            echo "$HELP"
            exit 7
    esac
done

[[ -f "$PDF" ]] || err_exit "missing input PDF file '$PDF'"

[[ -d "$OUT_DIR" ]] || err_exit "missing output directory $OUT_DIR"

echo ">>> First extract pages from the pdf in to images ready for tesseract using imagemagick"
convert         \
   -verbose     \
   -density 300 \
   $PDF         \
    ${OUT_DIR}/page-%d.png
ex=$?
[[ $ex == 0 ]] || err_exit "Imagemagick convert failed with exit code $ex"

echo ">>> Next, use tesseract to extract Alto XML from pages using OCR"
for page in ${OUT_DIR}/page-*.png; do
    echo tesseract "$page" ${OUT_DIR}/$(basename ${page%.png}) alto
done | xargs -P $NUM_PROCS -I {} /bin/bash -c ' {}'

check=(ls -1 ${OUT_DIR}/page-*.alto)
[[ -n "$CHECK" ]] && err_exit "don't seem to have any alto files from tesseract"

echo ">>> Finally, use xsltproc to map the alto XML to json"
for page in ${OUT_DIR}/page-*.xml; do
    echo xsltproc -o ${OUT_DIR}/$(basename ${page%.xml}.json) $XSLT $page
done | xargs -P $NUM_PROCS -I {} /bin/bash -c ' {}'

echo ">>> You have" $(ls -1 ${OUT_DIR}/page-*.png | wc -l) "png files," \
    $(ls -1 ${OUT_DIR}/page-*.xml | wc -l) "alto xml files, and" \
    $(ls -1 ${OUT_DIR}/page-*.json | wc -l) "json files"