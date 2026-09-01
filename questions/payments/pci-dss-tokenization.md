# PCI DSS Compliance & Payment Tokenization

## Question 1: Why don't you store card details directly in your database?

**Answer:**
Storing card details requires PCI DSS (Payment Card Industry Data Security Standard) compliance which involves:
- Annual security audits costing $50K-500K
- Strict infrastructure requirements (encrypted storage, access controls, network segmentation)
- Legal liability if breached — you're responsible for all fraud
- Dedicated security team and processes

Instead, we use **tokenization** — payment providers like Stripe store the actual card and give us a token (reference ID). We store only the token.

---

## Question 2: How does tokenization work?

**Answer:**
```
User enters card: 4242-4242-4242-4242
           ↓
    [Stripe's Secure Server]
           ↓
Stripe returns token: "tok_1N2abc3XYZ"
           ↓
    [Your Database]
    Stores: token, last_4_digits, card_type (for display)
```

When charging:
```python
stripe.PaymentIntent.create(
    amount=1000,
    currency="inr",
    payment_method="pm_1N2abc3XYZ"  # Token, not actual card
)
```

Our server **never sees** the actual card number. Stripe maps token → card → processes payment.

---

## Question 3: If Stripe stores card details, why isn't compliance a problem for them?

**Answer:**
Stripe IS PCI compliant — they're **PCI Level 1 certified** (highest level).

| Aspect | Your Startup | Stripe |
|--------|--------------|--------|
| Core Business | Subscription platform | Payment processing |
| Security Investment | Limited budget | Hundreds of millions |
| PCI Audit Cost | $50K-500K (painful) | Part of their business model |
| Security Team | 1-2 engineers | 500+ security engineers |
| Infrastructure | Regular cloud servers | HSM (Hardware Security Modules), encrypted vaults |
| If Breached | Startup dies | $100M+ insurance coverage |

**Analogy:** You don't build a bank vault in your house — you use a bank. Similarly, you don't store cards yourself — you use Stripe.

---

## Question 4: What is PCI DSS exactly?

**Answer:**
PCI DSS = Payment Card Industry Data Security Standard

- Created by Visa, Mastercard, Amex, Discover
- **Not a penalty** — it's a security certification
- 12 requirement categories (network security, encryption, access control, monitoring, etc.)
- **Levels based on transaction volume:**
  - Level 1: 6M+ transactions/year (Stripe, Amazon)
  - Level 2: 1M-6M transactions
  - Level 3: 20K-1M transactions
  - Level 4: <20K transactions

---

## Question 5: What do you store in your payment_methods table?

**Answer:**
```sql
payment_methods
├── payment_method_id (PK, UUID)
├── user_id (FK)
├── provider (stripe/razorpay)
├── provider_token (Stripe's token - "pm_xxx")
├── type (card/upi/netbanking)
├── last_4_digits (for display: "Visa ending 4242")
├── card_brand (visa/mastercard/amex)
├── expiry_month
├── expiry_year
├── is_default (boolean)
├── is_deleted (soft delete)
├── created_at
```

**We store:**
- Token (reference to Stripe)
- Display info (last 4 digits, brand)
- Metadata (default card, active/deleted)

**We NEVER store:**
- Full card number
- CVV
- Full expiry in exploitable format

---

## Question 6: User updates their card. Create new record or update existing?

**Answer:**
**Create new record, don't update.**

```
User adds Card A → payment_method_id = 1, is_default = true
User adds Card B → payment_method_id = 2, is_default = true
                   Card A → is_default = false (kept for history)
```

**Why keep old cards?**
1. **Payment history** — Past transactions reference old payment method
2. **User might switch back** — "Use my old card again"
3. **Audit trail** — Legal requirement for financial records
4. **Refunds** — May need to refund to original card

---

## Question 7: User has multiple subscriptions, each with different payment method. How?

**Answer:**
```sql
user_subscriptions
├── sub_id
├── user_id
├── plan_id
├── payment_method_id (FK) ← Links to specific card/UPI
├── ...
```

Each subscription can have its own `payment_method_id`. When charging:
1. Get subscription's `payment_method_id`
2. If NULL, use user's default payment method
3. Charge using that token

---

## Follow-up Questions Interviewer Might Ask:

1. "What happens if user's card expires?"
2. "How do you handle payment failures and retries?"
3. "What if Stripe is down? How do you handle that?"
4. "How do you test payments without real cards?" (Stripe test mode)
5. "What's the difference between Payment Intent and Charge in Stripe?"

---

## Key Terms to Know:

- **PCI DSS** — Security standard for card data
- **Tokenization** — Replace sensitive data with non-sensitive token
- **HSM (Hardware Security Module)** — Specialized hardware for storing encryption keys
- **Payment Intent** — Stripe's modern API for handling payments
- **Idempotency Key** — Prevent duplicate charges on retry
