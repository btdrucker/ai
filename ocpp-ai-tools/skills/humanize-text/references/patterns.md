# AI Writing Patterns Reference

A catalog of detectable patterns in AI-generated text, organized by category with severity tiers. Each pattern includes a description, what to watch for, and before/after examples drawn from technical and professional writing contexts.

**Note on examples:** The "After" versions throughout this catalog contain invented specifics (version numbers, timing data, team anecdotes) to illustrate what human-written prose looks and feels like. They are not literal rewrites of the "Before" text. When applying this catalog to real documents, do not fabricate details -- cut vague claims or describe evidence that actually exists.

---

## Document Type Matrix

Not all patterns apply equally to all writing. Identify the document type before rewriting.

| Document type | Voice | Precise counts | Structured lists | Consistent formatting |
|---|---|---|---|---|
| Investigation report, analysis | First person ("we found"), flag uncertainty | When they serve analysis | Fine | Natural variation OK |
| Architecture overview, design doc | First person OK for authored docs | When they clarify scale | Fine | Consistency is fine |
| Decision document, options analysis | Team first person ("we recommend") | When comparing options | Yes | Consistency expected |
| Field mapping, API reference, spec | Third person, clarity over voice | Yes -- precision matters | Yes -- scannability matters | Consistency expected |
| Internal wiki, knowledge base | Depends on content type | When useful | Yes | Consistency is fine |
| README, changelog | Third person typical | When useful | Yes | Consistency expected |
| Email, Slack post, status update | First person | As needed | Rarely | Not applicable |
| PR description, commit message | First person OK | Rarely | Rarely | Not applicable |
| Presentation notes, slide deck | Match presenter voice | Approximate | Collapse into talking points | Natural variation OK |
| Code comments | Third person, terse | When they clarify | No | Not applicable |
| Runbook, playbook | Second person imperative ("Run," "Check") | When specifying thresholds | Yes -- steps must be unambiguous | Consistency expected |
| Incident post-mortem | First person ("we observed"), past tense | Timeline precision matters | Fine | Natural variation OK |
| RFC, design proposal | First person OK ("we propose") | When comparing alternatives | Fine | Consistency is fine |

Patterns 1-24 (vocabulary, filler, formatting) apply almost universally. Patterns 25-35 (structural) depend on context. A field mapping table should be consistently formatted. An investigation summary should not read like an omniscient narrator.

---

## Severity and Priority

**Always fix (high severity):** Never acceptable in published text.
- 19 (chatbot artifacts), 20 (knowledge-cutoff disclaimers), 21 (sycophantic tone), 17 (emojis in prose), 22 (filler phrases), 24 (generic conclusions)

**Fix when you see them (medium severity):** Almost always a problem, occasionally legitimate.
- 1 (inflated significance), 3 (-ing padding), 4 (promotional language), 5 (vague attributions), 7 (AI vocabulary), 8 (copula avoidance), 9 (negative parallelisms), 11 (synonym cycling), 23 (excessive hedging)

**Fix by density, not by instance (low severity):** One occurrence is normal English. A cluster is a tell.
- 10 (rule of three), 12 (false ranges), 13 (em dashes), 14 (boldface), 16 (title case)

**Context-dependent (structural):** Apply per document type.
- 25-35 (all structural patterns), 6 (challenges sections), 15 (inline-header lists), 2 (notability emphasis), 30 (inventory counts)

### Density Detection

Do not flag isolated instances. Look for clusters. A paragraph with "Additionally," one em dash, and "robust" has three independent patterns co-occurring in a few sentences -- that's a rewrite candidate. A paragraph with one "Additionally" surrounded by clean prose is probably fine.

A practical threshold: three or more distinct patterns within a two-paragraph span is a cluster. Below that, you're looking at normal English variation.

---

## Avoiding Over-Correction

The most common failure mode is fixing things that were not broken.

**Do not strip useful structure.** If a document uses bold headers in a list and the headers add information beyond what the body says, leave them. Removing useful structure to chase a "more human" feel makes the document worse.

**Do not make technical docs casual.** A field mapping that says "this field is basically the same as that one" is worse than one that says "maps directly to `targetField`." Match the register.

**Do not rewrite clean prose.** If a paragraph triggers no patterns, leave it. The goal is to fix problems, not to rewrite everything in a different voice.

**Do not substitute your own cliches.** Replacing "leverages" with "uses" is good. Replacing every formal construction with a casual one trades one uniform voice for another.

**When in doubt, leave it.** A slightly AI-sounding paragraph that is accurate and clear is better than a rewritten one that is muddled or inaccurate.

---

## Voice and Authenticity

Removing AI patterns is necessary but not sufficient. Replacing them with manufactured personality is equally detectable. Follow concrete rules instead:

1. **Use first person when the author is known and the document describes their work.** "We reviewed the codebase" is more accurate than "The codebase was reviewed." Skip first person in reference docs, API docs, and field mappings.
2. **Express uncertainty only where it is genuine.** If you could not verify something, say so. If you could, state it plainly. Do not hedge verified facts and do not manufacture uncertainty for texture.
3. **Do not consciously try to "vary rhythm."** Instead, do not let every sentence land at the same length. If you notice uniformity, break one sentence short or let another run longer. The goal is absence of artificial uniformity, not presence of artificial variation.
4. **Match section depth to actual complexity** in prose docs. In structured reference material, consistent depth per entry is correct.
5. **Never fabricate specifics to replace vague ones.** No invented people, studies, statistics, or sources. Cut the vague claim or describe the evidence honestly.

---

## Content Patterns

### 1. Inflated Significance

AI writing inflates the importance of ordinary things. Statements about how something "represents a shift" or "plays a crucial role" appear where plain description would suffice.

Words to watch: stands/serves as, is a testament, crucial/pivotal/vital/key role, underscores/highlights its importance, reflects broader, setting the stage for, represents a shift, evolving landscape, indelible mark

**Before:**
> Enabling the Gradle build cache represents a pivotal shift in the team's development workflow, setting the stage for dramatically faster builds across the entire platform.

**After:**
> Enabling the Gradle 8.5 build cache cut clean-build times from about 4 minutes to 90 seconds. It caches task outputs locally and pulls from the remote cache on CI.

---

### 2. Notability and Coverage Claims

AI insists on telling you how important or well-known something is, often listing sources or metrics without analytical purpose.

**Before:**
> The Kubernetes autoscaler is a critical component of our infrastructure and has been widely recognized as a cornerstone of the platform's scaling strategy.

**After:**
> The HPA scales the checkout pods between 3 and 40 replicas based on CPU. During last year's Cyber Monday it peaked at 38 and stayed there for about six hours.

---

### 3. -ing Padding

Present participle phrases tacked onto sentences to simulate depth: highlighting, underscoring, ensuring, reflecting, showcasing, fostering, contributing to, encompassing.

**Before:**
> The Terraform module provisions a VPC with private subnets, ensuring network isolation while fostering a consistent infrastructure baseline across environments.

**After:**
> The Terraform module provisions a VPC with private subnets in three AZs. Each environment gets the same CIDR layout, so security group rules don't need per-env overrides.

---

### 4. Promotional Language

AI defaults to a promotional register, especially when describing systems or teams. In internal docs this sounds like marketing copy for your own code.

Words to watch: robust, cutting-edge, best-in-class, state-of-the-art, world-class, vibrant, rich, profound, groundbreaking, stunning, commitment to excellence

**Before:**
> Our robust and cutting-edge Jenkins shared library delivers a seamless, best-in-class CI experience that streamlines development velocity across all engineering teams.

**After:**
> The Jenkins shared library has four pipeline templates: Java service, Node app, Docker image, and Terraform plan. Teams import it with `@Library('cicd-lib@v3')`.

---

### 5. Vague Attributions

AI attributes claims to unnamed authorities rather than citing specifics. Watch for: industry reports, experts argue, some critics suggest, observers note, several publications.

**Before:**
> Industry best practices recommend using Redis for session management. Experts agree that in-memory stores significantly outperform disk-backed alternatives for this use case.

**After:**
> We switched session storage from PostgreSQL to Redis because sessions were adding about 15ms to every authenticated request. Redis brought that under 1ms. The trade-off is we lose sessions on restart, but the TTL is only 30 minutes anyway.

---

### 6. Formulaic Challenges Sections

Sections with headings like "Challenges and Future Prospects" or "Despite its challenges" where AI acknowledges difficulties in a formulaic way and then pivots to optimism.

**Before:**
> Despite these challenges, the team remains committed to delivering a world-class CI pipeline. The future looks promising as GitHub Actions continues to evolve.

**After:**
> The macOS runners are still slow -- a full iOS build takes 22 minutes versus 8 on Linux. We filed a request with GitHub for larger runners but haven't heard back. For now we only run the iOS matrix on release branches.

---

## Language and Grammar Patterns

### 7. AI Vocabulary

Words that appear far more frequently in post-2023 text and often co-occur. In prose, replace with simpler alternatives. In technical writing, some ("modular," "scalable") are legitimate terms of art -- flag them only when used as filler.

High-frequency AI words: Additionally, align with, crucial, curated, delve, emphasizing, enduring, enhance, ensures, facilitate, fostering, garner, highlight (verb), holistic, interplay, intricate, key (adjective), landscape (abstract), leverage, notably, pivotal, robust, seamless, showcase, streamline, tapestry, testament, underscore (verb), valuable, vibrant

**Before:**
> Additionally, the Datadog integration leverages a holistic approach to monitoring, ensuring seamless observability across all key services while showcasing the team's commitment to robust operational practices.

**After:**
> The Datadog agent runs as a DaemonSet and collects traces from every service in the `prod` namespace. We enabled APM about six months ago and it's mostly been useful for tracking down slow database queries, though the trace sampling at 10% sometimes misses the exact request we're looking for.

---

### 8. Copula Avoidance

AI substitutes elaborate constructions for simple "is," "are," or "has": serves as, stands as, marks, represents, boasts, features, offers.

**Before:**
> The LaunchDarkly wrapper serves as the single entry point for all feature flag evaluations. It boasts support for user targeting and features server-side streaming.

**After:**
> The LaunchDarkly wrapper is the entry point for flag evaluations. It picks up changes via server-side streaming, usually within 2-3 seconds -- though we've seen it lag up to 10 seconds when the LD relay proxy is under load, which bit us during a Black Friday rollback.

---

### 9. Negative Parallelisms

Constructions like "Not only...but..." or "It's not just about..., it's about..." AI overuses these as rhetorical devices.

**Before:**
> This Dockerfile refactor is not just about reducing image size; it's about fundamentally rethinking how the team approaches containerization.

**After:**
> The multi-stage build dropped the image from 1.2 GB to 340 MB.

---

### 10. Rule of Three

AI forces ideas into groups of three to appear comprehensive.

**Before:**
> We tuned the alerts for accuracy, timeliness, and actionability. The new thresholds deliver precision, reliability, and clarity.

**After:**
> We tuned the Splunk alerts mainly to cut noise -- the on-call was getting about 40 non-actionable pages a week. After raising the error-rate threshold from 1% to 5%, that dropped to roughly 6.

---

### 11. Synonym Cycling

AI's repetition-penalty produces excessive synonym substitution within short spans. The same concept gets three different names in three sentences.

**Before:**
> The SQS consumer processes failed messages from the dead-letter queue. The message handler retries each failed event up to three times. The event processor logs the outcome and removes the item.

**After:**
> The SQS consumer processes failed messages from the dead-letter queue, retrying each up to three times. It logs the outcome and deletes the message afterward.

---

### 12. False Ranges

"From X to Y" constructions where X and Y are not on a meaningful scale.

**Before:**
> The upgrade touched everything from dependency management to runtime configuration, from test frameworks to deployment scripts.

**After:**
> The Spring Boot 3.2 upgrade mostly meant bumping Jakarta namespace imports and fixing two broken Mockito matchers. The deployment scripts didn't need changes.

---

## Style Patterns

### 13. Em Dash Overuse

AI uses em dashes more frequently than humans, mimicking punchy editorial writing. One em dash in a paragraph is fine. Three is a tell.

**Before:**
> The composite alarm fires when the error rate exceeds 5% -- combining three child alarms -- which each monitor a different endpoint -- and notifies the on-call channel -- triggering the PagerDuty integration -- so the team can respond quickly.

**After:**
> The CloudWatch composite alarm fires when the API error rate exceeds 5%. It combines three child alarms, one per endpoint, and notifies the on-call channel through PagerDuty.

---

### 14. Boldface Overuse

AI mechanically bolds every proper noun, acronym introduction, or concept it considers important.

**Before:**
> The **Kafka Connect** cluster runs **three connectors**: a **JDBC source connector** reading from **PostgreSQL**, an **S3 sink connector** writing to the **data lake**, and an **Elasticsearch sink connector** for the **search index**.

**After:**
> The Kafka Connect cluster runs three connectors: a JDBC source connector reading from PostgreSQL, an S3 sink connector writing to the data lake, and an Elasticsearch sink connector for the search index.

---

### 15. Inline-Header Vertical Lists

Every list item starts with a bolded header followed by a colon, and the text after the colon restates the header. This is a problem when the structure adds no information. In reference docs and specs, structured lists with informative headers are the correct format.

**Before (headers restate body):**
> - **URL Versioning:** API versions are included in the URL path.
> - **Header Negotiation:** Version selection is performed through content-type headers.
> - **Deprecation Policy:** Deprecated versions are handled according to the deprecation policy.

**After:**
> We use URL path versioning (`/v2/orders`). We tried content-type header negotiation early on but clients kept forgetting to set it, so we dropped it after v1. Deprecated versions return a `Sunset` header with the shutdown date.

---

### 16. Title Case in Headings

AI defaults to title case for all headings regardless of the document's existing convention.

**Before (document otherwise uses sentence case):**
> ## Nightly Data Sync DAG Configuration And Retry Policy

**After:**
> ## Nightly data sync DAG configuration and retry policy

---

### 17. Emojis in Prose

AI decorates headings or bullets with emojis.

**Before:**
> 🚀 **Deploy Started:** Build #4471 deploying to staging
> 💡 **Reminder:** Check the Grafana dashboard after deploy
> ✅ **Action Required:** Run smoke tests and report back

**After:**
> Build #4471 deploying to staging. Check the Grafana dashboard after deploy and run smoke tests.

---

### 18. Curly Quotation Marks

Some AI outputs use curly (smart) quotes instead of straight quotes. The pairs -- left/right double (" ") and left/right single (' ') -- look identical to straight `"` and `'` in most fonts but are different Unicode code points (U+201C/U+201D and U+2018/U+2019).

In code-adjacent docs, markdown, and configuration references, use straight quotes. Curly quotes break grep patterns, syntax highlighting, and copy-paste into terminals.

**Detection:** Search for U+201C, U+201D, U+2018, U+2019. Replace with their straight equivalents (U+0022, U+0027).

**Applies to:** Markdown, code-adjacent docs, config files, anything copy-pasted into terminals or editors.
**Does not apply to:** Published prose in proportional fonts where curly quotes are the typographic convention.

---

## Communication Patterns

### 19. Chatbot Artifacts

Text meant as conversation gets pasted as content. Watch for: I hope this helps, Of course!, Certainly!, You're absolutely right!, Would you like me to, Let me know if, Here is a...

**Before:**
> Here is a summary of the k6 load test results. I hope this helps! Let me know if you'd like me to break down the percentile data further.

**After:**
> (Remove the wrapper entirely. Start with the content.)

---

### 20. Knowledge-Cutoff Disclaimers

AI disclaimers about incomplete information left in the text. Watch for: as of [date], While specific details are limited, based on available information, Up to my last training update.

**Before:**
> While specific details about the schema migration sequence are not extensively documented in readily available sources, it appears the `orders` table was altered sometime during the v2.3 release cycle.

**After:**
> The `orders` table was altered in the v2.3 release to add the `fulfillment_center_id` column. (Or if genuinely unknown: "We couldn't find when `fulfillment_center_id` was added -- the migration files predate our current Flyway setup.")

---

### 21. Sycophantic Tone

Overly positive, agreeable language.

**Before:**
> Great question! You're absolutely right that the shade plugin is causing the classpath conflict. That's an excellent catch on the duplicate `META-INF/services` entries.

**After:**
> The shade plugin is duplicating `META-INF/services` entries. That's what's causing the classpath conflict.

---

## Filler and Hedging

### 22. Filler Phrases

Common substitutions:
- "In order to achieve this goal" → "To"
- "Due to the fact that" → "Because"
- "At this point in time" → "Now"
- "In the event that" → "If"
- "The system has the ability to" → "The system can"
- "It is important to note that the data shows" → "The data shows"
- "It is worth mentioning that" → (delete, then say the thing)

---

### 23. Excessive Hedging

Over-qualifying statements with stacked qualifiers.

**Before:**
> It could potentially be argued that adjusting the Memcached TTL might possibly improve cache hit rates under certain high-traffic conditions.

**After:**
> Bumping the Memcached TTL from 5 minutes to 15 should improve the hit rate during traffic spikes. We haven't tested it under real load yet, so we're going on gut feel and some napkin math.

---

### 24. Generic Positive Conclusions

Vague upbeat endings that add no information.

**Before:**
> The future looks bright for the component library migration. The team is well-positioned to deliver exceptional results as they continue their journey toward a unified design system.

**After:**
> We still have 34 React components on the old library. Plan is to migrate five per sprint and finish by end of Q3, assuming nobody adds new ones in the meantime.

---

## Structural and Professional Writing Patterns

These patterns are structural tells in longer technical documents. They are subtler than vocabulary patterns and more context-dependent.

### 25. Rigid Section Templates

Every section follows an identical skeleton: bold label, one-sentence summary, detail paragraph. When every section uses the same structure, it reads as template-filled.

**Applies to:** Prose docs, analysis reports, architecture overviews.
**Does not apply to:** Field mappings, API references, structured tables.

**Before:**
> ### Build Stage
> **Tool:** Gradle
> The build stage is handled by Gradle. Source code is compiled and artifacts are produced.
>
> ### Test Stage
> **Tool:** JUnit
> The test stage is handled by JUnit. Unit tests and integration tests are executed against the compiled artifacts.

**After:**
> ### Build stage
> Gradle compiles the source and produces a fat JAR. This takes about 3 minutes with a warm cache, closer to 7 without one.
>
> ### Test stage
> JUnit runs unit and integration tests in parallel. Integration tests spin up a Postgres container via Testcontainers, which occasionally times out on the shared GitLab runners -- if that happens, just retry the job.

---

### 26. Symmetric Treatment of Asymmetric Content

AI gives roughly equal word count and depth to topics that differ wildly in complexity. A major subsystem gets the same two paragraphs as a trivial configuration flag.

**Applies to:** Analysis reports, architecture docs, investigation summaries.
**Does not apply to:** Tables, glossaries, or structured reference where consistent entry depth is expected.

**Before:**
> ### ELK Stack
> The ELK stack handles centralized logging for all production services. It collects logs from 14 services, indexes them in Elasticsearch, and provides search and visualization through Kibana. The cluster processes approximately 2 million log events per hour during peak traffic.
>
> ### Log Retention Flag
> The log retention flag controls how long logs are kept in the system. It is configured in the cluster settings and affects all indices equally. The default value is 30 days, which was chosen to balance storage costs with debugging needs.

**After:**
> ### ELK stack
> The ELK stack handles centralized logging for all production services. Filebeat ships logs from 14 services into Elasticsearch. At peak we ingest about 2 million events per hour, and the cluster needs three dedicated data nodes to keep up. Most of our on-call debugging starts here.
>
> ### Log retention flag
> `ILM_RETENTION_DAYS` in the cluster config. Default is 30 days.

---

### 27. Absence of First Person in Team-Authored Work

A document says it was written by a team but never uses "we," "our," or "us." A real team describing their own findings says "we found," "we were not able to confirm," "as far as we could tell."

**Applies to:** Investigation reports, analysis docs, architecture reviews with identified authors.
**Does not apply to:** API references, field mappings, docs without an identified author.

**Before:**
> This document summarizes the findings from the March 15 outage investigation. The root cause was identified as a misconfigured health check. The recommendation is to add integration tests for health check endpoints.

**After:**
> We looked into the March 15 outage and we're fairly sure the root cause was a misconfigured health check on the payments service -- the timeout was set to 200ms but the service regularly takes 300ms to warm up after a deploy. We're adding integration tests for health check endpoints, though honestly we should have caught this in staging.

---

### 28. Zero Expressed Uncertainty in Analysis

A document based on investigation makes definitive claims about everything and expresses uncertainty about nothing. Real analysis has gaps: things that could not be verified, ambiguous evidence, unclear lineage.

**Applies to:** Investigation reports, data analysis, migration assessments.
**Does not apply to:** Reference docs or specs that describe known systems definitively.

Express uncertainty only where it is genuine. If you verified it, state it plainly.

**Before:**
> The Prometheus cluster stores 1.4 million active time series. Cardinality growth is driven by the `http_request_duration` metric, which creates a new series for each unique label combination.

**After:**
> The Prometheus cluster stores about 1.4 million active time series, though the exact number fluctuates. We're fairly confident the cardinality growth is mostly from `http_request_duration` -- some services are passing request IDs as labels, which is almost certainly a mistake. We haven't traced all the offending services yet.

---

### 29. Perfect Formatting Consistency

Every field name backtick-wrapped, every link formatted identically, every table cell at the same level of detail across hundreds of lines with zero lapses.

In structured reference docs, formatting consistency is correct. This pattern is a tell in prose documents, where humans naturally vary slightly.

**Before (prose analysis):**
> The `UserService` calls the `AuthClient` to validate tokens against the `IdentityProvider`. The `OrderService` checks inventory through the `StockClient` connected to the `WarehouseAPI`. The `NotificationService` dispatches alerts via the `EmailGateway` and the `SMSProvider`. The `AnalyticsService` streams events to the `DataLakeIngester`.

**After:**
> `UserService` calls `AuthClient` to validate tokens. The order service checks inventory through StockClient (the naming is inconsistent, yes -- legacy), and notifications go out via the email and SMS gateways. AnalyticsService streams to the data lake but that pipeline is being deprecated in favor of the Kinesis firehose.

---

### 30. Precise-but-Purposeless Inventory Counts

AI reports everything it counted: "7 schemas, 1,537 SQL files, 147 views, 33 tables." These breakdowns often serve no analytical purpose.

In technical reference docs, precise counts are often what the reader needs. This pattern is a problem only when the counts exist because the AI counted, not because the number matters.

**Before (counts as padding):**
> The documentation site contains 47 pages, 12 navigation sections, 3 custom plugins, 8 CSS overrides, and 2 JavaScript extensions across 4 top-level directories.

**After (when exact numbers do not matter):**
> It's a standard MkDocs site with a dozen or so nav sections and a few custom plugins.

**When exact numbers matter, keep them.** A migration doc saying "47 fields mapped, 12 with gaps" is more useful than "most fields mapped, some with gaps."

---

### 31. Uniform Sentence Length

Sentences cluster in a narrow length band with little variation. No short punches. No longer, more complex constructions that let a thought breathe.

Read the text aloud. If every sentence takes roughly the same breath to say, the rhythm is too flat. Break some short. Let others run when the thought needs room.

**Before:**
> The test suite runs across four parallel containers in CircleCI. Each container receives an equal share of the test files. The splitting algorithm distributes tests based on historical timing data. Slow test files are spread evenly across different containers. The total suite runtime decreased from twelve minutes to four minutes. Test results are collected and merged after all containers finish.

**After:**
> Tests run across four CircleCI containers, split by timing data. Total runtime went from twelve minutes to four. One gotcha: the splitter doesn't know about our Testcontainers tests, so container 2 almost always finishes last because it gets the Postgres integration suite, which takes about 90 seconds on its own just to spin up.

---

### 32. Exhaustive Cross-Referencing

Every named system, tool, or concept includes a hyperlink or "see also" reference. Human writers link selectively -- the links they expect the reader to follow.

**Before:**
> The checkout page (see [Page Components](#components)) uses the CartProvider (see [State Management](#state)) to display line items from the ProductAPI (see [API Layer](#api)). Validation errors render via the ErrorBoundary (see [Error Handling](#errors)) and are tracked through the AnalyticsHook (see [Telemetry](#telemetry)).

**After:**
> The checkout page pulls cart state from CartProvider and displays line items. Validation errors render through the shared ErrorBoundary. See [Error Handling](#errors) for how errors surface to users.

---

### 33. Transition Word Density

AI opens a disproportionate number of sentences with transition words: Additionally, Furthermore, Moreover, However, Consequently, Nevertheless. One or two per section is normal. One per paragraph is a tell.

**Before:**
> The Ansible playbook configures the application servers. Additionally, it installs system packages. Furthermore, it sets up log rotation. Moreover, the rotation policy applies to all services. Consequently, disk usage stays below the 80% threshold.

**After:**
> The playbook configures the app servers: installs packages, deploys the service, and sets up log rotation. The rotation policy keeps disk usage below 80%.

---

### 34. Passive Voice Density in Authored Work

Occasional passive voice is fine. Sustained passive voice in a document that has an identified author or team sounds like AI hedging away from ownership.

**Before:**
> The test suite was restructured. Flaky tests were identified and quarantined. A tagging convention was introduced to separate unit tests from integration tests.

**After:**
> We restructured the JUnit suite: tagged unit vs. integration tests and quarantined the flaky ones. There were eleven flaky tests, mostly around time-dependent assertions.

---

### 35. Premature Summarization

AI restates what it just said at the end of each section or at the top of the next. Readers do not need the conclusion of a three-sentence paragraph restated immediately.

**Before:**
> The queue is mirrored across three RabbitMQ nodes with automatic synchronization. Each message is written to all replicas before being acknowledged. In summary, all messages are replicated to three nodes and acknowledged only after full synchronization.

**After:**
> The queue is mirrored across three RabbitMQ nodes. Messages aren't acked until all replicas confirm the write.

---

## Full Examples

### Example 1: Confluence Wiki Page (Kafka Consumer)

**Before:**
> The order event consumer serves as a robust and scalable solution for processing real-time order events from the Kafka cluster. It leverages a modular consumer group architecture, ensuring reliable message processing while facilitating seamless integration with downstream services. Additionally, the consumer encompasses comprehensive offset management, deserialization, and dead-letter routing, showcasing the team's commitment to operational excellence. The system boasts 6 consumer instances, 24 partitions, and 3 retry topics. Despite challenges inherent in distributed event processing, the consumer continues to deliver exceptional throughput.

**After:**
> The order event consumer reads from the `order-events` topic (24 partitions, 6 consumer instances). It deserializes Avro messages, validates them, and writes to the fulfillment database. If a message fails three times it goes to `order-events-dlq`. We see about 1,200 msgs/sec at peak, though it spikes higher on Monday mornings when the weekend batch from the warehouse system catches up. Offset commits are async every 5 seconds -- we lost about 30 seconds of reprocessing during the last consumer rebalance, which was acceptable.

**Patterns fixed:** 8 (serves as), 7 (robust, scalable, leverages, facilitating, seamless, encompasses, comprehensive, showcasing), 4 (commitment to operational excellence, exceptional throughput), 3 (-ing padding: ensuring, facilitating, showcasing), 30 (inventory padding), 6 (formulaic "despite challenges"), 22 (Additionally).

### Example 2: Incident Post-Mortem (Certificate Expiration)

**Before:**
> This document provides a comprehensive analysis of the March 12 service disruption. The investigation revealed that the root cause was a certificate expiration that impacted the API gateway. Additionally, the analysis highlighted that the monitoring system failed to detect the expiring certificate, underscoring the need for enhanced observability. Industry best practices suggest implementing automated certificate rotation. The team remains committed to preventing similar incidents, and the future looks promising as new automation tooling is adopted.

**After:**
> On March 12 at 06:14 UTC, the API gateway started returning 502s to all external traffic. We got paged at 06:17 and had it fixed by 06:41. Root cause was an expired TLS certificate on the gateway's upstream listener -- it had a one-year cert that nobody renewed because the team that originally provisioned it rotated off the project last summer. Our monitors didn't catch it because they check HTTP status from outside the gateway, and a 502 is still a valid HTTP response, not a connection failure. We're not 100% sure there isn't another cert with the same problem; Jamie is auditing the rest this week. Immediate fix was manual renewal. Longer term we're setting up cert-manager with Let's Encrypt for auto-rotation, though we still need to figure out how that works with our internal CA for the service mesh certs.

**Patterns fixed:** 7 (comprehensive, enhanced), 22 (Additionally), 1 (underscoring the need), 5 (industry best practices), 4 (committed to, promising), 24 (generic positive conclusion), 27 (no first person), 28 (zero uncertainty), 3 (-ing padding: underscoring).
