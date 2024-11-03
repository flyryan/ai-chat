#!/bin/bash
gunicorn -c backend/gunicorn.conf.py backend/main:app