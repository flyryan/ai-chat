#!/bin/bash
gunicorn -c gunicorn.conf.py main:app