# Mince Pie Monitor 🥧

Tracks early mince pie sightings across the UK via BlueSky and manual submissions.
Shows them on a live map, updated in real time.

---

## How it works

1. **BlueSky poller** — searches for "mince pie" mentions every 5 minutes
2. **Claude classifier** — filters posts to only retail sightings (not recipes, eating at home, etc.)
3. **Geocoder** — extracts UK postcodes and converts them to lat/lng via [postcodes.io](https://postcodes.io)
4. **Supabase** — stores sightings; powers realtime map updates
5. **Leaflet map** — clustered pins, coloured by retailer, with popups

---

## Prerequisites

- Python 3.11+
- A [Supabase](https://supabase.com) account (free tier is fine)
- An [Anthropic API key](https://console.anthropic.com)

---

## Setup

### 1. Supabase

1. Create a new Supabase project
2. Open the **SQL Editor** and run [`supabase/schema.sql`](supabase/schema.sql)
3. In **Project Settings → API**, copy your **Project URL** and **service_role** key

### 2. Backend

```bash
cd backend
cp ../.env.example .env
# Edit .env with your keys
pip install -r requirements.txt
uvicorn main:app --reload
```

The server runs at `http://localhost:8000`.  
It begins polling BlueSky immediately on startup.

### 3. Frontend

Edit the `CONFIG` block at the top of `frontend/app.js`:

```js
const CONFIG = {
  API_BASE:          "http://localhost:8000",          // your backend
  SUPABASE_URL:      "https://YOUR_PROJECT.supabase.co",
  SUPABASE_ANON_KEY: "YOUR_ANON_KEY",                  // public anon key is safe here
};
```

Then open `frontend/index.html` in a browser, or serve it with any static host.

---

## Deployment

### Backend — Railway

1. Create a new Railway project from this repo
2. Set the root directory to `backend/`
3. Add the environment variables from `.env`
4. Railway will run `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Frontend — GitHub Pages

Push the repo; enable GitHub Pages pointing at the `frontend/` folder.  
Update `API_BASE` in `app.js` to your Railway URL.

---

## Structured sightings (the #uksnow mechanic)

Encourage people to post on BlueSky with:

```
Just spotted mince pies at Tesco SW1A 1AA — it's only August! 🥧 #mincepie
```

The monitor will automatically:
- Classify it as a retail sighting
- Extract `Tesco` and `SW1A 1AA`
- Geocode the postcode and place a pin on the map

---

## Project structure

```
├── backend/
│   ├── main.py          FastAPI app + polling loop
│   ├── bluesky.py       BlueSky search
│   ├── classifier.py    Claude (Haiku) classification
│   ├── geocoder.py      Postcode + retailer extraction, postcodes.io
│   ├── processor.py     Orchestrates classify → geocode → store
│   ├── database.py      Supabase client
│   └── requirements.txt
├── frontend/
│   ├── index.html       Map UI
│   ├── app.js           Leaflet map + Supabase realtime + submission form
│   └── styles.css
├── supabase/
│   └── schema.sql       Table, trigger, indexes, RLS
└── .env.example
```
