#!/bin/bash

# Starte Backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Starte Frontend
cd ../frontend
npm start
