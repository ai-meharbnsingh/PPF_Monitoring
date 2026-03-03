-- Migration: Add cameras table for IP camera management
-- Created: 2026-03-03

-- Create cameras table
CREATE TABLE IF NOT EXISTS cameras (
    id SERIAL PRIMARY KEY,
    workshop_id INTEGER NOT NULL REFERENCES workshops(id) ON DELETE CASCADE,
    pit_id INTEGER UNIQUE REFERENCES pits(id) ON DELETE SET NULL,
    
    -- Camera identification
    device_id VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Camera type and model
    camera_type VARCHAR(50) NOT NULL DEFAULT 'ip_camera',
    model VARCHAR(100),
    manufacturer VARCHAR(100),
    firmware_version VARCHAR(50),
    
    -- Network configuration
    ip_address VARCHAR(50) NOT NULL,
    hostname VARCHAR(100),
    mac_address VARCHAR(17),
    port INTEGER NOT NULL DEFAULT 554,
    
    -- Stream URLs and config (stored as JSON)
    stream_urls JSONB,
    mediamtx_config JSONB,
    
    -- Credentials (consider encrypting in production)
    username VARCHAR(50),
    password VARCHAR(100),
    
    -- Capabilities
    resolutions JSONB,
    protocols JSONB,
    has_audio BOOLEAN NOT NULL DEFAULT FALSE,
    has_ptz BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    is_online BOOLEAN NOT NULL DEFAULT FALSE,
    is_assigned BOOLEAN NOT NULL DEFAULT FALSE,
    last_seen TIMESTAMP WITH TIME ZONE,
    
    -- Discovery info
    discovered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    discovered_via VARCHAR(20) NOT NULL DEFAULT 'manual',
    
    -- Additional config
    config JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_cameras_workshop_id ON cameras(workshop_id);
CREATE INDEX IF NOT EXISTS idx_cameras_pit_id ON cameras(pit_id);
CREATE INDEX IF NOT EXISTS idx_cameras_device_id ON cameras(device_id);
CREATE INDEX IF NOT EXISTS idx_cameras_status ON cameras(status);
CREATE INDEX IF NOT EXISTS idx_cameras_is_online ON cameras(is_online);
CREATE INDEX IF NOT EXISTS idx_cameras_is_assigned ON cameras(is_assigned);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_cameras_updated_at ON cameras;
CREATE TRIGGER update_cameras_updated_at
    BEFORE UPDATE ON cameras
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Update pit model to reference camera (optional, for backward compatibility)
-- Note: The camera_id column in pits table is handled by the ORM relationship
