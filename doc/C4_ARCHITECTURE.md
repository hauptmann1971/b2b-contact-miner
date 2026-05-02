# C4 Architecture Diagrams - B2B Contact Miner

## Level 1: System Context Diagram

```mermaid
graph TB
    User[User/Business Analyst] -->|Uses| WebUI[Web UI Dashboard]
    User -->|Runs| Pipeline[Contact Mining Pipeline]
    
    WebUI -->|Displays| System[B2B Contact Miner System]
    Pipeline -->|Executes| System
    
    System -->|Queries| SERP[SERP API<br/>Yandex/Google Search]
    System -->|Crawls| Websites[Target Websites]
    System -->|Extracts with| LLM[LLM Service<br/>YandexGPT/GigaChat]
    System -->|Stores in| MySQL[(MySQL Database)]
    
    System -->|Monitored by| SonarCloud[SonarCloud<br/>Code Quality]
    System -->|Deployed on| Server[Production Server<br/>85.198.86.237]
    
    style System fill:#1168bd,color:#fff
    style User fill:#08427b,color:#fff
    style MySQL fill:#08427b,color:#fff
    style LLM fill:#08427b,color:#fff
    style SERP fill:#08427b,color:#fff
```

**Description:** The B2B Contact Miner system helps users discover business contacts by searching for keywords, crawling websites, and extracting contact information using AI.

---

## Level 2: Container Diagram

```mermaid
graph TB
    subgraph "Production Server (85.198.86.237)"
        Nginx[Nginx Reverse Proxy<br/>Port 80] -->|Proxies to| FlaskApp[Flask Web Server<br/>web_server.py<br/>Port 5000]
        Nginx -->|Health checks| FastAPI[FastAPI Monitoring<br/>api_server.py<br/>Port 8000]
        
        FlaskApp <-->|Reads/Writes| MySQL[(MySQL<br/>Remote)]
        FastAPI <-->|Reads| MySQL
        MainPipeline[Main Pipeline<br/>main.py] <-->|Reads/Writes| MySQL
        MainPipeline -->|Task Queue| TaskQueue[Task Queue Worker<br/>workers/db_task_queue.py]
        TaskQueue <-->|Reads/Writes| MySQL
        
        Supervisor[Supervisor<br/>Process Manager] -->|Manages| FlaskApp
        Supervisor -->|Manages| FastAPI
    end
    
    subgraph "External Services"
        SERP[SERP API Provider]
        Websites[Target Websites]
        LLM[LLM Provider<br/>YandexGPT/GigaChat]
        GitHub[GitHub Repository]
        SonarCloud[SonarCloud SaaS]
    end
    
    MainPipeline -->|Search queries| SERP
    MainPipeline -->|Crawls| Websites
    MainPipeline -->|Extracts contacts| LLM
    
    GitHub -->|CI/CD| SonarCloud
    SonarCloud -->|Quality reports| GitHub
    
    style FlaskApp fill:#1168bd,color:#fff
    style FastAPI fill:#1168bd,color:#fff
    style MainPipeline fill:#1168bd,color:#fff
    style TaskQueue fill:#1168bd,color:#fff
    style MySQL fill:#08427b,color:#fff
    style Nginx fill:#438dd5,color:#fff
```

**Containers:**
1. **Nginx** - Reverse proxy for secure external access
2. **Flask Web Server** - User interface for viewing results
3. **FastAPI Monitoring** - Health check and metrics API
4. **Main Pipeline** - Core contact mining orchestrator
5. **Task Queue Worker** - Async task processing
6. **MySQL** - Persistent data storage (Docker examples use image `mysql:8.0` in `doc/docker-compose.yml`; production host version is not pinned in this repo)
7. **Database-backed Task Queue** - Persistent async processing in MySQL

---

## Level 3: Component Diagram - Main Pipeline

```mermaid
graph TB
    subgraph "main.py - Pipeline Orchestrator"
        KeywordLoader[Keyword Loader<br/>pending keywords from DB] --> StateManager[State Manager<br/>utils/state_manager.py → pipeline_state]
        StateManager --> SearchOrchestrator[Search Orchestrator]
        
        SearchOrchestrator --> SERPGetter[SERP Getter<br/>getters/serp_getter.py]
        SERPGetter --> SearchResultProcessor[Search Result Processor<br/>services/crawler_service.py]
        
        SearchResultProcessor --> DomainCrawler[Domain Crawler<br/>Playwright; DomainRateLimiter per domain;<br/>delay between pages; regex e.g. sitemap loc, quick contact hints]
        DomainCrawler --> ContentExtractor[Content Extractor<br/>services/extraction_service.py]
        
        ContentExtractor --> LLMCaller[LLM Caller<br/>calls YandexGPT/GigaChat]
        LLMCaller --> ContactParser[Contact Parser<br/>parses LLM response]
        
        ContactParser --> ResultSaver[Result Saver<br/>services/export_service.py]
        ResultSaver --> DBWriter[Database Writer<br/>models/database.py]
        
        DBWriter --> TaskQueueWriter[Task Queue Writer<br/>workers/db_task_queue.py]
    end
    
    MySQL[(MySQL)]
    KeywordLoader <-->|KeywordService.get_pending_keywords| MySQL
    StateManager <-->|PipelineState rows| MySQL
    DBWriter <-->|domain_contacts, contacts, crawl_logs, …| MySQL
    TaskQueueWriter <-->|task_queue rows| MySQL
    
    subgraph "Supporting Components"
        Config[Configuration<br/>config/settings.py]
        Logger[Logging System<br/>utils/logger.py]
        ErrorHandler[Error Handler<br/>retry logic]
    end
    
    Config --> KeywordLoader
    Config --> SERPGetter
    Config --> LLMCaller
    Config --> DBWriter
    
    Logger --> SearchOrchestrator
    Logger --> DomainCrawler
    Logger --> ResultSaver
    
    ErrorHandler --> SERPGetter
    ErrorHandler --> LLMCaller
    ErrorHandler --> DBWriter
    
    style SearchOrchestrator fill:#1168bd,color:#fff
    style DomainCrawler fill:#1168bd,color:#fff
    style ContentExtractor fill:#1168bd,color:#fff
    style ResultSaver fill:#1168bd,color:#fff
```

**Key Components:**
1. **Keyword Loader** - Loads pending keywords (`is_processed == false`) via `KeywordService.get_pending_keywords`
2. **State Manager** - Persists run/progress to `pipeline_state` in MySQL (`StateManager`)
3. **Search Orchestrator** - Coordinates search → crawl → extract pipeline
4. **SERP Getter** - Fetches search results from SERP API
5. **Domain Crawler** - Playwright crawl with per-domain semaphore (`DomainRateLimiter`, `MAX_CONCURRENT_DOMAINS_PER_SITE`), `DELAY_BETWEEN_REQUESTS` between pages, and regex helpers (e.g. sitemap `<loc>`, quick contact hints in text)
6. **Content Extractor** - Uses LLM to extract contacts from HTML
7. **Result Saver** - Saves extracted contacts to database
8. **Task Queue Writer** - Inserts rows into `task_queue` for async workers (workers also read/update `task_queue` and persist crawl/results tables)

---

## Level 3: Component Diagram - Web UI

```mermaid
graph TB
    subgraph "web_server.py - Flask Application"
        Browser[Web Browser] -->|HTTP Requests| FlaskRoutes[Flask Routes]
        
        FlaskRoutes --> DashboardView[Dashboard View<br/>templates/index.html]
        FlaskRoutes --> KeywordsView[Keywords Management<br/>templates/keywords.html]
        FlaskRoutes --> ContactsView[Contacts Viewer<br/>templates/contacts.html]
        FlaskRoutes --> HealthCheck[Health Check API<br/>/health endpoint]
        
        DashboardView --> StatsService[Statistics Service<br/>calculates metrics]
        KeywordsView --> KeywordService[Keyword Service<br/>services/keyword_service.py]
        ContactsView --> ExportService[Export Service<br/>services/export_service.py]
        
        StatsService --> DBQuery[Database Queries<br/>models/database.py]
        KeywordService --> DBQuery
        ExportService --> DBQuery
        HealthCheck --> DBQuery
        
        DBQuery <-->|SQL| MySQL[(MySQL)]
    end
    
    subgraph "Templates"
        BaseTemplate[base.html<br/>base layout]
        DashboardTemplate[index.html<br/>main dashboard]
        KeywordsTemplate[keywords.html<br/>keyword management]
        ContactsTemplate[contacts.html<br/>contact viewer]
        LlmDataTemplate[llm_data.html<br/>LLM telemetry]
    end
    
    FlaskRoutes --> BaseTemplate
    DashboardView --> DashboardTemplate
    KeywordsView --> KeywordsTemplate
    ContactsView --> ContactsTemplate
    FlaskRoutes --> LlmDataTemplate
    
    style FlaskRoutes fill:#1168bd,color:#fff
    style DBQuery fill:#1168bd,color:#fff
    style ExportService fill:#1168bd,color:#fff
```

**Key Components:**
1. **Flask Routes** - HTTP request handlers
2. **Dashboard View** - Shows statistics and pipeline status
3. **Keywords Management** - Add/edit/search keywords
4. **Contacts Viewer** - Browse and filter extracted contacts
5. **Export Service** - Export contacts to CSV/Excel
6. **Health Check** - System health monitoring endpoint

---

## Level 3: Component Diagram - Task Queue System

```mermaid
graph TB
    subgraph "workers/db_task_queue.py - Task Queue"
        TaskProducer[Task Producer<br/>adds tasks to queue] --> TaskTable[(task_queue table)]
        
        TaskConsumer[Task Consumer<br/>worker loop] <-->|locks rows, runs handlers| TaskTable
        TaskConsumer --> RetryHandler[Retry Handler<br/>handles failures]
        
        RetryHandler -->|Re-queues| TaskTable
        RetryHandler -->|Marks failed| TaskTable
        
        TaskScheduler[Task Scheduler<br/>scripts/scheduler.py] -->|Scheduled tasks| TaskTable
        
        MonitorWorker[Monitor Worker<br/>scripts/monitor_workers.py] <-->|Reads status| TaskTable
    end
    
    MySQL_TQ[(MySQL)]
    TaskTable <-->|read/write| MySQL_TQ
    TaskConsumer <-->|handlers persist search_results, domain_contacts, contacts, crawl_logs, keywords| MySQL_TQ
    
    subgraph "Task Types"
        SearchTask[search_keyword<br/>Fetch SERP results]
        CrawlTask[crawl_domain<br/>Crawl website]
        ExtractTask[extract_contacts<br/>LLM extraction]
        SaveTask[save_results<br/>Save to DB]
    end
    
    TaskProducer --> SearchTask
    TaskProducer --> CrawlTask
    TaskProducer --> ExtractTask
    TaskProducer --> SaveTask
    
    TaskConsumer --> SearchTask
    TaskConsumer --> CrawlTask
    TaskConsumer --> ExtractTask
    TaskConsumer --> SaveTask
    
    style TaskConsumer fill:#1168bd,color:#fff
    style TaskProducer fill:#1168bd,color:#fff
    style RetryHandler fill:#1168bd,color:#fff
```

**Key Components:**
1. **Task Producer** - Creates tasks when pipeline runs (`add_task` inserts into `task_queue`)
2. **Task Consumer** - Worker loop locks rows, runs `search_keyword` / `crawl_domain` / `extract_contacts` / `save_results` handlers, updates `task_queue` and related tables via SQLAlchemy sessions
3. **Retry Handler** - Implements retry logic with exponential backoff
4. **Task Scheduler** - Schedules recurring tasks
5. **Monitor Worker** - Monitors queue health and stuck tasks

---

## Level 4: Code Structure - Services Layer

```mermaid
graph LR
    subgraph "services/ - Business Logic"
        CrawlerService[crawler_service.py<br/>Website crawling]
        ExtractionService[extraction_service.py<br/>LLM contact extraction]
        ExportService[export_service.py<br/>export_to_flat_csv, export_to_csv,<br/>export_to_excel, get_export_summary]
        KeywordService[keyword_service.py<br/>Keyword management]
    end
    
    subgraph "getters/ - Data Retrieval"
        SERPGetter[serp_getter.py<br/>SERP API client]
        YandexGetter[yandex_getter.py<br/>Yandex specific]
        GoogleGetter[google_getter.py<br/>Google specific]
    end
    
    subgraph "checkers/ - Validation"
        KeywordChecker[keyword_checker.py<br/>Validate keywords]
        ContactChecker[contact_checker.py<br/>Validate contacts]
    end
    
    subgraph "utils/ - Utilities"
        StateManager[state_manager.py<br/>Progress tracking]
        Logger[logger.py<br/>Logging setup]
        Helpers[helpers.py<br/>Common utilities]
    end
    
    CrawlerService --> SERPGetter
    CrawlerService --> YandexGetter
    CrawlerService --> GoogleGetter
    
    ExtractionService --> CrawlerService
    ExportService --> ExtractionService
    
    KeywordService --> KeywordChecker
    CrawlerService --> ContactChecker
    
    CrawlerService --> StateManager
    ExtractionService --> Logger
    ExportService --> Logger
    
    style CrawlerService fill:#1168bd,color:#fff
    style ExtractionService fill:#1168bd,color:#fff
    style ExportService fill:#1168bd,color:#fff
```

**Key Components:**
1. **crawler_service.py** - Website crawling with Playwright, per-domain limits, link and page content extraction
2. **extraction_service.py** - LLM-based contact extraction from HTML and response handling
3. **export_service.py** - DB export: flat CSV, per-domain CSV, Excel, and `get_export_summary`
4. **keyword_service.py** - Keywords in DB: add, pending selection, `is_processed`, summaries
5. **serp_getter.py** - SERP client for search results (as labeled on the diagram)
6. **yandex_getter.py** - Yandex-oriented getter (as labeled on the diagram)
7. **google_getter.py** - Google-oriented getter (as labeled on the diagram)
8. **keyword_checker.py** - Keyword validation rules (as labeled on the diagram)
9. **contact_checker.py** - Contact validation rules (as labeled on the diagram)
10. **state_manager.py** - Pipeline run progress in `pipeline_state` (`StateManager`)
11. **logger.py** - Logging setup used by services (as labeled on the diagram)
12. **helpers.py** - Shared helper utilities (as labeled on the diagram)

*Note:* Arrows show dependency direction (A → B means A uses B). Blue node fill marks emphasized `services/` modules. Diagram file names are the intended code-level split; compare with `services/`, `getters/`, `checkers/`, and `utils/` in the repo—some labels may not match the current tree.

---

## Database Schema Overview

```mermaid
erDiagram
    KEYWORDS ||--o{ SEARCH_RESULTS : has
    SEARCH_RESULTS ||--o{ DOMAIN_CONTACTS : found_on
    DOMAIN_CONTACTS ||--o{ CONTACTS : contains
    KEYWORDS ||--o{ PIPELINE_STATE : tracked_by
    TASK_QUEUE ||--o{ TASK_QUEUE : "depends_on (self-ref)"
    
    KEYWORDS {
        int id PK
        string keyword
        string language
        string country
        boolean is_processed
        datetime created_at
    }
    
    SEARCH_RESULTS {
        int id PK
        int keyword_id FK
        string url
        string title
        text snippet
        int position
        boolean is_processed
    }
    
    DOMAIN_CONTACTS {
        int id PK
        int search_result_id FK
        string domain
        json tags
        json metadata
        json contacts_json
        string extraction_method
        int confidence_score
    }
    
    CONTACTS {
        int id PK
        int domain_contact_id FK
        enum contact_type
        string value
        boolean is_verified
    }
    
    PIPELINE_STATE {
        int id PK
        string run_id
        int keyword_id FK
        string status
        int progress_percent
        int websites_processed
        int contacts_found
    }
    
    TASK_QUEUE {
        int id PK
        string task_name
        string task_type
        text payload
        string status
        int priority
        int retry_count
        int max_retries
        int depends_on_task_id FK
    }
    
    CRAWL_LOGS {
        int id PK
        string domain
        string url
        int status_code
        text error_message
        int pages_crawled
        int duration_seconds
        text llm_request
        text llm_response
        string llm_model
        datetime crawled_at
    }
```

---

## Deployment Architecture

```mermaid
graph TB
    subgraph "Developer Machine"
        DevCode[Development Code] -->|git push| GitHub[GitHub Repository]
    end
    
    subgraph "GitHub Actions CI/CD"
        GitHub -->|Triggers| SonarScan[SonarCloud Scan]
        SonarScan -->|Quality Report| SonarCloud[SonarCloud Dashboard]
        SonarScan -->|Pass/Fail| GitHub
    end
    
    subgraph "Production Server (85.198.86.237)"
        GitHub -->|git pull| ServerCode[Server Code]
        
        ServerCode --> Nginx[Nginx<br/>Port 80]
        ServerCode --> FlaskApp[Flask App<br/>Port 5000]
        ServerCode --> FastAPI[FastAPI<br/>Port 8000]
        ServerCode --> Pipeline[Main Pipeline]
        
        Supervisor[Supervisor] -->|Manages| FlaskApp
        Supervisor -->|Manages| FastAPI
        
        FlaskApp <-->|Reads/Writes| RemoteDB[(Remote MySQL<br/>kalmyk3j.beget.tech)]
        FastAPI <-->|Reads| RemoteDB
        Pipeline <-->|Reads/Writes| RemoteDB
        
    end
    
    User[End User] -->|http://85.198.86.237| Nginx
    Admin[Administrator] -->|SSH| ServerCode
    Admin -->|scp .env| ServerCode
    
    style GitHub fill:#438dd5,color:#fff
    style SonarCloud fill:#438dd5,color:#fff
    style RemoteDB fill:#08427b,color:#fff
```

---

## Key Design Decisions

### 1. Database Choice
- **MySQL** for persistent storage (relational data, ACID compliance); local Docker example uses image `mysql:8.0` (`doc/docker-compose.yml`)

### 2. Task Queue
- **Database-backed queue** instead of external message brokers
- Pros: Persistence, no extra infrastructure, easy monitoring
- Cons: Slower than message brokers, but acceptable for this use case

### 3. LLM Integration
- **Multiple providers** (YandexGPT, GigaChat) for redundancy
- **Fallback mechanism** if one provider fails

### 4. Web Framework
- **Flask** for UI (simple, lightweight, Jinja2 templates)
- **FastAPI** for monitoring API (async, auto-generated docs)

### 5. Deployment
- **Nginx reverse proxy** for security and performance
- **Supervisor** for process management
- **SSH + Git** for deployment (simple, no Docker overhead)

### 6. Code Quality
- **SonarCloud** for continuous code quality monitoring
- **GitHub Actions** for automated analysis on every push

---

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | HTML/CSS/JS + Jinja2 | Web UI templates |
| **Backend Web** | Flask 3.x | Web application framework |
| **Backend API** | FastAPI | Monitoring and health check API |
| **Database** | MySQL (`mysql:8.0` in `doc/docker-compose.yml`) | Primary data storage |
| **Browser Automation** | Playwright | Website crawling |
| **AI/ML** | YandexGPT, GigaChat | Contact extraction from HTML |
| **Task Queue** | Custom DB-based | Async task processing |
| **Web Server** | Nginx | Reverse proxy |
| **Process Manager** | Supervisor (`apt install supervisor` on deploy) | Process supervision |
| **CI/CD** | GitHub Actions | Automated testing and analysis |
| **Code Quality** | SonarCloud | Static code analysis |
| **Deployment** | SSH + Git | Manual deployment |

---

## Security Considerations

1. **Network Security**
   - Flask binds to localhost only (127.0.0.1)
   - Nginx provides external access with security headers
   - SSH key authentication for server access

2. **Data Security**
   - `.env` file not committed to Git
   - Database credentials in environment variables
   - SonarCloud token stored securely

3. **Application Security**
   - Input validation on all user inputs
   - SQL injection prevention (SQLAlchemy ORM)
   - XSS protection (security headers)

4. **Monitoring**
   - Health check endpoints
   - Error logging
   - SonarCloud vulnerability scanning
