import requests

def main():
    base_url = "http://localhost:8000/api/v1"

    print("1. Login...")
    login_data = {
        "username": "super_admin",
        "password": "super_admin_password_change_me"
    }
    resp = requests.post(f"{base_url}/auth/login", json=login_data)
    if resp.status_code != 200:
        print("Login failed:", resp.text)
        return
    token = resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    print("2. Get Workshop...")
    resp = requests.get(f"{base_url}/workshops", headers=headers)
    if not resp.json():
        resp = requests.post(f"{base_url}/workshops", headers=headers, json={"name": "Demo Workshop"})
        workshop_id = resp.json()
    else:
        workshop_id = resp.json()[0]["id"]
    print(f"Workshop ID: {workshop_id}")

    print("3. Get Pit...")
    resp = requests.get(f"{base_url}/workshops/{workshop_id}/pits", headers=headers)
    if not resp.json():
        resp = requests.post(f"{base_url}/workshops/{workshop_id}/pits", headers=headers, json={"name": "Bay 1", "pit_number": 1})
        pit_id = resp.json()["id"]
    else:
        pit_id = resp.json()[0]["id"]
    print(f"Pit ID: {pit_id}")

    print("4. Get Customer...")
    resp = requests.get(f"{base_url}/users", headers=headers)
    users = resp.json()
    cust_id = None
    for u in users:
        if u["role"] == "customer":
            cust_id = u["id"]
            break
            
    if not cust_id:
        user_data = {
            "username": "demo_customer",
            "email": "demo_customer@test.com",
            "password": "temp_password",
            "role": "customer",
            "first_name": "Demo",
            "workshop_id": workshop_id
        }
        resp = requests.post(f"{base_url}/users", headers=headers, json=user_data)
        if resp.status_code in [200, 201]:
           cust_id = resp.json()["id"]
        else:
           print("Failed to create customer:", resp.text)

    print(f"Customer ID: {cust_id}")

    print("5. Create Job...")
    job_data = {
        "pit_id": pit_id,
        "customer_user_id": cust_id,
        "work_type": "Full Body Stealth PPF",
        "car_model": "Porsche 911 GT3 RS",
        "car_plate": "M-PPF001"
    }
    resp = requests.post(f"{base_url}/workshops/{workshop_id}/jobs", headers=headers, json=job_data)
    if resp.status_code not in [200, 201]:
        print("Failed to create job:")
        print(f"Status Code: {resp.status_code}")
        print(f"Response: {resp.text}")
        return
    job_id = resp.json()["id"]
    print(f"Job created! ID: {job_id}")

    print("6. Update status to generate token...")
    resp = requests.post(f"{base_url}/jobs/{job_id}/status", headers=headers, json={"status": "in_progress", "notes": ""})
    if resp.status_code == 200:
        print("Success! Created Tracking Token:")
        print(resp.json())
    else:
        print("Failed to update status: ", resp.text)

if __name__ == "__main__":
    main()
