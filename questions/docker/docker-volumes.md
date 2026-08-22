# Docker Volumes - Data Persistence

## Question
"What happens to data when a Docker container is deleted? How do you persist data?"

---

## Answer

> "By default, when a container is deleted, all data inside it is lost. To persist data, we use **Docker Volumes**.
>
> Volumes are stored on the host machine, outside the container's filesystem. When we mount a volume to a container, data written to that path goes to the host's storage instead of the container's ephemeral layer.
>
> Even if you delete and recreate the container, the volume data remains intact."

---

## Visual Explanation

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DOCKER VOLUMES                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   WITHOUT VOLUME:                                                   │
│   ┌─────────────────────┐                                           │
│   │     Container       │                                           │
│   │   ┌─────────────┐   │                                           │
│   │   │   Data      │   │   docker rm container                     │
│   │   │  (inside)   │   │   ──────────────────▶  💀 DATA GONE!      │
│   │   └─────────────┘   │                                           │
│   └─────────────────────┘                                           │
│                                                                     │
│   ─────────────────────────────────────────────────────────────     │
│                                                                     │
│   WITH VOLUME:                                                      │
│   ┌─────────────────────┐       ┌─────────────────────┐             │
│   │     Container       │       │    Host Machine     │             │
│   │   ┌─────────────┐   │       │   ┌─────────────┐   │             │
│   │   │   Data      │◀──┼───────┼──▶│   Volume    │   │             │
│   │   │  (mounted)  │   │       │   │  (on disk)  │   │             │
│   │   └─────────────┘   │       │   └─────────────┘   │             │
│   └─────────────────────┘       └─────────────────────┘             │
│                                                                     │
│   docker rm container → Container gone, but VOLUME SAFE! ✅         │
│   docker run (new) → Mount same volume → Data is back! ✅           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Docker Compose Syntax

```yaml
services:
  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
        ───────────── ────────────────────────
             │                    │
        Volume name       Path INSIDE container
        (on host)         (where Postgres stores data)

volumes:
  postgres_data:    # Declare the volume
```

---

## Volume Types

| Type | Syntax | Use Case |
|------|--------|----------|
| **Named Volume** | `myvolume:/data` | Production, managed by Docker |
| **Bind Mount** | `./local/path:/data` | Development, edit files directly |
| **tmpfs** | `tmpfs:/data` | Temporary, in-memory only |

---

## Follow-up Questions

### Q1: "What's the difference between named volumes and bind mounts?"

**Answer**:

```
Named Volume:
- Docker manages location (somewhere in /var/lib/docker/volumes/)
- Portable across machines
- Better for production data (databases)

Bind Mount:
- YOU specify exact path (./my-folder:/container-path)
- Good for development (edit code, see changes immediately)
- Not portable (path might not exist on another machine)
```

### Q2: "How do you backup volume data?"

**Answer**:
```bash
# Option 1: Copy from volume to host
docker run --rm -v postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz /data

# Option 2: Use docker cp
docker cp container_name:/var/lib/postgresql/data ./backup

# Option 3: For databases, use native dump
docker exec postgres pg_dump -U postgres mydb > backup.sql
```

### Q3: "What happens to volumes when you run `docker-compose down`?"

**Answer**:
```bash
docker-compose down      # Stops and removes containers, KEEPS volumes
docker-compose down -v   # Stops, removes containers AND volumes (DATA LOST!)
```

**Always be careful with `-v` flag!**

---

## Interview Tips

1. **Know the difference** between volumes and bind mounts
2. **Explain WHY** - "Containers are ephemeral, data shouldn't be"
3. **Mention backups** - Shows production thinking
4. **Know the danger** - `docker-compose down -v` deletes data!
