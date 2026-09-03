# Python OOPs Interview Questions

> For Apple-level backend engineer interviews

---

## Part 1: OOP Fundamentals

### 1. What are the 4 pillars of OOP?

| Pillar | Definition | Python Example |
|--------|------------|----------------|
| **Encapsulation** | Bundling data + methods, hiding internal state | Private attributes with `_` or `__` |
| **Abstraction** | Hiding complexity, showing only essentials | Abstract classes, interfaces |
| **Inheritance** | Creating new class from existing class | `class Child(Parent)` |
| **Polymorphism** | Same interface, different implementations | Method overriding, duck typing |

---

### 2. Explain Encapsulation with example

```python
class BankAccount:
    def __init__(self, balance):
        self.__balance = balance  # Private attribute (name mangling)
    
    def deposit(self, amount):
        if amount > 0:
            self.__balance += amount
    
    def get_balance(self):
        return self.__balance

account = BankAccount(1000)
account.deposit(500)
print(account.get_balance())  # 1500
# print(account.__balance)    # AttributeError!
print(account._BankAccount__balance)  # 1500 (name mangling workaround)
```

**Note:** Python doesn't have true private variables. `__` prefix uses name mangling (`_ClassName__attribute`).

---

### 3. Explain Inheritance types

```python
# Single Inheritance
class Animal:
    def speak(self):
        pass

class Dog(Animal):
    def speak(self):
        return "Woof!"

# Multiple Inheritance
class Flyable:
    def fly(self):
        return "Flying"

class Swimmable:
    def swim(self):
        return "Swimming"

class Duck(Animal, Flyable, Swimmable):
    def speak(self):
        return "Quack!"

# Method Resolution Order (MRO)
print(Duck.__mro__)  # Shows inheritance order
```

---

### 4. What is Polymorphism in Python?

**Duck Typing:** "If it walks like a duck and quacks like a duck, it's a duck"

```python
class Cat:
    def speak(self):
        return "Meow"

class Dog:
    def speak(self):
        return "Woof"

def animal_sound(animal):
    print(animal.speak())  # Works with any object that has speak()

animal_sound(Cat())  # Meow
animal_sound(Dog())  # Woof
```

**Method Overriding:**
```python
class Shape:
    def area(self):
        raise NotImplementedError

class Rectangle(Shape):
    def __init__(self, width, height):
        self.width = width
        self.height = height
    
    def area(self):
        return self.width * self.height

class Circle(Shape):
    def __init__(self, radius):
        self.radius = radius
    
    def area(self):
        return 3.14 * self.radius ** 2
```

---

### 5. Abstract Classes vs Interfaces

```python
from abc import ABC, abstractmethod

# Abstract Class
class PaymentProcessor(ABC):
    def __init__(self, api_key):
        self.api_key = api_key  # Can have state
    
    @abstractmethod
    def process_payment(self, amount):
        pass  # Must be implemented by subclass
    
    def log(self, message):  # Can have concrete methods
        print(f"[LOG] {message}")

class StripeProcessor(PaymentProcessor):
    def process_payment(self, amount):
        self.log(f"Processing ${amount} via Stripe")
        # Stripe-specific implementation
```

**Python doesn't have interfaces like Java.** Use ABC with only abstract methods to simulate.

---

## Part 2: Python Magic Methods (Dunder Methods)

### 6. Common Magic Methods

```python
class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price
    
    def __str__(self):  # For print(), str()
        return f"{self.name}: ${self.price}"
    
    def __repr__(self):  # For debugging, repr()
        return f"Product('{self.name}', {self.price})"
    
    def __eq__(self, other):  # For ==
        return self.name == other.name and self.price == other.price
    
    def __lt__(self, other):  # For <, enables sorting
        return self.price < other.price
    
    def __hash__(self):  # For dict keys, sets
        return hash((self.name, self.price))
    
    def __len__(self):  # For len()
        return len(self.name)

p1 = Product("Phone", 999)
p2 = Product("Phone", 999)
print(p1)           # Phone: $999
print(repr(p1))     # Product('Phone', 999)
print(p1 == p2)     # True
```

---

### 7. Context Managers (`__enter__`, `__exit__`)

```python
class DatabaseConnection:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.connection = None
    
    def __enter__(self):
        print("Opening connection")
        self.connection = "Connected"  # Actual connection logic
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Closing connection")
        self.connection = None
        return False  # Don't suppress exceptions

# Usage
with DatabaseConnection("postgres://localhost") as db:
    print(db.connection)  # Connected
# Connection automatically closed here
```

---

### 8. Callable Objects (`__call__`)

```python
class Multiplier:
    def __init__(self, factor):
        self.factor = factor
    
    def __call__(self, value):
        return value * self.factor

double = Multiplier(2)
triple = Multiplier(3)

print(double(5))   # 10
print(triple(5))   # 15
print(callable(double))  # True
```

---

## Part 3: Class Methods & Static Methods

### 9. `@staticmethod` vs `@classmethod` vs Instance Method

```python
class Pizza:
    base_price = 100  # Class variable
    
    def __init__(self, toppings):
        self.toppings = toppings  # Instance variable
    
    # Instance method: Has access to instance (self)
    def get_price(self):
        return self.base_price + len(self.toppings) * 20
    
    # Class method: Has access to class (cls), not instance
    @classmethod
    def margherita(cls):
        return cls(["cheese", "tomato"])  # Factory method
    
    # Static method: No access to class or instance
    @staticmethod
    def is_valid_topping(topping):
        valid = ["cheese", "tomato", "mushroom", "pepperoni"]
        return topping in valid

# Usage
pizza = Pizza(["cheese", "mushroom"])
print(pizza.get_price())  # 140

margherita = Pizza.margherita()  # Factory pattern
print(Pizza.is_valid_topping("cheese"))  # True
```

---

### 10. Property Decorators

```python
class Temperature:
    def __init__(self, celsius):
        self._celsius = celsius
    
    @property
    def celsius(self):
        return self._celsius
    
    @celsius.setter
    def celsius(self, value):
        if value < -273.15:
            raise ValueError("Temperature below absolute zero!")
        self._celsius = value
    
    @property
    def fahrenheit(self):
        return self._celsius * 9/5 + 32
    
    @fahrenheit.setter
    def fahrenheit(self, value):
        self._celsius = (value - 32) * 5/9

temp = Temperature(25)
print(temp.celsius)     # 25
print(temp.fahrenheit)  # 77.0
temp.fahrenheit = 100   # Sets celsius to 37.78
```

---

## Part 4: Advanced OOP

### 11. Descriptors

```python
class Positive:
    """Descriptor that ensures value is positive"""
    def __set_name__(self, owner, name):
        self.name = name
    
    def __get__(self, obj, objtype=None):
        return obj.__dict__.get(self.name)
    
    def __set__(self, obj, value):
        if value < 0:
            raise ValueError(f"{self.name} must be positive")
        obj.__dict__[self.name] = value

class Product:
    price = Positive()
    quantity = Positive()
    
    def __init__(self, name, price, quantity):
        self.name = name
        self.price = price
        self.quantity = quantity

p = Product("Phone", 999, 10)
# p.price = -100  # Raises ValueError
```

---

### 12. Metaclasses

```python
class SingletonMeta(type):
    """Metaclass that makes a class Singleton"""
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class Database(metaclass=SingletonMeta):
    def __init__(self):
        self.connection = "Connected"

db1 = Database()
db2 = Database()
print(db1 is db2)  # True - same instance
```

---

### 13. `__slots__` for Memory Optimization

```python
class WithoutSlots:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class WithSlots:
    __slots__ = ['x', 'y']  # Only these attributes allowed
    
    def __init__(self, x, y):
        self.x = x
        self.y = y

# WithSlots uses less memory and is slightly faster
# But: No __dict__, can't add new attributes dynamically
```

---

## Part 5: Design Principles (SOLID)

### 14. Single Responsibility Principle

```python
# BAD: Multiple responsibilities
class User:
    def __init__(self, name):
        self.name = name
    
    def save_to_database(self):  # Persistence logic
        pass
    
    def send_email(self):  # Email logic
        pass

# GOOD: Single responsibility
class User:
    def __init__(self, name):
        self.name = name

class UserRepository:
    def save(self, user):
        pass

class EmailService:
    def send_welcome_email(self, user):
        pass
```

---

### 15. Open/Closed Principle

```python
# BAD: Must modify class to add new discount type
class DiscountCalculator:
    def calculate(self, order, discount_type):
        if discount_type == "percentage":
            return order.total * 0.1
        elif discount_type == "fixed":
            return 50
        # Adding new type requires modifying this class

# GOOD: Open for extension, closed for modification
class DiscountStrategy(ABC):
    @abstractmethod
    def calculate(self, order):
        pass

class PercentageDiscount(DiscountStrategy):
    def __init__(self, percent):
        self.percent = percent
    
    def calculate(self, order):
        return order.total * self.percent / 100

class FixedDiscount(DiscountStrategy):
    def __init__(self, amount):
        self.amount = amount
    
    def calculate(self, order):
        return self.amount

# New discount? Just add new class, don't modify existing code
class BuyOneGetOneDiscount(DiscountStrategy):
    def calculate(self, order):
        return order.cheapest_item_price
```

---

### 16. Dependency Inversion Principle

```python
# BAD: High-level module depends on low-level module
class MySQLDatabase:
    def save(self, data):
        print("Saving to MySQL")

class UserService:
    def __init__(self):
        self.db = MySQLDatabase()  # Tightly coupled

# GOOD: Both depend on abstraction
class Database(ABC):
    @abstractmethod
    def save(self, data):
        pass

class MySQLDatabase(Database):
    def save(self, data):
        print("Saving to MySQL")

class PostgresDatabase(Database):
    def save(self, data):
        print("Saving to Postgres")

class UserService:
    def __init__(self, db: Database):  # Inject dependency
        self.db = db
    
    def create_user(self, data):
        self.db.save(data)

# Easy to swap databases
service = UserService(PostgresDatabase())
```

---

## Part 6: Common Interview Questions

### 17. What is `self` in Python?

`self` is a reference to the current instance of the class. It's passed automatically when calling instance methods.

```python
class MyClass:
    def method(self):
        print(id(self))

obj = MyClass()
obj.method()      # Automatically passes obj as self
MyClass.method(obj)  # Explicit call, same result
```

---

### 18. What is `super()`?

```python
class Parent:
    def __init__(self, name):
        self.name = name

class Child(Parent):
    def __init__(self, name, age):
        super().__init__(name)  # Call parent's __init__
        self.age = age
```

**In multiple inheritance, `super()` follows MRO (Method Resolution Order).**

---

### 19. Difference between `is` and `==`

```python
a = [1, 2, 3]
b = [1, 2, 3]
c = a

print(a == b)  # True (same value)
print(a is b)  # False (different objects)
print(a is c)  # True (same object)
```

- `==` compares values (calls `__eq__`)
- `is` compares identity (memory address)

---

### 20. What are Mixins?

```python
# Mixins add functionality without being a "parent" conceptually
class JSONSerializableMixin:
    def to_json(self):
        import json
        return json.dumps(self.__dict__)

class XMLSerializableMixin:
    def to_xml(self):
        return f"<object>{self.__dict__}</object>"

class User(JSONSerializableMixin, XMLSerializableMixin):
    def __init__(self, name, email):
        self.name = name
        self.email = email

user = User("John", "john@example.com")
print(user.to_json())  # {"name": "John", "email": "john@example.com"}
```

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────┐
│           PYTHON OOP INTERVIEW CHECKLIST        │
├─────────────────────────────────────────────────┤
│ 4 Pillars:    Encapsulation, Abstraction,       │
│               Inheritance, Polymorphism         │
│                                                 │
│ Magic Methods: __init__, __str__, __repr__,     │
│               __eq__, __hash__, __call__,       │
│               __enter__, __exit__               │
│                                                 │
│ Decorators:   @property, @classmethod,          │
│               @staticmethod, @abstractmethod    │
│                                                 │
│ SOLID:        Single Responsibility,            │
│               Open/Closed, Liskov,              │
│               Interface Segregation,            │
│               Dependency Inversion              │
│                                                 │
│ Advanced:     Descriptors, Metaclasses,         │
│               __slots__, MRO                    │
└─────────────────────────────────────────────────┘
```
