# Project Management Dashboard API

## Scope
* Management of projects (creation, metadata tracking, and ownership).
* Control of documents within projects (uploading, downloading, and associating with specific projects).
* Handling of user authentication and project access control via specific participant roles:
  * **Owner:** Full access (creator of the project, can do anything).
  * **Participant:** User invited to the project, can modify, cannot delete.

## Architecture & Choices
* **Database:** PostgreSQL. Structured in 3NF (e.g., extracting participant roles into a dedicated `roles` enum table).
* **ORM & DB Access:** SQLAlchemy 2.0. Database communication will be encapsulated within a Singleton class inside the `services/` directory to act as the sole interface between the FastAPI routes and the database.
* **Auth:** FastAPI `OAuth2PasswordBearer`, JWT (PyJWT), and password hashing via `passlib` (bcrypt).
* **Files:** Stored locally via Docker-compose volume mapping to ensure persistence. File metadata and paths are stored in the database.

## API Summary

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create a new user account |
| POST | `/auth/login` | Authenticate and retrieve JWT |
| GET | `/projects` | List all projects accessible to the user |
| POST | `/projects` | Create a new project (sets user as owner) |
| GET | `/projects/{id}` | Retrieve detailed information for a specific project |
| PATCH| `/projects/{id}` | Update project metadata |
| DELETE | `/projects/{id}` | Remove a project and its documents (Owner only) |
| GET | `/projects/{id}/documents` | List all documents attached to a project |
| POST | `/projects/{id}/documents` | Upload a new document to a project |
| GET | `/documents/{id}` | Download a specific document |
| DELETE | `/documents/{id}` | Delete a specific document |
| POST | `/projects/{id}/invite` | Grant another user access to the project |

---

## Detailed API Specification

### POST /auth/register
Create a new user account.
**Request:**
```json
{
  "username": "jdoe",
  "email": "jdoe@example.com",
  "password": "securepassword123"
}
```
**Response (201 Created):**
```json
{
  "id": 1,
  "username": "jdoe",
  "email": "jdoe@example.com"
}
```
**Errors:**
* `400` Username or Email already exists.
* `422` Validation Error (e.g., weak password).

### POST /auth/login
Authenticate user credentials and issue a JWT.
**Request (Form Data):**
`username=jdoe&password=securepassword123`
**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5c...",
  "token_type": "bearer"
}
```
**Errors:**
* `401` Incorrect username or password.

### POST /projects
Create a new project. The creator is automatically assigned the "Owner" role.
**Request:**
```json
{
  "title": "Alpha Migration",
  "description": "Server migration planning."
}
```
**Response (201 Created):**
```json
{
  "id": 101,
  "title": "Alpha Migration",
  "description": "Server migration planning.",
  "created_by": 1,
  "created_at": "2026-06-18T10:00:00Z"
}
```
**Errors:**
* `401` Unauthorized (Missing or invalid JWT).

### PATCH /projects/{id}
Update specific fields of an existing project.
**Request - partial update:**
```json
{
  "description": "Updated server migration planning scope."
}
```
**Response (200 OK):**
```json
{
  "id": 101,
  "title": "Alpha Migration",
  "description": "Updated server migration planning scope.",
  "created_by": 1,
  "created_at": "2026-06-18T10:00:00Z"
}
```
**Errors:**
* `404` Project not found.
* `403` Forbidden (Requires Owner or Participant role).

### POST /projects/{id}/documents
Upload a new document to a specific project.
**Request (Multipart/Form-Data):**
`file: [binary_data]`
**Response (201 Created):**
```json
{
  "id": 505,
  "project_id": 101,
  "filename": "migration_architecture.pdf",
  "file_path": "/uploads/101/migration_architecture.pdf",
  "created_by": 1,
  "created_at": "2026-06-18T10:05:00Z"
}
```
**Errors:**
* `404` Project not found.
* `403` Forbidden (Insufficient permissions).
* `413` Payload Too Large (File size limit exceeded).

### POST /projects/{id}/invite
Grant another user access to the project by assigning them a specific role.
**Request:**
```json
{
  "user_id": 2,
  "role_id": 2 
}
```
*(Note: role_id 2 corresponds to the 'Participant' enum)*
**Response (200 OK):**
```json
{
  "project_id": 101,
  "user_id": 2,
  "role_id": 2,
  "role_name": "Participant"
}
```
**Errors:**
* `404` Project or User not found.
* `403` Forbidden (Only Owners can invite participants).