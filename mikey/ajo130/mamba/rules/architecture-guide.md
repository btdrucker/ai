# Architecture Guide — mpe.app.mamba-android (Shop IT2)

> This document maps the iOS architecture decisions to Android patterns and references existing conventions in the mamba-android codebase. Follow these patterns when implementing any Shop IT2 feature.

## Architecture Overview

The Shop IT2 architecture follows a **5-layer Unified Content System (UCS)** for managing content across Shop surfaces, built on top of the existing MPE modular architecture (capabilities/components/features/foundation with api/impl/glue sub-modules).

```
+-------------------------------------------------------------+
|  DISPLAY: @Composable CardView (switches on sealed class)   |
+-------------------------------------------------------------+
|  SELECT: ContentSelectionCoordinator (filter > rank > limit) |
+-------------------------------------------------------------+
|  ACCESS: CardContentProvider (query layer over store)        |
+-------------------------------------------------------------+
|  STORE: CardContentStore (StateFlow<Map<ContentId, Content>>)|
+-------------------------------------------------------------+
|  FETCH: ContentAggregator (parallel coroutine fetching)     |
+-------------------------------------------------------------+
```

---

## Architecture Decision Mapping (iOS to Android)

### Decision 1: State Management

| Aspect | Implementation |
|--------|---------------|
| Pattern | `@HiltViewModel` with single `_state: MutableStateFlow<SealedUiState>` |
| Enforcement | Custom Detekt `ViewModelArchitectureRule` — one MutableStateFlow per ViewModel |
| Collection | `state.collectAsStateWithLifecycle()` in Compose (Detekt-enforced, never `collectAsState()`) |
| Thread safety | `viewModelScope` defaults to `Dispatchers.Main.immediate` |
| State shape | `sealed interface` with `Loading`, `Content`/`Loaded`/`Success`, `Error` variants |

**Example (existing pattern in codebase):**
```kotlin
@HiltViewModel
internal class ShopViewModel @Inject constructor(
    private val contentAggregator: ContentAggregator,
    private val selectionCoordinator: ContentSelectionCoordinator,
    private val dispatcher: CoroutineDispatcher
) : ViewModel() {
    private val _state = MutableStateFlow<ShopState>(ShopState.Loading)
    val state = _state.asStateFlow()
}
```

### Decision 2: Dependency Injection

| Aspect | Implementation |
|--------|---------------|
| Framework | Hilt / Dagger |
| ViewModels | `@HiltViewModel class VM @Inject constructor(...)` |
| Interfaces | Defined in `api/` modules (public) |
| Implementations | In `impl/` modules (internal) |
| Bindings | In `glue/` modules via `@Binds` in `@Module @InstallIn(SingletonComponent::class)` |
| Naming | `*ModuleBinds` for `@Binds` interfaces; `*Module` for `@Provides` companions |

**Existing binding chain (Doorway example):**
```
api/DoorwayRepository.kt (public interface)
  > impl/DoorwayRepositoryImpl.kt (internal class @Inject constructor)
    > glue/DoorwayCapabilityModule.kt (@Binds fun bind...(): DoorwayRepository)
```

### Decision 3: API Client Strategy

| Aspect | Implementation |
|--------|---------------|
| Library | Connect-Kotlin (Buf) 0.7.2 via `ProtocolClientInterface` |
| Pattern | Inject `ProtocolClientInterface`, create generated service client |
| Request building | Protobuf `.newBuilder().setField(value).build()` |
| Response handling | `response.success { it.message }` / `response.failure { throw it.cause }` |
| Auth | OkHttp interceptor chain handles Nike SSO tokens |

**Existing pattern (SpotlightV2):**
```kotlin
class SpotlightV2RepositoryImpl @Inject constructor(
    protocolClient: ProtocolClientInterface,
    private val telemetryProvider: TelemetryProvider
) : SpotlightV2Repository {
    private val client = SpotlightV2ServiceClient(client = protocolClient)

    override suspend fun getSpotlight(...): GetSpotlightResponse? {
        val request = GetSpotlightRequest.newBuilder()
            .setChannel(channel).setMarketplace(marketplace).build()
        val response = client.getSpotlight(request = request)
        val result = response.success { it.message }
        response.failure { throw it.cause }
        return result
    }
}
```

### Decision 4: SDUI Component Registry

| Aspect | Implementation |
|--------|---------------|
| iOS equivalent | `Stacks.ComponentView(component, themeID:, tapHandler:)` |
| Android | SDUI Composable renderer (Android stacks library equivalent) |
| Action handling | Sealed interface for navigation destinations from SDUI actions |
| External URLs | `context.startActivity(Intent(ACTION_VIEW, uri))` |

### Decision 5: Navigation

| Aspect | Implementation |
|--------|---------------|
| Current pattern | Fragment-based navigation via `FragmentNavigator.loadFragment()` |
| Destinations | `sealed class Screens` with `@Serializable` subtypes |
| Per-feature | Each feature defines its own `*Destination` sealed type |
| Deep linking | Intent-based via `ShopActivity` |
| Cross-feature | `BridgeViewModel` pattern with `MutableSharedFlow` |

### Decision 6: Error Handling and Retry

| Aspect | Implementation |
|--------|---------------|
| Repository layer | Connect RPC `response.success {}` / `response.failure {}` |
| Use case layer | Return `Result<T>` or `Either<Success, Failure>` |
| ViewModel layer | Map to sealed UI state `Error(networkErrorState)` |
| Shared errors | `NetworkErrorState` sealed interface in `foundation/configuration-api/` |
| Retry | Exponential backoff (1s, 2s, 4s — max 10s, 3 attempts) |

### Decision 7: Caching Strategy

| Aspect | Implementation |
|--------|---------------|
| MVP | In-memory caching in repository/store classes |
| Video | ExoPlayer `CacheDataSource` / `SimpleCache` |
| Preferences | DataStore Preferences 1.1.7 |
| Future | Room database for offline content persistence |

### Decision 8: Personalization Scoring

| Aspect | Implementation |
|--------|---------------|
| Pattern | Server provides `RankingConfig`; client executes scoring |
| Config delivery | Via Connect-Kotlin protobuf response |
| Scoring | Client-side `ShopRanker` class applies config to CDP profile |
| Fallback | Non-personalized default ordering for new/anonymous users |

---

## Unified Content System — Android Architecture

### Layer 1: FETCH — ContentAggregator

```kotlin
interface ContentAggregator {
    suspend fun fetchAllContent(
        channel: String, marketplace: Marketplace,
        language: Language, gender: Gender
    ): ContentFetchResult

    suspend fun retryFailed(
        failedTypes: Set<ContentType>,
        channel: String, marketplace: Marketplace,
        language: Language, gender: Gender
    ): ContentFetchResult
}
```

Implementation uses `supervisorScope { async { } }` for parallel fetching with per-API failure isolation.

### Layer 2: STORE — CardContentStore

```kotlin
interface CardContentStore {
    val state: StateFlow<CardContentStoreState>
    fun populate(from: ContentFetchResult)
    fun clear()
    fun setLoading(isLoading: Boolean)
}

data class CardContentStoreState(
    val items: Map<ContentId, CardContent> = emptyMap(),
    val isLoading: Boolean = false,
    val fetchResult: FetchResult? = null,
    val lastFetchedAt: Instant? = null
)
```

### Layer 3: ACCESS — CardContentProvider

```kotlin
interface CardContentProvider {
    fun allContent(): List<CardContent>
    fun contentOfType(type: ContentType): List<CardContent>
    fun contentMatchingTags(tags: Set<Tag>): List<CardContent>
    fun contentById(id: ContentId): CardContent?
    fun contentExcluding(ids: Set<ContentId>): List<CardContent>
}
```

### Layer 4: SELECT — ContentSelectionCoordinator

```kotlin
interface ContentSelectionCoordinator {
    suspend fun selectForCarousel(
        config: ShopCarousel, rankingConfig: RankingConfig, profile: CdpProfile
    ): List<CardContent>

    suspend fun selectForFeed(
        rankingConfig: RankingConfig, excludingFeatured: Set<ContentId>, profile: CdpProfile
    ): List<CardContent>
}
```

### Layer 5: DISPLAY — CardView Composable

```kotlin
@Composable
fun CardView(
    content: CardContent,
    layout: CardLayout,
    onNavigate: (NavigationDestination) -> Unit,
    modifier: Modifier = Modifier
) {
    when (content) {
        is CardContent.Spotlight -> StacksComponentView(content.card)
        is CardContent.ProductCard -> StacksComponentView(content.card)
        is CardContent.ProductWallCard -> StacksComponentView(content.card)
        is CardContent.Recommendation -> RecommendationCardView(content.product)
    }
}
```

### CardContent Sealed Class

```kotlin
sealed interface CardContent {
    val id: ContentId
    val contentType: ContentType
    val tags: List<Tag>

    data class Spotlight(val card: SpotlightCard) : CardContent {
        override val id = card.id
        override val contentType = ContentType.SPOTLIGHT
        override val tags = card.variant.metadata.tagsList
    }
    data class ProductCard(val card: ProductCardProto) : CardContent { /* ... */ }
    data class ProductWallCard(val card: ProductWallCardProto) : CardContent { /* ... */ }
    data class Recommendation(val product: RecommendedProduct) : CardContent {
        override val id = product.productCode
        override val contentType = ContentType.RECOMMENDATION
        override val tags = emptyList()
    }
}

typealias ContentId = String

enum class ContentType { SPOTLIGHT, PRODUCT_CARD, PRODUCT_WALL_CARD, RECOMMENDATION }
```

---

## Module Structure for Shop IT2

```
capabilities/shop/
  api/     -- Public interfaces: CardContent, CardContentStore, ContentAggregator, etc.
  impl/    -- Internal implementations + ViewModels + Compose screens
  glue/    -- Hilt @Module bindings
  fake/    -- Fake implementations for testing

features/shop/
  api/     -- ShopProvider, ShopBridgeViewModel, ShopDestination
  impl/    -- ShopViewModel, ShopScreen, ShopFragment wrapper
  glue/    -- ShopModuleBinds

capabilities/shop/api/src/main/kotlin/.../
  unifiedcontent/
    CardContent.kt
    ContentType.kt
    CardContentStore.kt
    CardContentProvider.kt
    ContentAggregator.kt
    ContentSelectionCoordinator.kt
    CardLayout.kt
  recommendation/
    RecommendationCardRepository.kt
    RecommendedProduct.kt
  personalization/
    ShopRanker.kt
```

---

## Key Architectural Constraints

1. **Single _state MutableStateFlow per ViewModel** — enforced by Detekt rule
2. **collectAsStateWithLifecycle() only** — `collectAsState()` is banned by Detekt
3. **Composable max 100 lines** — enforced by Detekt `ComposableLongMethodRule`
4. **No State/StateFlow as Composable params** — enforced by Detekt
5. **ComposeView must set DisposeOnViewTreeLifecycleDestroyed** — enforced by Detekt
6. **No android.util.Log** — must use internal logging; enforced by Detekt
7. **No inline @Suppress** — must use Detekt baseline
8. **Context must not be cast to Activity** — use `Context.activity()` extension
9. **Internal visibility for impl classes** — only `api/` module types are public
10. **Fragment-based navigation** — current architecture uses Fragments, not Navigation Compose
