# Development Patterns — mpe.app.mamba-android

> Conventions and patterns derived from auditing the existing Android codebase. All AI agents and developers MUST follow these patterns when contributing code.

---

## 1. ViewModel Pattern

Every ViewModel follows this exact structure:

```kotlin
@HiltViewModel
internal class FeatureViewModel @Inject constructor(
    private val useCase: FeatureUseCase,
    private val analyticsUseCase: FeatureAnalyticsUseCase,
    private val dispatcher: CoroutineDispatcher = Dispatchers.Default
) : ViewModel() {

    private val _state = MutableStateFlow<FeatureState>(FeatureState.Loading)
    val state = _state.asStateFlow()

    fun fetchData(marketplace: Marketplace, language: Language) {
        viewModelScope.launch(dispatcher) {
            _state.update { FeatureState.Loading }
            useCase.getData(marketplace, language)
                .onSuccess { data -> _state.update { FeatureState.Content(data) } }
                .onFailure { error -> _state.update { FeatureState.Error(error.message ?: "Unknown") } }
        }
    }
}
```

**Rules:**
- Always `@HiltViewModel` + `@Inject constructor`
- Always `internal class` (never public)
- Exactly ONE `_state: MutableStateFlow<SealedState>` — Detekt enforces this
- At most ONE `MutableSharedFlow` for events
- Use `_state.update { }` for atomic state changes (not `.value = `)
- Inject `CoroutineDispatcher` for testability

---

## 2. Sealed State Pattern

```kotlin
internal sealed interface FeatureState {
    data object Loading : FeatureState
    data class Content(val items: List<Item>) : FeatureState
    data class Error(val networkErrorState: NetworkErrorState) : FeatureState
}
```

**Rules:**
- Always `sealed interface` (not `sealed class`)
- `Loading` is always `data object`
- Success state named `Content`, `Loaded`, or `Success` depending on context
- Error state carries `NetworkErrorState` from `foundation/configuration-api/`
- All states `internal` unless in `api/` module

**For complex states that share properties across variants:**
```kotlin
internal sealed interface FeatureState {
    val localization: Localization?
    data class Loading(override val localization: Localization? = null) : FeatureState
    data class Content(val data: Data, override val localization: Localization) : FeatureState
    data class Error(val error: NetworkErrorState, override val localization: Localization? = null) : FeatureState
}
```

---

## 3. Module Structure (api/impl/glue)

### api/ — Public contracts
```kotlin
// Public interface — NO implementation details
public interface FeatureRepository {
    public suspend fun getData(marketplace: Marketplace, language: Language): FeatureData?
}
```

### impl/ — Internal implementations
```kotlin
// Internal implementation — inject dependencies via constructor
internal class FeatureRepositoryImpl @Inject constructor(
    protocolClient: ProtocolClientInterface,
    private val telemetryProvider: TelemetryProvider
) : FeatureRepository {
    private val serviceClient = FeatureServiceClient(client = protocolClient)
    // ...
}
```

### glue/ — DI bindings only
```kotlin
@Module
@InstallIn(SingletonComponent::class)
internal interface FeatureModuleBinds {
    @Binds
    fun bindFeatureRepository(impl: FeatureRepositoryImpl): FeatureRepository
}
```

### fake/ — Test implementations (optional)
```kotlin
public class FakeFeatureRepository @Inject constructor() : FeatureRepository {
    override suspend fun getData(...): FeatureData? = FakeData.sampleFeatureData
}
```

---

## 4. Connect RPC Pattern

```kotlin
internal class FeatureRepositoryImpl @Inject constructor(
    protocolClient: ProtocolClientInterface,
    private val telemetryProvider: TelemetryProvider
) : FeatureRepository {

    private val client = FeatureServiceClient(client = protocolClient)

    override suspend fun getFeature(
        channel: String, marketplace: String, language: String
    ): FeatureResponse? {
        val request = GetFeatureRequest.newBuilder()
            .setChannel(channel)
            .setMarketplace(marketplace)
            .setLanguage(language)
            .build()

        val response = client.getFeature(request = request)
        val result = response.success { it.message }
        response.failure {
            telemetryProvider.recordError("getFeature failed", it.cause)
            throw it.cause
        }
        return result
    }
}
```

---

## 5. Compose Screen Pattern

```kotlin
@Composable
internal fun FeatureScreen(
    modifier: Modifier = Modifier,
    viewModel: FeatureViewModel,
    designProvider: DesignProviderV2,
    routeTo: FeatureDestinationHandler
) {
    val state = viewModel.state.collectAsStateWithLifecycle()

    when (val currentState = state.value) {
        is FeatureState.Loading -> ShimmerLoader(modifier)
        is FeatureState.Content -> FeatureContent(currentState, designProvider, routeTo, modifier)
        is FeatureState.Error -> ErrorScreen(currentState.networkErrorState, onRetry = { viewModel.retry() })
    }
}
```

**Detekt-enforced rules:**
- `collectAsStateWithLifecycle()` ONLY (never `collectAsState()`)
- Never pass `State<T>` or `StateFlow<T>` as Composable parameters
- Max 100 non-blank lines per `@Composable` function (excluding `@Preview`)
- `ComposeView` must set `DisposeOnViewTreeLifecycleDestroyed`

---

## 6. Provider Pattern (Feature Screens)

Features expose their UI via a `Provider` interface in `api/`:

```kotlin
// api/
public interface FeatureProvider {
    @Composable
    public fun FeatureScreen(
        marketplace: Marketplace,
        language: Language,
        scrollToTop: Flow<Boolean>,
        routeTo: FeatureDestinationHandler
    )
}

// impl/
internal class FeatureProviderImpl @Inject constructor() : FeatureProvider {
    @Composable
    override fun FeatureScreen(...) {
        val viewModel: FeatureViewModel = hiltViewModel()
        FeatureScreenInternal(viewModel = viewModel, ...)
    }
}
```

---

## 7. BridgeViewModel Pattern (Cross-Feature Communication)

```kotlin
// api/ — public, NOT @HiltViewModel (lifecycle-scoped manually)
public class FeatureBridgeViewModel : ViewModel() {
    private val scrollTo: MutableSharedFlow<Boolean> = MutableSharedFlow()
    private val routeTo: MutableSharedFlow<FeatureDestination> = MutableSharedFlow()

    public fun scrollToEvents(): Flow<Boolean> = scrollTo.asSharedFlow()
    public fun scrollToTop(): Job = viewModelScope.launch { scrollTo.emit(true) }
    public fun routeToEvents(): Flow<FeatureDestination> = routeTo.asSharedFlow()
    public fun navigateTo(dest: FeatureDestination): Job = viewModelScope.launch { routeTo.emit(dest) }
}
```

---

## 8. Error Handling Chain

```
Repository (Connect RPC response.failure -> throw)
    |
UseCase (try/catch -> Result.success/Result.failure)
    |
ViewModel (result.onSuccess/onFailure -> _state.update { Error(...) })
    |
Compose Screen (when state is Error -> ErrorScreen composable)
```

**NetworkErrorState mapping:**
```kotlin
fun Throwable.toNetworkErrorState(): NetworkErrorState = when {
    this is ConnectException && code == Code.UNAVAILABLE -> NetworkErrorState.Offline
    this is ConnectException && code == Code.NOT_FOUND -> NetworkErrorState.ContentNotFound
    this is ConnectException -> NetworkErrorState.ServerError
    this is IOException -> NetworkErrorState.Offline
    else -> NetworkErrorState.CriticalSystemFailure
}
```

---

## 9. Analytics Pattern

```kotlin
internal class FeatureAnalyticsUseCase @Inject constructor(
    private val clickstreamProvider: ClickstreamProvider,
    private val analyticsProvider: AnalyticsProvider,
    private val appScope: CoroutineScope  // Outlives ViewModel for fire-and-forget
) {
    fun trackSurfaceEntered() {
        val action = action {
            surfaceEntered = UserExperience.USER_EXPERIENCE_CONTENT_SHOP_FEED
        }
        clickstreamProvider.sendAction(action)
    }

    fun trackScreenView() {
        analyticsProvider.trackEvent(
            AnalyticsEvent.ScreenEvent(
                name = "shop_feed",
                experience = "shop",
                properties = mapOf("feature" to "shop_it2")
            )
        )
    }
}
```

**Rules:**
- Each feature has its own `*AnalyticsUseCase`
- Clickstream uses protobuf builders (`action { }`)
- Analytics uses `AnalyticsEvent.ScreenEvent`
- Inject `appScope: CoroutineScope` for fire-and-forget (outlives ViewModel)

---

## 10. Testing Pattern

```kotlin
class FeatureViewModelTest {
    private val testDispatcher = UnconfinedTestDispatcher()
    private val fakeRepository = FakeFeatureRepository()
    private val fakeAnalytics = FakeFeatureAnalyticsUseCase()

    private lateinit var sut: FeatureViewModel

    @Before
    fun setup() {
        sut = FeatureViewModel(
            useCase = FeatureUseCaseImpl(fakeRepository),
            analyticsUseCase = fakeAnalytics,
            dispatcher = testDispatcher
        )
    }

    @Test
    fun `fetch success updates state to Content`() = runTest {
        fakeRepository.setResponse(FakeData.sampleData)

        sut.state.test {  // Turbine
            sut.fetchData(Marketplace.MARKETPLACE_US, Language.LANGUAGE_EN)

            val loading = awaitItem()
            loading.shouldBeInstanceOf<FeatureState.Loading>()

            val content = awaitItem()
            content.shouldBeInstanceOf<FeatureState.Content>()
            (content as FeatureState.Content).items.shouldNotBeEmpty()
        }
    }
}
```

**Conventions:**
- Constructor-inject fakes (no Hilt in unit tests)
- Use `UnconfinedTestDispatcher` + `runTest { }`
- Use Turbine `state.test { awaitItem() }` for StateFlow assertions
- Use Kotest matchers (`shouldBe`, `shouldBeInstanceOf`, `shouldNotBeEmpty`)
- Fakes use `Fake*` prefix (not `Mock*`)
- Fakes live in `src/test/.../fake/` directories

---

## 11. File Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| ViewModel | `{Feature}ViewModel.kt` | `ShopViewModel.kt` |
| Screen | `{Feature}Screen.kt` | `ShopScreen.kt` |
| State | `{Feature}State.kt` or `{Feature}UiState.kt` | `ShopState.kt` |
| Repository (interface) | `{Feature}Repository.kt` | `ShopRepository.kt` |
| Repository (impl) | `{Feature}RepositoryImpl.kt` | `ShopRepositoryImpl.kt` |
| UseCase | `{Feature}UseCase.kt` / `{Feature}UseCaseImpl.kt` | `ShopNavMenuUseCase.kt` |
| DI Module | `{Feature}ModuleBinds.kt` or `{Feature}Module.kt` | `ShopModuleBinds.kt` |
| Analytics | `{Feature}AnalyticsUseCase.kt` | `ShopAnalyticsUseCase.kt` |
| Provider | `{Feature}Provider.kt` / `{Feature}ProviderImpl.kt` | `ShopProvider.kt` |
| Bridge VM | `{Feature}BridgeViewModel.kt` | `ShopBridgeViewModel.kt` |
| Destination | `{Feature}Destination.kt` | `ShopDestination.kt` |
| Fake | `Fake{Feature}Repository.kt` | `FakeShopRepository.kt` |
| Test | `{Feature}ViewModelTest.kt` | `ShopViewModelTest.kt` |
| Proto aliases | `{Feature}TypeAliases.kt` | `ShopTypeAliases.kt` |

---

## 12. Visibility Rules

| Module | Default visibility | Rationale |
|--------|-------------------|-----------|
| `api/` | `public` | Consumed by other modules |
| `impl/` | `internal` | Implementation detail |
| `glue/` | `internal` | DI wiring only |
| `fake/` | `public` | Used by other modules tests |
| ViewModels | `internal` | Only accessed via Provider |
| Composables | `internal` | Only accessed within impl |
| State classes | `internal` (in impl) | Only used by ViewModel + Composable |
| Repository impls | `internal` | Accessed via interface in api |
