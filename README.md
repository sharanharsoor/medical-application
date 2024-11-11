# Medical Research Assistant

A full-stack application that provides AI-powered analysis of medical research data, medical research trends,
clinical trials, and research trends.

## Features
- Daily updates of medical research trends
- Clinical trial analysis
- Research paper summaries
- Interactive query system for medical research questions
- Automated daily updates with scheduler

## Tech Stack
- Backend: FastAPI, MongoDB, LangChain, Google Gemini
- Frontend: React, React Bootstrap
- Deployment: Render.com

## Project Structure
- `backend/`: FastAPI backend with MongoDB integration
- `frontend/`: React frontend with Bootstrap UI

## Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
export GEMINI_API_KEY=your_gemini_api_key
export PUBMED_API_KEY=your_pubmed_api_key
```

### Frontend
```bash
cd frontend
npm install
```

## Running the Application

### Backend
```bash
cd backend
uvicorn src.api.main:app --reload
```

### Frontend
```bash
cd frontend/medical-research-ui/
npm start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000