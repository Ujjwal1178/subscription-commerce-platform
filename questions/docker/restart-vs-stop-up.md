# Docker: restart vs stop/up - Environment Variables Reload

## Question 1: `docker-compose restart` aur `docker-compose stop` + `up` mein kya difference hai?

### Answer:

**`docker-compose restart`:**
- Same container restart hota hai
- Container recreate NAHI hota
- **Environment variables reload NAHI hote!**
- Container ID same rehta hai
- Fast operation

**`docker-compose stop` + `docker-compose up`:**
- Container pehle stop hota hai
- Fir naya container create hota hai (recreate)
- **Environment variables fresh load hote hain!**
- Container ID change ho sakta hai
- Slightly slower but ensures fresh state

### Practical Example:

```yaml
# docker-compose.yml
services:
  auth-service:
    env_file:
      - .env
```

```bash
# .env updated with new value
ENCRYPTION_KEY=new-32-byte-key-here-for-security

# This WON'T pick up new .env values!
docker-compose restart auth-service

# This WILL pick up new .env values!
docker-compose stop auth-service
docker-compose up -d auth-service
```

### Verification:

```bash
# Check what env vars are actually in container
docker exec scp_auth_service printenv ENCRYPTION_KEY
```

---

## Question 2: Production mein `.env` update karne ke baad restart kaafi hai ya recreate chahiye?

### Answer:

**Recreate chahiye!** `restart` se naye environment variables load nahi honge.

**Safe Production Flow:**
1. Update `.env` file
2. `docker-compose stop service-name`
3. `docker-compose up -d service-name`
4. Verify: `docker exec container printenv VARIABLE_NAME`

**Even safer with zero downtime:**
```bash
docker-compose up -d --force-recreate service-name
```
`--force-recreate` ensures container is recreated even if config hasn't changed.

---

## Question 3: Volume mounts ke through code changes toh auto-reload hote hain, fir .env kyun nahi?

### Answer:

**Great observation!**

| What | How it works | Auto-reload? |
|------|-------------|--------------|
| Code files | Volume mount (bind mount) | Yes! (with --reload) |
| Environment vars | Set at container START | No (fixed at creation) |

**Reason:**
- **Volume mount** = Live connection, always synced
- **Environment vars** = Copied INTO container at creation time, not linked

```
Host .env ─────────────────────────────→ Container env
                  │                           │
            (copied at                   (frozen copy,
             container                    not linked)
             creation)
```

**Code with volume mount:**
```
Host code ←────────────────────────────→ Container /app
                  │                           │
            (live link,                  (same files,
             shared)                      always synced)
```

---

## Question 4: Kya `docker-compose down` + `up` bhi environment reload karta hai?

### Answer:

**Yes!** Even more thorough than just stop + up.

| Command | Network | Volumes | Container | Env Reload |
|---------|---------|---------|-----------|------------|
| restart | Kept | Kept | Same | ❌ No |
| stop + up | Kept | Kept | Recreated | ✅ Yes |
| down + up | Recreated | Kept* | Recreated | ✅ Yes |

`*` Volumes kept unless you use `-v` flag: `docker-compose down -v`

**When to use what:**
- **restart:** Quick restart, no config changes
- **stop + up:** Config changed, need fresh env
- **down + up:** Network issues, fresh start needed

---

## Question 5: Interview scenario - Production mein config change kiya but `restart` se kaam nahi chala, debugging kaise karoge?

### Answer:

**Step-by-step debugging:**

```bash
# 1. Check what container actually has
docker exec container_name printenv | grep CONFIG_VAR

# 2. Check what .env has
cat .env | grep CONFIG_VAR

# 3. If different, container has old value
# Fix: Recreate container
docker-compose stop service-name
docker-compose up -d service-name

# 4. Verify again
docker exec container_name printenv CONFIG_VAR
```

**Red flag in interview:** If candidate says "just restart the container", they don't understand how Docker handles environment variables!

---

## Summary Table

| Scenario | Command |
|----------|---------|
| Code change (with volume mount) | No command needed (auto-reload) |
| .env change | `stop` + `up -d` |
| requirements.txt change | `build` + `up -d` |
| Dockerfile change | `build` + `up -d` |
| Quick restart (no config change) | `restart` |
| Fresh start (networking issues) | `down` + `up -d` |

---

## Tags
`docker` `docker-compose` `environment-variables` `debugging` `production`
