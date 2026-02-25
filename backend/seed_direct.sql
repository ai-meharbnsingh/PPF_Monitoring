INSERT INTO workshops (id, name)
VALUES (999, 'Direct Workshop')
ON CONFLICT (id) DO NOTHING;

INSERT INTO users (id, username, email, password_hash, role, is_active, login_attempt_count, is_temporary_password, workshop_id)
VALUES (999, 'direct_owner', 'owner@x.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'owner', true, 0, false, 999)
ON CONFLICT (id) DO NOTHING;

INSERT INTO pits (id, name, pit_number, workshop_id, description)
VALUES (999, 'Direct Pit', 99, 999, 'Test Pit')
ON CONFLICT (id) DO NOTHING;

INSERT INTO jobs (id, workshop_id, pit_id, work_type, status, customer_view_token, created_at, updated_at, currency)
VALUES (999, 999, 999, 'PPF', 'in_progress', 'GT3RSX', NOW(), NOW(), 'USD')
ON CONFLICT (id) DO UPDATE SET status = 'in_progress', customer_view_token = 'GT3RSX';
