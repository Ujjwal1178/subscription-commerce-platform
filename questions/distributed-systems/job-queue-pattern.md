# Job Queue Pattern

## Question
"You have recurring payments that need to run daily. How would you design this? What if multiple workers try to process the same job?"

---

## Answer

> "I'd implement a **Job Queue Pattern** with database-backed jobs:
>
> 1. **Scheduler** scans for due payments and creates job records
> 2. **Workers** pick up PENDING jobs and process them
> 3. To prevent duplicate processing, I'd use **SELECT FOR UPDATE SKIP LOCKED**
>
> This ensures only one worker processes each job, even with multiple workers running in parallel."

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PAYMENT SCHEDULER FLOW                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐                                                   │
│  │  SCHEDULER   │  (Runs every X minutes)                           │
│  │              │                                                   │
│  │  "Check for  │                                                   │
│  │   due        │                                                   │
│  │   payments"  │                                                   │
│  └──────┬───────┘                                                   │
│         │                                                           │
│         ▼                                                           │
│  ┌──────────────────────────────────────────────────────┐           │
│  │                    JOBS TABLE                        │           │
│  │  job_id | user_id | amount | status    | created_at  │           │
│  │  ─────────────────────────────────────────────────── │           │
│  │  1      | 101     | 1000   | PENDING   | 2024-01-15  │           │
│  │  2      | 102     | 2000   | PENDING   | 2024-01-15  │           │
│  │  3      | 103     | 1500   | RUNNING   | 2024-01-15  │           │
│  │  4      | 104     | 1000   | COMPLETED | 2024-01-15  │           │
│  │  5      | 105     | 2500   | FAILED    | 2024-01-15  │           │
│  └──────────────────────────────────────────────────────┘           │
│                                                                     │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐             │
│  │   WORKER 1   │   │   WORKER 2   │   │   WORKER 3   │             │
│  │              │   │              │   │              │             │
│  │ 1. Pick job  │   │ 1. Pick job  │   │ 1. Pick job  │             │
│  │ 2. Lock it   │   │ 2. Lock it   │   │ 2. Lock it   │             │
│  │ 3. Process   │   │ 3. Process   │   │ 3. Process   │             │
│  │ 4. Update    │   │ 4. Update    │   │ 4. Update    │             │
│  └──────────────┘   └──────────────┘   └──────────────┘             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## The Race Condition Problem

```
WITHOUT LOCKING:

Worker 1                         Worker 2
   │                                │
   │  SELECT * FROM jobs            │
   │  WHERE status = 'PENDING'      │  SELECT * FROM jobs
   │  LIMIT 1;                      │  WHERE status = 'PENDING'
   │                                │  LIMIT 1;
   ▼                                ▼
┌──────┐                        ┌──────┐
│Job #1│  (SAME JOB!)           │Job #1│
└──────┘                        └──────┘
   │                                │
   │  UPDATE status = 'RUNNING'     │  UPDATE status = 'RUNNING'
   │                                │
   ▼                                ▼
BOTH process same payment! 💀 DOUBLE CHARGE!
```

---

## Solution: SELECT FOR UPDATE SKIP LOCKED

```sql
-- This query LOCKS the row it selects
-- Other workers will SKIP locked rows

BEGIN TRANSACTION;

SELECT * FROM jobs 
WHERE status = 'PENDING' 
LIMIT 1
FOR UPDATE SKIP LOCKED;  -- 🔑 Magic line!

-- If we got a job, mark it as running
UPDATE jobs SET status = 'RUNNING', started_at = NOW() 
WHERE id = <selected_job_id>;

COMMIT;
```

**How it works:**
- `FOR UPDATE` → Locks the selected row
- `SKIP LOCKED` → If row is already locked, skip it and get next one

```
WITH LOCKING:

Worker 1                         Worker 2
   │                                │
   │  SELECT FOR UPDATE             │
   │  SKIP LOCKED                   │  SELECT FOR UPDATE
   ▼                                │  SKIP LOCKED
┌──────┐                            ▼
│Job #1│ (LOCKED by Worker 1)   ┌──────┐
└──────┘                        │Job #2│ (Gets different job!)
   │                            └──────┘
   │                                │
Process Job 1                    Process Job 2

NO DUPLICATE PROCESSING! ✅
```

---

## Follow-up Questions

### Q1: "What if a worker crashes while processing a job?"

**Answer**: Implement job timeouts and recovery!

```sql
-- Job stays in RUNNING state forever if worker crashes
-- Solution: Add timeout check

-- Scheduler also picks up "stuck" jobs
SELECT * FROM jobs 
WHERE status = 'PENDING'
   OR (status = 'RUNNING' AND started_at < NOW() - INTERVAL '10 minutes')
FOR UPDATE SKIP LOCKED;
```

**Additional fields:**
```sql
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    user_id INT,
    amount INT,
    status VARCHAR(20),  -- PENDING, RUNNING, COMPLETED, FAILED
    attempts INT DEFAULT 0,
    max_attempts INT DEFAULT 3,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### Q2: "How do you handle retries for failed jobs?"

**Answer**: Exponential backoff!

```python
def calculate_next_retry(attempts: int) -> datetime:
    # 1st retry: 1 min
    # 2nd retry: 4 min
    # 3rd retry: 16 min
    delay_seconds = (2 ** attempts) * 60
    return datetime.now() + timedelta(seconds=delay_seconds)

async def process_job(job_id: int):
    job = await get_job(job_id)
    
    try:
        await charge_payment(job.user_id, job.amount)
        await mark_completed(job_id)
    except PaymentError as e:
        job.attempts += 1
        if job.attempts >= job.max_attempts:
            await mark_failed(job_id, str(e))
            await notify_user_payment_failed(job.user_id)
        else:
            await schedule_retry(job_id, calculate_next_retry(job.attempts))
```

---

### Q3: "Why not use Redis or Kafka for the job queue?"

**Answer**: It depends on the use case!

| Approach | Pros | Cons | Best For |
|----------|------|------|----------|
| **Database (PostgreSQL)** | ACID, durable, query flexibility | Not as fast | Payment jobs (reliability critical) |
| **Redis (Bull/BullMQ)** | Very fast, built-in retries | Data can be lost | Non-critical background tasks |
| **Kafka** | High throughput, replay | Overkill for simple jobs | Event streaming, millions of events |

For **payments**, I prefer database-backed queues because:
- ACID guarantees (no lost payments)
- Easy to query job history
- Audit trail built-in

---

### Q4: "How do you scale this to handle more jobs?"

**Answer**: Add more workers!

```
┌────────────────────────────────────────────────────────────────┐
│                     HORIZONTAL SCALING                         │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│   ┌──────────────────────────────────────────────────────┐     │
│   │                    JOBS TABLE                        │     │
│   │         (Single source of truth)                     │     │
│   └────────────────────────┬─────────────────────────────┘     │
│                            │                                   │
│     ┌──────────┬───────────┼───────────┬──────────┐            │
│     ▼          ▼           ▼           ▼          ▼            │
│ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐         │
│ │Worker 1│ │Worker 2│ │Worker 3│ │Worker 4│ │Worker 5│         │
│ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘         │
│                                                                │
│  All workers compete for jobs using SELECT FOR UPDATE          │
│  SKIP LOCKED ensures no duplicates                             │
│                                                                │
│  More jobs? Add more workers! (Kubernetes auto-scaling)        │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Code Example

```python
# Worker pseudo-code
class PaymentWorker:
    async def run(self):
        while True:
            job = await self.pick_job()
            if job:
                await self.process_job(job)
            else:
                await asyncio.sleep(300)  # 5 min sleep if no jobs
    
    async def pick_job(self):
        async with db.transaction():
            result = await db.execute("""
                SELECT * FROM jobs 
                WHERE status = 'PENDING'
                   OR (status = 'RUNNING' AND started_at < NOW() - INTERVAL '10 minutes')
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            """)
            job = result.fetchone()
            
            if job:
                await db.execute("""
                    UPDATE jobs 
                    SET status = 'RUNNING', started_at = NOW()
                    WHERE id = :id
                """, {"id": job.id})
            
            return job
    
    async def process_job(self, job):
        try:
            await payment_service.charge(job.user_id, job.amount)
            await self.mark_completed(job.id)
        except Exception as e:
            await self.handle_failure(job, e)
```

---

## Interview Tips

1. **Always mention the race condition** - Shows you understand distributed systems
2. **Explain the locking mechanism** - FOR UPDATE SKIP LOCKED
3. **Cover failure scenarios** - Worker crash, payment failure, retries
4. **Discuss scaling** - Add more workers, Kubernetes auto-scaling
