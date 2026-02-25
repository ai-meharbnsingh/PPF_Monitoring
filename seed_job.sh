#!/bin/bash
response=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=super_admin&password=super_admin_password_change_me")
TOKEN=$(echo "$response" | jq -r '.data.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo "Login failed: $response"
  exit 1
fi

W_ID=$(curl -s -X GET "http://localhost:8000/api/v1/workshops" -H "Authorization: Bearer $TOKEN" | jq -r '.[0].id')
if [ "$W_ID" == "null" ] || [ -z "$W_ID" ]; then
    W_ID=$(curl -s -X POST "http://localhost:8000/api/v1/workshops" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"name": "Demo Workshop"}' | jq -r .id)
fi

P_ID=$(curl -s -X POST "http://localhost:8000/api/v1/workshops/$W_ID/pits" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"name": "Live Streaming Bay", "pit_number": 1, "description": "Demo bay"}' | jq -r .id)
if [ "$P_ID" == "null" ] || [ -z "$P_ID" ]; then
    P_ID=$(curl -s -X GET "http://localhost:8000/api/v1/workshops/$W_ID/pits" -H "Authorization: Bearer $TOKEN" | jq -r '.[0].id')
fi

J_ID=$(curl -s -X POST "http://localhost:8000/api/v1/workshops/$W_ID/jobs" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "{\"pit_id\": $P_ID, \"work_type\": \"Full Body Stealth PPF\", \"car_model\": \"Porsche 911 GT3 RS\", \"car_plate\": \"M-PPF001\"}" | jq -r .id)

echo "Job created with ID: $J_ID"
curl -s -X POST "http://localhost:8000/api/v1/jobs/$J_ID/status" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"status": "in_progress", "notes": "Customer is waiting on tracking link."}' | jq .
