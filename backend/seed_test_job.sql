INSERT INTO users (id, email, username, first_name, last_name, password_hash, role, is_active)
VALUES (999, 'demo_owner@example.com', 'demo_owner', 'Demo', 'Owner', 'ignored', 'owner', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO workshops (id, name, owner_id)
VALUES (999, 'Demo Workshop', 999)
ON CONFLICT (id) DO NOTHING;

UPDATE users SET workshop_id = 999 WHERE id = 999;

INSERT INTO pits (id, name, pit_number, workshop_id, description, is_active)
VALUES (999, 'Demo Bay', 99, 999, 'Live stream demo bay', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO users (id, email, username, first_name, last_name, password_hash, role, is_active)
VALUES (1000, 'demo_customer@example.com', 'demo_customer', 'Demo', 'Customer', 'ignored', 'customer', true)
ON CONFLICT (id) DO NOTHING;

INSERT INTO jobs (
    id, customer_user_id, pit_id, workshop_id,
    car_model, car_plate, car_color, car_year,
    work_type, work_description,
    status, customer_view_token,
    estimated_duration_minutes,
    scheduled_start_time,
    created_at, updated_at,
    currency
) VALUES (
    999, 1000, 999, 999,
    'Porsche 911 GT3 RS', 'M-PPF001', 'Guards Red', 2024,
    'Full Body Stealth PPF', 'Applying Xpel stealth to full exterior. Customer waiting on updates.',
    'in_progress', 'GT3RSX',
    360,
    NOW() - INTERVAL '2 hours',
    NOW(), NOW(), 'INR'
) ON CONFLICT (id) DO UPDATE SET status = 'in_progress', customer_view_token = 'GT3RSX';
