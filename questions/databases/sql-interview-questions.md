# SQL & Database Design Interview Questions

> Sources: datacamp.com, interviewquery.com, geeksforgeeks.org (Content rephrased for compliance with licensing restrictions)

---

## Part 1: SQL Fundamentals

### 1. What's the difference between WHERE and HAVING?

**Answer:**
- `WHERE` filters rows BEFORE grouping
- `HAVING` filters groups AFTER GROUP BY

```sql
-- WHERE: Filter before grouping
SELECT department, COUNT(*) 
FROM employees 
WHERE salary > 50000        -- Filter individual rows first
GROUP BY department;

-- HAVING: Filter after grouping
SELECT department, COUNT(*) 
FROM employees 
GROUP BY department 
HAVING COUNT(*) > 5;        -- Filter groups
```

---

### 2. What's the difference between DELETE, TRUNCATE, and DROP?

| Command | What it does | Rollback? | WHERE clause? |
|---------|--------------|-----------|---------------|
| DELETE | Removes specific rows | Yes | Yes |
| TRUNCATE | Removes ALL rows, keeps structure | No | No |
| DROP | Removes entire table | No | N/A |

```sql
DELETE FROM users WHERE id = 5;  -- Remove specific row
TRUNCATE TABLE logs;              -- Remove all rows, reset auto-increment
DROP TABLE temp_data;             -- Delete table completely
```

---

### 3. Explain different types of JOINs

```sql
-- INNER JOIN: Only matching rows from both tables
SELECT u.name, o.order_id
FROM users u
INNER JOIN orders o ON u.id = o.user_id;

-- LEFT JOIN: All from left + matching from right
SELECT u.name, o.order_id
FROM users u
LEFT JOIN orders o ON u.id = o.user_id;

-- RIGHT JOIN: All from right + matching from left
SELECT u.name, o.order_id
FROM users u
RIGHT JOIN orders o ON u.id = o.user_id;

-- FULL OUTER JOIN: All from both tables
SELECT u.name, o.order_id
FROM users u
FULL OUTER JOIN orders o ON u.id = o.user_id;

-- CROSS JOIN: Cartesian product (every combination)
SELECT u.name, p.product_name
FROM users u
CROSS JOIN products p;
```

---

### 4. What is a subquery vs CTE?

**Subquery:**
```sql
SELECT name FROM users 
WHERE id IN (SELECT user_id FROM orders WHERE amount > 100);
```

**CTE (Common Table Expression):**
```sql
WITH high_value_orders AS (
    SELECT user_id FROM orders WHERE amount > 100
)
SELECT name FROM users 
WHERE id IN (SELECT user_id FROM high_value_orders);
```

**When to use CTE:**
- Query is complex and needs to be readable
- Same subquery used multiple times
- Recursive queries

---

### 5. Window Functions

```sql
-- ROW_NUMBER: Assign unique row numbers
SELECT name, salary,
       ROW_NUMBER() OVER (ORDER BY salary DESC) as rank
FROM employees;

-- RANK: Same value = same rank, gaps in ranking
SELECT name, salary,
       RANK() OVER (ORDER BY salary DESC) as rank
FROM employees;

-- DENSE_RANK: Same value = same rank, no gaps
SELECT name, salary,
       DENSE_RANK() OVER (ORDER BY salary DESC) as rank
FROM employees;

-- LAG/LEAD: Access previous/next row
SELECT name, salary,
       LAG(salary) OVER (ORDER BY hire_date) as prev_salary,
       LEAD(salary) OVER (ORDER BY hire_date) as next_salary
FROM employees;

-- Running total
SELECT order_date, amount,
       SUM(amount) OVER (ORDER BY order_date) as running_total
FROM orders;
```

---

## Part 2: Database Design

### 6. What is Normalization? Explain normal forms.

**1NF (First Normal Form):**
- No repeating groups
- Each cell has single value

```sql
-- BAD: Repeating groups
| user_id | phone_numbers           |
| 1       | 9876543210, 9123456789  |

-- GOOD: 1NF
| user_id | phone_number |
| 1       | 9876543210   |
| 1       | 9123456789   |
```

**2NF (Second Normal Form):**
- Must be in 1NF
- No partial dependencies (all non-key columns depend on ENTIRE primary key)

**3NF (Third Normal Form):**
- Must be in 2NF
- No transitive dependencies (non-key columns don't depend on other non-key columns)

```sql
-- BAD: Transitive dependency
| order_id | customer_id | customer_name |  -- customer_name depends on customer_id, not order_id

-- GOOD: 3NF (separate tables)
orders: order_id, customer_id
customers: customer_id, customer_name
```

---

### 7. When to Denormalize?

**Normalize when:**
- Data integrity is critical
- Write-heavy workload
- Storage is a concern

**Denormalize when:**
- Read performance is critical
- Complex joins are slowing queries
- Data doesn't change frequently

**Example:** Store `customer_name` in `orders` table to avoid join on every read.

---

### 8. What are Indexes? Types?

**Index = Data structure to speed up queries**

```sql
-- Create index
CREATE INDEX idx_users_email ON users(email);

-- Composite index
CREATE INDEX idx_orders_user_date ON orders(user_id, order_date);

-- Unique index
CREATE UNIQUE INDEX idx_users_email_unique ON users(email);
```

**Types:**
| Type | Description | Use Case |
|------|-------------|----------|
| B-Tree | Balanced tree, default | Most queries, range queries |
| Hash | Hash table | Exact match only |
| GiST | Generalized search tree | Full-text, geometric |
| GIN | Generalized inverted | Arrays, JSONB |

**When NOT to use indexes:**
- Small tables
- Columns with low cardinality (few unique values)
- Frequently updated columns
- Write-heavy tables

---

### 9. Explain ACID Properties

| Property | Meaning | Example |
|----------|---------|---------|
| **A**tomicity | All or nothing | Transfer: both debit AND credit must happen |
| **C**onsistency | Valid state to valid state | Balance can't be negative |
| **I**solation | Transactions don't interfere | Two transfers don't see partial state |
| **D**urability | Committed = permanent | Power failure doesn't lose data |

---

### 10. What are Transaction Isolation Levels?

| Level | Dirty Read | Non-Repeatable Read | Phantom Read |
|-------|------------|---------------------|--------------|
| Read Uncommitted | Yes | Yes | Yes |
| Read Committed | No | Yes | Yes |
| Repeatable Read | No | No | Yes |
| Serializable | No | No | No |

```sql
-- Set isolation level
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
BEGIN;
-- your queries
COMMIT;
```

---

## Part 3: Performance & Optimization

### 11. How to Optimize a Slow Query?

**Step 1: EXPLAIN ANALYZE**
```sql
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 5;
```

**Look for:**
- Seq Scan (full table scan) → Add index
- High cost numbers → Optimize
- Nested loops on large tables → Consider join order

**Step 2: Add appropriate indexes**
```sql
CREATE INDEX idx_orders_user ON orders(user_id);
```

**Step 3: Rewrite query**
- Use EXISTS instead of IN for large subqueries
- Avoid SELECT * (select only needed columns)
- Use LIMIT for pagination

---

### 12. What is Query Execution Order?

```sql
FROM        -- 1. Tables and joins
WHERE       -- 2. Filter rows
GROUP BY    -- 3. Group rows
HAVING      -- 4. Filter groups
SELECT      -- 5. Select columns
DISTINCT    -- 6. Remove duplicates
ORDER BY    -- 7. Sort results
LIMIT       -- 8. Limit rows
```

---

### 13. Clustered vs Non-Clustered Index

| Clustered | Non-Clustered |
|-----------|---------------|
| Data physically sorted by index | Separate structure pointing to data |
| Only ONE per table | Multiple per table |
| Primary key by default | Any column |
| Faster for range queries | Faster for specific lookups |

---

## Part 4: Practical SQL Problems

### 14. Find Second Highest Salary

```sql
-- Method 1: LIMIT OFFSET
SELECT DISTINCT salary FROM employees 
ORDER BY salary DESC 
LIMIT 1 OFFSET 1;

-- Method 2: Subquery
SELECT MAX(salary) FROM employees 
WHERE salary < (SELECT MAX(salary) FROM employees);

-- Method 3: DENSE_RANK
SELECT salary FROM (
    SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) as rank
    FROM employees
) ranked
WHERE rank = 2;
```

---

### 15. Find Duplicate Emails

```sql
SELECT email, COUNT(*) as count
FROM users
GROUP BY email
HAVING COUNT(*) > 1;
```

---

### 16. Find Employees Earning More Than Their Manager

```sql
SELECT e.name as employee
FROM employees e
JOIN employees m ON e.manager_id = m.id
WHERE e.salary > m.salary;
```

---

### 17. Running Total

```sql
SELECT 
    order_date,
    amount,
    SUM(amount) OVER (ORDER BY order_date) as running_total
FROM orders;
```

---

### 18. Find Consecutive Login Days

```sql
WITH login_groups AS (
    SELECT 
        user_id,
        login_date,
        login_date - ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date) * INTERVAL '1 day' as grp
    FROM logins
)
SELECT user_id, COUNT(*) as consecutive_days
FROM login_groups
GROUP BY user_id, grp
HAVING COUNT(*) >= 3;  -- At least 3 consecutive days
```

---

### 19. Pivot Table

```sql
-- Convert rows to columns
SELECT 
    product_id,
    SUM(CASE WHEN month = 'Jan' THEN sales ELSE 0 END) as Jan,
    SUM(CASE WHEN month = 'Feb' THEN sales ELSE 0 END) as Feb,
    SUM(CASE WHEN month = 'Mar' THEN sales ELSE 0 END) as Mar
FROM sales
GROUP BY product_id;
```

---

### 20. Self Join: Find Pairs

```sql
-- Find pairs of employees in same department
SELECT e1.name, e2.name
FROM employees e1
JOIN employees e2 ON e1.department = e2.department
WHERE e1.id < e2.id;  -- Avoid duplicates
```

---

## Part 5: PostgreSQL Specific

### 21. JSONB Queries

```sql
-- Query JSON field
SELECT * FROM users WHERE profile->>'city' = 'Mumbai';

-- Query nested JSON
SELECT * FROM orders WHERE items @> '[{"product_id": 5}]';

-- Update JSON field
UPDATE users SET profile = jsonb_set(profile, '{city}', '"Delhi"');
```

---

### 22. Array Operations

```sql
-- Array contains
SELECT * FROM posts WHERE tags @> ARRAY['python'];

-- Array overlap (any match)
SELECT * FROM posts WHERE tags && ARRAY['python', 'java'];

-- Unnest array
SELECT unnest(tags) as tag FROM posts;
```

---

### 23. Useful PostgreSQL Functions

```sql
-- String aggregation
SELECT department, STRING_AGG(name, ', ') as employees
FROM employees
GROUP BY department;

-- Date truncation
SELECT DATE_TRUNC('month', created_at) as month, COUNT(*)
FROM orders
GROUP BY 1;

-- Generate series
SELECT generate_series('2024-01-01'::date, '2024-12-31'::date, '1 month');

-- Coalesce (first non-null)
SELECT COALESCE(nickname, name, 'Anonymous') as display_name FROM users;
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────┐
│              SQL INTERVIEW CHECKLIST            │
├─────────────────────────────────────────────────┤
│ JOINs:        INNER, LEFT, RIGHT, FULL, CROSS   │
│ Aggregates:   COUNT, SUM, AVG, MIN, MAX         │
│ Window:       ROW_NUMBER, RANK, LAG, LEAD, SUM  │
│ Subqueries:   IN, EXISTS, CTE                   │
│ Indexes:      B-Tree, when to use, EXPLAIN      │
│ Normalization: 1NF, 2NF, 3NF, when to denorm    │
│ ACID:         Atomicity, Consistency, etc.      │
│ Isolation:    Read Committed, Repeatable Read   │
└─────────────────────────────────────────────────┘
```
