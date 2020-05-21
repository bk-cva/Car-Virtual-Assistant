#!/bin/sh
gunicorn \
    -k flask_sockets.worker \
    --workers 1 \
    --threads 1 \
    --timeout 120 \
    src.cva_app:app -b 0.0.0.0:5000
