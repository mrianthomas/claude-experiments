-- Mince Pie Monitor — Supabase schema
-- Run this in the Supabase SQL editor

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS sightings (
    id              UUID          DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at      TIMESTAMPTZ   DEFAULT NOW(),
    post_id         TEXT          UNIQUE,                 -- prevents duplicate ingestion
    post_url        TEXT,
    post_text       TEXT          NOT NULL,
    platform        TEXT          NOT NULL DEFAULT 'bluesky',
    author_handle   TEXT,
    postcode        TEXT,
    retailer        TEXT,
    lat             DOUBLE PRECISION,
    lng             DOUBLE PRECISION,
    geom            GEOGRAPHY(POINT, 4326),               -- auto-populated by trigger
    is_retail_sighting BOOLEAN    DEFAULT TRUE,
    confidence      REAL,
    raw_data        JSONB
);

-- Auto-populate geom from lat/lng on insert or update
CREATE OR REPLACE FUNCTION sightings_set_geom()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.lat IS NOT NULL AND NEW.lng IS NOT NULL THEN
        NEW.geom = ST_SetSRID(ST_MakePoint(NEW.lng, NEW.lat), 4326)::geography;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sightings_set_geom
    BEFORE INSERT OR UPDATE ON sightings
    FOR EACH ROW EXECUTE FUNCTION sightings_set_geom();

-- Indexes
CREATE INDEX IF NOT EXISTS idx_sightings_geom       ON sightings USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_sightings_created_at ON sightings(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_sightings_retailer   ON sightings(retailer);

-- Row Level Security
ALTER TABLE sightings ENABLE ROW LEVEL SECURITY;

-- Public reads (for the map)
CREATE POLICY "public_read" ON sightings
    FOR SELECT USING (true);

-- Only the service-role key (backend) can write
CREATE POLICY "service_write" ON sightings
    FOR INSERT WITH CHECK (auth.role() = 'service_role');
