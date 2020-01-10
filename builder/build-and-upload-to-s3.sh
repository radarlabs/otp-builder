#!/bin/bash

set -e
set -x

# python3 build.py

if [[ -z "$AWS_PATH" ]]; then
    echo "Must provide AWS_PATH in environment" 1>&2
    exit 1
fi

INDEX_VERSION=`ls -t graphs | grep -v default | head -n 1`
aws s3 cp --recursive graphs/$INDEX_VERSION $AWS_PATH

# write a sentinel to know the upload finished correctly
echo "" > /tmp/empty_file
aws s3 cp /tmp/empty_file $AWS_PATH/$INDEX_VERSION/_SUCCESS