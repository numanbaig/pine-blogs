# How Middleware and Auth Work in FastAPI

This document explains how authentication works in this project and clarifies the difference between FastAPI **middleware** and **dependencies**.

---

## Key Concept: We Use Dependencies, Not Middleware

What we built is a **dependency** (`get_current_user`), not traditional middleware. In FastAPI, dependencies are the preferred way to handle auth because they:

- Run only for routes that need them
- Integrate with FastAPI's dependency injection
- Provide typed parameters (e.g. `User`) to your route handlers

---

## Middleware vs Dependencies

| Aspect | Middleware | Dependencies |
|--------|------------|--------------|
| **Scope** | Runs for every request (or a subset by path) | Runs only for routes that declare them |
| **Access to route** | No direct access to route params or return value | Full access; can inject values into the route |
| **Typed output** | No – you attach data to `request.state` | Yes – e.g. `User` is passed as a parameter |
| **Typical use** | Logging, CORS, request timing | Auth, DB session, validation |

---

## How Our Auth Flow Works

```
┌─────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│   Client    │────▶│  Authorization:      │────▶│  FastAPI Route  │
│             │     │  Bearer <jwt_token>  │     │  (e.g. create   │
│             │     │                      │     │   blog)          │
└─────────────┘     └──────────────────────┘     └────────┬────────┘
                                                          │
                                                          │ Depends(get_current_user)
                                                          ▼
                                                 ┌─────────────────┐
                                                 │ get_current_user │
                                                 │ dependency      │
                                                 └────────┬────────┘
                                                          │
                     ┌────────────────────────────────────┘
                     │
                     ▼
            ┌────────────────┐     ┌────────────────┐
            │ 1. Extract     │────▶│ 2. Decode JWT  │
            │    Bearer token│     │    (jose)      │
            └────────────────┘     └───────┬──────┘
                                           │
                                           ▼
            ┌────────────────┐     ┌────────────────┐
            │ 4. Return User │◀────│ 3. Fetch user │
            │    to route    │     │    from DB    │
            └────────────────┘     └──────────────┘
```

---

## Step-by-Step: What Happens on a Request

### 1. Client Sends Request with JWT

```http
POST /blogs/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{"title": "My Blog", "content": "Hello world"}
```

### 2. FastAPI Sees the Dependency

```python
@router.post("/")
async def create_blog(
    blog: BlogCreate,
    current_user: User = Depends(get_current_user),  # ← FastAPI runs this first
    db: AsyncSession = Depends(get_db),
):
```

Before the route runs, FastAPI executes `get_current_user`.

### 3. `get_current_user` Runs

```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
```

- **`oauth2_scheme`** (HTTPBearer): Reads `Authorization: Bearer <token>` and gives you the token.
- If no header or invalid format → `credentials` is `None` → 401.
- If present → `credentials.credentials` is the JWT string.

### 4. Token Is Decoded and User Fetched

```python
user = await get_user_from_token(credentials.credentials, db)
```

- Decode JWT with `jose`, read `sub` (email).
- Query DB for user with that email.
- If not found or token invalid → 401.
- If found → return `User`.

### 5. User Is Injected Into the Route

```python
# FastAPI passes the returned User as current_user
async def create_blog(
    blog: BlogCreate,
    current_user: User,  # ← This is the User from get_current_user
    db: AsyncSession,
):
    db_blog = Blog(..., user_id=current_user.id)
```

---

## Code Locations

| File | What It Does |
|------|--------------|
| `app/core/security.py` | `get_current_user`, `get_current_user_optional`, `get_user_from_token`, JWT helpers |
| `app/api/routes/blogs.py` | Uses `Depends(get_current_user)` in `create_blog` |
| `app/api/routes/auth.py` | Login/signup; returns JWT to client |

---

## Two Auth Dependencies

### 1. `get_current_user` (Required Auth)

- Use when the route **must** be authenticated.
- Missing or invalid token → 401.
- Returns `User`.

```python
@router.post("/")
async def create_blog(
    current_user: User = Depends(get_current_user),
):
    # current_user is guaranteed to exist
```

### 2. `get_current_user_optional` (Optional Auth)

- Use when the route works for both logged-in and anonymous users.
- Missing/invalid token → `None`.
- Valid token → `User`.

```python
@router.get("/")
async def list_items(
    current_user: User | None = Depends(get_current_user_optional),
):
    if current_user:
        # Logged in
    else:
        # Anonymous
```

---

## If We Used Real Middleware Instead

Traditional middleware would look like this:

```python
from starlette.middleware.base import BaseHTTPMiddleware

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Runs for EVERY request
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            # Decode, fetch user, attach to request.state
            request.state.user = user
        else:
            request.state.user = None
        return await call_next(request)

app.add_middleware(AuthMiddleware)
```

**Problems with this approach:**

- Runs on every request, even `/health`, `/docs`, static files.
- Route gets `request.state.user` (untyped) instead of a `User` parameter.
- No per-route control; you’d need extra logic to require auth on specific routes.

---

## Summary

| Term | In This Project |
|------|-----------------|
| **Middleware** | Not used for auth |
| **Dependency** | `get_current_user` – runs only when a route declares it |
| **Flow** | Request → `HTTPBearer` extracts token → decode JWT → fetch user → inject `User` into route |
| **Usage** | Add `current_user: User = Depends(get_current_user)` to any route that needs auth |
