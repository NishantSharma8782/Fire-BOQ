# Fire BOQ Platform — README

## AI-Powered Fire Safety BOQ Generation Platform

A full-stack, single-user platform for generating Fire Bill of Quantities from building drawings using Google Gemini Vision AI.

---

## Quick Start

### Prerequisites
- Python 3.11+ installed
- Node.js 18+ installed
- MongoDB running locally on port 27017
- Google Gemini API Key

### Step 1 — Configure API Key

Edit `backend\.env` and add your Gemini API key:
```
GEMINI_API_KEY=your_actual_gemini_api_key_here
MONGODB_URL=mongodb://localhost:27017
```

### Step 2 — Start Backend

Double-click `start-backend.bat` or run:
```
cd backend
venv\Scripts\uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 3 — Start Frontend

Double-click `start-frontend.bat` or run:
```
cd frontend
npm run dev
```

### Step 4 — Open App

Visit: **http://localhost:3000**

API Docs: **http://localhost:8000/docs**

---

## Project Structure

```
AI-Fire-BOQ/
├── backend/                    FastAPI Python backend
│   ├── main.py                 App entry point
│   ├── .env                    Environment config
│   ├── requirements.txt        Python dependencies
│   ├── venv/                   Python virtual environment
│   ├── uploads/                Uploaded drawings stored here
│   └── app/
│       ├── config.py           Settings loader
│       ├── db/database.py      MongoDB connection
│       ├── models/             Pydantic schemas
│       ├── routers/            API route handlers
│       └── services/           Business logic
│           ├── gemini_service.py    Gemini Vision AI
│           ├── boq_engine.py        BOQ calculations
│           ├── layout_engine.py     Layout coordinates
│           └── export_service.py    PDF/Excel export
├── frontend/                   Next.js 14 frontend
│   ├── app/                    App Router pages
│   ├── components/             React components
│   ├── lib/                    Types, API client, utils
│   └── .env.local              Frontend env
├── start-backend.bat           Backend startup script
└── start-frontend.bat          Frontend startup script
```

---

## User Flow

1. **Create Project** → Enter project name, client, building type, hazard category
2. **Upload Drawing** → Drag & drop floor plan (PDF, PNG, JPG)
3. **AI Analysis** → Click "Analyze Drawing" → Gemini Vision extracts building data
4. **Layout** → Auto-generated fire equipment layout on interactive canvas
5. **Generate BOQ** → Click "Generate BOQ" → Full bill of quantities
6. **AI Assistant** → Ask questions about calculations, standards, recommendations
7. **Export** → Download PDF, Excel, or CSV reports

---

## Fire Standards Used

- NBC 2016 Part 4 — Fire & Life Safety
- IS 2189:2008 — Fire Detection & Alarm Systems
- IS 15105:2002 — Fire Sprinkler Systems
- IS 3844:1989 — Fire Hydrant Systems
- IS 2190:2010 — Fire Extinguishers

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| UI Components | Shadcn UI, Lucide Icons |
| State Management | React Query (TanStack) |
| Canvas | Konva.js / react-konva |
| Backend | FastAPI (Python) |
| Database | MongoDB (async with Motor) |
| AI | Google Gemini 2.0 Flash |
| PDF Export | ReportLab |
| Excel Export | openpyxl |
