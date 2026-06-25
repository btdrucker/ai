# Product Requirements — mpe.app.mamba-android (Shop IT2)

> Adapted from mpe.app.mamba-ios PRD (2026-02-02). This document governs all AI agent work on the Android Mamba project.

## Executive Summary

**Project Mamba Iteration 2** reinvents the Nike App Shop experience on Android. The current Nike App is transactional and fails to inspire emotional brand connection. IT2 addresses this with a modernized Shop surface featuring dynamic personalized content, rich Spotlight v2 storytelling templates, and Nav v2 with Material You / Material 3 support. The goal is a premium, brand-right shopping experience that showcases Nike storytelling while improving product discovery and wayfinding.

## Project Context

| Attribute | Value |
|-----------|-------|
| Project Type | Native Android mobile application |
| Domain | E-commerce with personalization |
| Complexity | High (multi-surface, cross-team dependencies) |
| Context | Brownfield (existing Nike App ecosystem) |
| Min Android Version | Android 10 (API 29) |
| Target Android Version | Android 16 (API 36) |
| Compile SDK | 35 |
| Language | Kotlin 2.2.20 |
| UI Framework | Jetpack Compose + Material 3 |
| DI Framework | Hilt / Dagger |
| Network | Connect-Kotlin (Buf) 0.7.2 + Ktor 3.0.3 + OkHttp 5.1.0 |

## Target Users

- **Primary:** Nike App consumers seeking products (mission-driven hunters and discovery-driven gatherers)
- **Secondary:** Content operators authoring and publishing Shop content via Content Composer
- **Tertiary:** Engineering teams maintaining and debugging the Shop experience

## Success Metrics

| Category | Metric | Target |
|----------|--------|--------|
| Engagement | Consumers see 3+ Shop cards | 50% |
| Engagement | Consumers click into Spotlight v2 | 10% |
| Engagement | Next-click from Spotlight v2 | 20% |
| A/B Test | Conversion Rate | Positive or neutral |
| A/B Test | App-wide Engagement | Positive or neutral |

---

## Functional Requirements

### Shop Feed & Navigation

| ID | Requirement |
|----|-------------|
| FR1 | Users can access a personalized Shop Feed as the primary Shop entry surface |
| FR2 | Users can scroll infinitely through the Shop Feed to discover content |
| FR3 | Users can navigate to Shop from the bottom navigation bar |
| FR4 | Users can access category-specific views via Apollo Navigation |
| FR5 | Users can see gender-specific content based on their persistent gender preference |
| FR6 | Users can switch gender selection and see content update accordingly |
| FR7 | System maintains scroll position when users navigate away and return (LazyListState persistence) |
| FR8 | Users can access Shop surfaces via deep-links from external sources (Android App Links / Intent filters) |

### Content Discovery

| ID | Requirement |
|----|-------------|
| FR9 | Users can view a Featured Carousel at the top of the Shop Feed |
| FR10 | Users can swipe horizontally through Featured Carousel items |
| FR11 | Users can tap a Spotlight card to enter the Spotlight v2 experience |
| FR12 | Users can view Spotlight v2 content in multiple template formats (Hero, Promo, Product Grid) |
| FR13 | Users can view auto-generated cover cards that summarize Spotlight content |
| FR14 | Users can view Doorway cards that link to category-specific surfaces |
| FR15 | Users can tap a Doorway card to navigate to its linked surface |
| FR16 | Users can view Promo Banner content within the Shop Feed |
| FR17 | Users can tap Promo Banner content to navigate to linked destinations |
| FR18 | Users can view Product Wall Cards displaying product grids within the Feed |
| FR19 | Users can view video content that auto-plays when visible (Media3 ExoPlayer) |
| FR20 | Users can see video respect device animation/autoplay settings |
| FR21 | Users can view Recently Viewed products carousel |

### Personalization

| ID | Requirement |
|----|-------------|
| FR22 | Users can see Shop Feed content personalized based on their profile |
| FR23 | Users can select interests during onboarding or in profile settings |
| FR24 | Users can see content prioritized based on their selected interests |
| FR25 | Users can see content influenced by their purchase and browse history (affinity) |
| FR26 | System applies personalization algorithm to sort Feed content |
| FR27 | System blends CDP profile data with content tags for relevance scoring |
| FR28 | System provides non-personalized fallback content for new/anonymous users |
| FR29 | System boosts recently selected interests for 30-day recency window |

### Content Management

| ID | Requirement |
|----|-------------|
| FR30 | Content operators can create Shop Feed content in Content Composer |
| FR31 | Content operators can apply tags (primary/secondary) to content items |
| FR32 | Content operators can pin content to specific positions in the Feed |
| FR33 | Content operators can boost content priority with multipliers |
| FR34 | Content operators can set publish and unpublish dates for content |
| FR35 | Content operators can preview content before publishing |
| FR36 | Content operators can publish content without requiring app release |
| FR37 | Content operators can create Spotlight v2 content using available templates |
| FR38 | Content operators can target content by gender, geo, and other attributes |

### Product Interaction

| ID | Requirement |
|----|-------------|
| FR39 | Users can tap products to navigate to Product Detail Page |
| FR40 | Users can add products to cart from PDP |
| FR41 | Users can view product grids within Spotlight v2 and Product Wall Cards |
| FR42 | Users can return from PDP to their previous scroll position (Fragment back stack / Navigation saved state) |
| FR43 | Users can view End Cap CTAs within Spotlight experiences |

### Platform & Accessibility

| ID | Requirement |
|----|-------------|
| FR44 | Users on Android 12+ experience Material You dynamic color theming and Material 3 navigation; Android 14+ additionally receive Predictive Back gesture with shared element transitions |
| FR45 | Users on pre-Android 12 experience equivalent functionality with a static Material 3 theme using Nike brand colors |
| FR46 | Users can access all content with Android font scaling support via sp units (up to 3X); Content Viewer for overflow |
| FR47 | Users can navigate with TalkBack screen reader support — all interactive elements provide contentDescription, logical focus order, and action announcements |
| FR48 | Users with "Remove animations" enabled in Accessibility settings see static alternatives to all animations (auto-advance carousels disabled, video autoplay disabled, transitions reduced) |
| FR49 | Platform parity with iOS — feature-complete IT2 experience on Android |

### System Operations

| ID | Requirement |
|----|-------------|
| FR50 | System caches previously loaded content for offline access |
| FR51 | System displays shimmer/skeleton loaders during content loading |
| FR52 | System handles component failures gracefully without breaking the Feed |
| FR53 | System logs algorithm decisions for debugging and analysis |
| FR54 | System falls back to cached/default content when APIs fail |
| FR55 | System tracks analytics events for content engagement |

---

## Non-Functional Requirements

### Performance (NFR1-NFR7)

| ID | Requirement | Target |
|----|-------------|--------|
| NFR1 | Shop Feed initial load | <1 second (navigation to first meaningful paint) |
| NFR2 | Feed card render (viewport) | <500ms (card entering viewport to rendered) |
| NFR3 | Scroll performance | 60 FPS (90/120 on high-refresh); validated with Macrobenchmark |
| NFR4 | Spotlight v2 load | <1 second (tap to content visible) |
| NFR5 | Video playback start | <2 seconds (visibility to first frame, Media3 ExoPlayer) |
| NFR6 | Deep-link resolution | <1.5 seconds (link tap to surface display) |
| NFR7 | API response (P95) | <500ms (NSP/Shop API endpoint) |

### Security (NFR8-NFR13)

| ID | Requirement |
|----|-------------|
| NFR8 | Authentication via Nike SSO integration (existing infrastructure) |
| NFR9 | TLS 1.3 for all API communications |
| NFR10 | EncryptedSharedPreferences / encrypted storage for cached content and preferences |
| NFR11 | CDP profile data accessed via authenticated APIs only |
| NFR12 | Token-based session with secure refresh handling |
| NFR13 | Content Composer publish signed with integrity verification |

### Scalability (NFR14-NFR18)

| ID | Requirement |
|----|-------------|
| NFR14 | Support concurrent users during peak traffic (major product drops) |
| NFR15 | Support 500+ active content items in Feed pool |
| NFR16 | Personalization scoring at scale without latency degradation |
| NFR17 | Global CDN for content assets |
| NFR18 | Handle 10x baseline traffic during launches |

### Accessibility (NFR19-NFR24)

| ID | Requirement |
|----|-------------|
| NFR19 | WCAG 2.1 AA minimum compliance |
| NFR20 | TalkBack full support — all Composables annotated with contentDescription and semantics; logical traversal order |
| NFR21 | Android font scaling via sp units up to 3X; layout adapts without clipping |
| NFR22 | Disable auto-advance and autoplay when "Remove animations" is enabled (check Settings.Global.ANIMATOR_DURATION_SCALE) |
| NFR23 | Color contrast minimum 4.5:1 for text; 3:1 for large text |
| NFR24 | Minimum 48x48dp touch targets (Material Design guidelines) |

### Integration (NFR25-NFR29)

| ID | System | Requirement |
|----|--------|-------------|
| NFR25 | Content Composer (CC) | 99.9% publish success rate |
| NFR26 | Nike Service Platform (NSP) | 99.9% uptime; <500ms P95 |
| NFR27 | CDP (Consumer Data Platform) | Graceful fallback if unavailable |
| NFR28 | AIR (Recommendations) | Graceful fallback if unavailable |
| NFR29 | Apollo | Cached fallback if unavailable |

### Reliability (NFR30-NFR34)

| ID | Requirement |
|----|-------------|
| NFR30 | Shop Surface availability 99.9% uptime |
| NFR31 | Content updates visible within 5 minutes of publish |
| NFR32 | Component failures don't break Feed (graceful degradation) |
| NFR33 | Auto-retry failed content loads (max 3 attempts, exponential backoff) |
| NFR34 | <0.1% session crash rate |

### Android-Specific (NFR35-NFR38)

| ID | Requirement |
|----|-------------|
| NFR35 | R8 full mode for release builds; mapping files archived per release |
| NFR36 | Google Play pre-launch report passes; target SDK meets Play Store requirements |
| NFR37 | Distribution via AAB format |
| NFR38 | Baseline Profiles generated for Shop startup and scroll paths |

---

## Epic Summary

| # | Epic | Stories | Android Notes |
|---|------|---------|---------------|
| 1 | Shop Surface — Core infrastructure and SDUI rendering | 7 | Compose + ViewModel + StateFlow; Hilt DI; Connect-Kotlin API |
| 2 | Shop Top Nav — Gender/category navigation bar | 3 | Compose TopAppBar or custom; Material 3 |
| 3 | Shop Feed — Infinite scroll with personalization (UCS) | 10 | LazyColumn with paging; ShopRanker; CardContentStore via StateFlow |
| 4 | Shop Carousel — Featured carousel with auto-advance | 5 | HorizontalPager with SnapFlingBehavior; coroutine timer |
| 5 | Doorways & Doorway Component | 4 | LazyVerticalGrid; existing DoorwayRepository |
| 6 | Product Card — Base card component (S/M/L variants) | 3 | Compose Card with variants |
| 7 | Product Wall Card — Product grid cards | 4 | Bento grid layout |
| 8 | Product Recs Card — AIR-powered recommendations | 7 | Kotlin coroutines for AIR calls; fallback chain |
| 9 | Promo Banner | 2 | No platform-specific changes |
| 10 | Interests — Interest editing sheet | 7 | ModalBottomSheet (Material 3); TalkBack support |
| 11 | Theming — Design system, Nightfall mode | 4 | dynamicDarkColorScheme/dynamicLightColorScheme on API 31+ |
| 12 | Clickstream / Events | 6 | Existing ClickstreamProvider + AnalyticsProvider |
| 13 | Spotlight V2 Surface | 6 | Media3 ExoPlayer for video; motion setting check |
| 14 | Deep Linking & Navigation | 3 | Fragment-based nav (current); Intent filters |
| 15 | Recently Viewed Carousel | 2 | DataStore for persistence |
| 16 | Platform Compatibility — Material You, accessibility | 5 | Material 3 dynamic theming; TalkBack; font scaling |
| 17 | System Operations — Caching, error handling | 6 | OkHttp cache; coroutine retry |

**Total: 17 Epics, ~84 Stories**

## Marketplace & Rollout

| Attribute | Value |
|-----------|-------|
| Initial Markets | NA (US, Canada) — Q4 FY26 |
| Languages | 16 supported |
| Growth Markets | EMEA, APLA (post-MVP) |

## Compliance

| Requirement | Status |
|-------------|--------|
| Google Play Store Policies | Required |
| Material Design 3 Guidelines | Required |
| Google Play Data Safety Section | Required |
| GDPR (EU users) | Required |
| CCPA (California users) | Required |
