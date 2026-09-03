# Apple System Design (HLD) Interview Questions

> Sources: educative.io, designgurus.io, prachub.com, interviewquery.com (Content rephrased for compliance with licensing restrictions)

---

## Apple-Specific HLD Questions (Actually Asked)

### 1. Design Apple Music Streaming System

**Requirements:**
- Music streaming with millions of songs
- Upload and transcoding of new music
- Playlist management
- Offline playback support
- Payment/subscription integration

**Key Components:**
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────>│    CDN      │────>│ Blob Store  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                                       ▲
       ▼                                       │
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Load Balancer│───>│ App Servers │────>│ Transcoder  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │
       ▼                   ▼
┌─────────────┐     ┌─────────────┐
│  User DB    │     │ Metadata DB │
└─────────────┘     └─────────────┘
```

**Discussion Points:**
- How to handle different audio qualities (128kbps, 256kbps, lossless)?
- How to minimize latency for streaming?
- How to handle offline downloads and sync?
- DRM (Digital Rights Management) for content protection?

---

### 2. Design iCloud Photo Sync

**Requirements:**
- Sync photos across all Apple devices
- Handle large volumes (billions of photos)
- Offline-first behavior
- Conflict resolution
- Privacy-first (end-to-end encryption)

**Key Challenges:**
- Client-side caching strategy
- Delta sync (only sync changes)
- Handling conflicts when same photo edited on two devices
- Thumbnail generation at different resolutions

**Apple-Specific Focus:**
- Privacy: How to enable features like face recognition while maintaining privacy?
- Battery optimization: How to sync without draining battery?

---

### 3. Design Push Notification System

**Requirements:**
- Deliver notifications to millions of devices
- Support for iOS, macOS, watchOS
- High reliability (notifications must not be lost)
- Low latency delivery

**Architecture:**
```
Producer Service → Message Queue → Notification Service → APNS → Device
                                         │
                                         ▼
                                   Device Token DB
```

**Key Questions:**
- How to handle device tokens expiring?
- How to prioritize notifications (urgent vs marketing)?
- How to handle rate limiting per app?
- How to track delivery and read receipts?

---

### 4. Design App Store System

**Requirements:**
- App discovery and search
- App download and updates
- Reviews and ratings
- Developer analytics
- Payment processing for purchases

**Scale:**
- 2M+ apps
- Billions of downloads
- Peak traffic during new iPhone launches

**Components:**
- Search service with ranking algorithm
- Download service with CDN
- Review/Rating service
- Payment service
- Analytics pipeline

---

### 5. Design AirTag Tracking System

**Requirements:**
- Track AirTags using Find My network
- Leverage billions of Apple devices as detection points
- Privacy-preserving (no one knows who owns which AirTag)
- Low power consumption

**Key Challenges:**
- Crowdsourced location without privacy leaks
- How to anonymize device contributions?
- How to prevent stalking misuse?
- Bluetooth vs UWB precision

---

### 6. Design Logging/Monitoring System (Commonly Asked)

**Requirements:**
- Collect logs from thousands of microservices
- Make logs searchable within seconds of emission
- Support time-range queries
- Handle TB+ of logs daily

**Architecture:**
```
Services → Log Agents → Kafka → Log Processor → Elasticsearch
                                     │
                                     ▼
                              S3 (Long-term)
```

**Discussion Points:**
- How to handle log spikes during incidents?
- Hot vs cold storage strategy
- Structured vs unstructured logs
- Alerting on log patterns

---

## General HLD Questions (High Priority)

### 7. Design URL Shortener (bit.ly)

**Requirements:**
- Shorten URLs
- Redirect to original URL
- Analytics (click counts)
- Custom short URLs

**Key Decisions:**
- How to generate unique short codes? (Base62 encoding, counter, hash)
- How to handle collisions?
- How to scale reads (10:1 read:write ratio)?
- Cache strategy for hot URLs

---

### 8. Design Rate Limiter

**Requirements:**
- Limit API requests per user/IP
- Different limits for different endpoints
- Distributed (works across multiple servers)

**Algorithms:**
- Token Bucket
- Sliding Window
- Fixed Window Counter

**Implementation:**
- Redis for distributed counting
- Headers to communicate limit status (X-RateLimit-Remaining)

---

### 9. Design Notification Service

**Requirements:**
- Send Email, SMS, Push notifications
- Template management
- Scheduling (send at specific time)
- Delivery tracking

**Architecture:**
```
API → Kafka → Workers (Email/SMS/Push) → Providers (SES/Twilio/FCM)
                        │
                        ▼
                   Status DB
```

---

### 10. Design Chat System (WhatsApp/Messenger)

**Requirements:**
- 1:1 and group messaging
- Online/offline status
- Read receipts
- Media sharing

**Key Components:**
- WebSocket servers for real-time
- Message queue for async delivery
- Fan-out for group messages
- Media storage with CDN

---

### 11. Design Video Streaming (Netflix/YouTube)

**Requirements:**
- Upload and transcode videos
- Adaptive bitrate streaming
- Recommendations
- Watch history

**Key Concepts:**
- HLS/DASH streaming protocols
- CDN for global delivery
- Pre-computed recommendations
- Thumbnail generation

---

### 12. Design E-commerce System (Amazon)

**Requirements:**
- Product catalog
- Search and filtering
- Cart and checkout
- Order management
- Inventory tracking

**Key Challenges:**
- Handling flash sales (inventory race conditions)
- Search relevance
- Payment failure handling
- Distributed transactions

---

### 13. Design Ride-Sharing (Uber/Ola)

**Requirements:**
- Real-time driver location
- Ride matching
- ETA calculation
- Surge pricing
- Payment integration

**Key Components:**
- Geospatial indexing (QuadTree, Geohash)
- Real-time location updates (WebSocket)
- Matching algorithm
- Pricing engine

---

### 14. Design Food Delivery (Swiggy/Zomato)

**Requirements:**
- Restaurant discovery
- Menu management
- Order placement
- Delivery tracking
- Reviews and ratings

**Key Challenges:**
- Real-time order tracking
- Delivery partner assignment
- Dynamic pricing
- Handling peak hours

---

### 15. Design Social Media Feed (Twitter/Instagram)

**Requirements:**
- Post content (text, images, videos)
- Follow/unfollow
- News feed generation
- Likes, comments, shares

**Key Concepts:**
- Fan-out on write vs fan-out on read
- Feed ranking algorithm
- Caching strategies
- Celebrity problem (millions of followers)

---

## Apple Interview Tips

### What Apple Looks For:

1. **Privacy-First Thinking**
   - Always consider user privacy in your design
   - "How would you implement this without collecting user data?"

2. **Hardware-Software Integration**
   - Consider how software interacts with Apple hardware
   - Battery optimization, sensor usage

3. **User Experience**
   - Designs should prioritize seamless UX
   - "How does this feel to the user?"

4. **Trade-off Discussion**
   - Apple values engineers who can articulate trade-offs
   - "What are the pros/cons of this approach?"

5. **Attention to Detail**
   - Edge cases matter more at Apple
   - "What happens when network is flaky?"

---

## Interview Framework (45-60 mins)

| Phase | Time | Focus |
|-------|------|-------|
| Requirements | 5-10 min | Clarify scope, ask questions |
| High-Level Design | 15-20 min | Draw components, data flow |
| Deep Dive | 15-20 min | Detail specific components |
| Trade-offs | 5-10 min | Discuss alternatives |
| Q&A | 5 min | Questions for interviewer |

---

## Quick Reference: NFRs to Always Mention

```
┌─────────────────────────────────────────────────┐
│            ALWAYS DISCUSS THESE                 │
├─────────────────────────────────────────────────┤
│ Latency:      p50, p95, p99 targets             │
│ Throughput:   Requests per second               │
│ Availability: 99.9%, 99.99% - what's needed?    │
│ Consistency:  Strong vs Eventual - when?        │
│ Durability:   Data loss tolerance               │
│ Security:     Auth, encryption, PCI             │
│ Scalability:  How to 10x traffic?               │
└─────────────────────────────────────────────────┘
```
