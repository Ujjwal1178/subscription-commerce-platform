# Functions vs Classes - Interview Questions

## Q1: When to use Functions vs Classes?

**Answer:**

| Use | When |
|-----|------|
| **Functions** | Stateless operations - input → output, no memory |
| **Classes** | Stateful operations - need to remember data |

**Functions - Perfect for:**
```python
# No state needed, just transform input to output
hash_password("secret")   # → hashed string
encrypt_data("email")     # → encrypted string
generate_otp()            # → random OTP
calculate_tax(amount)     # → tax amount
```

**Classes - Perfect for:**
```python
# Need to maintain state across operations
class User:
    def __init__(self, name, email):
        self.name = name      # State!
        self.email = email    # State!
    
    def update_email(self, new):
        self.email = new      # Modifies state

class DatabaseConnection:
    def __init__(self, url):
        self.connection = connect(url)  # State!
    
    def query(self, sql):
        return self.connection.execute(sql)
```

---

## Q2: What is "Stateless" vs "Stateful"?

**Answer:**

**Stateless:**
- Function doesn't remember anything between calls
- Same input always gives same output
- No side effects

```python
def add(a, b):
    return a + b  # No state, pure function

add(2, 3)  # → 5
add(2, 3)  # → 5 (always same)
```

**Stateful:**
- Object remembers data between method calls
- Output can depend on internal state
- State can change over time

```python
class Counter:
    def __init__(self):
        self.count = 0  # State!
    
    def increment(self):
        self.count += 1
        return self.count

c = Counter()
c.increment()  # → 1
c.increment()  # → 2 (different output, same call!)
```

---

## Q3: Why not use class for everything?

**Answer:**

**Unnecessary complexity:**

```python
# Overkill - class for stateless operation
class PasswordHasher:
    def __init__(self):
        pass  # Nothing to initialize!
    
    def hash(self, password):
        return bcrypt.hashpw(password)

# Usage (verbose)
hasher = PasswordHasher()
hashed = hasher.hash("secret")
```

```python
# Better - simple function
def hash_password(password):
    return bcrypt.hashpw(password)

# Usage (simple)
hashed = hash_password("secret")
```

**Rule:** Don't force OOP where it's not needed. Simpler code is better code.

---

## Q4: What are the signs you need a class?

**Answer:**

Ask yourself:

| Question | If Yes → |
|----------|----------|
| Do I need to store data between operations? | Class |
| Do I have multiple related functions sharing data? | Class |
| Do I need initialization/configuration? | Class |
| Is it just input → output transformation? | Function |

**Examples:**

```python
# Multiple operations on same data → Class
class ShoppingCart:
    def __init__(self):
        self.items = []
    
    def add_item(self, item):
        self.items.append(item)
    
    def get_total(self):
        return sum(item.price for item in self.items)
    
    def clear(self):
        self.items = []
```

```python
# Just transformations → Functions
def validate_email(email): ...
def format_phone(phone): ...
def calculate_discount(price, percent): ...
```

---

## Q5: What about utility classes with all static methods?

**Answer:**

```python
# Common anti-pattern
class StringUtils:
    @staticmethod
    def uppercase(s):
        return s.upper()
    
    @staticmethod
    def lowercase(s):
        return s.lower()

# Usage
StringUtils.uppercase("hello")
```

**Problem:** This is just a namespace, not real OOP.

**Better approach:**

```python
# Just use a module (file) as namespace
# string_utils.py
def uppercase(s):
    return s.upper()

def lowercase(s):
    return s.lower()

# Usage
from string_utils import uppercase
uppercase("hello")
```

**Modules ARE namespaces in Python!**

---

## Q6: What is a "Pure Function"?

**Answer:**

A function that:
1. Same input → Same output (deterministic)
2. No side effects (doesn't modify external state)

```python
# Pure function ✅
def add(a, b):
    return a + b

# NOT pure ❌ (side effect - modifies external list)
results = []
def add_and_store(a, b):
    result = a + b
    results.append(result)  # Side effect!
    return result

# NOT pure ❌ (depends on external state)
tax_rate = 0.18
def calculate_tax(amount):
    return amount * tax_rate  # Depends on external variable
```

**Pure functions are:**
- Easier to test
- Easier to reason about
- Can be cached/memoized
- Parallelization-friendly

---

## Follow-up Questions:

1. "When would you refactor functions into a class?"
   → When you find yourself passing same data to multiple functions

2. "What's the difference between @staticmethod and regular function?"
   → Functionally same, @staticmethod is just for organizing related functions in a class namespace

3. "Is functional programming better than OOP?"
   → Neither is "better" - use the right tool for the job. Often a mix is best.
