# backend server

cd backend
python -m uvicorn app.main_with_db:app --host 127.0.0.1 --port 8002 --reload

# frontend

npm run dev
