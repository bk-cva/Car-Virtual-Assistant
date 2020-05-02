#!/bin/sh
gunicorn \
    --workers 1 \
    --threads 1 \
    --timeout 120 \
    src.app:app -b 0.0.0.0:5000
