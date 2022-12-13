#!/bin/bash

#
# When run with the -d flag, this script is a front-end for itself within a docker container
#

function err_exit {
    echo  "[FATAL] "$*
    exit 1
}

if [[ ! -e $(which realpath)  ]]; then
    realpath() (
        OURPWD=$PWD
        cd "$(dirname "$1")"
        LINK=$(readlink "$(basename "$1")")
        while [ "$LINK" ]; do
            cd "$(dirname "$LINK")"
            LINK=$(readlink "$(basename "$1")")
        done
        REALPATH="$PWD/$(basename "$1")"
        cd "$OURPWD"
        echo "$REALPATH"
    )
fi

XSLT=to-json.xslt
NUM_PROCS=4
DOCKER_IMG_REF='robinharvey/pdftxt'

HELP="$(cat <<EOF
Extract text in various formats from a PDF file.
When run with the -d flag, this script is a front-end for itself within a docker container

Usage: $0 <options>:
    -h              show this message
    -d              run as a front-end to a docker container
    -i  <pdf file>  the source pdf file
    -o  <directory> the directory for outputs
EOF
)"

opts="hdi:o:"
PDF=
OUT_DIR=
RUN_IN_CONTAINER=0
while getopts $opts opt; do
    case $opt in
        h)
            echo "$HELP"
            exit 4
            ;;
        i)  PDF=$OPTARG ;;
        o)  OUT_DIR=$OPTARG ;;
        d)  RUN_IN_CONTAINER=1 ;;
        *)
            echo "Unknown arg $opt"
            echo "$HELP"
            exit 7
    esac
done

[[ -f "$PDF" ]] || err_exit "missing input PDF file '$PDF'"

[[ -d "$OUT_DIR" ]] || err_exit "missing output directory $OUT_DIR"

function metal_run {

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
}

function docker_run {
    OUT_DIR=$(realpath "${OUT_DIR}")
    PDF=$(realpath "${PDF}")
    docker pull $DOCKER_IMG_REF
    docker run -ti \
        --mount type=bind,source=${OUT_DIR},destination=/output \
        -v ${PDF}:/input.pdf \
        $DOCKER_IMG_REF -i /input.pdf -o /output
}

if [[ $RUN_IN_CONTAINER == 0 ]]; then
    metal_run
else
    docker_run
fi