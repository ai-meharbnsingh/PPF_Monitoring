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

    print("2. Get or create Workshop...")
    resp = requests.post(f"{base_url}/workshops", headers=headers, json={"name": "Demo Workshop"})
    if resp.status_code in [200, 201]:
        workshop_id = resp.json()
    else:
        resp = requests.get(f"{base_url}/workshops", headers=headers)
        if hasattr(resp.json(), '__iter__') and len(resp.json()) > 0:
            workshop_id = resp.json()[0]["id"]
        else:
            print("Failed to get workshop:", resp.text)
            return

    print("3. Get or create Pit...")
    resp = requests.post(f"{base_url}/workshops/{workshop_id}/pits", headers=headers, json={"name": "Bay 1", "pit_number": 1})
    if resp.status_code in [200, 201]:
        pit_id = resp.json()["id"]
    else:
        resp = requests.get(f"{base_url}/workshops/{workshop_id}/pits", headers=headers)
        if hasattr(resp.json(), '__iter__') and len(resp.json()) > 0:
            pit_id = resp.json()[0]["id"]
        else:
            print("Failed to get pit:", resp.text)
            return

    print("4. Get or Create Customer User...")
    user_data = {
        "username": "demo_customer",
        "email": "demo_customer@test.com",
        "password": "temp_password",
        "role": "customer",
        "first_name": "Demo"
    }
    requests.post(f"{base_url}/users", headers=headers, json=user_data) # Ignore if exists

    print("5. Create Job...")
    job_data = {
        "pit_id": pit_id,
        "work_type": "Full Body Stealth PPF",
        "car_model": "Porsche 911 GT3 RS",
        "car_plate": "M-PPF001"
    }
    resp = requests.post(f"{base_url}/workshops/{workshop_id}/jobs", headers=headers, json=job_data)
    if resp.status_code not in [200, 201]:
        print("Failed to create job:", resp.text)
        return
    job_id = resp.json()["id"]

    print("6. Update status to generate token...")
    resp = requests.post(f"{base_url}/jobs/{job_id}/status", headers=headers, json={"status": "in_progress", "notes": ""})
    if resp.status_code == 200:
        print("Success! Created Tracking Token:")
        print(resp.json().get("customer_view_token", resp.json()))
    else:
        print("Failed to update status: ", resp.text)

if __name__ == "__main__":
    main()
