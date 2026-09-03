# Low-Level Design (LLD) & Machine Coding Interview Questions

> Sources: geeksforgeeks.org, workat.tech, algomaster.io, github.com/ashishps1/awesome-low-level-design (Content rephrased for compliance with licensing restrictions)

---

## What is LLD/Machine Coding Round?

- **Time:** 45-90 minutes
- **Focus:** Design classes, interfaces, and relationships for a given problem
- **Language:** Usually your choice (Python, Java, C++)
- **Evaluation:** OOP principles, code structure, extensibility, edge cases

---

## Top Priority LLD Problems (Must Practice)

### 1. Design Parking Lot System

**Requirements:**
- Multiple floors, each with different slot types
- Slot types: Compact, Large, Handicapped, Motorcycle
- Vehicle types: Car, Bike, Truck
- Entry/exit with ticketing
- Payment based on duration

**Classes to Design:**
```python
class ParkingLot:
    floors: List[ParkingFloor]
    
class ParkingFloor:
    floor_number: int
    slots: List[ParkingSlot]
    
class ParkingSlot:
    slot_id: str
    slot_type: SlotType  # COMPACT, LARGE, HANDICAPPED
    is_available: bool
    vehicle: Optional[Vehicle]
    
class Vehicle:
    license_plate: str
    vehicle_type: VehicleType
    
class Ticket:
    ticket_id: str
    vehicle: Vehicle
    slot: ParkingSlot
    entry_time: datetime
    
class Payment:
    calculate_fee(ticket: Ticket) -> float
```

**Key Concepts:**
- Strategy pattern for different pricing
- Factory pattern for creating vehicles
- Thread-safety for concurrent entry/exit

---

### 2. Design Movie Ticket Booking (BookMyShow)

**Requirements:**
- Browse movies by city
- View showtimes and theaters
- Select seats
- Book tickets with payment
- Handle concurrent bookings (seat locking)

**Classes:**
```python
class Movie:
    movie_id: str
    name: str
    duration: int
    genre: str

class Theater:
    theater_id: str
    name: str
    city: str
    screens: List[Screen]

class Screen:
    screen_id: str
    seats: List[Seat]

class Seat:
    seat_id: str
    row: str
    number: int
    seat_type: SeatType  # REGULAR, PREMIUM, RECLINER
    
class Show:
    show_id: str
    movie: Movie
    screen: Screen
    start_time: datetime
    available_seats: List[Seat]

class Booking:
    booking_id: str
    show: Show
    seats: List[Seat]
    user: User
    status: BookingStatus  # PENDING, CONFIRMED, CANCELLED
```

**Key Challenges:**
- Concurrent seat booking (pessimistic locking)
- Seat hold timeout (temporary reservation)
- Payment failure rollback

---

### 3. Design Splitwise (Expense Sharing)

**Requirements:**
- Add users and groups
- Add expenses with different split types
- Equal split, exact amounts, percentage split
- Track balances between users
- Settle balances

**Classes:**
```python
class User:
    user_id: str
    name: str
    email: str
    balances: Dict[str, float]  # user_id -> amount owed

class Group:
    group_id: str
    name: str
    members: List[User]
    expenses: List[Expense]

class Expense:
    expense_id: str
    description: str
    amount: float
    paid_by: User
    split_type: SplitType
    splits: List[Split]

class Split(ABC):
    user: User
    
class EqualSplit(Split):
    pass
    
class ExactSplit(Split):
    amount: float
    
class PercentSplit(Split):
    percent: float
```

**Key Concepts:**
- Strategy pattern for split calculation
- Graph simplification for settlements (min transactions)

---

### 4. Design Elevator System

**Requirements:**
- Multiple elevators in a building
- Handle floor requests (inside and outside)
- Optimize for minimum wait time
- Handle different elevator algorithms

**Classes:**
```python
class Building:
    elevators: List[Elevator]
    floors: int
    
class Elevator:
    elevator_id: int
    current_floor: int
    direction: Direction  # UP, DOWN, IDLE
    requests: List[Request]
    
class Request:
    source_floor: int
    destination_floor: int
    direction: Direction

class ElevatorController:
    def request_elevator(floor: int, direction: Direction) -> Elevator
    def move_elevator(elevator: Elevator)
```

**Algorithms:**
- FCFS (First Come First Serve)
- SCAN (Elevator moves in one direction, then reverses)
- LOOK (Like SCAN but doesn't go to end if no requests)

---

### 5. Design LRU Cache

**Requirements:**
- Fixed capacity cache
- O(1) get and put operations
- Evict least recently used when full

**Implementation:**
```python
class Node:
    key: int
    value: int
    prev: Optional[Node]
    next: Optional[Node]

class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.cache = {}  # key -> Node
        self.head = Node(0, 0)  # dummy head
        self.tail = Node(0, 0)  # dummy tail
        self.head.next = self.tail
        self.tail.prev = self.head
    
    def get(self, key: int) -> int:
        if key in self.cache:
            node = self.cache[key]
            self._remove(node)
            self._add(node)
            return node.value
        return -1
    
    def put(self, key: int, value: int):
        if key in self.cache:
            self._remove(self.cache[key])
        node = Node(key, value)
        self._add(node)
        self.cache[key] = node
        if len(self.cache) > self.capacity:
            lru = self.head.next
            self._remove(lru)
            del self.cache[lru.key]
```

**Data Structure:** HashMap + Doubly Linked List

---

### 6. Design Rate Limiter

**Requirements:**
- Limit requests per user/IP
- Different limits for different endpoints
- Return remaining quota

**Algorithms:**

**Token Bucket:**
```python
class TokenBucket:
    def __init__(self, capacity: int, refill_rate: int):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.time()
    
    def allow_request(self) -> bool:
        self._refill()
        if self.tokens > 0:
            self.tokens -= 1
            return True
        return False
    
    def _refill(self):
        now = time.time()
        tokens_to_add = (now - self.last_refill) * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
```

---

### 7. Design Logging Framework (log4j style)

**Requirements:**
- Multiple log levels (DEBUG, INFO, WARN, ERROR)
- Multiple outputs (Console, File, Database)
- Configurable formatters
- Thread-safe

**Classes:**
```python
class LogLevel(Enum):
    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4

class Logger:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Logger()
        return cls._instance
    
    def __init__(self):
        self.handlers: List[LogHandler] = []
        self.level = LogLevel.INFO
    
    def log(self, level: LogLevel, message: str):
        if level.value >= self.level.value:
            for handler in self.handlers:
                handler.handle(level, message)

class LogHandler(ABC):
    @abstractmethod
    def handle(self, level: LogLevel, message: str): pass

class ConsoleHandler(LogHandler):
    def handle(self, level, message):
        print(f"[{level.name}] {message}")

class FileHandler(LogHandler):
    def __init__(self, filename: str):
        self.filename = filename
    
    def handle(self, level, message):
        with open(self.filename, 'a') as f:
            f.write(f"[{level.name}] {message}\n")
```

**Design Patterns:** Singleton, Chain of Responsibility, Strategy

---

### 8. Design Snake and Ladder Game

**Requirements:**
- Multiple players
- Board with snakes and ladders
- Dice roll
- Win condition

**Classes:**
```python
class Board:
    size: int
    snakes: Dict[int, int]   # head -> tail
    ladders: Dict[int, int]  # bottom -> top

class Player:
    name: str
    position: int

class Dice:
    def roll(self) -> int:
        return random.randint(1, 6)

class Game:
    board: Board
    players: List[Player]
    current_player_index: int
    
    def play_turn(self):
        roll = self.dice.roll()
        player = self.players[self.current_player_index]
        new_position = player.position + roll
        
        # Check for snake or ladder
        if new_position in self.board.snakes:
            new_position = self.board.snakes[new_position]
        elif new_position in self.board.ladders:
            new_position = self.board.ladders[new_position]
        
        player.position = new_position
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
```

---

### 9. Design Wallet System (Paytm/PhonePe)

**Requirements:**
- Add money to wallet
- Transfer money between users
- Transaction history
- Handle concurrent transactions

**Classes:**
```python
class Wallet:
    wallet_id: str
    user: User
    balance: float
    transactions: List[Transaction]
    
    def add_money(self, amount: float) -> Transaction
    def transfer(self, to_wallet: Wallet, amount: float) -> Transaction
    def get_balance(self) -> float

class Transaction:
    transaction_id: str
    from_wallet: Optional[Wallet]
    to_wallet: Optional[Wallet]
    amount: float
    type: TransactionType  # CREDIT, DEBIT, TRANSFER
    timestamp: datetime
    status: TransactionStatus
```

**Key Challenge:** ACID transactions for transfers (both debit and credit must succeed)

---

### 10. Design In-Memory File System

**Requirements:**
- Create files and directories
- Read/write files
- Navigate directories (cd, ls, pwd)
- Delete files/directories

**Classes:**
```python
class FileSystemNode(ABC):
    name: str
    parent: Optional[Directory]

class File(FileSystemNode):
    content: str
    
    def read(self) -> str
    def write(self, content: str)

class Directory(FileSystemNode):
    children: Dict[str, FileSystemNode]
    
    def add(self, node: FileSystemNode)
    def remove(self, name: str)
    def list(self) -> List[str]

class FileSystem:
    root: Directory
    current: Directory
    
    def mkdir(self, path: str)
    def touch(self, path: str)
    def cd(self, path: str)
    def ls(self) -> List[str]
    def pwd(self) -> str
```

**Design Pattern:** Composite pattern

---

## More LLD Problems (Medium Priority)

| # | Problem | Key Concepts |
|---|---------|--------------|
| 11 | Library Management System | CRUD, fine calculation, reservation |
| 12 | ATM Machine | State machine, transaction handling |
| 13 | Vending Machine | State pattern, inventory management |
| 14 | Hotel Booking System | Room allocation, date ranges |
| 15 | Chess Game | Piece movement, check/checkmate |
| 16 | Tic-Tac-Toe | Game state, win detection |
| 17 | Online Shopping Cart | Cart management, checkout flow |
| 18 | Notification Service | Observer pattern, multiple channels |
| 19 | Task Scheduler | Priority queue, cron expressions |
| 20 | Ride Sharing (Uber) | Matching algorithm, location |

---

## Design Patterns to Know

### Creational Patterns
| Pattern | Use Case | Example |
|---------|----------|---------|
| Singleton | Single instance | Logger, Config |
| Factory | Object creation | VehicleFactory |
| Builder | Complex objects | QueryBuilder |

### Structural Patterns
| Pattern | Use Case | Example |
|---------|----------|---------|
| Adapter | Interface conversion | PaymentAdapter |
| Decorator | Add behavior | CoffeeDecorator |
| Composite | Tree structures | FileSystem |

### Behavioral Patterns
| Pattern | Use Case | Example |
|---------|----------|---------|
| Strategy | Interchangeable algorithms | SplitStrategy |
| Observer | Event notification | NotificationSystem |
| State | State machines | VendingMachine |
| Command | Action encapsulation | RemoteControl |

---

## SOLID Principles Checklist

| Principle | Question to Ask |
|-----------|-----------------|
| **S** - Single Responsibility | Does each class have ONE reason to change? |
| **O** - Open/Closed | Can I extend without modifying existing code? |
| **L** - Liskov Substitution | Can I replace parent with child without breaking? |
| **I** - Interface Segregation | Are interfaces small and focused? |
| **D** - Dependency Inversion | Do high-level modules depend on abstractions? |

---

## Machine Coding Round Tips

1. **First 5 mins:** Clarify requirements, ask questions
2. **Next 10 mins:** Identify entities, draw class diagram
3. **Next 25-30 mins:** Write code (start with core classes)
4. **Last 5 mins:** Walk through code, discuss edge cases

**DO:**
- Start with interfaces/abstract classes
- Use meaningful names
- Handle edge cases
- Show extensibility

**DON'T:**
- Write everything in one class
- Ignore thread-safety if relevant
- Skip validation
- Over-engineer early
