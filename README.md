# Wings ApprovalHub (Java + MVVM)

Multi-module Android app — **Java 17 only** (no Kotlin sources).

## Architecture

```
Fragment / XML (View)
   ↓ observes LiveData<UiState>
ViewModel (feature modules)
   ↓
Domain (RBAC, workflow, amount rules)
   ↓
Data (Room + SharedPreferences + FakeRemoteApi)
```

### Stack
- Language: **Java 17**
- UI: XML · Data Binding · findViewById · RecyclerView · Navigation Component
- Pattern: **MVVM** (`ViewModel` + `LiveData` + `UiState`)
- Modules: `:app` · `:feature:*` · `:domain` · `:data` · `:core:*`
- DI: manual `AppContainer` + `ViewModelFactory` (`HasAppContainer`)

### Demo accounts
| User | Password | Role |
|------|----------|------|
| staff / staff2 | staff123 | STAFF |
| supervisor | spv123 | SUPERVISOR |
| manager | mgr123 | MANAGER |
| director | dir123 | DIRECTOR |
| admin | admin123 | ADMIN |

### Build
```bash
./gradlew :app:assembleDebug
```
