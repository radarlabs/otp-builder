#!/bin/sh

../shared/download_otp.py

echo 'http://localhost:8080'
OTP_JAR=`../shared/download_otp.py name`
java -Xmx2G -jar $OTP_JAR --router default --graphs graphs --server
