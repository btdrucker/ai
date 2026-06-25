# Search Engineering Metadata Model

## A. Team and Organization

| Field | Value |
|-------|-------|
| Mission | Discover Everything Nike |
| Location | WHQ Swift / Various Remote |
| Email | Lst-digitaltech.CiCSearch@nike.com |
| Confluence Space | SENG -- https://confluence.nike.com/spaces/SENG |
| PagerDuty | https://nikeb2c.pagerduty.com/schedules#POJ75K8 |
| Blog | https://pages.github.nike.com/search-engineering/blogs/ |

### Slack Channels

| Channel | Purpose |
|---------|---------|
| #search-platform-squad | Primary team channel |
| #nde-search-devs | Developer channel |
| #content-discovery | Cross-squad content discovery |
| #nde-search-monitoring | Monitoring and alerting |
| #search-support-triage | Intake for stakeholder support requests |
| #nde-product-feeds | Product Feeds squad |
| #cic-seonav | SEO and Navigation squad |
| #consumer-product-data | Consumer Product Data squad |
| #search_feed_collab | Feed collaboration |
| #search-integration | Integration discussions |
| #cm-search-grid-dynamics-collab | Grid Dynamics collaboration |

### Jira

| Project Key | Board |
|-------------|-------|
| SRPLT | https://jira.nike.com/secure/RapidBoard.jspa?rapidView=25116&projectKey=SRPLT |

**Open epics:** https://jira.nike.com/issues/?jql=Issuetype%20%3D%20Epic%20AND%20Project%20%3D%20SRPLT%20AND%20status%20!%3D%20Done%20ORDER%20BY%20created%20DESC

---

## B. Squads and Rosters

Rosters change frequently. **Always fetch live data** -- do not rely on hardcoded names.

| Source | Confluence Page ID | URL |
|--------|--------------------|-----|
| Scrum Squads and Rosters | 296516891 | https://confluence.nike.com/pages/viewpage.action?pageId=296516891 |

To retrieve the current roster, use:

```
confluence_get_page(page_id="296516891")
```

The page contains squad membership tables organized by squad name (e.g. Operational Tools / Dora, Data Services / Meili, Product Feeds, SEO and Navigation, Consumer Product Data) with roles, engineers, tech leads, data scientists, product managers, and support staff (principal engineers, engineering managers, directors).

---

## C. Service Inventory

> **Source:** https://confluence.nike.com/pages/viewpage.action?pageId=1316266559
> For the latest, use: `confluence_get_page(page_id="1316266559")`

56 active services (fetch live page for current count). Mostly EC2; Lambdas, web, and server noted in tables. GitHub org: `nike-internal`.

### Query-time (OCSP)

| # | Service | Repo | Pipeline |
|---|---------|------|----------|
| 1 | kingpin-v1 | search.service.kingpin-v1 | searchscience BMX |
| 2 | searchservice-v2 | search.service.searchservice-v2 | searchscience BMX |
| 3 | searchservice-v3 | search.service.searchservice-v3 | searchscience BMX |
| 4 | searchclusters-v1 | search.service.searchclusters | searchscience BMX |
| 5 | searchclusters-v2 | search.service.searchclusters-v2 | searchscience BMX |
| 6 | searchindexes-v2 | search.service.searchindexes-v2 | searchscience BMX |
| 7 | searchindexes-v3 | search.service.searchindexes-v3 | searchscience BMX |
| 8 | searchschemas-v3 | search.service.searchschemas-v3 | searchscience BMX |
| 9 | searchschemas-v4 | search.service.searchschemas-v4 | searchscience BMX |
| 10 | searchstrategies | search.service.searchstrategies | searchscience BMX |
| 11 | searchtypeahead | search.service.searchtypeahead | searchscience BMX |
| 12 | searchupgradeshim-v2 | search.service.searchupgradeshim-v2 | searchscience BMX |
| 13 | ingestupgradeshim-v2 | search.service.ingestupgradeshim-v2 | searchscience BMX |

### Ingest Pipeline

| # | Service | Repo | Pipeline |
|---|---------|------|----------|
| 1 | envoy | search.service.envoy | productfeed BMX |
| 2 | searchingest-v2 | search.service.searchingest-v2 | searchscience BMX |
| 3 | searchreplicator-v3 | search.service.searchreplicator-v3 | searchscience BMX |
| 4 | searchregionreplicationloader | search.service.searchregionreplicationloader | searchscience BMX |

### Product Feeds

| # | Service | Repo | Pipeline |
|---|---------|------|----------|
| 1 | productfeedv2 | search.service.productfeedv2 | productfeed BMX |
| 2 | pfeventhandler | search.service.pfeventhandler | productfeed BMX |
| 3 | productfeedprocessorv2 | search.service.productfeedprocessorv2 | productfeed BMX |
| 4 | productfeedcardv2 | search.service.productfeedcardv2 | productfeed BMX |
| 5 | productfeedrollupsv2 | search.service.productfeedrollupsv2 | productfeed BMX |
| 6 | productfeedstreamv2 | search.service.productfeedstreamv2 | productfeed BMX |
| 7 | productfeedoinkv1 | search.service.productfeedoinkv1 | productfeed BMX |
| 8 | pfthreadcrusher | search.service.pfthreadcrusher | productfeed BMX |
| 9 | pfmonitor | search.service.pfmonitor | productfeed BMX |
| 10 | pfinventory | search.service.pfinventory | searchscience BMX |

### GC Services

| # | Service | Repo | Pipeline |
|---|---------|------|----------|
| 1 | pfetl | gcde.service.pfetl | productfeed BMX |
| 2 | pfthreadlistener | gcde.service.pfthreadlistener | productfeed BMX |
| 3 | pfbatchingester | gcde.service.pfbatchingester | productfeed BMX |

### Smart Search Pipeline

| # | Service | Repo | Pipeline |
|---|---------|------|----------|
| 1 | smartsearch-v1 | search.service.smartsearch-v1 | searchscience BMX |
| 2 | raptor-v1 | search.service.raptor-v1 | searchscience BMX |
| 3 | conceptzero (commerce) | search.service.conceptzero | searchscience BMX |
| 4 | conceptzero-v3 (waffle) | search.service.conceptzerov3 | searchscience BMX |
| 5 | conceptingest (commerce) | search.service.conceptingest | searchscience BMX |
| 6 | conceptingest-v3 (waffle) | search.service.conceptingestv3 | searchscience BMX |
| 7 | conceptsetl-v3 | search.service.conceptsetl-v3 | searchscience BMX |
| 8 | recommendconcepts-v1 | search.service.recommendconcepts-v1 | searchscience BMX |

### Rules and Ranking

| # | Service | Repo | Pipeline |
|---|---------|------|----------|
| 1 | compositerules-v1 | search.service.compositerules-v1 | searchscience BMX |
| 2 | compositerules-v2 | search.service.compositerules-v2 | searchscience BMX |
| 3 | recommendrules-v2 | search.service.recommendrules-v2 | searchscience BMX |
| 4 | recommendnav-v1 | search.service.recommendnavv1 | searchscience BMX |
| 5 | navattributes-v2 (waffle only) | search.service.navattributes-v2 | searchscience BMX |
| 6 | sdrrecommendationsservice-v2 | search.service.sdrrecommendationsservice-v2 | searchscience BMX |
| 7 | threadsignalcomposer-v2 | search.service.threadsignalcomposer-v2 | searchscience BMX |

### Collections

| # | Service | Repo | Pipeline |
|---|---------|------|----------|
| 1 | collections-v2 | search.service.collectionsv2 | productfeed BMX |
| 2 | collectionsmanager-v2 | search.service.collectionsmanagerv2 | productfeed BMX |
| 3 | collectionsui | search.web.collectionsui | -- |

### Other Services

| # | Service | Repo | Pipeline |
|---|---------|------|----------|
| 1 | kirby-v2 | search.service.kirbyv2 | productfeed BMX |
| 2 | maestro | search.service.maestro | productfeed BMX |
| 3 | visualsearchservice | search.service.visualsearchservice | productfeed BMX |
| 4 | apolloauthentication-v1 | search.server.apolloauthenticationv1 | -- |

### Lambda Functions

| # | Service | Repo | Pipeline |
|---|---------|------|----------|
| 1 | elasticsearchstatscollector | search.lambda.elasticsearchstatscollector | searchscience BMX |
| 2 | replicationlistener | search.lambda.replicationlistener | searchscience BMX |
| 3 | s3replicationlistener | search.lambda.s3replicationlistener | searchscience BMX |
| 4 | s3regionreplicator | search.lambda.s3regionreplicator | searchscience BMX |

---

## D. Architecture

> **Sources:**
> - Architecture overviews: https://confluence.nike.com/pages/viewpage.action?pageId=1723904004
> - OCSP Product Ingest: https://confluence.nike.com/pages/viewpage.action?pageId=594897671
> - Product Feed V2 HLD: https://confluence.nike.com/pages/viewpage.action?pageId=194766412
> - Nike.net OCSP HLA: https://confluence.nike.com/pages/viewpage.action?pageId=1504674707
> - Kingpin API: https://confluence.nike.com/pages/viewpage.action?pageId=708435971

### OCSP (OmniChannel Search Platform)

The current-generation search platform. Key concepts:

- **Kingpin** is the query-time API (endpoint: `/search/products/v1/secured`). It serves hydrated lists of ranked product results for product walls, LHN (left-hand navigation) filters, and search results. Primarily consumer-facing (nike.com, Nike App) but also supports internal use cases (store athletes, consumer services, merchandisers).

- **Kingpin query flow:**
  1. **Match** -- ConceptZero v2/v3 converts search terms into matched concepts and an enhanced Elasticsearch query. Uses vector search (Bronto matching) when exact match fails.
  2. **Rules** -- CompositeRules v2 returns DOC_FILTER rules (product eligibility), merchandising rules (boosts/buries/excludes), and navigation rules (LHN filters).
  3. **L1 Ranking** -- OpenSearch query using signals-based ranking strategy.
  4. **L2 Ranking** -- Bronto ML re-ranking of top 100 results (cached in Redis, TTL=15min).
  5. **Final query** -- Combines L2 boosts, filters, aggregations (LHN), collapse (rollups), and hydration fields. Executes against OpenSearch.
  6. **Navigation** -- Label ordering library builds navigation URLs; RecommendConcepts provides labels and navIds.

- **Kingpin dependencies:**

| Dependency | Service | Purpose |
|------------|---------|---------|
| ConceptZero v2/v3 | /search/concepts/v2 | Query understanding -- matched concepts + enhanced ES query |
| CompositeRules v2 | /composite/rules/v2 | DOC_FILTER, merch rules, navigation rules |
| RecommendConcepts v1 | /recommend/concepts/v1 | Concept details (type, navId, labels, parents) |
| Collections v2 | /product_feed/dynamic_collections/v2 | Dynamic collection where clauses |
| Bronto Ranking | /ranking/bronto/v1 | ML re-ranking of L1 results |

### Product Ingest (OCSP)

Envoy is the notification gateway. It receives events from upstream data sources and routes them through the OCSP indexing pipeline.

**Data sources and notification volumes (per hour, prod):**

| Source | Volume | Type |
|--------|--------|------|
| CPA External | ~380k/hr | SQS |
| CPG (product groups) | ~170k/hr | Kafka |
| Collections | ~6/hr | Kafka |
| Signals | 1/day (batch) | S3 |
| Concepts | ~40/day | NSP |
| CPA Full Load | ~3.6M/hr (60k/min) | SQS |

### Product Feeds (Legacy)

The legacy ingest pipeline, still active for several clusters:

**Clusters:** product_feed_threads, product_feed_rollups, product_feed_retail, product_feed_cards, product_feed_active_rollups

**Data sources:** Content (SQS), Merch (SQS), Collections (NSP), Inventory (NSP), Launch (SQS), Concepts (NSP), Customization (SQS)

**Hydration sources:** Content, Merch (merchproduct, merchskus, merchprice, productcontent), Collections, Inventory (availableskus, availablegtins), Launch, Concepts (recommend concepts), Customization

### OpenSearch / Elasticsearch Clusters

- **search-consumer-products** -- OCSP main index
- **product_feed_threads** -- PF threads
- **product_feed_rollups** -- PF rollups
- **product_feed_retail** -- PF retail
- **product_feed_cards** -- PF cards
- **product_feed_active_rollups** -- PF active rollups

### Region Replication

S3-based cross-region replication between:
- Commerce East / Commerce West (Prod/Test)
- Waffle East / Waffle West (Prod/Test)

Services involved: searchreplicator-v3, searchregionreplicationloader, replicationlistener (lambda), s3replicationlistener (lambda), s3regionreplicator (lambda).

### Nike.net (Wholesale)

OCSP extended via Discover layer for wholesale (Nike.net) use cases. Architecture documented at page 1504674707.

### Hybrid Search (Vector + Lexical)

Kingpin integrates with AWS Sagemaker for generating text embeddings used in hybrid search (vector + lexical). Documented at page 1630276319.

---

## E. Observability

### SignalFx Dashboards

| Dashboard | URL |
|-----------|-----|
| Domain | https://app.signalfx.com/#/dashboard/DedW4UPAYAA?groupId=DedW4OvAcCQ&configId=DoN5ebBAgAM |
| Core Search | https://app.signalfx.com/#/dashboard/EXOHspDAYAA?groupId=EXOHmCgAYE4&configId=EXOHu1EAgAA |
| Product Feed | https://app.signalfx.com/#/dashboard/DanhqbCAgAA?groupId=DYrKRGkAYAA&configId=DoN5BR-AcAA |
| Front-end Experience | https://app.signalfx.com/#/dashboard/DwV7ln8AYAA?groupId=DwV7lkuAcAA&configId=DwV7mLiAgAA |
| Kingpin v1 | https://app.signalfx.com/#/dashboard/GKQEytpAYAA?groupId=D6EXYIbAYAA&configId=GKQFdxCAgAA |

### Splunk

- URL: https://nike.splunkcloud.com/
- App: nike_search
- Common filters: `index=app environment=prod`

### Ops Tools

| Tool | Environment | URL |
|------|-------------|-----|
| Search Admin (OCSP) | Waffle Prod | https://searchadmin.search-prod.nikecloud.com/search |
| Search Admin (OCSP) | Waffle Test | https://searchadmin.search-test.nikecloud.com/search |
| Apollo | Waffle Prod | https://apollo.search-prod.nikecloud.com/apolloproductwallsv1/ |
| Apollo | Waffle Test | https://apollo.search-test.nikecloud.com/apolloproductwallsv1 |
| Search Admin | Commerce Prod | https://adminops.prod.commerce.nikecloud.com/searchadminv2/clusters/list |
| Search Admin | Commerce Test | https://adminops.test.commerce.nikecloud.com/searchadminv2/clusters/list |
| Apollo | Commerce Prod | https://adminops.prod.commerce.nikecloud.com/apollov1/ |
| Apollo | Commerce Test | https://adminops.test.commerce.nikecloud.com/apollov1/ |

---

## F. Runbooks and Support

| Runbook | Page ID | URL |
|---------|---------|-----|
| On-Call Runbook | 1412924074 | https://confluence.nike.com/pages/viewpage.action?pageId=1412924074 |
| OCSP Runbook | 1067450707 | https://confluence.nike.com/pages/viewpage.action?pageId=1067450707 |
| OCSP - Kingpin Runbook | 1001758528 | https://confluence.nike.com/pages/viewpage.action?pageId=1001758528 |
| Elasticsearch Snapshot & Restore | 1678219506 | https://confluence.nike.com/pages/viewpage.action?pageId=1678219506 |
| Production Support Procedures | 1109989205 | https://confluence.nike.com/pages/viewpage.action?pageId=1109989205 |
| Support Triage | 365599973 | https://confluence.nike.com/pages/viewpage.action?pageId=365599973 |
| OCSP Alerts | 1067450610 | https://confluence.nike.com/pages/viewpage.action?pageId=1067450610 |
| OCSP SignalFX Audit | 1062753920 | https://confluence.nike.com/pages/viewpage.action?pageId=1062753920 |

---

## G. Onboarding

> **Source:** https://confluence.nike.com/pages/viewpage.action?pageId=372992442

Key onboarding steps (full details on Confluence):

1. **Access:** Okta, Jira (SRPLT project), Confluence (via BAAT), PagerDuty, Splunk, SignalFx
2. **GitHub:** Access to nike-internal org, add to search-meili or search-denali teams
3. **BMX:** App.BMX.SRCHSCIENCE.Users and Application.BMX.productfeed.Users (via IDLocker)
4. **AWS:** Waffle Iron test (554036784086) and prod (832844619813) PowerRole
5. **Cerberus/NSP:** App.cerberus.sdb.search.global, App.Application.NSP.Search.Admin
6. **Dev tools:** Xcode CLT, Homebrew, Git, JQ, container runtime (Podman, Colima, etc. -- not Docker Desktop; see `podman` skill for one option), ElasticSearch 7.1, Java (OpenJDK), IntelliJ Ultimate / Cursor, Bruno (API testing)

### Architecture Learning Sessions

> **Source:** https://confluence.nike.com/pages/viewpage.action?pageId=1723904004

**High-level overviews:**
- Search 101: Core Search & Current Platform -- https://nike.box.com/s/mgv7px1pwla2coak98m7bqpzfyrg6l1i
- Core Search & Current Architecture Overview (May 2021) -- https://nike.box.com/s/ml59r30d7ii6vfhsmyay9bddoo95vv3c
- Search Architecture Follow Up (June 2021) -- https://nike.box.com/s/gbr92gb4aqi8xteizqm8r5ttpbfih9oe

**Current-gen (OCSP) deep dives:**
- Kingpin -- https://nike.ent.box.com/s/xrkr1do0fetri0iwkz6gpnxrdw0y3d63
- Concept Zero v2 -- https://nike.box.com/s/tiykhvi7a2yr7qyalmys753owqgj0a3l
- ConceptZero/ConceptIngest deep dives -- https://confluence.nike.com/spaces/SENG/pages/436639642
- Dotnet 101 series -- https://nikedigital.slack.com/archives/C06K31HMB5L/p1742252700045649
- Apollo V2 demo -- https://nike.box.com/s/d5r7ql1zgvgrox5d83f4zhoy964gnzep

**Product Feeds deep dives:**
- Code Repo Rundown (June 2021) -- https://nike.box.com/s/oq7p14dtmg80ce2uil9gu9fxlfqj79r6
- Product Feed Processor v2 walkthrough -- https://nike.box.com/s/oxtossl7wywe0ie4zxneeizfjh1g9d31
- Product Feed Event Handler v2 walkthrough -- https://nike.box.com/s/b74y40cbcsjc8ia8puciitt0mjxa5cjr
- Product Feed Oink walkthrough -- https://nike.box.com/s/55s1p25cq9rf43wzfsw4tqm6n5pycofx
- Product Feed Threads walkthrough -- https://nike.box.com/s/b3tzw04e398gznrlxjf9ajn2n23vpmnu

**Core Search deep dives:**
- Schemas & Querying walkthrough -- https://nike.box.com/s/kssuflmuxznazyzoe65nu6ydgdhncwui
- Region Replication & Replicator v3 -- https://nike.box.com/s/lqisz86a3m4mxvsqtyrc3lyoh74jiap4
- SDR Walkthrough -- https://nike.box.com/s/hdpinkt8ijfxgt69iayt65wie7kdhth7
- SDR Signal Ingestion deep dive -- https://nike.box.com/s/dut33vrixaetsubm1b5dcna143lvfa0f
- Concept Ingest & Concept Zero walkthrough -- https://nike.box.com/s/cglrsbjkhkqfrorkxpe1zuijjq5x5q6c
- Navigation deep dive -- https://nike.box.com/s/1mqy30maf54dok6zdqoocfkrqqxpo5aq
- Autocomplete v2 -- https://confluence.nike.com/display/SENG/AutoComplete+-+Functional+Deep+Dive+-+WIP

**Operations:**
- Production Support Onboarding -- https://nike.box.com/s/oftvbztcv0ja304593813b75rpgryive
- Performance Testing intro -- https://nike.box.com/s/i37pxx652uua36di3wwegtgg28rntmpu

---

## H. CI/CD and Pipelines

### BMX Jenkins Instances

| Instance | URL | Services |
|----------|-----|----------|
| Search Science | https://searchscience.jenkins.bmx.nikecloud.com/ | Core search, OCSP, smart search, concepts, rules, ranking |
| Product Feed | https://productfeed.jenkins.bmx.nikecloud.com/ | Product feeds, envoy, collections, kirby, maestro |
| Smart Search | https://smartsearch.jenkins.bmx.nikecloud.com/ | Smart search specific builds |

### AWS Accounts

| Account | ID | Purpose |
|---------|----|---------|
| Waffle Iron Test | 554036784086 | Non-prod / test |
| Waffle Iron Prod | 832844619813 | Production |
| Commerce Test | (fetch from Confluence page 372992442) | Legacy test |
| Commerce Prod | (fetch from Confluence page 372992442) | Legacy production |

### Deployment Environments

Services deploy across four environment pairs:
- **Commerce East** -- Prod / Test
- **Commerce West** -- Prod
- **Waffle East** -- Prod / Test
- **Waffle West** -- Prod

---

## I. Key Confluence Pages Index

### Portal and Team

| Page | ID | URL |
|------|----|-----|
| Search Engineering Portal | 360218896 | https://confluence.nike.com/pages/viewpage.action?pageId=360218896 |
| Scrum Squads and Rosters | 296516891 | https://confluence.nike.com/pages/viewpage.action?pageId=296516891 |
| Team Agreements | 476747303 | https://confluence.nike.com/pages/viewpage.action?pageId=476747303 |
| Onboarding for Search | 372992442 | https://confluence.nike.com/pages/viewpage.action?pageId=372992442 |
| Team Demos | 377272008 | https://confluence.nike.com/pages/viewpage.action?pageId=377272008 |
| ITC Squad | 847649718 | https://confluence.nike.com/pages/viewpage.action?pageId=847649718 |

### Architecture and Design

| Page | ID | URL |
|------|----|-----|
| Architecture Overviews & Deep Dives | 1723904004 | https://confluence.nike.com/pages/viewpage.action?pageId=1723904004 |
| OCSP Search API (Kingpin) | 708435971 | https://confluence.nike.com/pages/viewpage.action?pageId=708435971 |
| OCSP - Product Ingest | 594897671 | https://confluence.nike.com/pages/viewpage.action?pageId=594897671 |
| Product Feed V2 HLD | 194766412 | https://confluence.nike.com/pages/viewpage.action?pageId=194766412 |
| Nike.net OCSP HLA | 1504674707 | https://confluence.nike.com/pages/viewpage.action?pageId=1504674707 |
| OCSP Future Architecture (WIP) | 1241244211 | https://confluence.nike.com/pages/viewpage.action?pageId=1241244211 |
| OCSP Platform | 372307105 | https://confluence.nike.com/pages/viewpage.action?pageId=372307105 |
| Kingpin Sagemaker Integration | 1630276319 | https://confluence.nike.com/pages/viewpage.action?pageId=1630276319 |
| HybridSearch workflow in Kingpin | 1497237608 | https://confluence.nike.com/pages/viewpage.action?pageId=1497237608 |
| Nike.net OCSP Offerings Flow | 1497675690 | https://confluence.nike.com/pages/viewpage.action?pageId=1497675690 |
| Nike.net OCSP Inventory Flow | 1497247911 | https://confluence.nike.com/pages/viewpage.action?pageId=1497247911 |
| Nike.net OCSP Consumer Product Flow | 1497247905 | https://confluence.nike.com/pages/viewpage.action?pageId=1497247905 |
| Nike.net OCSP Complete Ingest Flow | 1452412765 | https://confluence.nike.com/pages/viewpage.action?pageId=1452412765 |
| Search Personalization Tracker | 1635262137 | https://confluence.nike.com/pages/viewpage.action?pageId=1635262137 |

### Deployment and Operations

| Page | ID | URL |
|------|----|-----|
| Service Deployment Matrix | 1316266559 | https://confluence.nike.com/pages/viewpage.action?pageId=1316266559 |
| Kingpin Performance Testing | 1367485479 | https://confluence.nike.com/pages/viewpage.action?pageId=1367485479 |
| Kingpin Perf Tests with HOD | 1653448756 | https://confluence.nike.com/pages/viewpage.action?pageId=1653448756 |
| Secure Kingpin Endpoint | 1265086499 | https://confluence.nike.com/pages/viewpage.action?pageId=1265086499 |
| OCSP NPE Cluster Setup | 1497241081 | https://confluence.nike.com/pages/viewpage.action?pageId=1497241081 |
| Search Team Tagging | 688761958 | https://confluence.nike.com/pages/viewpage.action?pageId=688761958 |
| OCSP Vulnerabilities Fix | 1683063599 | https://confluence.nike.com/pages/viewpage.action?pageId=1683063599 |
| Nike.net OCSP Work Breakdown | 1504674685 | https://confluence.nike.com/pages/viewpage.action?pageId=1504674685 |

### Support

| Page | ID | URL |
|------|----|-----|
| Search Engineering Support | 371693153 | https://confluence.nike.com/pages/viewpage.action?pageId=371693153 |
| Search Support Triage | 365599973 | https://confluence.nike.com/pages/viewpage.action?pageId=365599973 |
| Production Support Procedures | 1109989205 | https://confluence.nike.com/pages/viewpage.action?pageId=1109989205 |
| On-Call Runbook | 1412924074 | https://confluence.nike.com/pages/viewpage.action?pageId=1412924074 |
| Splunk Alert: concepts ingest | 1152340462 | https://confluence.nike.com/pages/viewpage.action?pageId=1152340462 |

### Additional Spaces

| Space | Key | Notes |
|-------|-----|-------|
| Search Engineering | SENG | Primary space |
| Product Feeds API | DEN | Product Feed V2 HLD and related docs |
