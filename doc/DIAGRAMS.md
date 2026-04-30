# 📊 Диаграммы взаимодействия модулей

## 1. Общая архитектура системы

```mermaid
graph TB
    User[Пользователь] -->|Запускает| Main[main.py<br/>ContactMiningPipeline]
    
    Main -->|Инициализирует| DB[(MySQL Database)]
    Main -->|Создает| Workers[Task Workers<br/>20 async workers]
    
    Main -->|Использует| KeywordSvc[Keyword Service]
    Main -->|Использует| SerpSvc[SERP Service]
    Main -->|Использует| CrawlerSvc[Crawler Service]
    Main -->|Использует| ExtractSvc[Extraction Service]
    
    KeywordSvc -->|Читает/Пишет| DB
    SerpSvc -->|DuckDuckGo API| Internet[Интернет]
    CrawlerSvc -->|Playwright| Internet
    ExtractSvc -->|YandexGPT API| Internet
    
    Workers -->|Обрабатывают задачи| CrawlerSvc
    
    style Main fill:#e1f5ff
    style DB fill:#fff4e1
    style Internet fill:#f0f0f0
```

---

## 2. Поток выполнения пайплайна

```mermaid
sequenceDiagram
    participant M as main.py
    participant K as Keyword Service
    participant S as SERP Service
    participant C as Crawler Service
    participant E as Extraction Service
    participant DB as Database
    
    M->>K: get_pending_keywords()
    K->>DB: SELECT * FROM keywords WHERE is_processed=0
    DB-->>K: Список ключевых слов
    K-->>M: [keyword1, keyword2, ...]
    
    loop Для каждого ключевого слова
        M->>S: search(keyword, country, language)
        S->>Internet: DuckDuckGo API запрос
        Internet-->>S: Результаты поиска (URLs)
        S-->>M: List[SearchResult]
        
        M->>DB: save_results(search_results)
        
        loop Для каждого сайта (до 5)
            M->>C: crawl_domain(url)
            C->>Internet: Playwright краулинг
            Internet-->>C: HTML контент страниц
            C-->>M: List[{url, content, type}]
            
            M->>E: extract_contacts(content_list)
            E->>E: Regex извлечение
            alt Обфусцированные email
                E->>Internet: YandexGPT API
                Internet-->>E: Распарсенные контакты
            end
            E->>E: MX верификация email
            E-->>M: ContactInfo
            
            M->>DB: save domain_contacts + contacts
        end
        
        M->>K: mark_as_processed(keyword_id)
    end
```

---

## 3. Взаимодействие сервисов при краулинге

```mermaid
graph LR
    A[Crawler Service] -->|1. Проверка| B{Robots.txt}
    B -->|Заблокировано| C[Пропустить домен]
    B -->|Разрешено| D[2. Запуск Playwright]
    
    D -->|3. Загрузка| E[Sitemap.xml]
    E -->|Есть sitemap| F[Извлечь URLs]
    E -->|Нет sitemap| G[Парсинг главной страницы]
    
    F --> H[4. Приоритизация URL]
    G --> H
    
    H -->|Высокий приоритет| I[/contact, /contacts]
    H -->|Средний приоритет| J[/about, /team]
    H -->|Низкий приоритет| K[Остальные страницы]
    
    I --> L[5. Краулинг страниц]
    J --> L
    K --> L
    
    L -->|Таймаут 30с| M{Успех?}
    L -->|Успех| M
    
    M -->|Контакты найдены| N[Ранняя остановка ✓]
    M -->|10 страниц| O[Достигнут лимит]
    M -->|Нет контактов| P[Продолжить]
    
    N --> Q[Возврат контента]
    O --> Q
    P --> Q
    
    style N fill:#90EE90
    style C fill:#FFB6C6
```

---

## 4. Извлечение контактов (Extraction Pipeline)

```mermaid
flowchart TD
    A[HTML Контент] --> B{Тип страницы?}
    
    B -->|Contact page| C[Поиск обфускации]
    B -->|Обычная страница| D[Regex извлечение]
    
    C -->|Есть obfuscation| E[Добавить в LLM очередь]
    C -->|Нет obfuscation| D
    
    D --> F[Email regex]
    D --> G[Telegram regex]
    D --> H[LinkedIn regex]
    D --> I[Phone regex]
    
    F --> J{Найдено email?}
    J -->|Да| K[Проверка формата]
    J -->|Нет| L[Пропустить]
    
    K --> M[MX верификация]
    M -->|Valid MX| N[Сохранить email ✓]
    M -->|Invalid MX| O[Отметить как непроверенный]
    
    E --> P{LLM включен?}
    P -->|Да| Q[YandexGPT запрос]
    P -->|Нет| R[Пропустить LLM]
    
    Q --> S[Парсинг JSON ответа]
    S --> T[Извлеченные контакты]
    
    N --> U[ContactInfo объект]
    O --> U
    T --> U
    G --> U
    H --> U
    I --> U
    
    style N fill:#90EE90
    style Q fill:#FFE4B5
```

---

## 5. База данных - схема отношений

```mermaid
erDiagram
    KEYWORDS ||--o{ SEARCH_RESULTS : "has"
    SEARCH_RESULTS ||--o{ DOMAIN_CONTACTS : "contains"
    DOMAIN_CONTACTS ||--o{ CONTACTS : "stores"
    
    KEYWORDS {
        int id PK
        string keyword
        string language
        string country
        boolean is_processed
        datetime last_crawled_at
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
        string extraction_method
        int confidence_score
        boolean is_verified
    }
    
    CONTACTS {
        int id PK
        int domain_contact_id FK
        enum contact_type
        string value
        boolean is_verified
        datetime verification_date
    }
```

---

## 6. Асинхронная очередь задач

```mermaid
graph TB
    subgraph "Task Queue System"
        Q[(MySQL task_queue table)]
        
        subgraph "Workers Pool"
            W1[Worker 1]
            W2[Worker 2]
            W3[Worker 3]
            WDots[...]
            W20[Worker 20]
        end
    end
    
    Main[Main Pipeline] -->|add_task| Q
    Q -->|lock & fetch task| W1
    Q -->|lock & fetch task| W2
    Q -->|lock & fetch task| W3
    Q -->|lock & fetch task| W20
    
    W1 -->|execute| Task1[Crawl Domain]
    W2 -->|execute| Task2[Extract Contacts]
    W3 -->|execute| Task3[Save/Retry Task]
    
    Task1 -->|status update| Q
    Task2 -->|status update| Q
    Task3 -->|status update| Q
    
    style Q fill:#FFE4B5
    style W1 fill:#90EE90
    style W2 fill:#90EE90
    style W3 fill:#90EE90
```

---

## 7. Retry механизм и обработка ошибок

```mermaid
flowchart TD
    A[Начало операции] --> B{Попытка 1}
    
    B -->|Успех| C[✓ Возврат результата]
    B -->|Ошибка| D{Попытка 2?<br/>wait 2s}
    
    D -->|Успех| C
    D -->|Ошибка| E{Попытка 3?<br/>wait 4s}
    
    E -->|Успех| C
    E -->|Ошибка| F{Попытка 4?<br/>wait 8s}
    
    F -->|Успех| C
    F -->|Ошибка| G[✗ Логирование ошибки]
    
    G --> H{Критическая ошибка?}
    H -->|Да| I[Остановить пайплайн]
    H -->|Нет| J[Пропустить и продолжить]
    
    C --> K[Сохранение в БД]
    J --> K
    
    style C fill:#90EE90
    style G fill:#FFB6C6
    style I fill:#FF6B6B
```

---

## 8. Пример полного цикла обработки одного ключевого слова

```mermaid
graph TB
    Start[Начало: 'финтех стартап'] --> Step1[1. SERP Search]
    
    Step1 -->|DuckDuckGo| Results[10 результатов]
    
    Results --> Site1[Сайт 1: wikipedia.org]
    Results --> Site2[Сайт 2: generation-startup.ru]
    Results --> Site3[Сайт 3: mkechinov.ru]
    Results --> Site4[Сайт 4: rb.ru]
    Results --> Site5[Сайт 5: vitvet.com]
    
    Site1 -->|robots.txt OK| Crawl1[Краулинг: 10 страниц<br/>31 сек]
    Crawl1 --> Extract1[Извлечение: 0 email]
    Extract1 --> Save1[Сохранено в БД]
    
    Site2 -->|robots.txt BLOCKED| Skip2[Пропущен ✗]
    
    Site3 -->|robots.txt OK| Crawl3[Краулинг: 1 страница<br/>42 сек]
    Crawl3 --> Extract3[Извлечение: 1 email]
    Extract3 --> Verify3[MX верификация ✓]
    Verify3 --> Save3[Сохранено: info@mkechinov.ru]
    
    Site4 -->|robots.txt OK| Crawl4[Краулинг: 1 страница<br/>8 сек]
    Crawl4 --> Extract4[Извлечение: 1 email]
    Extract4 --> Verify4[MX верификация ✓]
    Verify4 --> Save4[Сохранено: team@rb.ru]
    
    Site5 -->|robots.txt OK| Crawl5[Краулинг: TIMEOUT<br/>30с на страницу]
    Crawl5 --> Timeout5[Все страницы таймаутятся]
    
    Save1 --> Summary[Итог ключевого слова]
    Skip2 --> Summary
    Save3 --> Summary
    Save4 --> Summary
    Timeout5 --> Summary
    
    Summary --> Final[2 контакта найдено<br/>5 сайтов обработано<br/>~5 минут]
    
    style Save3 fill:#90EE90
    style Save4 fill:#90EE90
    style Skip2 fill:#FFB6C6
    style Timeout5 fill:#FFD700
```

---

## 9. Компоненты надежности

```mermaid
graph LR
    subgraph "Reliability Features"
        R1[Retry Logic<br/>tenacity]
        R2[Error Isolation<br/>try-except]
        R3[Graceful Shutdown<br/>Ctrl+C handler]
        R4[Connection Pool<br/>SQLAlchemy]
        R5[Rate Limiting<br/>Semaphores]
        R6[Deduplication<br/>Domain/DB rules]
    end
    
    R1 --> Protect[Защита от сбоев]
    R2 --> Protect
    R3 --> Protect
    R4 --> Protect
    R5 --> Protect
    R6 --> Protect
    
    Protect --> Stable[Стабильная работа<br/>пайплайна]
    
    style Protect fill:#90EE90
    style Stable fill:#90EE90
```

---

## 10. Конфигурация и настройка

```mermaid
graph TB
    EnvFile[.env файл] --> Settings[config/settings.py<br/>Pydantic Settings]
    
    Settings --> DB_Config[Database Config]
    Settings --> SERP_Config[SERP Provider Config]
    Settings --> LLM_Config[LLM Config]
    Settings --> Crawler_Config[Crawler Config]
    
    DB_Config --> Main[main.py]
    SERP_Config --> Main
    LLM_Config --> Main
    Crawler_Config --> Main
    
    Main --> Services[Все сервисы]
    
    EnvFile -.->|DATABASE_URL| DB_Config
    EnvFile -.->|SERP_API_PROVIDER| SERP_Config
    EnvFile -.->|YANDEX_IAM_TOKEN| LLM_Config
    EnvFile -.->|MAX_PAGES_PER_DOMAIN| Crawler_Config
    
    style EnvFile fill:#FFE4B5
    style Settings fill:#E1F5FF
    style Main fill:#90EE90
```

---

Эти диаграммы показывают, как все модули взаимодействуют друг с другом для выполнения задачи поиска и извлечения контактной информации!
