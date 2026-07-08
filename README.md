# Project Management Dashboard API

## Scope
* Management of projects (creation, metadata tracking, and ownership).
* Control of documents within projects (uploading, downloading, and associating with specific projects).
* Handling of user authentication and project access control via specific participant roles:
  * **Owner:** Full access (creator of the project, can do anything).
  * **Participant:** User invited to the project, can modify, cannot delete.

## Architecture & Choices
* **Database:** PostgreSQL. 
* **ORM & DB Access:** SQLAlchemy 2.0. The application strictly follows a **Layered Architecture**. Database queries are encapsulated within **Repositories**, while business logic and validations are handled by **Services**. FastAPI routers act only as the HTTP entry points, ensuring a highly decoupled and testable system.
* **Auth:** FastAPI `OAuth2PasswordBearer`, JWT (PyJWT), and password hashing via `passlib` (bcrypt).
* **Files:** Object storage managed via MinIO (S3-compatible API) for local development, with production environments fully utilizing native **AWS S3** via IAM roles. File metadata is tracked securely in the database.
* **Deployment:** Containerized via Docker. Production environment is orchestrated using AWS ECS (backed by an EC2 instance to remain within the AWS Free Tier), connecting to a managed Amazon RDS PostgreSQL instance.

### Database Architecture & Design
This project utilizes a relational database structure designed with PostgreSQL and managed via SQLAlchemy ORM. The architecture prioritizes data integrity and strictly follows normalization principles to minimize redundancy.

**Entity Relationship & Normalization**
The database is structured in **Third Normal Form (3NF)** to ensure robust data consistency:
* **Users Table:** Holds core user authentication data.
* **Projects Table:** Contains project-specific metadata, linked to the creator/owner.
* **Roles Table:** Extracts participant roles into a dedicated enum table.
* **Documents Table:** Stores file metadata (including unique S3 object paths). It maintains a strict Many-to-One relationship with the `Projects` table via a foreign key constraint (`project_id`).

By normalizing the `Documents` schema into its own table rather than embedding file arrays inside the project entity, we ensure:
1. **Data Integrity:** Orphaned files are avoided, and updating file attributes doesn't affect core project metadata.
2. **Storage Optimization:** Database records remain lightweight and predictable, keeping binary or string-heavy file paths isolated.

**Query Optimization & Loading Strategy**
To balance normalization with application performance, the API implements explicit relationship loading strategies. Instead of relying on standard lazy-loading (which can cause silent data omissions or lead to the classic N+1 query problem), heavy operations like project deletion utilize explicit loading (`selectinload`). This efficiently fetches and processes cascading records (like deleting corresponding S3 objects) in an optimized database round-trip.

## Quick Start (Local Development)

This project is fully containerized. You do not need to install Python or PostgreSQL on your local machine to run it.

**1. Setup Environment Variables**
Copy the example environment file and fill in your local values (or leave the defaults for testing):
`cp .env.example .env`

**2. Boot the Architecture**
Ensure the Docker daemon is running, then start the API, Database, and MinIO storage containers:
`docker compose up -d --build`

**3. Access the Services**
* **API Interactive Docs (Swagger):** `http://127.0.0.1:8000/docs`
* **MinIO Storage Dashboard:** `http://127.0.0.1:9001`

---

## API Summary

| Method | Path | Description |
|---|---|---|
| POST | `/auth` | Create a new user account |
| POST | `/login` | Authenticate and retrieve JWT |
| GET | `/projects` | List all projects accessible to the user (includes details & documents) |
| POST | `/projects` | Create a new project (sets user as Owner) |
| GET | `/projects/{id}` | Retrieve detailed information for a specific project |
| PATCH| `/projects/{id}` | Update project metadata (name, description) |
| DELETE | `/projects/{id}` | Delete project and corresponding documents (Owner only) |
| GET | `/projects/{id}/documents` | List all documents attached to a project |
| POST | `/projects/{id}/documents` | Upload document(s) to a project |
| GET | `/projects/{project_id}/documents/{document_id}/download` | Download a specific document |
| PUT | `/projects/{project_id}/documents/{document_id}` | Update a document's filename |
| DELETE | `/projects/{project_id}/documents/{document_id}` | Delete a document |
| POST | `/projects/{id}/invite` | Grant another user access to the project (Owner only) |

---

## Detailed API Specification

### POST /auth
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

### POST /login
Authenticate user credentials and issue a JWT. (JWT lasts 1 hour)
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
  "created_at": "2026-06-18T10:00:00Z",
  "documents": []
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
  "description": "Updated scope.",
  "created_by": 1,
  "created_at": "2026-06-18T10:00:00Z",
  "documents": []
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
  "file_size": 1048576,
  "created_by": 1
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
  "role_name": "Participant"
}
```
**Errors:**
* `404` Project or User not found.
* `403` Forbidden (Only Owners can invite participants).