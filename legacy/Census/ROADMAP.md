Phase 0: existing infrastructure (done)
0A. Superset load monitoring
superset-conf-lab FastAPI + PostgreSQL + Superset + Nginx + Redis
done Mock Cisco server (CUCM/UCCX simulation)
done Proxy gateway — auto-collects every 60s
done Time-series PostgreSQL storage
done Superset dashboards (CPU, calls in queue, agents)
done Docker Compose orchestration with health checks
0B. CUCM phone management app
CUCM-PHONE-APP FastAPI + Alembic + Docker
done FastAPI backend with modular app/ structure
done Alembic DB migrations setup
done Admin user creation script
done Dockerfile + docker-compose
0C. Meetings/conferences app
Meetings-App React (Vite) frontend for CMS/MP
done React + Vite project scaffold
in progress Conference management UI
next Connect to CMS CAPI for live moderator
0D. CENSUS skeleton
CENSUS FastAPI shell — no models or services yet
done docker-compose.yml with pgvector/pg15
done main.py — lifespan, CORS, health check, scheduler
done requirements.txt with all dependencies
done .env / .env.example configuration
Phase 1: CENSUS core database (you are here)
1A. Data models (SQLAlchemy)
Create the 5-dimension schema in PostgreSQL
current database/models.py — User, Endpoint, Location, TelephonyLine, SwitchConnection, KnowledgeTicket
next database/session.py — async engine + session factory + init_db
next core/config.py — Pydantic Settings with all .env vars
next Alembic initial migration
File to create: database/models.py, database/session.py, core/config.py
1B. API layer (Pydantic + FastAPI routes)
Expose CENSUS data to frontend and other services
next schemas/census.py — UserResponse, EndpointResponse, LocationResponse
next api/routers/census.py — GET /endpoints, GET /users, GET /locations
next POST /api/v1/census/sync — manual sync trigger (background task)
File to create: schemas/census.py, api/routers/census.py
Phase 2: data extraction services
2A. CUCM data extraction (via AXLerate)
Pull devices + users + lines from CUCM through your existing REST gateway
next services/axlerate_client.py — HTTP client to AXLerate
next Method: fetch_registered_endpoints() — devices + IPs + model
next Method: fetch_cucm_users() — enduser table (replaces AD)
next Method: fetch_telephony_lines() — DN + CSS + partition
Depends on: AXLerate running in same Docker network. SQL queries go to CUCM Informix DB via AXL executeSQLQuery
2B. Network topology scraper
Extract switch + port from each phone's CDP web page
next services/phone_scraper.py — async HTTP scraper (aiohttp + BeautifulSoup)
next Semaphore for max 200 concurrent connections
next CDP parsing: switch name + port extraction from HTML
next Filter by LOCAL_SUBNET_PREFIX (lab safety)
Prerequisite: CUCM Web Access must be enabled on phones. Check Enterprise Parameters.
2C. Sync engine (the brain)
Orchestrate all extractors, cross-reference, bulk upsert to DB
next services/sync_engine.py — run_full_sync() async function
next Step A: upsert users from CUCM
next Step B: upsert endpoints with IP addresses
next Step C: scrape CDP and upsert switch connections
next Step D: upsert telephony lines
next Wire to APScheduler (nightly 03:00)
This is the most critical file. It connects AXLerate + Scraper + DB into one pipeline.
Phase 3: Superset integration + load prediction
3A. Connect Superset to CENSUS DB
superset-conf-lab Add census_db as data source in Superset
later Add CENSUS PostgreSQL as second database in Superset
later Create dashboard: device inventory heatmap by building
later Create dashboard: unregistered devices alert panel
3B. Replace mock with real CUCM/UCCX
Switch from simulation to production data
later Update proxy gateway URLs to real CUCM/UCCX IPs
later Add CUCM AXL authentication (application user)
later CDR/CMR ingestion pipeline (FTP pull from billing server)
3C. Load prediction (Erlang C)
Predict staffing needs based on UCCX + Finesse data
later services/erlang_engine.py — Erlang C calculation
later Finesse REST API integration (agent states)
later UCCX historical queue data pipeline
later Superset gauge: pressure meter 0-100 for shift manager
Phase 4: action modules
4A. Horizon — remote hardware reset
SSH to switches for PoE bounce on stuck phones
later services/horizon.py — Netmiko SSH to Cisco IOS switches
later power inline never / auto on specific port
later API endpoint: POST /horizon/bounce/{mac_address}
later Pull switch_ip + port from CENSUS (no manual lookup)
Prerequisite: TACACS+ service account for switch SSH access. Request from network team.
4B. Zero touch deployment
Barcode scan to provision phones + VC endpoints
later services/zero_touch.py — AXL addPhone + addLine
later xAPI hardening for VC (disable BT/WiFi)
later Frontend: barcode input page with auto-focus
later Auto-assign next free DN from pool
4C. Smart ticket + knowledge base
AI-powered troubleshooting with pgvector RAG
later services/smart_ticket.py — CRUD + pre-check event
later services/knowledge_base.py — pgvector semantic search
later Sentence-transformers embedding (all-MiniLM-L6-v2)
later Resolution suggestion from ticket history
4D. VC self-service + call drop analyzer
Meetings-App CMS CAPI integration
later CMS CAPI client — list callLegs, mute, drop
later Disconnect reason translator (SIP codes to Hebrew)
later Connect Meetings-App React frontend to these APIs
4E. Auto phone heal + ghost sweeper
Background jobs that fix problems without human intervention
later Nightly: detect unregistered devices in CENSUS
later Auto ITL reset via SSH if phone stuck
later Ghost sweeper: flag devices of deactivated users
later Auto-remove orphaned phones from CUCM
Phase 5: CMA portal (unified React frontend)
5A. Core portal shell
Single React app that replaces all separate UIs
later React SPA with routing (device view, tickets, VC, analytics)
later Device inventory table with search/filter/sort
later Smart ticket dashboard with AI suggestions
later Barcode scanning page for zero touch
later Finesse-style visual agent display
Phase 6: production deployment
6A. Air-gapped deployment
Package everything for the secure network
later Docker save all images to .tar files
later Transfer via approved media to classified network
later Production .env with real CUCM/UCCX/CMS IPs
later Firewall rules: port 80/443 to Voice VLAN for scraper
later CUCM Application User with Standard AXL API Access role
later User acceptance testing with technicians