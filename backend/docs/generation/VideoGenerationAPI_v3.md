# ?ìƒ ?ì„± API v3

## ê°œìš”

?ˆë¡œ??ë©€???Œì´ë¸?êµ¬ì¡° ê¸°ë°˜ ?ìƒ ?œì‘ ?œìŠ¤??(video_projects, company_characters, workflow_execution)

**?‘ì—… ê¸°ê°„**: 2026-01-22  
**?„ì¹˜**: `scripts/generation/v3/`

---

## v2?ì„œ ë³€ê²½ëœ ?¬í•­

### ì¶”ê???ê²?
- **ìºë¦­???¬ì‚¬??*: ?¹ì¸??ìºë¦­?°ë? ?¬ëŸ¬ ?„ë¡œ?íŠ¸?ì„œ ?¬ì‚¬??ê°€??
- **ìºë¦­???ì‚° ê´€ë¦?*: company_characters ?Œì´ë¸”ë¡œ ?Œì‚¬ë³?ìºë¦­??ê´€ë¦?
- **?„ë¡œ?íŠ¸ ë¶„ë¦¬**: video_projects ?Œì´ë¸”ë¡œ ?„ë¡œ?íŠ¸?€ ?Œí¬?Œë¡œ??ë¶„ë¦¬
- **?„í„°ë§?& ?˜ì´ì§€?¤ì´??*: ?„ë¡œ?íŠ¸ ëª©ë¡ ì¡°íšŒ ???¤ì–‘???„í„° ?µì…˜
- **?Œí¬?Œë¡œ???¨ê³„ ì¶”ì **: workflow_stages ?Œì´ë¸”ë¡œ ?¨ê³„ë³??ì„¸ ë¡œê·¸
- **?‰ê·  ì²˜ë¦¬ ?œê°„ ê³„ì‚°**: ?µê³„ ê¸°ëŠ¥ ì¶”ê?

### ê°œì„ ??ê²?
- **?°ì´??êµ¬ì¡°**: ?„ë¡œ?íŠ¸(video_projects) ???¤í–‰(workflow_execution) ë¶„ë¦¬
- **ìºë¦­??ê´€ë¦?*: ?¹ì¸??ìºë¦­?°ëŠ” company_characters???€?¥ë˜???¬ì‚¬??
- **?•ì¥??*: ë©€???Œì´ë¸?êµ¬ì¡°ë¡??¥í›„ ê¸°ëŠ¥ ì¶”ê? ?©ì´

---

## ?œìŠ¤??êµ¬ì¡°

### ì¼€?´ìŠ¤ 1: ê¸°ì¡´ ìºë¦­???¬ìš©
```
?¬ìš©???”ì²­ (character_id ?œê³µ)
  ??
VideoProject ?ì„± (character_id ?°ê²°)
  ??
WorkflowExecution ?ì„± (status="processing")
  ??
?ìƒ ?ì„± ?œì‘
  ??
?„ë£Œ (status="completed")
```

### ì¼€?´ìŠ¤ 2: ??ìºë¦­???ì„±
```
?¬ìš©???”ì²­ (ë¶„ìœ„ê¸??¤í????…ë ¥)
  ??
VideoProject ?ì„± (character_id=null)
  ??
WorkflowExecution ?ì„± (status="generating_character")
  ??
AIê°€ ìºë¦­???ì„±
  ??
CompanyCharacter ?ì„± (approval_status="pending")
  ??
?¬ìš©??ê²€??(ë¯¸ë¦¬ë³´ê¸°)
  ??
?¹ì¸ (approval_status="approved", is_active=true)
  ??
VideoProject??character_id ?°ê²°
  ??
?ìƒ ?ì„± ?œì‘ (status="processing")
  ??
?„ë£Œ (status="completed")
```

---

## ?°ì´?°ë² ?´ìŠ¤ êµ¬ì¡°

### video_projects ?Œì´ë¸?
```sql
CREATE TABLE video_projects (
    project_id            SERIAL PRIMARY KEY,
    company_id            INT NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    account_id            INT NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    character_id          INT REFERENCES company_characters(character_id) ON DELETE SET NULL,
    
    -- ?œí’ˆ ?•ë³´
    item_name             VARCHAR(255) NOT NULL,
    item_category         VARCHAR(100),
    item_description       TEXT,
    item_url              VARCHAR(500),
    item_images           TEXT[] DEFAULT '{}',
    
    -- ìºë¦­???…ë ¥ê°?(?ˆë¡œ ?ì„±????
    character_mood        VARCHAR(255),
    character_style       VARCHAR(255),
    voice_tone            VARCHAR(255),
    voice_description     TEXT,
    
    -- ë°??•ë³´
    meme_id               INT REFERENCES memes(meme_id) ON DELETE SET NULL,
    
    -- ìµœì¢… ê²°ê³¼ë¬?
    final_video_url       TEXT,
    
    -- ?íƒœ ë°?ê´€ë¦?
    status                VARCHAR(50) DEFAULT 'draft',
    reference_notes       TEXT,
    
    -- ë¹„ìš© ë°??œê°„
    cost_estimate         NUMERIC(10, 4) DEFAULT 0,
    processing_time       INT,
    
    -- ?œê°„ ?•ë³´
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at          TIMESTAMPTZ,
    
    -- ?œì•½ ì¡°ê±´
    CONSTRAINT chk_item_images_count CHECK (cardinality(item_images) <= 3)
);

-- ?¸ë±??
CREATE INDEX idx_video_projects_company ON video_projects(company_id);
CREATE INDEX idx_video_projects_account ON video_projects(account_id);
CREATE INDEX idx_video_projects_character ON video_projects(character_id);
CREATE INDEX idx_video_projects_status ON video_projects(status);
CREATE INDEX idx_video_projects_created ON video_projects(created_at DESC);
```

**ì°¸ê³ **: `company_name`?€ ?Œì´ë¸”ì— ?€?¥í•˜ì§€ ?Šê³ , ì¡°íšŒ ??`companies` ?Œì´ë¸”ê³¼ JOIN?˜ì—¬ ê°€?¸ì˜µ?ˆë‹¤.

### company_characters ?Œì´ë¸?
```sql
CREATE TABLE company_characters (
    character_id SERIAL PRIMARY KEY,
    company_id INT NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    character_name VARCHAR(255) NOT NULL,
    character_mood VARCHAR(255) NOT NULL,
    character_style VARCHAR(255) NOT NULL,
    voice_tone VARCHAR(255) NOT NULL,
    image_url TEXT NOT NULL,
    voice_url TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    approval_status VARCHAR(20) DEFAULT 'approved' CHECK (approval_status IN ('pending', 'approved', 'rejected')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### workflow_execution ?Œì´ë¸?(V3)
```sql
CREATE TABLE workflow_execution (
    execution_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id INT NOT NULL REFERENCES video_projects(project_id) ON DELETE CASCADE,
    company_id INT NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    account_id INT NOT NULL REFERENCES accounts(account_id) ON DELETE CASCADE,
    meme_id INT REFERENCES memes(meme_id) ON DELETE SET NULL,
    
    workflow_type VARCHAR(50) DEFAULT 'video',
    status VARCHAR(50) DEFAULT 'created' CHECK (status IN (
        'created', 'generating_character', 'pending_approval', 
        'approved', 'rejected', 'processing', 'completed', 'failed', 'cancelled'
    )),
    current_stage VARCHAR(100),
    progress_percentage INT DEFAULT 0 CHECK (progress_percentage BETWEEN 0 AND 100),
    approval_status VARCHAR(50),
    
    total_cost_usd NUMERIC(10, 4) DEFAULT 0,
    retry_count INT DEFAULT 0 CHECK (retry_count BETWEEN 0 AND 10),
    error_message TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);
```

### workflow_stages ?Œì´ë¸?(?¨ê³„ë³?ë¡œê·¸)
```sql
CREATE TABLE workflow_stages (
    stage_id SERIAL PRIMARY KEY,
    execution_id UUID NOT NULL REFERENCES workflow_execution(execution_id) ON DELETE CASCADE,
    
    stage_name VARCHAR(100) NOT NULL,
    stage_order INT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'skipped')),
    
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INT,
    
    error_message TEXT
);
```

---

## API ?”ë“œ?¬ì¸??

### 1. POST /api/videos/generate

?ìƒ ?œì‘ ?”ì²­ (ê¸°ì¡´ ìºë¦­???¬ìš© OR ??ìºë¦­???ì„±)

**?”ì²­ (Multipart Form Data)**

**ì¼€?´ìŠ¤ 1: ê¸°ì¡´ ìºë¦­???¬ìš©**
```
?„ìˆ˜ ?„ë“œ:
- product_name (string): ?œí’ˆ ?´ë¦„
- product_category (string): ?œí’ˆ ì¹´í…Œê³ ë¦¬
- product_highlight (string): ?œí’ˆ ê°•ì¡°ë¬¸êµ¬ (DB??item_description???€??
- character_id (int): ê¸°ì¡´ ìºë¦­??ID
- product_images (file[]): ?œí’ˆ ?´ë?ì§€ (ìµœë? 3??

? íƒ ?„ë“œ:
- item_url (string): ?œí’ˆ ?ì„¸ ?˜ì´ì§€ URL
- meme_id (int): ë°?ID
- reference_notes (string): ì°¸ê³  ?¬í•­
```

**ì¼€?´ìŠ¤ 2: ??ìºë¦­???ì„±**
```
?„ìˆ˜ ?„ë“œ:
- product_name (string): ?œí’ˆ ?´ë¦„
- product_category (string): ?œí’ˆ ì¹´í…Œê³ ë¦¬
- product_highlight (string): ?œí’ˆ ê°•ì¡°ë¬¸êµ¬ (DB??item_description???€??
- character_mood (string): ìºë¦­??ë¶„ìœ„ê¸?(?? "ë°ê³  ?œê¸°ì°?)
- character_style (string): ìºë¦­???¤í???(?? "20?€ ?¬ì„±")
- voice_tone (string): ?Œì„± ??(?? "ì¹œê·¼??)
- character_name (string): ìºë¦­???´ë¦„
- product_images (file[]): ?œí’ˆ ?´ë?ì§€ (ìµœë? 3??

? íƒ ?„ë“œ:
- item_url (string): ?œí’ˆ ?ì„¸ ?˜ì´ì§€ URL
- meme_id (int): ë°?ID
- reference_notes (string): ì°¸ê³  ?¬í•­
```

**?‘ë‹µ (ê¸°ì¡´ ìºë¦­???¬ìš©)**
```json
{
  "execution_id": "uuid",
  "project_id": 123,
  "status": "processing",
  "message": "?ìƒ ?ì„±???œì‘?˜ì—ˆ?µë‹ˆ??
}
```

**?‘ë‹µ (??ìºë¦­???ì„±)**
```json
{
  "execution_id": "uuid",
  "project_id": 123,
  "status": "generating_character",
  "message": "ìºë¦­???ì„± ?”ì²­???‘ìˆ˜?˜ì—ˆ?µë‹ˆ?? ? ì‹œ ??ë¯¸ë¦¬ë³´ê¸°ë¥??•ì¸?˜ì„¸??
}
```

### 2. GET /api/videos/character/{character_id}

ìºë¦­??ë¯¸ë¦¬ë³´ê¸° ì¡°íšŒ

**?‘ë‹µ**
```json
{
  "character_id": 1,
  "character_name": "ë°ì? ?¬ì„± ìºë¦­??,
  "character_mood": "ë°ê³  ?œê¸°ì°?,
  "character_style": "20?€ ?¬ì„±",
  "voice_tone": "ì¹œê·¼??,
  "image_url": "presigned_url",
  "voice_url": "presigned_url",
  "approval_status": "pending",
  "created_at": "2026-01-22T10:30:00Z"
}
```

### 3. POST /api/videos/character/{character_id}/approve

ìºë¦­???¹ì¸/ê±°ë?

**?”ì²­**
```json
{
  "approved": true,
  "rejection_reason": "?Œì„± ?¤ì´ ë§ì? ?ŠìŒ"
}
```

**?‘ë‹µ (?¹ì¸ ??**
```json
{
  "character_id": 1,
  "status": "approved",
  "message": "ìºë¦­?°ê? ?¹ì¸?˜ì—ˆ?µë‹ˆ?? ?ìƒ ?ì„±???œì‘?©ë‹ˆ??
}
```

**?‘ë‹µ (ê±°ë? ??**
```json
{
  "character_id": 1,
  "status": "rejected",
  "message": "ìºë¦­?°ê? ê±°ë??˜ì—ˆ?µë‹ˆ??
}
```

### 4. GET /api/videos/characters

?Œì‚¬ ìºë¦­??ëª©ë¡ ì¡°íšŒ

**ì¿¼ë¦¬ ?Œë¼ë¯¸í„°**
- `active_only` (bool): ?œì„±?”ëœ ìºë¦­?°ë§Œ ì¡°íšŒ (ê¸°ë³¸ true)

**?‘ë‹µ**
```json
[
  {
    "character_id": 1,
    "character_name": "ë°ì? ?¬ì„± ìºë¦­??,
    "character_mood": "ë°ê³  ?œê¸°ì°?,
    "character_style": "20?€ ?¬ì„±",
    "voice_tone": "ì¹œê·¼??,
    "image_url": "s3://bucket/characters/1/image.jpg",
    "is_active": true,
    "created_at": "2026-01-22T10:30:00Z"
  }
]
```

### 5. GET /api/videos/my-projects

???„ë¡œ?íŠ¸ ëª©ë¡ ì¡°íšŒ (?„í„°ë§? ?˜ì´ì§€?¤ì´??

**ì¿¼ë¦¬ ?Œë¼ë¯¸í„°**
- `offset` (int): ?œì‘ ?„ì¹˜ (ê¸°ë³¸ 0)
- `limit` (int): ì¡°íšŒ ê°œìˆ˜ (ê¸°ë³¸ 10, ìµœë? 100)
- `status` (string): ?íƒœ ?„í„° (created, processing, completed, failed ??
- `date_from` (string): ?œì‘ ? ì§œ (ISO 8601 ?•ì‹)
- `date_to` (string): ì¢…ë£Œ ? ì§œ (ISO 8601 ?•ì‹)
- `sort_by` (string): ?•ë ¬ ê¸°ì? (created_at, completed_at)
- `order` (string): ?•ë ¬ ?œì„œ (asc, desc)

**?‘ë‹µ**
```json
{
  "total_count": 50,
  "offset": 0,
  "limit": 10,
  "workflows": [
    {
      "execution_id": "uuid",
      "project_id": 123,
      "status": "completed",
      "current_stage": "?ìƒ ?ì„± ?„ë£Œ",
      "progress_percentage": 100,
      "error_message": null,
      "created_at": "2026-01-22T10:00:00Z",
      "completed_at": "2026-01-22T11:30:00Z"
    }
  ]
}
```

---

## ì£¼ìš” ?Œì¼

### scripts/generation/v3/video_routes_v3.py

API ?”ë“œ?¬ì¸???•ì˜

ì£¼ìš” ë³€ê²½ì‚¬??
- `generate_video()`: ê¸°ì¡´ ìºë¦­???¬ìš© OR ??ìºë¦­???ì„± ? íƒ ê°€??
- `get_character_preview()`: ìºë¦­??ë¯¸ë¦¬ë³´ê¸° ì¡°íšŒ
- `approve_character_endpoint()`: ìºë¦­???¹ì¸/ê±°ë?
- `get_company_characters()`: ?Œì‚¬ ìºë¦­??ëª©ë¡ ì¡°íšŒ
- `get_my_projects()`: ?„í„°ë§?& ?˜ì´ì§€?¤ì´??ì§€??

### scripts/generation/v3/database_v3.py

?°ì´?°ë² ?´ìŠ¤ ëª¨ë¸ ë°??¨ìˆ˜

ì£¼ìš” ë³€ê²½ì‚¬??
- `VideoProject`: ?„ë¡œ?íŠ¸ ?•ë³´ ?€??
- `CompanyCharacter`: ?Œì‚¬ë³?ìºë¦­???ì‚° ê´€ë¦?
- `WorkflowExecution`: ?¤í–‰ ?íƒœ ê´€ë¦?(project_id ì°¸ì¡°)
- `WorkflowStage`: ?¨ê³„ë³??ì„¸ ë¡œê·¸
- `get_workflows_by_company_filtered()`: ?„í„°ë§?& ?˜ì´ì§€?¤ì´??
- `get_average_processing_time()`: ?‰ê·  ì²˜ë¦¬ ?œê°„ ê³„ì‚°

---

## ?ŒìŠ¤??ë°©ë²•

### 1. ?œë²„ ?¤í–‰

```bash
uv run uvicorn scripts.main:app --reload --port 8000
```

### 2. API ?ŒìŠ¤??- ê¸°ì¡´ ìºë¦­???¬ìš©

```python
import requests

# ë¡œê·¸??
response = requests.post('http://localhost:8000/auth/v3/login', json={
    'email': 'user@company.com',
    'password': 'password'
})
token = response.json()['access_token']

# ìºë¦­??ëª©ë¡ ì¡°íšŒ
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('http://localhost:8000/api/videos/characters', headers=headers)
characters = response.json()
character_id = characters[0]['character_id']

# ?ìƒ ?ì„± ?”ì²­ (ê¸°ì¡´ ìºë¦­???¬ìš©)
files = {
    'product_images': ('product.jpg', open('product.jpg', 'rb'), 'image/jpeg')
}
data = {
    'product_name': '?œí’ˆëª?,
    'product_category': 'ì¹´í…Œê³ ë¦¬',
    'product_highlight': 'ê°•ì¡°ë¬¸êµ¬',
    'character_id': character_id,
    'item_url': 'https://example.com/product'
}

response = requests.post(
    'http://localhost:8000/api/videos/generate',
    files=files,
    data=data,
    headers=headers
)
print(response.json())
```

### 3. API ?ŒìŠ¤??- ??ìºë¦­???ì„±

```python
# ?ìƒ ?ì„± ?”ì²­ (??ìºë¦­???ì„±)
files = {
    'product_images': ('product.jpg', open('product.jpg', 'rb'), 'image/jpeg')
}
data = {
    'product_name': '?œí’ˆëª?,
    'product_category': 'ì¹´í…Œê³ ë¦¬',
    'product_highlight': 'ê°•ì¡°ë¬¸êµ¬',
    'character_mood': 'ë°ê³  ?œê¸°ì°?,
    'character_style': '20?€ ?¬ì„±',
    'voice_tone': 'ì¹œê·¼??,
    'character_name': 'ë°ì? ?¬ì„± ìºë¦­??,
    'item_url': 'https://example.com/product'
}

response = requests.post(
    'http://localhost:8000/api/videos/generate',
    files=files,
    data=data,
    headers=headers
)
result = response.json()
execution_id = result['execution_id']

# ìºë¦­??ë¯¸ë¦¬ë³´ê¸° ì¡°íšŒ (AIê°€ ?ì„± ?„ë£Œ ??
# character_id???Œí¬?Œë¡œ?°ì—???•ì¸ ?„ìš”
response = requests.get(
    f'http://localhost:8000/api/videos/character/{character_id}',
    headers=headers
)
print(response.json())

# ìºë¦­???¹ì¸
response = requests.post(
    f'http://localhost:8000/api/videos/character/{character_id}/approve',
    json={'approved': True},
    headers=headers
)
print(response.json())
```

### 4. ?„ë¡œ?íŠ¸ ëª©ë¡ ì¡°íšŒ (?„í„°ë§?

```python
# ?„ë£Œ???„ë¡œ?íŠ¸ë§?ì¡°íšŒ
params = {
    'status': 'completed',
    'limit': 20,
    'sort_by': 'completed_at',
    'order': 'desc'
}
response = requests.get(
    'http://localhost:8000/api/videos/my-projects',
    params=params,
    headers=headers
)
print(response.json())

# ? ì§œ ë²”ìœ„ë¡?ì¡°íšŒ
params = {
    'date_from': '2026-01-01T00:00:00Z',
    'date_to': '2026-01-31T23:59:59Z',
    'offset': 0,
    'limit': 50
}
response = requests.get(
    'http://localhost:8000/api/videos/my-projects',
    params=params,
    headers=headers
)
print(response.json())
```

---

## ?íƒœ ?„í™˜ ?ë¦„

### ê¸°ì¡´ ìºë¦­???¬ìš©
```
created (?”ì²­ ?‘ìˆ˜)
  ??
processing (?ìƒ ?ì„± ì¤?
  ??
completed (?„ë£Œ)
```

### ??ìºë¦­???ì„±
```
created (?”ì²­ ?‘ìˆ˜)
  ??
generating_character (AIê°€ ìºë¦­???ì„± ì¤?
  ??
pending_approval (?¬ìš©??ê²€???€ê¸?
  ??
  ?œâ? approved (?¹ì¸) ??processing (?ìƒ ?ì„±) ??completed
  ??
  ?”â? rejected (ê±°ë?) ??(?¬ìƒ??ê°€??
```

---

## v2 ?€ë¹??¥ì 

### 1. ìºë¦­???¬ì‚¬??
- ?¹ì¸??ìºë¦­?°ë? company_characters???€??
- ?¬ëŸ¬ ?„ë¡œ?íŠ¸?ì„œ ?™ì¼ ìºë¦­???¬ì‚¬??ê°€??
- ìºë¦­???ì„± ?œê°„ ë°?ë¹„ìš© ?ˆì•½

### 2. ?°ì´??êµ¬ì¡° ê°œì„ 
- ?„ë¡œ?íŠ¸(video_projects)?€ ?¤í–‰(workflow_execution) ë¶„ë¦¬
- ?„ë¡œ?íŠ¸ ?•ë³´ ?êµ¬ ë³´ê?
- ?Œí¬?Œë¡œ???¬ì‹¤??ê°€??

### 3. ìºë¦­???ì‚° ê´€ë¦?
- ?Œì‚¬ë³?ìºë¦­???¼ì´ë¸ŒëŸ¬ë¦?êµ¬ì¶•
- ìºë¦­???œì„±??ë¹„í™œ?±í™” ê´€ë¦?
- ìºë¦­??ê²€??ë°??„í„°ë§?

### 4. ê³ ê¸‰ ?„í„°ë§?
- ?íƒœë³? ? ì§œë³??„ë¡œ?íŠ¸ ì¡°íšŒ
- ?˜ì´ì§€?¤ì´?˜ìœ¼ë¡??€???°ì´??ì²˜ë¦¬
- ?•ë ¬ ?µì…˜ (?ì„±?? ?„ë£Œ??

### 5. ?µê³„ ê¸°ëŠ¥
- ?‰ê·  ì²˜ë¦¬ ?œê°„ ê³„ì‚°
- ?Œì‚¬ë³??µê³„ ë¶„ì„ ê°€??
- ?Œí¬?Œë¡œ???¨ê³„ë³??Œìš” ?œê°„ ì¶”ì 

### 6. ?•ì¥??
- ë©€???Œì´ë¸?êµ¬ì¡°ë¡?ê¸°ëŠ¥ ì¶”ê? ?©ì´
- ìºë¦­??ë²„ì „ ê´€ë¦?ê°€??
- ?„ë¡œ?íŠ¸ ?œí”Œë¦?ê¸°ëŠ¥ ì¶”ê? ê°€??

---

## ?€?ê³¼???‘ì—… (DB ê¸°ë°˜ ?µì‹ )

### ?€?ì´ êµ¬í˜„??ë¶€ë¶?1: ìºë¦­???ì„±

```python
# 1. DB?ì„œ status="generating_character" ?Œí¬?Œë¡œ??ì°¾ê¸°
workflows = db.query(WorkflowExecution).filter(
    WorkflowExecution.status == "generating_character"
).all()

# 2. ê°??Œí¬?Œë¡œ?°ì— ?€??ìºë¦­???ì„±
for workflow in workflows:
    # ?„ë¡œ?íŠ¸ ?•ë³´ ê°€?¸ì˜¤ê¸?
    project = get_project_by_id(db, workflow.project_id)
    
    # AIë¡??´ë?ì§€/?Œì„± ?ì„±
    image_url = generate_character_image(
        project.character_mood, 
        project.character_style
    )
    voice_url = generate_character_voice(project.voice_tone)
    
    # CompanyCharacter ?ì„±
    character = create_company_character(
        db=db,
        company_id=project.company_id,
        character_name=f"{project.character_style} ìºë¦­??,
        character_mood=project.character_mood,
        character_style=project.character_style,
        voice_tone=project.voice_tone,
        image_url=image_url,
        voice_url=voice_url,
        approval_status='pending'
    )
    
    # ?„ë¡œ?íŠ¸??ìºë¦­???°ê²°
    update_project_character(db, project.project_id, character.character_id)
    
    # ?Œí¬?Œë¡œ???íƒœ ?…ë°?´íŠ¸
    update_workflow_status(
        db, 
        workflow.execution_id, 
        "pending_approval", 
        "ìºë¦­???ì„± ?„ë£Œ, ?¹ì¸ ?€ê¸?, 
        30
    )
```

### ?€?ì´ êµ¬í˜„??ë¶€ë¶?2: ?ìƒ ?ì„±

```python
# 1. DB?ì„œ status="processing" ?Œí¬?Œë¡œ??ì°¾ê¸°
workflows = db.query(WorkflowExecution).filter(
    WorkflowExecution.status == "processing"
).all()

# 2. ê°??Œí¬?Œë¡œ?°ì— ?€???ìƒ ?ì„±
for workflow in workflows:
    # ?„ë¡œ?íŠ¸ ?•ë³´ ê°€?¸ì˜¤ê¸?
    project = get_project_by_id(db, workflow.project_id)
    
    # ìºë¦­???•ë³´ ê°€?¸ì˜¤ê¸?
    character = get_character_by_id(db, project.character_id)
    
    # ?ìƒ ?ì„±
    video_url = generate_video(
        character_image=character.image_url,
        character_voice=character.voice_url,
        product_images=project.item_images,
        product_name=project.item_name,
        product_highlight=project.item_highlight
    )
    
    # ?„ë¡œ?íŠ¸ ?…ë°?´íŠ¸
    project.final_video_url = video_url
    project.status = 'completed'
    project.completed_at = datetime.utcnow()
    db.commit()
    
    # ?Œí¬?Œë¡œ???íƒœ ?…ë°?´íŠ¸
    update_workflow_status(
        db, 
        workflow.execution_id, 
        "completed", 
        "?ìƒ ?ì„± ?„ë£Œ", 
        100
    )
```

---

## ?œí•œ?¬í•­

- ìºë¦­???ì„± ?œê°„ ?Œìš” (AI ì²˜ë¦¬)
- ?€?ì˜ AI ?œìŠ¤???„ìš”
- DB ?´ë§ ë°©ì‹ (?¤ì‹œê°„ì„± ??Œ)
- ìºë¦­???¬ìƒ??????character_id ?ì„± (?´ë ¥ ê´€ë¦??„ìš”)

---

## ?¤ìŒ ?¨ê³„

- [ ] ìºë¦­??ë²„ì „ ê´€ë¦?(?˜ì • ?´ë ¥)
- [ ] ?„ë¡œ?íŠ¸ ?œí”Œë¦?ê¸°ëŠ¥
- [ ] ìºë¦­???œê·¸ ë°?ê²€??ê¸°ëŠ¥
- [ ] ?Œí¬?Œë¡œ???¬ì‹¤??ê¸°ëŠ¥
- [ ] ?¤ì‹œê°??Œë¦¼ (WebSocket)
- [ ] ìºë¦­??ê³µìœ  ê¸°ëŠ¥ (?Œì‚¬ ê°?
- [ ] ë¹„ìš© ì¶”ì  ë°?ë¦¬í¬??
- [ ] ?ìƒ ?¸ì§‘ ê¸°ëŠ¥

---

## ?„ë¡ ?¸ì—”???°ë™ ê°€?´ë“œ

### 1. ê¸°ì¡´ ìºë¦­?°ë¡œ ?ìƒ ?ì„±

```javascript
// 1. ìºë¦­??ëª©ë¡ ì¡°íšŒ
const token = localStorage.getItem('access_token');
const response = await fetch('http://localhost:8000/api/videos/characters', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const characters = await response.json();

// 2. ?ìƒ ?ì„± ?”ì²­
const formData = new FormData();
formData.append('product_name', '?œí’ˆëª?);
formData.append('product_category', 'ì¹´í…Œê³ ë¦¬');
formData.append('product_highlight', 'ê°•ì¡°ë¬¸êµ¬');
formData.append('character_id', characters[0].character_id);
formData.append('item_url', 'https://example.com/product');
formData.append('product_images', productImageFile);

const response = await fetch('http://localhost:8000/api/videos/generate', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
});

const result = await response.json();
// result = {execution_id: "uuid", project_id: 123, status: "processing", ...}
```

### 2. ??ìºë¦­???ì„± ???ìƒ ?ì„±

```javascript
// 1. ?ìƒ ?ì„± ?”ì²­ (??ìºë¦­??
const formData = new FormData();
formData.append('product_name', '?œí’ˆëª?);
formData.append('product_category', 'ì¹´í…Œê³ ë¦¬');
formData.append('product_highlight', 'ê°•ì¡°ë¬¸êµ¬');
formData.append('character_mood', 'ë°ê³  ?œê¸°ì°?);
formData.append('character_style', '20?€ ?¬ì„±');
formData.append('voice_tone', 'ì¹œê·¼??);
formData.append('character_name', 'ë°ì? ?¬ì„± ìºë¦­??);
formData.append('item_url', 'https://example.com/product');
formData.append('product_images', productImageFile);

const response = await fetch('http://localhost:8000/api/videos/generate', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` },
  body: formData
});

const result = await response.json();
// result = {execution_id: "uuid", project_id: 123, status: "generating_character", ...}

// 2. ìºë¦­???ì„± ?„ë£Œ ?€ê¸?(?´ë§ ?ëŠ” WebSocket)
// character_id???Œí¬?Œë¡œ???íƒœ?ì„œ ?•ì¸ ?„ìš”

// 3. ìºë¦­??ë¯¸ë¦¬ë³´ê¸° ì¡°íšŒ
const charResponse = await fetch(
  `http://localhost:8000/api/videos/character/${characterId}`,
  { headers: { 'Authorization': `Bearer ${token}` } }
);
const character = await charResponse.json();

// 4. ìºë¦­???¹ì¸
const approvalResponse = await fetch(
  `http://localhost:8000/api/videos/character/${characterId}/approve`,
  {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ approved: true })
  }
);
```

### 3. ?„ë¡œ?íŠ¸ ëª©ë¡ ì¡°íšŒ (?„í„°ë§?

```javascript
// ?„ë£Œ???„ë¡œ?íŠ¸ë§?ì¡°íšŒ
const params = new URLSearchParams({
  status: 'completed',
  limit: 20,
  sort_by: 'completed_at',
  order: 'desc'
});

const response = await fetch(
  `http://localhost:8000/api/videos/my-projects?${params}`,
  { headers: { 'Authorization': `Bearer ${token}` } }
);

const data = await response.json();
// data = {total_count: 50, offset: 0, limit: 20, workflows: [...]}
```

---

## ?‘ì—… ?„ë£Œ??

2026.01.22

