import uuid

from fastapi.testclient import TestClient


def test_create_user_success(client: TestClient) -> None:
    unique_id = uuid.uuid4()
    unique_email = f"testuser_{unique_id}@example.com"
    unique_username = f"user_{unique_id.hex[:8]}"

    user_payload = {
        "username": unique_username,
        "email": unique_email,
        "password": "securepassword123",
        "repeat_password": "securepassword123",
    }

    # Send the payload to the users endpoint
    response = client.post("/auth", json=user_payload)

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


def test_create_user_duplicate_email(client: TestClient) -> None:
    # 1. ARRANGE: Create a user first
    email = "duplicate@example.com"
    user_payload = {
        "username": "tester1",
        "email": email,
        "password": "password123",
        "repeat_password": "password123",
    }
    client.post("/auth", json=user_payload)

    # 2. ACT: Try to create another user with the SAME email
    duplicate_payload = {
        "username": "tester2",
        "email": email,
        "password": "password123",
        "repeat_password": "password123",
    }
    response = client.post("/auth", json=duplicate_payload)

    # 3. ASSERT: Expect a failure
    # Most APIs use 400 (Bad Request) or 409 (Conflict) for duplicates
    assert response.status_code == 400

    # Verify the error message says something about the email being taken
    assert "email" in response.json()["detail"].lower()


def test_login_success(client: TestClient) -> None:
    unique_id = uuid.uuid4()
    email = f"login_test_{unique_id}@example.com"
    username = f"loginuser_{unique_id.hex[:8]}"
    password = "supersecretpassword"

    setup_response = client.post(
        "/auth",
        json={
            "username": username,
            "email": email,
            "password": password,
            "repeat_password": password,
        },
    )
    assert setup_response.status_code in (200, 201), f"Setup failed: {setup_response.text}"

    # attempt to log in
    response = client.post("/login", data={"username": username, "password": password})

    print("\n--- LOGIN ERROR ---")
    print(response.json())
    print("-------------------\n")

    assert response.status_code == 200
    response_data = response.json()
    assert "access_token" in response_data
    assert response_data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient) -> None:
    unique_id = uuid.uuid4()
    username = f"wrongpass_{unique_id.hex[:8]}"
    client.post(
        "/auth",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "correctpassword",
            "repeat_password": "correctpassword",
        },
    )

    # Try to log in with a bad password
    response = client.post("/login", data={"username": username, "password": "WRONGpassword123"})

    # ASSERT: Should be rejected
    assert response.status_code == 401
    assert "access_token" not in response.json()


def test_login_nonexistent_user(client: TestClient) -> None:
    response = client.post(
        "/login", data={"username": "ghost_user_999", "password": "somepassword"}
    )

    assert response.status_code == 401
