# Docker: Do You Need to Rebuild Image on Code Change?

## The Question
> "When you change your application code, do you need to rebuild the Docker image and create a new container?"

## Quick Answer
**It depends on the environment:**
- **Production:** Yes, rebuild required (images are immutable)
- **Development:** No, use volume mounts + hot reload

---

## Deep Dive

### Why Images Need Rebuild in Production

Docker images are **immutable** (unchangeable). Your code gets copied into the image at build time:

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . /app                    # ← Code copied HERE at BUILD time
CMD ["uvicorn", "main:app"]
```

```
┌─────────────────────────────────────────────────┐
│              DOCKER IMAGE (Immutable)           │
│  ┌───────────────────────────────────────────┐  │
│  │  Layer 1: Base OS (python:3.11-slim)      │  │
│  ├───────────────────────────────────────────┤  │
│  │  Layer 2: Dependencies (pip install)      │  │
│  ├───────────────────────────────────────────┤  │
│  │  Layer 3: Your Code (COPY . /app)    ← 🔒 │  │
│  ├───────────────────────────────────────────┤  │
│  │  Layer 4: Startup Command                 │  │
│  └───────────────────────────────────────────┘  │
│                                                  │
│  Once built, these layers are FROZEN            │
└─────────────────────────────────────────────────┘
```

**Code change = Layer 3 needs to change = Rebuild image**

---

### Development Solution: Volume Mounts

Instead of copying code INTO the image, we **mount** our local folder:

```yaml
# docker-compose.yml (development)
services:
  auth_service:
    build: ./services/auth_service
    volumes:
      - ./services/auth_service:/app   # 👈 Mount local → container
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8001
    #                         ^^^^^^^^ Watch for changes
```

```
┌─────────────────────────────────────────────────────────────┐
│  VOLUME MOUNT (Development Magic)                           │
│                                                              │
│  Your Machine              Container                        │
│  ─────────────             ─────────                        │
│  D:\project\app\  ←─SYNC─→  /app                            │
│       │                        │                            │
│  Edit main.py          Container sees it instantly!         │
│       │                        │                            │
│  Save file             Uvicorn --reload restarts server     │
│                                                              │
│  ✅ No rebuild needed                                       │
│  ✅ Changes reflect in seconds                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Decision Matrix

| Scenario | New Image? | New Container? | Why? |
|----------|-----------|----------------|------|
| Code change (dev + volume mount) | ❌ No | ❌ No | Volume syncs changes, hot reload restarts |
| Code change (production) | ✅ Yes | ✅ Yes | Image is immutable, code is baked in |
| Add new pip dependency | ✅ Yes | ✅ Yes | `pip install` runs at build time only |
| Change environment variable | ❌ No | ✅ Yes | Container restart picks up new env |
| Change exposed port | ❌ No | ✅ Yes | Port mapping is container-level |
| Modify Dockerfile | ✅ Yes | ✅ Yes | Dockerfile = image recipe |

---

## Follow-up Questions

### Q1: "Why not use volume mounts in production?"

**Answer:**
1. **Security:** Don't want to expose host filesystem
2. **Consistency:** Image should be self-contained, same everywhere
3. **Portability:** Image runs on any machine; bind mount depends on host paths
4. **Versioning:** Image tags (v1.0, v1.1) track exactly what code is deployed

### Q2: "What if I add a new library (pip install something)?"

**Answer:** 
Dependencies require rebuild because `pip install` runs during `docker build`, not at runtime.

**Temporary workaround for dev:**
```bash
docker exec -it container_name pip install new-library
```
But this is lost when container restarts. Proper way = update requirements.txt + rebuild.

### Q3: "What's the difference between volume and bind mount?"

| Feature | Bind Mount | Docker Volume |
|---------|-----------|---------------|
| Source | Your folder path | Docker-managed storage |
| Syntax | `./local/path:/container/path` | `volume_name:/container/path` |
| Use case | Development (source code) | Production (database data) |
| Managed by | You | Docker |
| Portable | No (path-dependent) | Yes |

### Q4: "How does hot reload work?"

Tools like **uvicorn --reload** or **nodemon**:
1. Watch the mounted directory for file changes
2. When `.py` file changes, they detect it
3. Restart the application process inside container
4. No container restart needed, just app restart

---

## Production vs Development Setup

```yaml
# docker-compose.yml

# DEVELOPMENT
services:
  auth_service:
    build: ./services/auth_service
    volumes:
      - ./services/auth_service:/app    # Mount code
    command: uvicorn main:app --reload  # Hot reload ON
    environment:
      - DEBUG=true

---

# PRODUCTION (docker-compose.prod.yml)
services:
  auth_service:
    image: myregistry/auth_service:v1.2.3   # Pre-built image
    # NO volumes for code                   # Code is IN the image
    command: uvicorn main:app               # No --reload (performance)
    environment:
      - DEBUG=false
```

---

## Real Interview Answer

> "In production, yes - Docker images are immutable by design, which is actually beneficial for consistency and versioning. Any code change requires rebuilding the image, usually through CI/CD pipelines that build, tag, and push images.
>
> In development, we use bind mounts to sync our local source code into the container, combined with hot-reload tools like uvicorn's `--reload` flag. This gives us instant feedback without rebuilding.
>
> This separation is intentional - dev optimizes for speed, prod optimizes for reliability and reproducibility."

---

## Commands Reference

```bash
# Rebuild image after code/dependency change
docker-compose build auth_service

# Rebuild and restart
docker-compose up -d --build auth_service

# Just restart container (env var change, port change)
docker-compose restart auth_service

# View if image needs rebuild
docker-compose config  # Shows current config
```

---

## Key Takeaway

> **Images are immutable blueprints. In development, we bypass this with volume mounts. In production, we embrace it for consistency.**
