# Functional vs Non-Functional Requirements

## Question
**"What's the difference between functional and non-functional requirements? Give examples from a system you've built."**

---

## Core Difference

| Aspect | Functional (FR) | Non-Functional (NFR) |
|--------|-----------------|---------------------|
| Defines | **WHAT** system does | **HOW WELL** it does |
| Focus | Features, behaviors | Quality attributes |
| Testable by | Feature works? YES/NO | Metrics (latency, uptime) |
| Example | "User can login" | "Login < 500ms" |

---

## Simple Rule

```
Functional   = "Can the user do X?"
Non-Functional = "How fast/secure/reliable is X?"
```

---

## Examples from Auth Service

### Functional Requirements:
| Requirement | Why Functional? |
|-------------|-----------------|
| User can register with email | It's a feature/action |
| User can login | Action |
| User can reset password via OTP | Action + flow |
| Block user after 3 wrong OTPs | Business rule |
| Single device login (logout old device) | Business rule |
| Unverified user must verify before reset | Business logic |
| OTP expires in 10 minutes | Business rule |

### Non-Functional Requirements:
| Requirement | Category | Why Non-Functional? |
|-------------|----------|---------------------|
| Login response < 500ms | Performance | Quality metric |
| Handle 10K concurrent users | Scalability | Capacity |
| 99.9% uptime | Availability | Reliability metric |
| Passwords hashed with bcrypt (cost 12) | Security | How secure |
| PII encrypted with AES-256 | Security | How secure |
| Logs must not contain passwords | Security/Compliance | Constraint |
| API works on mobile + web | Compatibility | Platform support |
| Data encrypted at rest and in transit | Security | Constraint |

---

## Trick Question: Is Security FR or NFR?

**Answer: BOTH!**

- **Functional:** "User must enter OTP to verify email" → Action/behavior
- **Non-Functional:** "OTP must be hashed before storing" → How securely

---

## Categories of Non-Functional Requirements

| Category | Examples |
|----------|----------|
| **Performance** | Response time, throughput |
| **Scalability** | Users, data volume, geographic |
| **Availability** | Uptime (99.9%), failover |
| **Security** | Encryption, authentication strength |
| **Reliability** | Error rates, data integrity |
| **Maintainability** | Code quality, documentation |
| **Usability** | Accessibility, learning curve |
| **Compliance** | GDPR, PCI-DSS, HIPAA |

---

## Interview Follow-ups

### Q1: "How do you gather requirements?"
> "I start with functional requirements - what features users need. Then I define non-functional requirements based on expected load, security needs, and business constraints. For auth service, I identified features like login/register, then set targets like <500ms latency and bcrypt for passwords."

### Q2: "How do you prioritize NFRs?"
> "Based on business impact:
> 1. Security - Non-negotiable for auth
> 2. Availability - Users can't login = business stops
> 3. Performance - Affects user experience
> 4. Scalability - Plan for growth"

### Q3: "What happens if NFRs conflict?"
Example: Security vs Performance
- Bcrypt with cost 20 = Very secure but slow
- Bcrypt with cost 8 = Fast but less secure

> "I find the balance. Cost 12 gives ~300ms hash time - secure enough for production while meeting performance targets."

### Q4: "How do you test NFRs?"
> "Different from functional testing:
> - Performance: Load testing (k6, JMeter)
> - Scalability: Stress testing, auto-scale verification
> - Security: Penetration testing, code audit
> - Availability: Chaos engineering, failover drills"

---

## Real-World Example: Our Auth Service

**Functional:**
```
- User can register with email, name, phone, password
- User receives OTP for email verification
- User can login after verification
- User can reset password via 3-step flow
- System blocks user after 3 wrong OTP attempts
```

**Non-Functional:**
```
- Login latency < 500ms
- OTP verification < 100ms (rate limit check)
- Support 1000 concurrent logins
- 99.9% availability
- bcrypt cost factor 12
- AES-256 for PII encryption
- Rate limiting: 10 requests/minute per IP
- Session history retained for 30 days
```

---

## Interview Answer Template

> "Functional requirements define what the system does - features like login, register, password reset. Non-functional requirements define how well it does them - performance targets, security standards, scalability needs.
>
> In my auth service, functional requirements included features like 3-step forgot password and single-device login. Non-functional requirements specified <500ms response time, bcrypt with cost 12 for passwords, and AES encryption for PII.
>
> The key is that functional requirements are testable as YES/NO (does login work?), while non-functional requirements are measured against metrics (is login under 500ms?)."

---

## Code Reference
This project demonstrates both types:
- **Functional:** All 9 API endpoints with business logic
- **Non-Functional:** bcrypt, AES, rate limiting, connection pooling
