#!/bin/sh
gunicorn app:app --bind localhost:5000 --worker-class aiohttp.GunicornWebWorker
