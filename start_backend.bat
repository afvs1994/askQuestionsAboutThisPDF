@echo off
cd /d c:\Users\afvs1\askQuestionsAboutThisPDF\backend
venv\Scripts\python -m uvicorn app.main:app --reload --port 8000

