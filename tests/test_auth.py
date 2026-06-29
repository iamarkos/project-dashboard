import uuid
from fastapi.testclient import TestClient

def test_create_user_success(client: TestClient) -> None:
    unique_id = uuid.uuid4()
    unique_email = f"testuser_{unique_id}@example.com"
    unique_username = f"user_{unique_id.hex[:8]}" 

    user_payload = {
        "username": unique_username,
        "email": unique_email,
        "password": "securepassword123"
    }

    # Send the payload to the users endpoint
    response = client.post("/users/", json=user_payload)


    # 1. Check the HTTP status code (assuming 200 OK or 201 Created)
    assert response.status_code in (200, 201)
    
    # 2. Parse the JSON response
    response_data = response.json()
    
    # 3. Check that the returned data matches what we created
    assert response_data["email"] == unique_email
    assert response_data["username"] == unique_username
    # 4. Check that the database assigned an ID and stripped the password
    assert "id" in response_data
    assert "password" not in response_data