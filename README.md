# Project Management Dashboard API

## Implementation Plan
Proceeding with a **Columnar approach**:
1. Authentication (JWT, User Models)
2. Project Endpoints (CRUD, assigning Owner)
3. Document Endpoints (Upload/Download, checking Project access)
4. Sharing & Access Control (Participant roles)

## Architecture & Choices
* **Database:** PostgreSQL.
* **ORM:** SQLAlchemy 2.0 (using Repository Pattern for "with and without ORM").
* **Auth:** FastAPI `OAuth2PasswordBearer`, JWT (PyJWT), and password hashing via `passlib` (bcrypt).
* **Files:** Saved locally, paths stored in DB.

## API Specification

### Auth
* `POST /auth` - Create user.
* `POST /login` - Get JWT.

### Projects
* `GET /projects` - List accessible projects.
* `POST /projects` - Create project (sets user as owner).
* `GET /project/{id}/info` - Get details.
* `PUT /project/{id}/info` - Update details.
* `DELETE /project/{id}` - Delete project (owner only).

### Documents
* `GET /project/{id}/documents` - List documents.
* `POST /project/{id}/documents` - Upload document(s).
* `GET /document/{id}` - Download document.
* `PUT /document/{id}` - Update document.
* `DELETE /document/{id}` - Delete document.

### Sharing
* `POST /project/{id}/invite?user={login}` - Grant participant access.