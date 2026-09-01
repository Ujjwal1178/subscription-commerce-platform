# Subscription Service - Database Design

## Overview

This document covers the database schema for the Subscription Service of the Subscription Commerce Platform. The design supports:
- Multiple subscription plans with flexible pricing
- Various billing cycles (monthly, yearly, one-time, recurring)
- Payment method management (tokenized, PCI compliant)
- Complete payment transaction history

---

## Entity Relationship Diagram

```
┌──────────────┐       ┌──────────────────┐       ┌────────────────────┐
│    users     │       │      plans       │       │    plan_prices     │
│ (auth_db)    │       ├──────────────────┤       ├────────────────────┤
├──────────────┤       │ plan_id (PK)     │──────<│ price_id (PK)      │
│ user_id (PK) │       │ plan_name        │       │ plan_id (FK)       │
└──────┬───────┘       │ plan_type        │       │ billing_cycle      │
       │               │ plan_features    │       │ duration_months    │
       │               │ is_active        │       │ amount             │
       │               │ created_at       │       │ currency           │
       │               │ updated_at       │       │ is_recurring       │
       │               └──────────────────┘       │ created_at         │
       │                        │                 │ updated_at         │
       │                        │                 └────────────────────┘
       │                        │                          │
       │                        ▼                          │
       │              ┌─────────────────────┐              │
       │              │  user_subscriptions │              │
       │              ├─────────────────────┤              │
       └─────────────>│ sub_id (PK)         │              │
                      │ user_id (FK)        │              │
                      │ plan_id (FK)        │<─────────────┘
                      │ price_id (FK)       │<─────────────┘
                      │ payment_method_id   │<─────────┐
                      │ locked_price        │          │
                      │ currency            │          │
                      │ sub_status          │          │
                      │ current_period_start│          │
                      │ current_period_end  │          │
                      │ next_billing_date   │          │
                      │ created_at          │          │
                      │ updated_at          │          │
                      │ cancelled_at        │          │
                      └─────────┬───────────┘          │
                                │                      │
                                │                      │
                                ▼                      │
                ┌───────────────────────────┐          │
                │   payment_transactions    │          │
                ├───────────────────────────┤          │
                │ transaction_id (PK)       │          │
                │ sub_id (FK)               │          │
                │ user_id (FK)              │          │
                │ payment_method_id (FK)    │          │
                │ amount                    │          │
                │ currency                  │          │
                │ status                    │          │
                │ provider_transaction_id   │          │
                │ failure_reason            │          │
                │ attempt_number            │          │
                │ idempotency_key           │          │
                │ billing_period_start      │          │
                │ billing_period_end        │          │
                │ created_at                │          │
                └───────────────────────────┘          │
                                                       │
       ┌───────────────────────────┐                   │
       │     payment_methods       │                   │
       ├───────────────────────────┤                   │
       │ payment_method_id (PK)    │───────────────────┘
       │ user_id (FK)              │
       │ provider                  │
       │ provider_token            │
       │ type                      │
       │ last_4_digits             │
       │ card_brand                │
       │ expiry_month              │
       │ expiry_year               │
       │ is_default                │
       │ is_deleted                │
       │ created_at                │
       │ updated_at                │
       └───────────────────────────┘
```

---

## Table Definitions

### 1. Plans

Stores subscription plan definitions (Basic, Premium, Family, etc.)

```sql
CREATE TABLE plans (
    plan_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_name       VARCHAR(50) NOT NULL,
    plan_type       VARCHAR(30),                    -- bundle grouping: "basic", "premium", "jumbo"
    plan_features   JSONB NOT NULL DEFAULT '{}',    -- {"4k": true, "downloads": 25, "screens": 4}
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index for active plans lookup
CREATE INDEX idx_plans_active ON plans(is_active) WHERE is_active = true;
```

**Example Data:**
| plan_id | plan_name | plan_type | plan_features |
|---------|-----------|-----------|---------------|
| uuid-1 | Free | basic | {"screens": 1, "quality": "480p", "downloads": 0} |
| uuid-2 | Premium | premium | {"screens": 3, "quality": "1080p", "downloads": 10} |
| uuid-3 | Family | premium | {"screens": 5, "quality": "4k", "downloads": 25} |

---

### 2. Plan Prices

Flexible pricing for each plan — supports multiple billing cycles and currencies.

```sql
CREATE TABLE plan_prices (
    price_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id         UUID NOT NULL REFERENCES plans(plan_id),
    billing_cycle   VARCHAR(20) NOT NULL,           -- "monthly", "yearly"
    duration_months INTEGER NOT NULL,               -- 1 for monthly, 12 for yearly
    amount          DECIMAL(10,2) NOT NULL,
    currency        VARCHAR(3) NOT NULL DEFAULT 'INR',
    is_recurring    BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index for price lookup by plan
CREATE INDEX idx_plan_prices_plan_id ON plan_prices(plan_id);

-- Unique constraint: one price per plan/cycle/currency/recurring combo
CREATE UNIQUE INDEX idx_plan_prices_unique 
ON plan_prices(plan_id, billing_cycle, currency, is_recurring);
```

**Example Data:**
| price_id | plan_id | billing_cycle | duration_months | amount | currency | is_recurring |
|----------|---------|---------------|-----------------|--------|----------|--------------|
| uuid-p1 | uuid-2 | monthly | 1 | 149.00 | INR | true |
| uuid-p2 | uuid-2 | monthly | 1 | 149.00 | INR | false |
| uuid-p3 | uuid-2 | yearly | 12 | 1499.00 | INR | false |
| uuid-p4 | uuid-2 | yearly | 12 | 149.00 | INR | true |

**Pricing Logic:**
| billing_cycle | duration_months | amount | is_recurring | Meaning |
|---------------|-----------------|--------|--------------|---------|
| monthly | 1 | 149 | false | One-time 1 month purchase, expires |
| monthly | 1 | 149 | true | Monthly subscription, auto-renews |
| yearly | 12 | 1499 | false | Yearly one-time full payment (discounted) |
| yearly | 12 | 149 | true | Yearly commitment, monthly payments (12x) |

---

### 3. Payment Methods

Tokenized payment methods — we NEVER store actual card numbers.

```sql
CREATE TABLE payment_methods (
    payment_method_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL,              -- FK to auth_db.users
    provider            VARCHAR(20) NOT NULL,       -- "stripe", "razorpay"
    provider_token      VARCHAR(255) NOT NULL,      -- "pm_1N2abc3XYZ"
    type                VARCHAR(20) NOT NULL,       -- "card", "upi", "netbanking"
    last_4_digits       VARCHAR(4),                 -- "4242" (nullable for UPI)
    card_brand          VARCHAR(20),                -- "visa", "mastercard" (nullable for UPI)
    expiry_month        INTEGER,                    -- 12 (nullable for UPI)
    expiry_year         INTEGER,                    -- 2028 (nullable for UPI)
    is_default          BOOLEAN NOT NULL DEFAULT false,
    is_deleted          BOOLEAN NOT NULL DEFAULT false,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index for user's payment methods
CREATE INDEX idx_payment_methods_user ON payment_methods(user_id) WHERE is_deleted = false;

-- Ensure only one default per user
CREATE UNIQUE INDEX idx_payment_methods_default 
ON payment_methods(user_id) WHERE is_default = true AND is_deleted = false;
```

**Security Note:**
- `provider_token` is Stripe/Razorpay's token, NOT actual card number
- We store `last_4_digits` only for display: "Visa ending 4242"
- Actual card data resides with payment provider (PCI compliant)

---

### 4. User Subscriptions

Core table linking users to their subscription plans.

```sql
CREATE TABLE user_subscriptions (
    sub_id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID NOT NULL,              -- FK to auth_db.users
    plan_id                 UUID NOT NULL REFERENCES plans(plan_id),
    price_id                UUID NOT NULL REFERENCES plan_prices(price_id),
    payment_method_id       UUID REFERENCES payment_methods(payment_method_id),
    locked_price            DECIMAL(10,2) NOT NULL,     -- price snapshot at subscription time
    currency                VARCHAR(3) NOT NULL DEFAULT 'INR',
    sub_status              VARCHAR(20) NOT NULL DEFAULT 'active',
    current_period_start    TIMESTAMP NOT NULL,
    current_period_end      TIMESTAMP NOT NULL,
    next_billing_date       TIMESTAMP,                  -- NULL for one-time purchases
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cancelled_at            TIMESTAMP
);

-- Index for user's subscriptions
CREATE INDEX idx_user_subscriptions_user ON user_subscriptions(user_id);

-- Index for billing worker: find subscriptions due for payment
CREATE INDEX idx_user_subscriptions_billing 
ON user_subscriptions(next_billing_date) 
WHERE sub_status = 'active' AND next_billing_date IS NOT NULL;

-- Index for expired subscriptions cleanup
CREATE INDEX idx_user_subscriptions_period_end 
ON user_subscriptions(current_period_end) 
WHERE sub_status = 'active';
```

**Subscription Status Values:**
| Status | Description |
|--------|-------------|
| `trial` | Free trial period |
| `active` | Paid and active |
| `paused` | User paused (can resume) |
| `past_due` | Payment failed, in grace period |
| `cancelled` | User cancelled (may still have access until period_end) |
| `expired` | Access ended |

**Important Fields Explained:**
- `locked_price`: Price at subscription time (won't change even if plan_prices changes)
- `current_period_start/end`: Current billing period (for access control)
- `next_billing_date`: When to charge next (NULL for one-time)
- `cancelled_at`: When user cancelled (for audit)

---

### 5. Payment Transactions

Complete payment history for audit, refunds, and debugging.

```sql
CREATE TABLE payment_transactions (
    transaction_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sub_id                  UUID NOT NULL REFERENCES user_subscriptions(sub_id),
    user_id                 UUID NOT NULL,              -- FK to auth_db.users
    payment_method_id       UUID REFERENCES payment_methods(payment_method_id),
    amount                  DECIMAL(10,2) NOT NULL,
    currency                VARCHAR(3) NOT NULL DEFAULT 'INR',
    status                  VARCHAR(20) NOT NULL,       -- "pending", "success", "failed", "refunded"
    provider_transaction_id VARCHAR(255),               -- Stripe's "pi_xxx" or "ch_xxx"
    failure_reason          TEXT,
    attempt_number          INTEGER NOT NULL DEFAULT 1,
    idempotency_key         VARCHAR(255) NOT NULL,      -- prevent duplicate charges
    billing_period_start    TIMESTAMP NOT NULL,
    billing_period_end      TIMESTAMP NOT NULL,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index for subscription's payment history
CREATE INDEX idx_payment_transactions_sub ON payment_transactions(sub_id);

-- Index for user's payment history
CREATE INDEX idx_payment_transactions_user ON payment_transactions(user_id);

-- Unique constraint on idempotency key (prevent duplicate charges)
CREATE UNIQUE INDEX idx_payment_transactions_idempotency ON payment_transactions(idempotency_key);

-- Index for failed transactions (for retry worker)
CREATE INDEX idx_payment_transactions_failed 
ON payment_transactions(status, created_at) 
WHERE status = 'failed';
```

**Transaction Status Values:**
| Status | Description |
|--------|-------------|
| `pending` | Payment initiated, waiting for provider response |
| `success` | Payment completed successfully |
| `failed` | Payment failed (check failure_reason) |
| `refunded` | Payment was refunded |

---

## Key Design Decisions

### 1. Price Locking
User's price is locked at subscription time in `locked_price` column. If plan_prices changes (festival discount), existing users continue paying their original price.

### 2. Separate Payment Methods Table
- One user can have multiple cards/UPI
- Each subscription can use different payment method
- Old methods kept for payment history reference

### 3. Tokenization (PCI Compliance)
We never store actual card numbers. Only Stripe/Razorpay tokens are stored. If our database is breached, attackers get useless tokens.

### 4. Idempotency Keys
Every payment transaction has unique `idempotency_key` to prevent duplicate charges on retry. Format: `{sub_id}_{billing_period_start}_{attempt_number}`

### 5. Billing Indexes
Specific indexes for billing worker queries:
- Find subscriptions due today
- Find failed payments for retry
- Find expired subscriptions

---

## Common Queries

### Get user's active subscription
```sql
SELECT s.*, p.plan_name, p.plan_features
FROM user_subscriptions s
JOIN plans p ON s.plan_id = p.plan_id
WHERE s.user_id = :user_id 
  AND s.sub_status = 'active'
  AND s.current_period_end > CURRENT_TIMESTAMP;
```

### Get subscriptions due for billing today
```sql
SELECT s.*, pm.provider_token
FROM user_subscriptions s
JOIN payment_methods pm ON s.payment_method_id = pm.payment_method_id
WHERE s.next_billing_date <= CURRENT_TIMESTAMP
  AND s.sub_status = 'active'
  AND s.next_billing_date IS NOT NULL;
```

### Get user's payment history
```sql
SELECT pt.*, p.plan_name
FROM payment_transactions pt
JOIN user_subscriptions s ON pt.sub_id = s.sub_id
JOIN plans p ON s.plan_id = p.plan_id
WHERE pt.user_id = :user_id
ORDER BY pt.created_at DESC;
```

### Check if payment already attempted (idempotency)
```sql
SELECT * FROM payment_transactions
WHERE idempotency_key = :idempotency_key;
```

---

## Future Enhancements (Out of MVP Scope)

1. **Discount/Coupon Table** — Promotional codes, percentage/flat discounts
2. **Plan Features Table** — Normalized features for querying
3. **Subscription History Table** — Track plan changes (upgrades/downgrades)
4. **Invoice Table** — Generate PDF invoices
5. **Tax Configuration** — GST, regional taxes

---

## Related Documents

- [Architecture Overview](./architecture.md)
- [PCI DSS & Tokenization](../questions/payments/pci-dss-tokenization.md)
- [Auth Service DB Design](./auth-service-db-design.md)
