# Medical Research Assistant

An AI-powered medical research analysis tool that provides daily updates on medical research trends, clinical trials, and research papers.

## Features
- Daily automated updates of medical research trends
- Clinical trial analysis
- Research paper summaries
- Interactive query system
- MongoDB integration for data persistence
- Scheduled updates with automated reminders

## Tech Stack
- Backend: FastAPI, MongoDB, LangChain, Google Gemini
- Frontend: React, React Bootstrap
- Database: MongoDB Atlas
- Deployment: Render.com

## Local Development

### Prerequisites
- Python 3.9+
- Node.js 16+
- MongoDB Atlas account
- Google Gemini API key
- PubMed API key

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Then edit with your API keys
```

Start the backend:
```bash
uvicorn src.api.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env  # Then edit with your API URL
```

Start the frontend:
```bash
npm start
```

## Deployment
This project is configured for deployment on Render.com.

1. Fork this repository
2. Create a new Render account
3. Connect your GitHub repository
4. Add environment variables in Render dashboard:
   - GEMINI_API_KEY
   - PUBMED_API_KEY
   - MONGODB_URI

## API Documentation
When running locally, visit: http://localhost:8000/docs

## Environment Variables

### Backend (.env)
```
GEMINI_API_KEY=your_key
PUBMED_API_KEY=your_key
MONGODB_URI=your_mongodb_uri
```

### Frontend (.env)
```
REACT_APP_API_URL=http://localhost:8000
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first.

## License
MIT
