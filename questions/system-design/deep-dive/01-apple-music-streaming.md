# System Design Deep Dive: Apple Music Streaming Service

> **Difficulty:** Medium-Hard
> **Companies:** Apple, Spotify, Amazon Music, YouTube Music
> **Time in Interview:** 45-60 minutes

---

## Table of Contents
1. [Problem Statement](#problem-statement)
2. [Clarifying Questions](#clarifying-questions)
3. [Functional Requirements](#functional-requirements)
4. [Non-Functional Requirements](#non-functional-requirements)
5. [Scale Estimation](#scale-estimation)
6. [High-Level Architecture](#high-level-architecture)
7. [Database Design](#database-design)
8. [API Design](#api-design)
9. [Deep Dive Components](#deep-dive-components)
10. [Edge Cases & Challenges](#edge-cases--challenges)
11. [Interview Follow-up Questions](#interview-follow-up-questions)

---

## Problem Statement

**Interviewer says:**

*"Design a music streaming service like Apple Music or Spotify. Users should be able to stream songs, create playlists, and download music for offline listening. We have around 100 million monthly active users. You have 45 minutes."*

---

## Clarifying Questions (Real Interview Conversation)

**Pehle 3-5 minutes mein ye questions pucho. Ye dikhata hai ki tum directly code nahi likhte, pehle problem samajhte ho.**

---

### The Conversation:

**You:** *"Thank you for the problem. Before I start designing, I'd like to ask a few clarifying questions to make sure I understand the scope correctly. Is that okay?"*

**Interviewer:** *"Sure, go ahead."*

---

**You:** *"So when you say music streaming service — are we designing the complete system including how artists upload their music? Or should I focus only on the user-facing side where users stream and listen to music?"*

**Interviewer:** *"Good question. Let's focus on the user-facing side for now — streaming, playlists, that kind of thing. Artist uploads can be a separate discussion."*

**You:** *"Got it, that helps narrow the scope significantly."*

---

**You:** *"For the content itself — are we dealing with just audio streaming? Or do we also need to consider music videos, lyrics display, podcasts like Spotify has?"*

**Interviewer:** *"Let's keep it simple — just audio streaming for this discussion."*

**You:** *"Okay, audio only. That simplifies our storage and CDN requirements."*

---

**You:** *"Regarding the usage pattern — I'm assuming this is a read-heavy system? Like most operations would be users playing songs, and writes would be things like creating playlists or liking songs?"*

**Interviewer:** *"Yes, that's correct. You can assume roughly 99% reads and 1% writes."*

**You:** *"That's helpful. So we can optimize heavily for read performance and use caching aggressively."*

---

**You:** *"For audio quality — do we need to support multiple quality levels? Like users on slow mobile data might want lower quality, while users on WiFi might want lossless audio?"*

**Interviewer:** *"Yes, we should support multiple qualities. Think 128kbps, 256kbps, and lossless. Adaptive streaming based on network conditions would be great."*

**You:** *"So we'll need to store each song in multiple formats and implement adaptive bitrate streaming. Noted."*

---

**You:** *"Are we designing for a specific region, or is this a global service with users from all around the world?"*

**Interviewer:** *"Global. Assume users from all continents — North America, Europe, Asia, everywhere."*

**You:** *"Global distribution means we'll definitely need a strong CDN strategy with edge locations worldwide to minimize latency."*

---

**You:** *"You mentioned offline downloads — is that a must-have feature or nice-to-have? Because offline introduces complexity around DRM, storage management, license expiry..."*

**Interviewer:** *"It's a must-have. Users expect to download songs and listen on flights, in subways, places without internet."*

**You:** *"Understood. So we'll need to design a proper DRM system to protect downloaded content and handle license management."*

---

**You:** *"One last question — should I consider content protection and DRM? Because music labels are very particular about unauthorized distribution."*

**Interviewer:** *"Yes, definitely. We need to make sure songs can't be easily pirated or shared. DRM is important."*

---

### Summarizing Back (Very Important!):

**You:** *"Great, let me summarize what I understood to make sure we're aligned:*

*I'm designing a music streaming service for approximately 100 million monthly active users. The focus is on:*
- *User-facing features: streaming, playlists, search, recommendations*
- *Audio only, no video or podcasts*
- *Multiple audio qualities with adaptive streaming*
- *Global user base, so CDN is critical*
- *Offline downloads with DRM protection*
- *Read-heavy system (99% reads)*

*Artist upload and content management is out of scope for this discussion.*

*Does that sound right?"*

**Interviewer:** *"Perfect, that's exactly right. Go ahead with your design."*

---

### Why This Approach Works:

| What You Did | Why It Impresses Interviewer |
|--------------|------------------------------|
| Asked before designing | Shows you don't make assumptions |
| Repeated back | Shows active listening |
| Mentioned implications | "CDN for global" shows you're thinking ahead |
| Clarified scope | Shows you can manage complexity |
| Used technical terms naturally | Shows you know the domain |

---

## Functional Requirements

**Ye features system MUST support kare:**

### Core Features (Must Have):

#### 1. Music Discovery & Search
- Search by song name, artist, album, genre
- Browse curated playlists (Top 50, New Releases)
- Get personalized recommendations

#### 2. Music Streaming
- Play songs on-demand
- Controls: Play, Pause, Seek, Skip, Previous
- Queue management (Up Next)
- Shuffle and Repeat modes
- Continue playing where user left off (across devices)

#### 3. Playlist Management
- Create, edit, delete playlists
- Add/remove songs from playlist
- Reorder songs in playlist
- Collaborative playlists (multiple users can add songs)

#### 4. Offline Downloads
- Download songs/albums/playlists for offline
- Auto-delete expired downloads (if subscription ends)
- Sync downloads across devices (limited)

#### 5. User Library
- Like/save songs, albums, artists
- Recently played history
- Follow artists for updates

### Out of Scope (Explicitly mention in interview):
- Artist/label upload system
- Payment/subscription management
- Social features (sharing to social media)
- Podcasts, audiobooks
- Live radio stations

---

## Non-Functional Requirements

**System KAISE perform kare:**

### Performance Requirements:

| Metric | Target | Reasoning |
|--------|--------|-----------|
| **Streaming Start Latency** | < 200ms | User clicks play → music starts in 200ms |
| **Search Latency** | < 100ms | Instant search results |
| **API Latency (p99)** | < 500ms | 99% requests under 500ms |
| **Buffering** | < 0.1% of playtime | Minimal interruptions |

### Scale Requirements:

| Metric | Value | Calculation |
|--------|-------|-------------|
| **Monthly Active Users (MAU)** | 100 Million | Given |
| **Daily Active Users (DAU)** | 30 Million | ~30% of MAU |
| **Concurrent Users (Peak)** | 10 Million | ~10% of MAU at peak |
| **Songs in Library** | 100 Million | Industry standard |
| **New Songs Added/Day** | 50,000 | Growing library |

### Reliability Requirements:

| Metric | Target | Reasoning |
|--------|--------|-----------|
| **Availability** | 99.99% | 52 mins downtime/year max |
| **Durability** | 99.999999999% (11 9s) | User playlists must NEVER be lost |
| **Data Consistency** | Eventual (streaming), Strong (playlists) | Playlist changes must be immediate |

### Storage Requirements:

```
Average song size:
- 128 kbps = ~1 MB/min × 4 min = 4 MB
- 256 kbps = ~2 MB/min × 4 min = 8 MB
- Lossless = ~5 MB/min × 4 min = 20 MB

Total storage per song (all qualities): ~32 MB
100 Million songs × 32 MB = 3.2 PB (Petabytes)
```

---

## Scale Estimation

**Ye calculations interview mein karo — dikhata hai ki tum practical thinking karte ho.**

### Traffic Estimation:

```
100M MAU
30M DAU (30% daily active)
Average session: 30 minutes = ~8 songs

Daily song plays = 30M × 8 = 240 Million plays/day

Requests per second:
- 240M / 86400 seconds = ~2,800 plays/second (average)
- Peak (2-3x average) = ~8,000-10,000 plays/second
```

### Bandwidth Estimation:

```
Assume average streaming quality: 256 kbps

Concurrent streams at peak: 10 Million
Bandwidth = 10M × 256 kbps = 2.56 Tbps (Terabits per second)

This is HUGE — that's why we need CDN!
```

### Storage Estimation:

```
Songs: 100M × 32MB = 3.2 PB
Metadata: 100M × 1KB = 100 GB
User data: 100M users × 10KB = 1 TB
Playlists: Assume 500M playlists × 5KB = 2.5 TB

Total: ~3.2 PB (dominated by audio files)
```

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│  │   iOS    │  │ Android  │  │   Web    │  │  Desktop │                     │
│  │   App    │  │   App    │  │  Player  │  │   App    │                     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘                     │
└───────┼─────────────┼─────────────┼─────────────┼───────────────────────────┘
        │             │             │             │
        └─────────────┴──────┬──────┴─────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CDN LAYER                                       │
│                        (CloudFront / Akamai)                                │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  Edge Locations (100+ globally)                                      │   │
│   │  - Cached audio files (popular songs)                                │   │
│   │  - Cached thumbnails/album art                                       │   │
│   │  - ~80% of requests served from edge                                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                             │
                             │ Cache miss → fetch from origin
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LOAD BALANCER                                      │
│                    (AWS ALB / Nginx / HAProxy)                              │
│                                                                              │
│   - Distributes traffic across API servers                                  │
│   - Health checks                                                           │
│   - SSL termination                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY LAYER                                    │
│                                                                              │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│   │    Auth     │  │    Rate     │  │   Request   │  │   Logging   │       │
│   │  Middleware │  │   Limiter   │  │  Validation │  │  & Metrics  │       │
│   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        APPLICATION LAYER (Microservices)                     │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │    User      │  │   Catalog    │  │  Streaming   │  │   Search     │    │
│  │   Service    │  │   Service    │  │   Service    │  │   Service    │    │
│  │              │  │              │  │              │  │              │    │
│  │ - Auth       │  │ - Songs      │  │ - Play URL   │  │ - Full-text  │    │
│  │ - Profile    │  │ - Albums     │  │ - Quality    │  │ - Filters    │    │
│  │ - Preferences│  │ - Artists    │  │ - DRM tokens │  │ - Autocomplete│   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │                 │            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Playlist    │  │ Recommendation│ │   Download   │  │  Analytics   │    │
│  │   Service    │  │   Service    │  │   Service    │  │   Service    │    │
│  │              │  │              │  │              │  │              │    │
│  │ - CRUD       │  │ - ML models  │  │ - Offline    │  │ - Play counts│    │
│  │ - Collab     │  │ - Personalized│ │ - Sync       │  │ - User behavior│  │
│  │ - Share      │  │ - Similar    │  │ - Expiry     │  │ - Trending   │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
└─────────┼─────────────────┼─────────────────┼─────────────────┼────────────┘
          │                 │                 │                 │
          ▼                 ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            DATA LAYER                                        │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   PostgreSQL    │  │     Redis       │  │  Elasticsearch  │             │
│  │   (Primary DB)  │  │    (Cache)      │  │   (Search)      │             │
│  │                 │  │                 │  │                 │             │
│  │ - Users         │  │ - Session       │  │ - Song index    │             │
│  │ - Playlists     │  │ - Hot songs     │  │ - Artist index  │             │
│  │ - Play history  │  │ - User prefs    │  │ - Album index   │             │
│  │ - Metadata      │  │ - Rate limits   │  │ - Autocomplete  │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │    Cassandra    │  │   Amazon S3     │  │     Kafka       │             │
│  │  (Time-series)  │  │  (Blob Storage) │  │ (Event Stream)  │             │
│  │                 │  │                 │  │                 │             │
│  │ - Play events   │  │ - Audio files   │  │ - Play events   │             │
│  │ - Analytics     │  │ - Album art     │  │ - User actions  │             │
│  │ - Recommendations│ │ - All qualities │  │ - Analytics     │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Explanation:

#### 1. CDN (Content Delivery Network)
**Kya karta hai:** Audio files ko users ke paas cache karta hai.

**Kyun zaroori hai:**
- India mein user hai, S3 US mein hai → 200ms+ latency
- CDN edge Mumbai mein hai → 20ms latency
- 80% popular songs CDN se serve hote hain

**Example:**
```
User in Mumbai clicks "Play"
  → Request goes to CDN edge in Mumbai
  → If cached: Serve immediately (20ms)
  → If not cached: Fetch from S3, cache it, then serve
```

#### 2. Streaming Service
**Kya karta hai:** Audio file ka URL generate karta hai with authentication.

**Kyun zaroori hai:**
- Directly S3 URL nahi de sakte (security risk)
- DRM token attach karna hota hai
- Quality selection based on network

**How it works:**
```
1. User clicks Play
2. Client calls: GET /api/v1/stream/song/{song_id}
3. Streaming service:
   - Checks user subscription (active?)
   - Checks song availability (region?)
   - Generates signed CDN URL (expires in 1 hour)
   - Includes DRM token
4. Returns URL to client
5. Client fetches audio from CDN using signed URL
```

#### 3. Search Service (Elasticsearch)
**Kya karta hai:** Fast full-text search on songs, artists, albums.

**Kyun zaroori hai:**
- PostgreSQL LIKE queries slow hai for 100M songs
- Need fuzzy matching ("Coldpley" → "Coldplay")
- Need autocomplete as user types

#### 4. Recommendation Service
**Kya karta hai:** Personalized recommendations based on listening history.

**How it works:**
- Collaborative filtering: "Users like you also listened to..."
- Content-based: "Because you liked rock songs..."
- Uses ML models trained on play history data

---

## Database Design

### Tables:

#### 1. Users Table
```sql
CREATE TABLE users (
    user_id         UUID PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    name            VARCHAR(100),
    country         VARCHAR(2),           -- For regional content
    subscription_type VARCHAR(20),        -- free, premium, family
    subscription_end TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- Index for login
CREATE INDEX idx_users_email ON users(email);
```

#### 2. Songs Table
```sql
CREATE TABLE songs (
    song_id         UUID PRIMARY KEY,
    title           VARCHAR(255) NOT NULL,
    artist_id       UUID REFERENCES artists(artist_id),
    album_id        UUID REFERENCES albums(album_id),
    duration_seconds INTEGER NOT NULL,
    genre           VARCHAR(50),
    release_date    DATE,
    explicit        BOOLEAN DEFAULT FALSE,
    
    -- Storage references (S3 keys)
    audio_128_key   VARCHAR(255),         -- s3://bucket/songs/128/xyz.mp3
    audio_256_key   VARCHAR(255),
    audio_lossless_key VARCHAR(255),
    
    -- Metadata
    play_count      BIGINT DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_songs_artist ON songs(artist_id);
CREATE INDEX idx_songs_album ON songs(album_id);
CREATE INDEX idx_songs_genre ON songs(genre);
CREATE INDEX idx_songs_release ON songs(release_date DESC);
```

#### 3. Artists Table
```sql
CREATE TABLE artists (
    artist_id       UUID PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    bio             TEXT,
    image_url       VARCHAR(500),
    verified        BOOLEAN DEFAULT FALSE,
    monthly_listeners BIGINT DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_artists_name ON artists(name);
```

#### 4. Albums Table
```sql
CREATE TABLE albums (
    album_id        UUID PRIMARY KEY,
    title           VARCHAR(255) NOT NULL,
    artist_id       UUID REFERENCES artists(artist_id),
    release_date    DATE,
    cover_image_url VARCHAR(500),
    album_type      VARCHAR(20),          -- album, single, EP
    total_tracks    INTEGER,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_albums_artist ON albums(artist_id);
CREATE INDEX idx_albums_release ON albums(release_date DESC);
```

#### 5. Playlists Table
```sql
CREATE TABLE playlists (
    playlist_id     UUID PRIMARY KEY,
    user_id         UUID REFERENCES users(user_id),
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    is_public       BOOLEAN DEFAULT FALSE,
    is_collaborative BOOLEAN DEFAULT FALSE,
    cover_image_url VARCHAR(500),
    follower_count  INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_playlists_user ON playlists(user_id);
CREATE INDEX idx_playlists_public ON playlists(is_public) WHERE is_public = TRUE;
```

#### 6. Playlist Songs Table (Many-to-Many)
```sql
CREATE TABLE playlist_songs (
    playlist_id     UUID REFERENCES playlists(playlist_id),
    song_id         UUID REFERENCES songs(song_id),
    position        INTEGER NOT NULL,     -- Order in playlist
    added_by        UUID REFERENCES users(user_id),
    added_at        TIMESTAMP DEFAULT NOW(),
    
    PRIMARY KEY (playlist_id, song_id)
);

CREATE INDEX idx_playlist_songs_position ON playlist_songs(playlist_id, position);
```

#### 7. User Library (Liked Songs)
```sql
CREATE TABLE user_library (
    user_id         UUID REFERENCES users(user_id),
    song_id         UUID REFERENCES songs(song_id),
    added_at        TIMESTAMP DEFAULT NOW(),
    
    PRIMARY KEY (user_id, song_id)
);
```

#### 8. Play History (For Recommendations)
```sql
-- This goes in Cassandra (time-series optimized)
CREATE TABLE play_history (
    user_id         UUID,
    played_at       TIMESTAMP,
    song_id         UUID,
    duration_played INTEGER,              -- How long user listened
    completed       BOOLEAN,              -- Did they finish the song?
    source          VARCHAR(50),          -- playlist, album, search, radio
    
    PRIMARY KEY ((user_id), played_at)
) WITH CLUSTERING ORDER BY (played_at DESC);
```

#### 9. Downloads (Offline)
```sql
CREATE TABLE user_downloads (
    user_id         UUID REFERENCES users(user_id),
    song_id         UUID REFERENCES songs(song_id),
    quality         VARCHAR(20),          -- 128, 256, lossless
    downloaded_at   TIMESTAMP DEFAULT NOW(),
    expires_at      TIMESTAMP,            -- DRM expiry
    device_id       VARCHAR(255),
    
    PRIMARY KEY (user_id, song_id, device_id)
);
```

### Database Choice Reasoning:

| Data | Database | Why |
|------|----------|-----|
| Users, Playlists, Songs metadata | **PostgreSQL** | ACID needed, complex queries, relationships |
| Play history, Analytics | **Cassandra** | Time-series data, high write throughput |
| Search indexes | **Elasticsearch** | Full-text search, fuzzy matching |
| Session, Cache, Rate limits | **Redis** | Fast reads, TTL support |
| Audio files, Images | **S3** | Blob storage, cheap, durable |

---

## API Design

### 1. Search APIs

#### Search Songs/Artists/Albums
```
GET /api/v1/search?q=coldplay&type=song,artist,album&limit=20

Response:
{
  "songs": [
    {
      "song_id": "uuid-1",
      "title": "Yellow",
      "artist": {"artist_id": "uuid-a1", "name": "Coldplay"},
      "album": {"album_id": "uuid-al1", "title": "Parachutes"},
      "duration_seconds": 266,
      "cover_image": "https://cdn.music.com/covers/parachutes.jpg"
    }
  ],
  "artists": [
    {
      "artist_id": "uuid-a1",
      "name": "Coldplay",
      "image": "https://cdn.music.com/artists/coldplay.jpg",
      "monthly_listeners": 45000000
    }
  ],
  "albums": [...]
}
```

#### Autocomplete
```
GET /api/v1/search/autocomplete?q=cold

Response:
{
  "suggestions": [
    {"text": "Coldplay", "type": "artist"},
    {"text": "Cold Water", "type": "song"},
    {"text": "Cold Heart", "type": "song"}
  ]
}
```

---

### 2. Streaming APIs

#### Get Stream URL
```
GET /api/v1/stream/song/{song_id}?quality=256

Headers:
  Authorization: Bearer <jwt_token>

Response:
{
  "stream_url": "https://cdn.music.com/songs/256/xyz.mp3?token=abc&expires=1234567890",
  "duration_seconds": 266,
  "quality": "256kbps",
  "drm_token": "encrypted_drm_token",
  "expires_in": 3600
}
```

**Note:** Stream URL is signed and expires in 1 hour for security.

#### Report Playback (For Analytics)
```
POST /api/v1/playback/report

Body:
{
  "song_id": "uuid-1",
  "started_at": "2026-09-01T10:00:00Z",
  "duration_played": 180,
  "completed": false,
  "source": "playlist",
  "source_id": "playlist-uuid"
}

Response:
{
  "success": true
}
```

---

### 3. Playlist APIs

#### Create Playlist
```
POST /api/v1/playlists

Body:
{
  "name": "My Favorites",
  "description": "Songs I love",
  "is_public": false
}

Response:
{
  "playlist_id": "uuid-pl1",
  "name": "My Favorites",
  "song_count": 0,
  "created_at": "2026-09-01T10:00:00Z"
}
```

#### Add Song to Playlist
```
POST /api/v1/playlists/{playlist_id}/songs

Body:
{
  "song_id": "uuid-song1",
  "position": 0  // Optional, adds to end if not specified
}

Response:
{
  "success": true,
  "song_count": 15
}
```

#### Get Playlist with Songs
```
GET /api/v1/playlists/{playlist_id}?include_songs=true&limit=50&offset=0

Response:
{
  "playlist_id": "uuid-pl1",
  "name": "My Favorites",
  "owner": {"user_id": "uuid-u1", "name": "Ujjwal"},
  "song_count": 150,
  "duration_seconds": 36000,
  "songs": [
    {
      "song_id": "uuid-song1",
      "title": "Yellow",
      "artist": "Coldplay",
      "duration_seconds": 266,
      "position": 0
    },
    ...
  ],
  "pagination": {
    "offset": 0,
    "limit": 50,
    "total": 150
  }
}
```

#### Reorder Songs
```
PUT /api/v1/playlists/{playlist_id}/songs/reorder

Body:
{
  "song_id": "uuid-song1",
  "new_position": 5
}
```

---

### 4. Library APIs

#### Like a Song
```
POST /api/v1/library/songs/{song_id}

Response:
{
  "success": true,
  "message": "Song added to library"
}
```

#### Get Liked Songs
```
GET /api/v1/library/songs?limit=50&offset=0

Response:
{
  "songs": [...],
  "pagination": {...}
}
```

#### Follow an Artist
```
POST /api/v1/library/artists/{artist_id}/follow

Response:
{
  "success": true,
  "following": true
}
```

---

### 5. Download APIs (Offline)

#### Request Download
```
POST /api/v1/downloads

Body:
{
  "song_id": "uuid-song1",
  "quality": "256"
}

Response:
{
  "download_url": "https://cdn.music.com/download/...",
  "drm_token": "encrypted_token",
  "expires_at": "2026-10-01T00:00:00Z",
  "file_size_bytes": 8500000
}
```

#### Get My Downloads
```
GET /api/v1/downloads

Response:
{
  "downloads": [
    {
      "song_id": "uuid-song1",
      "title": "Yellow",
      "quality": "256kbps",
      "downloaded_at": "2026-09-01T10:00:00Z",
      "expires_at": "2026-10-01T00:00:00Z"
    }
  ]
}
```

---

### 6. Recommendation APIs

#### Get Home Feed
```
GET /api/v1/home

Response:
{
  "sections": [
    {
      "title": "Recently Played",
      "type": "songs",
      "items": [...]
    },
    {
      "title": "Made For You",
      "type": "playlists",
      "items": [...]
    },
    {
      "title": "New Releases",
      "type": "albums",
      "items": [...]
    },
    {
      "title": "Because you listened to Coldplay",
      "type": "artists",
      "items": [...]
    }
  ]
}
```

#### Get Similar Songs
```
GET /api/v1/recommendations/songs/{song_id}/similar?limit=20

Response:
{
  "songs": [...]
}
```

---

## Deep Dive Components

### 1. How Audio Streaming Actually Works

**Step-by-Step Flow:**

```
1. User opens app, sees home feed
   └── GET /api/v1/home (served from cache mostly)

2. User searches "Coldplay Yellow"
   └── GET /api/v1/search?q=coldplay%20yellow
   └── Elasticsearch returns matching songs

3. User clicks Play on "Yellow"
   └── Client calls: GET /api/v1/stream/song/{song_id}
   └── Server validates:
       - Is user authenticated? (JWT check)
       - Is subscription active?
       - Is song available in user's region?
   └── Server generates signed CDN URL
   └── Returns URL + DRM token

4. Client receives stream URL
   └── Example: https://cdn.music.com/songs/256/abc123.mp3?token=xyz&expires=123456
   
5. Client starts fetching audio from CDN
   └── CDN checks signature validity
   └── If valid + cached: Serve from edge
   └── If valid + not cached: Fetch from S3, cache, serve

6. Audio plays in chunks
   └── Client buffers 10-15 seconds ahead
   └── Adaptive bitrate: If network slow, switch to 128kbps

7. Client reports playback
   └── POST /api/v1/playback/report (async, non-blocking)
   └── Used for analytics and recommendations
```

### 2. CDN and Caching Strategy

**What gets cached where:**

| Data | Cache Location | TTL | Invalidation |
|------|----------------|-----|--------------|
| Popular songs (top 10,000) | CDN edge | 24 hours | Manual when file changes |
| Album art / thumbnails | CDN edge | 7 days | Versioned URLs |
| API responses (home feed) | Redis | 5 minutes | On data change |
| User session | Redis | 24 hours | On logout |
| Search results | Redis | 1 hour | On index update |

**CDN Cache Hit Ratio Target: 80%+**

This means 80% of audio requests are served from CDN edge (fast), only 20% go to origin (S3).

### 3. How Offline Downloads Work

```
1. User clicks "Download" on a song
   └── POST /api/v1/downloads {song_id, quality}

2. Server checks:
   └── Is user premium? (Only premium can download)
   └── Download limit reached? (Max 10,000 songs)
   └── Device limit? (Max 5 devices)

3. Server returns:
   └── Download URL (signed, expires in 24 hours)
   └── DRM license (encrypted, tied to device)

4. Client downloads file
   └── Stores encrypted audio locally
   └── Stores DRM license

5. Offline playback:
   └── Client decrypts using DRM license
   └── DRM license has expiry (e.g., 30 days)
   └── If expired, client must go online to refresh

6. Subscription ends:
   └── DRM licenses expire
   └── Downloaded files become unplayable
   └── Client shows "Renew subscription to play"
```

### 4. Recommendation System (Simplified)

**Two Main Approaches:**

#### A. Collaborative Filtering
*"Users similar to you liked these songs"*

```
1. Build user-song matrix:
   
   User    | Song A | Song B | Song C | Song D
   --------|--------|--------|--------|--------
   User 1  |   5    |   3    |   0    |   1
   User 2  |   4    |   0    |   0    |   1
   User 3  |   0    |   4    |   5    |   0

2. Find similar users (cosine similarity)
   User 1 and User 2 are similar (both like Song A and D)

3. Recommend:
   User 2 hasn't heard Song B
   User 1 liked Song B
   → Recommend Song B to User 2
```

#### B. Content-Based Filtering
*"Because you like rock songs with guitar"*

```
1. Extract song features:
   - Genre: Rock
   - Tempo: 120 BPM
   - Energy: High
   - Instruments: Guitar, Drums
   - Mood: Uplifting

2. Find songs with similar features

3. Recommend songs that match user's taste profile
```

**Apple Music uses BOTH + editorial curation (human-made playlists).**

---

## Edge Cases & Challenges

### 1. What if CDN is down?

**Solution: Fallback to origin**
```
Client → CDN (timeout) → Fallback to direct S3 URL
```
- Have health checks on CDN
- Client has fallback logic
- Slightly higher latency, but service continues

### 2. User is on slow network

**Solution: Adaptive Bitrate Streaming (ABR)**
```
1. Client continuously monitors download speed
2. If speed drops below threshold:
   - Switch from 256kbps to 128kbps mid-stream
   - Seamless transition (no user action needed)
3. If speed improves, switch back up
```

### 3. Same song played simultaneously on 2 devices

**Policy Decision:**
- Spotify: Pauses on old device
- Apple Music: Allows on family plan (6 devices)

**Implementation:**
```
1. On play request, check active_sessions in Redis
2. If too many concurrent streams:
   - Return error OR
   - Pause oldest session (send push notification)
```

### 4. Playlist has 10,000 songs — how to load fast?

**Solution: Pagination + Lazy Loading**
```
1. Initial load: First 50 songs only
2. As user scrolls, load more (infinite scroll)
3. Store playlist metadata separately (count, duration)
4. Don't load all songs for metadata queries
```

### 5. How to handle regional content restrictions?

**Solution:**
```
1. Songs table has 'available_regions' column (array or separate table)
2. On stream request:
   - Get user's country from profile
   - Check if song available in that region
   - If not: Return 451 (Unavailable For Legal Reasons)
```

### 6. How to prevent unauthorized sharing of stream URLs?

**Solution: Signed URLs + DRM**
```
1. Signed URL:
   - Includes expiry timestamp
   - Includes user token
   - Signed with secret key
   - CDN validates signature before serving

2. DRM (Digital Rights Management):
   - Audio encrypted
   - Only licensed devices can decrypt
   - License tied to subscription status
```

---

## Interview Follow-up Questions (Real Conversation Style)

**After you present your design, interviewer will dig deeper. Here's how those conversations go:**

---

### Follow-up 1: Handling Viral Releases

**Interviewer:** *"Interesting design. Now let's say Taylor Swift releases a new album at midnight, and suddenly 50 million users want to play it in the first hour. How does your system handle that?"*

**You:** *"Great question — this is the classic thundering herd problem. Let me walk through how I'd handle it:*

*First, we'd know about this release in advance — it's not a surprise. So we can prepare:*

*1. **Pre-warm the CDN**: Before the release, we push the audio files to ALL edge locations globally. Normally we let CDN cache on-demand, but for major releases, we proactively push. This way, the files are already sitting at edge locations in Mumbai, London, Tokyo before anyone even clicks play.*

*2. **Rate limiting per user**: Even if 50 million users are trying, each user can only play one song at a time. We enforce 1 request per second per user. This prevents any single user from overwhelming the system.*

*3. **Request queuing**: If we're still overloaded, we queue requests with an estimated wait time. User sees 'High demand, you're in queue, estimated wait: 30 seconds'. Better than a crash.*

*4. **Separate hot-content infrastructure**: For trending songs in the first 24 hours, we can route them to dedicated high-capacity servers instead of sharing infrastructure with long-tail content.*

*5. **Graceful degradation**: In extreme cases, we might temporarily serve only 128kbps instead of letting users choose quality. Lower quality = less bandwidth = more users served."*

**Interviewer:** *"What if even with pre-warming, the origin servers get overwhelmed?"*

**You:** *"Good point. For the origin, we'd have auto-scaling groups that spin up additional instances based on CPU/memory metrics. We'd also use a message queue between the API layer and the actual file serving — so if requests pile up, they queue instead of crashing the servers. The queue acts as a buffer.

Also, for a release this big, we'd probably have a war room — engineers monitoring dashboards, ready to manually intervene if automated systems aren't enough."*

---

### Follow-up 2: Audio Quality Consistency

**Interviewer:** *"You mentioned multiple audio qualities. How do you ensure the audio quality is consistent and doesn't degrade? What if a file gets corrupted?"*

**You:** *"File integrity is critical for a music service. Here's our approach:*

*1. **Transcoding pipeline with validation**: When a song is ingested, we transcode it to 128kbps, 256kbps, and lossless. After transcoding, we run automated quality checks — duration must match, no audio artifacts, no silence gaps.*

*2. **Checksum verification**: Every file has an MD5 or SHA256 hash stored in our database. When we upload to S3 or CDN, we verify the hash matches. If there's a mismatch, we know the file is corrupted and we reject it.*

*3. **Periodic integrity scans**: We have background jobs that randomly sample files from S3 and verify their checksums. If we find corruption, we re-transcode from the original master file.*

*4. **Client-side verification**: The client app can also verify chunks as they download. If a chunk is corrupted, it requests a re-download of just that chunk.*

*5. **Multiple copies**: We store files in S3 with 11 nines of durability, which means cross-region replication. If one copy is corrupted, we have others."*

**Interviewer:** *"What about real-time quality — like if users complain about buffering?"*

**You:** *"We'd monitor buffering events. Every time the client has to pause playback to buffer, it sends an event to our analytics pipeline. We track:*
- *Buffering rate (what % of playtime is spent buffering)*
- *Geographic patterns (is buffering worse in certain regions?)*
- *ISP patterns (is a particular ISP having issues?)*

*If buffering rate exceeds our SLA — say 0.5% — we get alerted and investigate. Could be CDN issue, ISP issue, or our own infrastructure."*

---

### Follow-up 3: Like Feature at Scale

**Interviewer:** *"Let's talk about the 'Like' feature. Users can like songs, and songs show their like count. With 100 million users potentially liking songs, how do you design this?"*

**You:** *"This is a classic high-write, high-read scenario. Let me break it down:*

*The naive approach would be: User likes a song → INSERT into user_library → UPDATE songs SET like_count = like_count + 1. But this has problems at scale — that UPDATE on a hot song creates lock contention.*

*Here's what I'd do instead:*

*1. **User's likes**: INSERT into user_library table is fine. It's partitioned by user_id, so no contention. Each user likes maybe 100 songs, not millions.*

*2. **Song's like count**: Instead of updating the songs table directly, I'd:*
   - *Write the like event to Kafka*
   - *A consumer aggregates likes in batches*
   - *Every minute, batch-update the songs table with accumulated counts*
   
*This way, if 10,000 users like a song in one minute, we do ONE update with +10,000 instead of 10,000 individual updates.*

*3. **For display**: I'd cache like counts in Redis with a TTL of 1 minute. User sees a slightly stale count, but that's acceptable. Nobody notices if like count shows 1,234,567 instead of 1,234,589.*

*4. **User's own like status**: This needs to be real-time. Did I like this song or not? This comes directly from user_library table or a user-specific Redis cache."*

**Interviewer:** *"What if the Kafka consumer falls behind?"*

**You:** *"Good edge case. We'd have lag monitoring on the Kafka consumer. If lag exceeds a threshold — say 5 minutes — we get alerted. We can scale up consumers horizontally since Kafka supports parallel consumption. 

Worst case, like counts are delayed by a few minutes, which is acceptable. The user's own like status is still real-time since that's a different path."*

---

### Follow-up 4: Debugging User Issues

**Interviewer:** *"A user contacts support saying 'My playlist with 500 songs is gone, I spent years making it!' How do you investigate this?"*

**You:** *"Oh, this is a nightmare scenario. Let me walk through my debugging approach:*

*1. **First, reassure the user**: Tell them we have backups and we'll investigate. Don't make promises yet, but don't panic them either.*

*2. **Check audit logs**: Every playlist operation should be logged — create, delete, add song, remove song. I'd search for:*
   ```
   user_id = <this user>
   resource_type = playlist
   action = delete
   ```
   *Did the user delete it themselves? When? From which device?*

*3. **Check soft-delete**: Hopefully our delete is a soft-delete (is_deleted = true), not a hard delete. If so, the playlist still exists in the database, just hidden. We can recover it easily.*

*4. **Check replication lag**: If they're reading from a replica and there's lag, they might not see recent changes. I'd query the primary directly to confirm the actual state.*

*5. **Check for API bugs**: Was there a deployment around the time this happened? Did we introduce a bug that accidentally deleted playlists?*

*6. **Database backups**: If all else fails and it's truly deleted, we have point-in-time recovery. We can restore the playlists table from backup and extract this user's data. It's painful but possible."*

**Interviewer:** *"How would you prevent this from happening?"*

**You:** *"Prevention:*
- *Soft delete with retention period (30 days) before hard delete*
- *Confirmation modal for deleting large playlists (>50 songs)*
- *'Recently Deleted' folder like iPhone Photos — user can self-recover*
- *Audit logging for all destructive operations*
- *Rate limiting on delete operations — can't delete more than 5 playlists per minute*"*

---

### Follow-up 5: Adding New Feature (Lyrics)

**Interviewer:** *"Product team wants to add synchronized lyrics — you know, where lyrics highlight in real-time as the song plays. How would you add this to your design?"*

**You:** *"Interesting feature! Let me think about the data model and sync mechanism:*

*1. **Data storage**: Lyrics need to be stored with timestamps. Something like:*
   ```json
   {
     "song_id": "uuid-123",
     "lyrics": [
       {"time_ms": 0, "text": "Is it getting better"},
       {"time_ms": 3500, "text": "Or do you feel the same"},
       {"time_ms": 7200, "text": "Will it make it easier on you now"},
       ...
     ]
   }
   ```
   *I'd store this in a separate lyrics table or even a separate service — it's a distinct domain.*

*2. **Sync mechanism**: The client already knows the current playback position in milliseconds. When lyrics are enabled:*
   - *Fetch lyrics data for the song (cache it locally)*
   - *As playback position changes, find the lyric line where time_ms <= current_position*
   - *Highlight that line*
   
*3. **Edge cases**:*
   - *User seeks to a different position → immediately update lyrics*
   - *Song doesn't have lyrics → show "Lyrics not available"*
   - *User has slow network → prefetch lyrics when song is added to queue*

*4. **Sourcing lyrics**: This is actually the hardest part. We'd either:*
   - *License from lyrics providers (Musixmatch, Genius)*
   - *Get from record labels directly*
   - *Lyrics have copyright too, so we can't just scrape them*"*

**Interviewer:** *"What about offline lyrics?"*

**You:** *"For offline, when user downloads a song, we'd also download and cache the lyrics file locally. Small file — maybe 10-50KB per song. Include it in the download package along with the audio and album art."*

---

### Follow-up 6: Cost Optimization

**Interviewer:** *"This system uses a lot of bandwidth and storage. How would you optimize costs?"*

**You:** *"Great question — at scale, infrastructure costs become significant. Here's how I'd optimize:*

*1. **Storage tiers**: Not all songs are equally popular.*
   - *Top 10% songs → S3 Standard (fast, expensive)*
   - *Next 40% → S3 Infrequent Access (cheaper, slightly slower)*
   - *Bottom 50% (long tail) → S3 Glacier (very cheap, slow retrieval)*
   - *Use access patterns to automatically move songs between tiers*

*2. **CDN optimization**:*
   - *Only cache popular songs at edge*
   - *Long-tail songs served from origin (acceptable for rarely played songs)*
   - *Use CDN analytics to identify what to cache*

*3. **Adaptive transcoding**: Maybe we don't need lossless for every song. If a song has been played only 10 times ever, just keep 128 and 256. Transcode lossless on-demand if someone actually requests it.*

*4. **Client-side caching**: Encourage the app to cache recently played songs locally. If user plays same song twice, second play is free for us.*

*5. **Reserved capacity**: For predictable base load, use reserved instances (3-year commitment) instead of on-demand. Can save 50-60% on compute costs."*

---

## Summary: What to Remember for Interview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    APPLE MUSIC SYSTEM DESIGN CHECKLIST                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. CLARIFY (3-5 min)                                                   │
│     - Scope: Streaming only or upload too?                              │
│     - Features: Audio only or video too?                                │
│     - Scale: Users, songs, concurrent streams                           │
│                                                                         │
│  2. REQUIREMENTS (3-5 min)                                              │
│     - Functional: Stream, Search, Playlist, Offline, Recommendations    │
│     - Non-functional: 200ms latency, 99.99% availability                │
│                                                                         │
│  3. SCALE ESTIMATION (2-3 min)                                          │
│     - 100M MAU → 10M concurrent → 10K RPS                               │
│     - Storage: 100M songs × 32MB = 3.2 PB                               │
│     - Bandwidth: 2.56 Tbps at peak (need CDN!)                          │
│                                                                         │
│  4. HIGH-LEVEL DESIGN (10-15 min)                                       │
│     - CDN for audio (80% cache hit)                                     │
│     - Microservices: User, Catalog, Stream, Search, Playlist            │
│     - Databases: PostgreSQL + Cassandra + Elasticsearch + Redis + S3    │
│                                                                         │
│  5. DEEP DIVE (10-15 min)                                               │
│     - Signed URLs for security                                          │
│     - DRM for content protection                                        │
│     - Adaptive bitrate for network changes                              │
│     - Recommendation: Collaborative + Content-based                     │
│                                                                         │
│  6. EDGE CASES (5 min)                                                  │
│     - CDN failure → fallback to origin                                  │
│     - Slow network → adaptive bitrate                                   │
│     - Hot release → pre-warm CDN                                        │
│     - Regional restrictions → availability check                        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Practice This Design

1. **Draw the architecture** on paper without looking
2. **Explain each component** out loud (practice speaking)
3. **Calculate scale numbers** quickly
4. **Know 3-4 deep dive topics** well

**Next Design to Study:** Rate Limiter or URL Shortener (simpler, good for building foundation)
