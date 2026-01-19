CREATE TABLE IF NOT EXISTS client_satellite_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    codice_cliente INTEGER REFERENCES clienti(codice_cliente) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    vlm_analysis JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(codice_cliente)
);

-- Enable RLS (Optional but recommended)
ALTER TABLE client_satellite_images ENABLE ROW LEVEL SECURITY;

-- Create policy to allow read access for authenticated users (or public if needed)
CREATE POLICY "Enable read access for all users" ON client_satellite_images
    FOR SELECT USING (true);

-- Create policy to allow full access for service role
-- Note: Service role always bypasses RLS.
