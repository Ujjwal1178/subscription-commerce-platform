# Subscription Service — API Design Document

## Overview

This document defines all APIs for the Subscription Service. The service handles:
- Plan management (Admin)
- Plan pricing (Admin)
- User subscriptions (User)
- Payment methods (User)

**Base URL:** `/api/v1`

---

## Non-Functional Requirements

### Latency Targets

| Operation Type | Target | Reasoning |
|----------------|--------|-----------|
| **Read APIs** (list plans, get subscription) | < 100ms | Simple DB reads, user expects instant |
| **Write APIs** (subscribe, upgrade, cancel) | < 500ms | DB transactions + external calls (payment) |

### Throughput

| Metric | Target |
|--------|--------|
| Requests per second | 15,000 RPS |
| Peak handling | 3-5x normal traffic |

### Availability

| Target | Downtime/Year | Why |
|--------|---------------|-----|
| **99.99%** | ~52 minutes | Revenue-critical, in signup path |

### Consistency

| Operation | Consistency | Why |
|-----------|-------------|-----|
| Subscribe/Upgrade/Cancel | **STRONG** | Money + access control involved |
| List Plans | Eventual OK | Plans rarely change |
| Subscription History | Eventual OK | Historical, delay acceptable |

### Security

| Asset | Protection |
|-------|------------|
| Payment tokens | Encrypted at rest, never logged |
| API endpoints | JWT auth, role-based (user/admin) |
| Admin APIs | Separate role, audit logging |
| All traffic | HTTPS only |

### Scalability

| Component | Strategy |
|-----------|----------|
| Service | Horizontal scaling (stateless pods) |
| DB Reads | Read replicas |
| DB Writes | Vertical → Sharding by user_id |
| Hot Data | Redis cache (plans, session) |
| Async Ops | Kafka (emails, analytics)

---

## 1. Plans APIs (Admin Only)

### 1.1 Create Plan

```
POST /api/v1/plans
```

**Description:** Create a new subscription plan.

**Headers:**
```
Authorization: Bearer <admin_jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "plan_name": "Premium",
  "plan_type": "premium",
  "plan_features": {
    "screens": 4,
    "quality": "4k",
    "downloads": 25,
    "ads": false
  }
}
```

**Success Response (201):**
```json
{
  "success": true,
  "message": "Plan created successfully.",
  "plan": {
    "plan_id": "uuid-xxx",
    "plan_name": "Premium",
    "plan_type": "premium",
    "plan_features": {
      "screens": 4,
      "quality": "4k",
      "downloads": 25,
      "ads": false
    },
    "is_active": true,
    "created_at": "2026-09-01T10:00:00Z"
  }
}
```

**Error Responses:**
- `400` — Invalid input (missing fields, invalid JSON)
- `401` — Unauthorized (no token)
- `403` — Forbidden (not admin)
- `409` — Plan name already exists

---

### 1.2 List All Plans

```
GET /api/v1/plans
```

**Description:** Get all available plans. Public API — no auth required.

**Query Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `active_only` | boolean | No | Default `true`. Set `false` to include inactive plans (admin) |

**Success Response (200):**
```json
{
  "success": true,
  "plans": [
    {
      "plan_id": "uuid-free",
      "plan_name": "Free",
      "plan_type": "basic",
      "plan_features": {
        "screens": 1,
        "quality": "480p",
        "downloads": 0,
        "ads": true
      },
      "is_active": true
    },
    {
      "plan_id": "uuid-premium",
      "plan_name": "Premium",
      "plan_type": "premium",
      "plan_features": {
        "screens": 4,
        "quality": "4k",
        "downloads": 25,
        "ads": false
      },
      "is_active": true
    }
  ]
}
```

---

### 1.3 Get Plan Details

```
GET /api/v1/plans/{plan_id}
```

**Description:** Get details of a specific plan including its prices.

**Path Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `plan_id` | UUID | Yes | Plan identifier |

**Success Response (200):**
```json
{
  "success": true,
  "plan": {
    "plan_id": "uuid-premium",
    "plan_name": "Premium",
    "plan_type": "premium",
    "plan_features": {
      "screens": 4,
      "quality": "4k",
      "downloads": 25,
      "ads": false
    },
    "is_active": true,
    "created_at": "2026-09-01T10:00:00Z",
    "prices": [
      {
        "price_id": "uuid-p1",
        "billing_cycle": "monthly",
        "duration_months": 1,
        "amount": 499.00,
        "currency": "INR",
        "is_recurring": true
      },
      {
        "price_id": "uuid-p2",
        "billing_cycle": "yearly",
        "duration_months": 12,
        "amount": 4999.00,
        "currency": "INR",
        "is_recurring": false
      }
    ]
  }
}
```

**Error Responses:**
- `404` — Plan not found

---

### 1.4 Update Plan

```
PUT /api/v1/plans/{plan_id}
```

**Description:** Update plan details. Admin only.

**Headers:**
```
Authorization: Bearer <admin_jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "plan_name": "Premium Plus",
  "plan_features": {
    "screens": 5,
    "quality": "4k",
    "downloads": 50,
    "ads": false
  },
  "is_active": true
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Plan updated successfully.",
  "plan": {
    "plan_id": "uuid-premium",
    "plan_name": "Premium Plus",
    "plan_features": {
      "screens": 5,
      "quality": "4k",
      "downloads": 50,
      "ads": false
    },
    "is_active": true,
    "updated_at": "2026-09-01T12:00:00Z"
  }
}
```

**Error Responses:**
- `400` — Invalid input
- `401` — Unauthorized
- `403` — Forbidden (not admin)
- `404` — Plan not found

---

### 1.5 Delete Plan

```
DELETE /api/v1/plans/{plan_id}
```

**Description:** Soft delete a plan (set `is_active = false`). Admin only.

**Headers:**
```
Authorization: Bearer <admin_jwt_token>
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Plan deleted successfully."
}
```

**Error Responses:**
- `401` — Unauthorized
- `403` — Forbidden (not admin)
- `404` — Plan not found
- `409` — Cannot delete: active subscriptions exist

---

## 2. Plan Prices APIs (Admin Only)

### 2.1 Add Price to Plan

```
POST /api/v1/plans/{plan_id}/prices
```

**Description:** Add a pricing option to a plan.

**Headers:**
```
Authorization: Bearer <admin_jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "billing_cycle": "monthly",
  "duration_months": 1,
  "amount": 499.00,
  "currency": "INR",
  "is_recurring": true
}
```

**Success Response (201):**
```json
{
  "success": true,
  "message": "Price added successfully.",
  "price": {
    "price_id": "uuid-price-1",
    "plan_id": "uuid-premium",
    "billing_cycle": "monthly",
    "duration_months": 1,
    "amount": 499.00,
    "currency": "INR",
    "is_recurring": true,
    "created_at": "2026-09-01T10:00:00Z"
  }
}
```

**Error Responses:**
- `400` — Invalid input
- `401` — Unauthorized
- `403` — Forbidden (not admin)
- `404` — Plan not found
- `409` — Price for this cycle/currency already exists

---

### 2.2 List Prices for Plan

```
GET /api/v1/plans/{plan_id}/prices
```

**Description:** Get all pricing options for a plan. Public API.

**Success Response (200):**
```json
{
  "success": true,
  "prices": [
    {
      "price_id": "uuid-p1",
      "billing_cycle": "monthly",
      "duration_months": 1,
      "amount": 499.00,
      "currency": "INR",
      "is_recurring": true
    },
    {
      "price_id": "uuid-p2",
      "billing_cycle": "yearly",
      "duration_months": 12,
      "amount": 4999.00,
      "currency": "INR",
      "is_recurring": false
    }
  ]
}
```

---

### 2.3 Update Price

```
PUT /api/v1/prices/{price_id}
```

**Description:** Update a price. Admin only. Note: This affects NEW subscriptions only, not existing ones (locked_price).

**Headers:**
```
Authorization: Bearer <admin_jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "amount": 599.00
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Price updated successfully.",
  "price": {
    "price_id": "uuid-p1",
    "amount": 599.00,
    "updated_at": "2026-09-01T12:00:00Z"
  }
}
```

**Error Responses:**
- `400` — Invalid input
- `401` — Unauthorized
- `403` — Forbidden (not admin)
- `404` — Price not found

---

### 2.4 Delete Price

```
DELETE /api/v1/prices/{price_id}
```

**Description:** Remove a pricing option. Admin only.

**Headers:**
```
Authorization: Bearer <admin_jwt_token>
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Price deleted successfully."
}
```

**Error Responses:**
- `401` — Unauthorized
- `403` — Forbidden (not admin)
- `404` — Price not found

---

## 3. User Subscriptions APIs

### 3.1 Create Subscription

```
POST /api/v1/subscriptions
```

**Description:** Create a new subscription for user. Called internally by Auth Service when user registers (creates free tier subscription).

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "plan_id": "uuid-free-plan",
  "price_id": "uuid-free-price",
  "payment_method_id": null
}
```

**Success Response (201):**
```json
{
  "success": true,
  "message": "Subscription created successfully.",
  "subscription": {
    "sub_id": "uuid-sub-1",
    "user_id": "uuid-user-1",
    "plan_id": "uuid-free-plan",
    "plan_name": "Free",
    "locked_price": 0.00,
    "currency": "INR",
    "sub_status": "active",
    "current_period_start": "2026-09-01T00:00:00Z",
    "current_period_end": "2026-10-01T00:00:00Z",
    "next_billing_date": null,
    "created_at": "2026-09-01T10:00:00Z"
  }
}
```

**Error Responses:**
- `400` — Invalid input
- `401` — Unauthorized
- `404` — Plan or price not found
- `409` — User already has active subscription

---

### 3.2 Get My Subscription

```
GET /api/v1/subscriptions/me
```

**Description:** Get current user's active subscription.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Success Response (200):**
```json
{
  "success": true,
  "subscription": {
    "sub_id": "uuid-sub-1",
    "plan": {
      "plan_id": "uuid-premium",
      "plan_name": "Premium",
      "plan_features": {
        "screens": 4,
        "quality": "4k",
        "downloads": 25,
        "ads": false
      }
    },
    "price": {
      "billing_cycle": "monthly",
      "amount": 499.00,
      "currency": "INR",
      "is_recurring": true
    },
    "locked_price": 499.00,
    "sub_status": "active",
    "current_period_start": "2026-09-01T00:00:00Z",
    "current_period_end": "2026-10-01T00:00:00Z",
    "next_billing_date": "2026-10-01T00:00:00Z",
    "payment_method": {
      "payment_method_id": "uuid-pm-1",
      "type": "card",
      "last_4_digits": "4242",
      "card_brand": "visa"
    }
  }
}
```

**Error Responses:**
- `401` — Unauthorized
- `404` — No active subscription found

---

### 3.3 Change Plan (Upgrade/Downgrade)

```
POST /api/v1/subscriptions/change-plan
```

**Description:** Change to a different plan. Backend determines if it's upgrade (charge proration) or downgrade (effective next cycle).

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "new_plan_id": "uuid-premium",
  "new_price_id": "uuid-price-monthly",
  "payment_method_id": "uuid-pm-1"
}
```

**Success Response (200) — Upgrade:**
```json
{
  "success": true,
  "message": "Plan upgraded successfully. Proration charged.",
  "subscription": {
    "sub_id": "uuid-sub-1",
    "plan_name": "Premium",
    "sub_status": "active",
    "locked_price": 499.00,
    "current_period_end": "2026-10-01T00:00:00Z",
    "next_billing_date": "2026-10-01T00:00:00Z"
  },
  "proration": {
    "amount_charged": 160.00,
    "days_remaining": 16,
    "calculation": "(499 - 199) × (16/30) = 160"
  }
}
```

**Success Response (200) — Downgrade:**
```json
{
  "success": true,
  "message": "Plan will be downgraded at end of current billing period.",
  "subscription": {
    "sub_id": "uuid-sub-1",
    "plan_name": "Premium",
    "sub_status": "active",
    "scheduled_plan_change": {
      "new_plan_name": "Basic",
      "effective_date": "2026-10-01T00:00:00Z"
    }
  }
}
```

**Error Responses:**
- `400` — Invalid input / Same plan selected
- `401` — Unauthorized
- `402` — Payment required (proration charge failed)
- `404` — Plan or price not found

---

### 3.4 Pause Subscription

```
POST /api/v1/subscriptions/pause
```

**Description:** Pause an active subscription. User retains access until current period ends, then access stops. No billing during pause.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "reason": "Taking a break"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Subscription paused. Access continues until current period ends.",
  "subscription": {
    "sub_id": "uuid-sub-1",
    "sub_status": "paused",
    "current_period_end": "2026-10-01T00:00:00Z",
    "paused_at": "2026-09-15T10:00:00Z"
  }
}
```

**Error Responses:**
- `400` — Cannot pause (already paused, free tier, etc.)
- `401` — Unauthorized
- `404` — No active subscription

---

### 3.5 Resume Subscription

```
POST /api/v1/subscriptions/resume
```

**Description:** Resume a paused subscription. Billing resumes from next cycle.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Subscription resumed. Billing will resume on next cycle.",
  "subscription": {
    "sub_id": "uuid-sub-1",
    "sub_status": "active",
    "next_billing_date": "2026-10-01T00:00:00Z",
    "resumed_at": "2026-09-20T10:00:00Z"
  }
}
```

**Error Responses:**
- `400` — Cannot resume (not paused)
- `401` — Unauthorized
- `402` — Payment method required

---

### 3.6 Cancel Subscription

```
POST /api/v1/subscriptions/cancel
```

**Description:** Cancel subscription. User moves to free tier at end of current period. No refund.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Request Body:**
```json
{
  "reason": "Too expensive",
  "feedback": "Would return if price was lower"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Subscription cancelled. Access continues until period end, then moves to Free tier.",
  "subscription": {
    "sub_id": "uuid-sub-1",
    "sub_status": "cancelled",
    "current_period_end": "2026-10-01T00:00:00Z",
    "cancelled_at": "2026-09-15T10:00:00Z",
    "will_move_to": "Free"
  }
}
```

**Error Responses:**
- `400` — Cannot cancel (already cancelled, free tier)
- `401` — Unauthorized

---

### 3.7 Get Subscription History

```
GET /api/v1/subscriptions/history
```

**Description:** Get user's subscription history (past and current).

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Query Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `page` | int | No | Default 1 |
| `limit` | int | No | Default 10, max 50 |

**Success Response (200):**
```json
{
  "success": true,
  "history": [
    {
      "sub_id": "uuid-sub-2",
      "plan_name": "Premium",
      "sub_status": "active",
      "locked_price": 499.00,
      "current_period_start": "2026-09-01T00:00:00Z",
      "current_period_end": "2026-10-01T00:00:00Z"
    },
    {
      "sub_id": "uuid-sub-1",
      "plan_name": "Basic",
      "sub_status": "cancelled",
      "locked_price": 199.00,
      "current_period_start": "2026-08-01T00:00:00Z",
      "current_period_end": "2026-09-01T00:00:00Z",
      "cancelled_at": "2026-08-25T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 2
  }
}
```

---

### 3.8 Delete Subscription (Admin Only)

```
DELETE /api/v1/subscriptions/{sub_id}
```

**Description:** Hard delete a subscription record. Admin only. Use with caution.

**Headers:**
```
Authorization: Bearer <admin_jwt_token>
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Subscription deleted."
}
```

**Error Responses:**
- `401` — Unauthorized
- `403` — Forbidden (not admin)
- `404` — Subscription not found

---

## 4. Payment Methods APIs

### 4.1 Add Payment Method

```
POST /api/v1/payment-methods
```

**Description:** Add a new payment method (card/UPI). Frontend sends Stripe token, not actual card details.

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "provider_token": "pm_1N2abc3XYZ",
  "type": "card",
  "set_as_default": true
}
```

**Success Response (201):**
```json
{
  "success": true,
  "message": "Payment method added successfully.",
  "payment_method": {
    "payment_method_id": "uuid-pm-1",
    "type": "card",
    "last_4_digits": "4242",
    "card_brand": "visa",
    "expiry_month": 12,
    "expiry_year": 2028,
    "is_default": true,
    "created_at": "2026-09-01T10:00:00Z"
  }
}
```

**Error Responses:**
- `400` — Invalid token / Stripe validation failed
- `401` — Unauthorized

---

### 4.2 List Payment Methods

```
GET /api/v1/payment-methods
```

**Description:** Get all payment methods for current user.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Success Response (200):**
```json
{
  "success": true,
  "payment_methods": [
    {
      "payment_method_id": "uuid-pm-1",
      "type": "card",
      "last_4_digits": "4242",
      "card_brand": "visa",
      "expiry_month": 12,
      "expiry_year": 2028,
      "is_default": true
    },
    {
      "payment_method_id": "uuid-pm-2",
      "type": "upi",
      "upi_id": "user@okicici",
      "is_default": false
    }
  ]
}
```

---

### 4.3 Get Payment Method

```
GET /api/v1/payment-methods/{payment_method_id}
```

**Description:** Get details of a specific payment method.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Success Response (200):**
```json
{
  "success": true,
  "payment_method": {
    "payment_method_id": "uuid-pm-1",
    "type": "card",
    "last_4_digits": "4242",
    "card_brand": "visa",
    "expiry_month": 12,
    "expiry_year": 2028,
    "is_default": true,
    "created_at": "2026-09-01T10:00:00Z"
  }
}
```

**Error Responses:**
- `401` — Unauthorized
- `403` — Not your payment method
- `404` — Payment method not found

---

### 4.4 Set Default Payment Method

```
PATCH /api/v1/payment-methods/{payment_method_id}/default
```

**Description:** Set a payment method as default for billing.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Payment method set as default.",
  "payment_method": {
    "payment_method_id": "uuid-pm-1",
    "is_default": true
  }
}
```

**Error Responses:**
- `401` — Unauthorized
- `403` — Not your payment method
- `404` — Payment method not found

---

### 4.5 Delete Payment Method

```
DELETE /api/v1/payment-methods/{payment_method_id}
```

**Description:** Remove a payment method. Cannot delete if it's the only method on an active paid subscription.

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Payment method removed."
}
```

**Error Responses:**
- `400` — Cannot delete (only payment method on active subscription)
- `401` — Unauthorized
- `403` — Not your payment method
- `404` — Payment method not found

---

## Summary

| Category | Count | Auth Required |
|----------|-------|---------------|
| Plans | 5 | Admin (except list/get) |
| Plan Prices | 4 | Admin (except list) |
| Subscriptions | 8 | User (delete = Admin) |
| Payment Methods | 5 | User |
| **Total** | **22** | |

---

## Related Documents

- [Database Design](./subscription-service-db-design.md)
- [Architecture Overview](./architecture.md)
- [PCI DSS & Tokenization](../questions/payments/pci-dss-tokenization.md)
