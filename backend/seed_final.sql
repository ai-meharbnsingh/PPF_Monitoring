-- Create the Workshop
INSERT INTO workshops (id, name, slug, total_pits, is_active, created_at, updated_at) 
VALUES (999, 'Test Tracking Workshop', 'test-workshop-999', 1, true, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- Create an owner user
INSERT INTO users (id, workshop_id, username, email, password_hash, role, is_active, login_attempt_count, is_temporary_password, created_at, updated_at) 
VALUES (999, 999, 'test_tracker', 'tracker@ppf.local', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'owner', true, 0, false, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- Create a pit
INSERT INTO pits (id, workshop_id, name, pit_number, description, status, camera_is_online, created_at, updated_at) 
VALUES (999, 999, 'Tracking Pit', 99, 'For tracking demo', 'active', false, NOW(), NOW())
ON CONFLICT (id) DO NOTHING;

-- Create the trackable job WITH an explicit expiration
INSERT INTO jobs (id, workshop_id, pit_id, work_type, status, car_model, car_plate, customer_view_token, customer_view_expires_at, scheduled_start_time, actual_start_time, estimated_duration_minutes, created_at, updated_at, currency) 
VALUES (999, 999, 999, 'PPF', 'in_progress', 'Porsche 911 GT3 RS', 'FST-888', 'GT3RSX', NOW() + INTERVAL '30 days', NOW() - INTERVAL '2 hours', NOW() - INTERVAL '1 hour', 480, NOW(), NOW(), 'USD')
ON CONFLICT (id) DO UPDATE SET 
    status = 'in_progress',
    customer_view_token = 'GT3RSX',
    customer_view_expires_at = NOW() + INTERVAL '30 days';
