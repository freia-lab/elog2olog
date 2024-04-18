#!/bin/bash

find $1 -name "20*xml" -exec python migrateElog2Olog.py {} $2 \;

