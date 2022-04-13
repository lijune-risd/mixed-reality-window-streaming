#!/bin/sh
gunicorn app:app --bind 0.0.0.0:5000 --worker-class aiohttp.GunicornWebWorker
