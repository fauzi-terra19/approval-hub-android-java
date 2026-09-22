# Porting Wings ApprovalHub → Progressive Web App (PWA)

Panduan kerja **end-to-end** untuk mem-port source Android di repo ini ke PWA, memakai **best practice Cursor**: Plan mode, rules, skills, slice kecil, verifikasi browser, Bugbot, dan prompt yang mengikat file sumber.

Dokumen ini **bukan** implementasi PWA. Ini adalah playbook agar agent Cursor (dan manusia) mengerjakan porting secara aman, terukur, dan 1:1 terhadap domain yang sudah ada.

---

## 0. Ringkasan produk yang di-port

**Wings ApprovalHub** adalah aplikasi approval multi-role (STAFF → SUPERVISOR → MANAGER → DIRECTOR → ADMIN).

| Lapisan Android | Isi | Harus 1:1 di PWA? |
| --- | --- | --- |
| `:core:model` | `User`, `ApprovalRequest`, `ApprovalAction`, enum Role/Permission/Status/Type | Ya |
| `:domain` | `RbacPolicy`, `ApprovalWorkflow`, `AmountBasedRules`, `PasswordHasher`, `AnalyticsCalculator` | Ya (port dulu, tes dulu) |
| `:data` | Room + prefs + fake sync + export CSV/PDF | Semantik ya; teknologi ganti |
| `:feature:*` | Login, Dashboard, Inbox, Create/Detail, Analytics, Audit, Settings | Ya, slice per fitur |
| `:feature:widget` | Home-screen widget | Tidak 1:1; ganti App Shortcut / Install PWA |
| `:core:notification` | Inbox notification | Web Push / Notification API |
| `EscalationWorker` | Periodic 6 jam | Periodic Background Sync / server cron / in-app timer |

Akun demo (tetap sama):

| User | Password | Role |
| --- | --- | --- |
| staff / staff2 | staff123 | STAFF |
| supervisor | spv123 | SUPERVISOR |
| manager | mgr123 | MANAGER |
| director | dir123 | DIRECTOR |
| admin | admin123 | ADMIN |

Aturan bisnis yang **tidak boleh diubah** saat port:

- Approval 3 level; submit selalu `PENDING_L1`.
- Idle escalate: **2 hari**.
- Purchase: `> 10_000_000` → L3, `> 2_000_000` → L2, else L1.
- Expense: `> 5_000_000` → L3, else L2.
- Leave / Access: max L2.
- Session timeout: **15 menit** tanpa aktivitas.
- Impersonate: read-only; cabut approve / force escalate / create / manage users.
- Audit & export: scoped ke request yang boleh dilihat; `EXPORT_AUDIT` untuk CSV/PDF.
- Escalation pass manual: butuh `FORCE_ESCALATE`; actor = user yang menjalankan (bukan id 1).
- Dashboard `approved/rejected/inPipeline` dihitung dari request **yang terlihat user**, bukan total global.

---

## 1. Best practice Cursor yang wajib dipatuhi

Ikuti urutan ini. Jangan mulai “buat seluruh PWA” dalam satu chat.

### 1.1 Repo baru, workspace terpisah

Jangan campur Gradle Android dengan Vite di root yang sama.

```
D:\fauzi\cursor\wings\
  android-approval\          ← source of truth (repo ini)
  approvalhub-pwa\           ← repo baru (target port)
```

Di Cursor: **File → Open Folder** ke `approvalhub-pwa`. Tambahkan Android sebagai folder kedua (multi-root) **atau** `@`-mention path Android secara eksplisit:

```text
@D:\fauzi\cursor\wings\android-approval\domain\src\main\java\com\fauzi\wings\domain
```

Alasan: agent tidak mencampur `build.gradle.kts` dengan `package.json`, dan context window tidak terisi `app/build/`.

### 1.2 Plan mode dulu, Agent mode sesudahnya

Untuk arsitektur, routing, IndexedDB schema, dan pilihan stack: **switch ke Plan mode**.

Setelah rencana disetujui (struktur folder + slice 0–N), **switch ke Agent mode** dan kerjakan **satu slice per chat** (atau satu slice per PR).

Jangan minta agent “port semua fitur sekarang”.

### 1.3 Rules + AGENTS.md sebelum kode aplikasi

Buat guidance persisten **sebelum** generate UI. Tanpa ini, agent akan mengarang stack, menambahkan library, atau “memperbaiki” rule bisnis.

Letak:

```
approvalhub-pwa/
  AGENTS.md
  .cursor/rules/
    pwa-port.mdc              alwaysApply: true
    domain-parity.mdc         globs: src/domain/**
    react-ui.mdc              globs: src/**/*.{ts,tsx}
    pwa-shell.mdc             globs: src/sw.ts,vite.config.ts,public/manifest.webmanifest
  .cursor/skills/
    port-android-slice/SKILL.md
    verify-pwa-flow/SKILL.md
```

### 1.4 Skill untuk pekerjaan berulang

Skill proyek (`/.cursor/skills/`) untuk:

- Port satu fitur Android → PWA (baca file Java yang di-`@`, tulis tes, baru UI).
- Verifikasi browser (login tiap role, inbox, timeout, impersonate).
- Mapping RBAC.

Skill **wajib** merujuk file sumber Android, bukan “buat approval app dari imajinasi”.

### 1.5 Prompt yang baik

Setiap task ke agent harus berisi:

1. **Tujuan 1 kalimat** (satu slice).
2. **File sumber Android** dengan `@`.
3. **File target PWA** (buat/ubah).
4. **Out of scope** (jangan sentuh slice lain).
5. **Acceptance** (tes yang harus hijau / alur browser).
6. **Larangan**: jangan rewrite domain, jangan ganti threshold, jangan commit kecuali diminta.

### 1.6 Slice vertikal, bukan layer horizontal

Urutan yang **salah**: “semua UI dulu, domain belakangan”.

Urutan yang **benar**:

1. Domain + tes (parity dengan Java).
2. Persistence + session.
3. Satu layar end-to-end (Login → Dashboard).
4. Fitur berikutnya memakai repository yang sama.
5. PWA shell (manifest, SW, offline, install) setelah app bisa dipakai.

### 1.7 Verifikasi

- Domain: Vitest, port test dari `:domain/src/test` jika ada.
- UI: buka app di browser tools Cursor, klik/ketik/submit. **Screenshot saja tidak cukup.**
- Setelah slice: `/review-bugbot` pada repo PWA (pastikan git sudah `init`).
- Jangan minta agent “fix all” sebelum Anda baca temuan.

### 1.8 Git di repo PWA

Repo Android saat ini **bukan** git repo. Repo PWA **harus** git sejak hari pertama agar Bugbot, PR, dan worktree berfungsi.

```bash
git init
git add AGENTS.md .cursor package.json
git commit -m "chore: bootstrap PWA workspace and Cursor rules"
```

Commit hanya jika Anda minta. Satu slice ≈ satu commit.

---

## 2. Stack target (kunci di rules, jangan diganti diam-diam)

| Concern | Android | PWA |
| --- | --- | --- |
| Bahasa | Java 17 | TypeScript (strict) |
| UI | Fragment + XML + Data Binding | React 19 + Vite |
| State layar | `LiveData<UiState>` | hook + state immutable, atau Zustand sempit |
| Navigasi | Navigation Component + bottom nav | React Router 7, layout + `<Outlet />` |
| DB | Room | Dexie (IndexedDB) |
| Prefs | SharedPreferences | `localStorage` (theme, lastActivity, sessionUserId) |
| DI | `AppContainer` + `ViewModelFactory` | factory `createAppContainer()` di `src/app/container.ts` |
| Sync | `FakeRemoteApi` + delay 400ms | `FakeRemoteApi` Promise + delay yang sama |
| Export | `ExportUtils` CSV/PDF | Blob + `URL.createObjectURL` / `jspdf` hanya jika parity butuh PDF |
| Notifikasi | `ApprovalNotifier` | Notification API (permission) + optional Web Push nanti |
| Theme | `AppCompatDelegate` | `class="dark"` + `prefers-color-scheme` |
| Work periodic | WorkManager 6h | `PeriodicBackgroundSync` jika tersedia; fallback `setInterval` saat tab terbuka |
| Widget | App Widget | Web App Manifest shortcuts (`wings://inbox` → `/inbox`) |
| Hash password | SHA-256 + pepper `approvalhub_v2_pepper` | Web Crypto `SHA-256`, **pepper sama** agar seed demo cocok |

CSS tokens (salin dari `core/ui/.../colors.xml`):

```css
:root {
  --ah-primary: #0f4c5c;
  --ah-primary-dark: #0a3440;
  --ah-accent: #2a9d8f;
  --ah-bg: #f5f7f8;
  --ah-surface: #ffffff;
  --ah-muted: #6b7280;
  --ah-danger: #c62828;
  --ah-success: #15803d;
  --ah-chip: #e8eef0;
  --ah-on-primary: #ffffff;
  --ah-on-surface: #1a1a1a;
}
```

**Jangan** Next.js kecuali Anda sadar ingin SSR. ApprovalHub adalah app offline-first dengan IndexedDB; Vite SPA + service worker lebih dekat ke Room lokal.

---

## 3. Mapping folder

```
approvalhub-pwa/
  AGENTS.md
  .cursor/rules/
  .cursor/skills/
  public/
    manifest.webmanifest
    icons/
  src/
    domain/                 ← port :domain (pure TS, no DOM)
      rbac/rbacPolicy.ts
      approval/workflow.ts
      approval/amountBasedRules.ts
      security/passwordHasher.ts
      analytics/analyticsCalculator.ts
      repositories/         ← interfaces only
    core/
      model/                ← port :core:model
      format/               ← DateFormatters, MoneyFormatters
    data/
      db/schema.ts          ← Dexie
      db/seeder.ts          ← DatabaseSeeder
      repository/appRepository.ts
      sync/syncRepository.ts
      export/exportUtils.ts
      network/fakeRemoteApi.ts
    app/
      container.ts
      sessionTimeout.ts
      theme.ts
      router.tsx
      layout/AppShell.tsx   ← bottom nav
    features/
      auth/
      dashboard/
      inbox/
      request/
      analytics/
      audit/
      settings/
    pwa/
      registerSw.ts
    styles/tokens.css
    main.tsx
  tests/
    domain/
    repository/
  e2e/                      ← Playwright, belakangan
```

Ekuivalensi konsep:

| Android | PWA |
| --- | --- |
| `Fragment` | Route component |
| `ViewModel` | `useXxx()` hook yang memanggil repository |
| `UiState` | `type XxxUiState` |
| `observeX(): LiveData` | Dexie live query (`useLiveQuery`) atau subscribe repository |
| `AppDatabase.IO.execute` | `async`/`await` |
| `NavRoutes.LOGIN` | `/login` |
| `action_global_to_login` + `popUpTo` | `navigate('/login', { replace: true })` + hapus history |
| `HasAppContainer` | React context `AppContainerContext` |

---

## 4. Fase 0 — Bootstrap Cursor (hari pertama, tanpa fitur)

### 4.1 Buat repo

Prompt (Agent mode, folder kosong `approvalhub-pwa`):

```text
Buat scaffold Vite + React + TypeScript strict untuk Wings ApprovalHub PWA.

Jangan implementasi fitur approval dulu.

Wajib:
- package.json: vite, react, react-router, dexie, vite-plugin-pwa, vitest, @testing-library/react
- tsconfig strict (noImplicitAny, strictNullChecks)
- src/main.tsx + placeholder <p>ApprovalHub PWA</p>
- git init jika belum
- Jangan commit kecuali saya minta
- Abaikan folder Android; ini repo terpisah

Out of scope: login, Room port, service worker logic
```

### 4.2 Tulis `AGENTS.md`

Isi minimum (salin lalu sesuaikan path Android di mesin Anda):

```markdown
# AGENTS.md — ApprovalHub PWA

Source of truth domain: D:/fauzi/cursor/wings/android-approval

## Product
Port of Wings ApprovalHub. Offline-first PWA. Demo accounts unchanged.

## Non-negotiables
- Port domain logic 1:1 from Java. Do not "improve" thresholds, RBAC, or workflow.
- Enforce RBAC in repository, not only in UI.
- Session timeout 15 minutes; login must replace history.
- Impersonation is read-only.
- Dashboard stats from visible requests only.
- Audit data scoped; EXPORT_AUDIT gates CSV/PDF.
- Manual escalation pass uses session.userId as actor.

## Stack
Vite, React, TypeScript strict, Dexie, React Router, vite-plugin-pwa.

## How to work
- One vertical slice per task.
- @-mention the Android Java files being ported.
- Tests for domain before UI.
- Verify UI in the browser by exercising the flow.
- Do not add libraries without updating this file.
```

### 4.3 Rule `alwaysApply`

File `.cursor/rules/pwa-port.mdc`:

```markdown
---
description: Global PWA port constraints for ApprovalHub
alwaysApply: true
---

# ApprovalHub PWA port

You are porting an existing Android app. Read Android sources before writing TS.

Never invent new roles, permissions, request types, or amount thresholds.

Prefer small diffs. Match existing PWA folder names in src/.

Do not modify Android sources unless the user asks.

Do not put secrets in git. Demo pepper is already in the Android hasher; keep it for demo parity only and document it as demo-only.
```

File `.cursor/rules/domain-parity.mdc`:

```markdown
---
description: Domain must stay 1:1 with Android Java
globs: src/domain/**
alwaysApply: false
---

Port functions as pure TypeScript. Mirror method names where practical.

After any domain change, run Vitest tests in tests/domain/.
```

### 4.4 Skill slice

`.cursor/skills/port-android-slice/SKILL.md`:

```markdown
---
name: port-android-slice
description: Port one Android feature slice into the PWA with tests and source file mapping.
---

# Port Android slice

1. Identify Android files the user @-mentioned.
2. List types, methods, and UI states to port.
3. Write or update Vitest cases from those behaviors.
4. Implement domain/data first, then the route.
5. Do not expand scope to other features.
6. Stop and summarize: files changed, how to verify.
```

Setelah Fase 0: buka `http://localhost:5173`, pastikan placeholder tampil. Baru commit jika Anda minta.

---

## 5. Fase 1 — Domain parity (paling penting)

Kerjakan **tanpa UI**. Ini fondasi; UI yang salah bisa diganti, rule bisnis yang salah merusak seluruh app.

### 5.1 Urutan file yang di-`@`

Satu chat per kelompok:

1. Model  
   `@android-approval/core/model/src/main/java/com/fauzi/wings/core/model`
2. RBAC  
   `@.../domain/rbac/RbacPolicy.java` `@.../Permission.java` `@.../Role.java`
3. Workflow + amount  
   `@.../ApprovalWorkflow.java` `@.../AmountBasedRules.java` `@.../ApprovalStatus.java`
4. Password  
   `@.../PasswordHasher.java`
5. Analytics  
   `@.../AnalyticsCalculator.java`

### 5.2 Prompt template Fase 1

```text
Gunakan skill port-android-slice.

Port HANYA RbacPolicy + Permission + Role ke src/domain.

Sumber:
@D:\fauzi\cursor\wings\android-approval\domain\src\main\java\com\fauzi\wings\domain\rbac\RbacPolicy.java
@D:\fauzi\cursor\wings\android-approval\core\model\src\main\java\com\fauzi\wings\core\model\Permission.java
@D:\fauzi\cursor\wings\android-approval\core\model\src\main\java\com\fauzi\wings\core\model\Role.java

Wajib tes Vitest:
- ADMIN punya FORCE_ESCALATE dan EXPORT_AUDIT
- STAFF tidak punya VIEW_ALL_REQUESTS
- impersonationPermissions menghapus APPROVE_LEVEL_*, FORCE_ESCALATE, CREATE_REQUEST, IMPERSONATE, MANAGE_USERS
- canApproveLevel 1/2/3 sesuai role

Out of scope: UI, Dexie, login.

Jangan commit.
```

Ulangi untuk workflow (tes: approve L1 dengan maxLevel 1 → APPROVED; maxLevel 3 → PENDING_L2; escalate terminal → null; idle 2 hari).

Ulangi untuk amount rules (angka threshold **exact**).

Ulangi hasher: `hash("staff123")` harus **byte-identical** dengan Java SHA-256 hex dari `approvalhub_v2_pepper:staff123`. Tulis tes vektor tetap.

### 5.3 Definition of done Fase 1

```bash
npx vitest run tests/domain
```

Semua hijau. Belum ada halaman.

---

## 6. Fase 2 — Data layer (Dexie = Room)

### 6.1 Schema

Port entity:

- `users` ← `UserEntity`
- `approval_requests` ← `ApprovalRequestEntity`
- `approval_actions` ← `ApprovalActionEntity`
- `sync_meta` ← `SyncMetaEntity`
- `metric_snapshots` (jika seeder memakainya)

Index yang sama secara semantik: `requesterId`, `status`, `updatedAt`, `requestId` pada actions.

### 6.2 Seeder

`@.../DatabaseSeeder.java` — port jumlah user, request sampel, dan hash password lewat `PasswordHasher`. Jangan hardcode hash berbeda.

### 6.3 Repository

Port perilaku (bukan signature LiveData) dari:

`@.../data/repository/AppRepository.java`

Wajib termasuk perilaku yang sudah di-harden:

| Method | Perilaku PWA |
| --- | --- |
| `login` | username trim, hasher.matches, simpan sessionUserId, touchActivity |
| `checkSessionTimeout` | 15 menit; logout + clear |
| `hasPermission` | role session, atau impersonationPermissions jika impersonate |
| `observeRequestsForCurrentUser` / `visibleRequests` | `canViewRequest` |
| `observeInbox` | `canActOn`; kosong jika impersonate |
| `observeDashboardStats` | hitung dari visible requests |
| `createRequest` | CREATE_REQUEST, bukan impersonate |
| `decide` | `canActOn` level |
| `forceEscalate` / `runEscalationPass` | FORCE_ESCALATE; actor = session.id |
| `visibleRequestsSnapshot` / `visibleActionsSnapshot` | filter action by visible ids |

### 6.4 Prompt

```text
Port AppRepository ke src/data/repository/appRepository.ts.

Sumber utama:
@D:\fauzi\cursor\wings\android-approval\data\src\main\java\com\fauzi\wings\data\repository\AppRepository.java

Pakai Dexie yang sudah ada di src/data/db.
Pakai domain yang sudah di-port; jangan salin ulang rule di repository.

Tulis tes repository (fake in-memory Dexie atau Dexie fake-indexeddb):
1. STAFF login tidak melihat request departemen lain
2. runEscalationPass tanpa FORCE_ESCALATE throw
3. runEscalationPass menulis actorId = session.id
4. dashboard approved tidak memakai total global
5. impersonate membuat inbox kosong dan createRequest throw

Out of scope: React pages.
```

### 6.5 Prefs & fake network

- `UserPreferences` → `src/data/prefs.ts` (tiga key yang sama).
- `FakeRemoteApi` → delay 400ms, `pullRequestCount = 2`.

---

## 7. Fase 3 — App shell + auth + timeout

### 7.1 Router

| Path | Android | Guard |
| --- | --- | --- |
| `/login` | `loginFragment` | public; jika sudah session → `/` |
| `/` | dashboard | auth |
| `/inbox` | inbox | auth |
| `/requests/new` | create | auth + CREATE_REQUEST |
| `/requests/:id` | detail | auth + can view |
| `/analytics` | analytics | auth |
| `/audit` | audit | auth (data tetap scoped) |
| `/settings` | settings | auth |

Bottom nav: Home, Inbox, Charts, Audit, Settings (label sama `menu_bottom.xml`). Sembunyikan nav di login, create, detail.

Timeout: listener `visibilitychange` + `pointerdown`/`keydown` → `touchActivity`. Di interval 30s atau on resume: jika timeout, `logout` lalu `navigate('/login', { replace: true })`. **Jangan** biarkan Back ke dashboard.

### 7.2 Prompt Login

```text
Implementasikan fitur auth PWA.

Sumber:
@.../LoginFragment.java
@.../LoginViewModel.java
@.../fragment_login.xml
@.../DemoAccounts.java

UI: form username/password, daftar akun demo, error "Username atau password salah".
Warna pakai tokens.css.

Verifikasi di browser:
- login staff / staff123 → dashboard
- password salah → error, tetap di /login
- refresh masih session (Dexie + prefs)
- setelah 15 menit dimock (saya boleh minta helper test), redirect /login replace

Out of scope: inbox, create request.
```

Skill verifikasi: klik nyata, bukan hanya render.

---

## 8. Fase 4 — Dashboard + Inbox + Request

Kerjakan **tiga chat terpisah**.

### 8.1 Dashboard

Sumber: `DashboardFragment`, `DashboardViewModel`, `fragment_dashboard.xml`, `RbacPolicy.dashboardTitle`.

Tampilkan lima angka dari stats yang sudah scoped. Tombol create hanya jika `CREATE_REQUEST`.

### 8.2 Inbox

Sumber: `InboxFragment`, `InboxViewModel`, `RequestListAdapter`, `item_request.xml`.

Klik item → `/requests/:id`. Impersonate → list kosong.

### 8.3 Create + Detail

Sumber: `CreateRequest*`, `ApprovalDetail*`, `AmountBasedRules.ruleLabel`.

Detail: Approve / Reject sesuai `canActOn`; Escalate hanya `FORCE_ESCALATE` dan status non-terminal.

Prompt detail (contoh):

```text
Port approval detail.

Sumber:
@.../ApprovalDetailFragment.java
@.../ApprovalDetailViewModel.java
@.../fragment_approval_detail.xml
@.../ApprovalWorkflow.java

Out of scope: analytics, audit, settings, PWA install.

Verifikasi browser dengan akun supervisor: approve request L1, status berubah sesuai maxLevel.
```

---

## 9. Fase 5 — Analytics, Audit, Settings

### 9.1 Analytics

Port `AnalyticsCalculator` + chart dari `statusCounts`. Ingat: Android `observeStatusCounts` masih **global**; PWA boleh:

- **Opsi A (parity ketat):** global seperti Android analytics.
- **Opsi B (lebih aman):** scoped seperti dashboard.

Tulis keputusan di `AGENTS.md` sebelum coding. Default playbook: **Opsi B** (scoped), dan sebutkan di PR bahwa ini sadar menyimpang dari analytics Android yang masih global.

### 9.2 Audit

Wajib:

- Subscribe session + impersonate + daftar visible requests.
- Saat impersonate menyempit: **langsung** kosongkan `canExport` dan konten lama, baru load ulang (parity `AuditViewModel` terbaru).
- Tombol CSV/PDF hanya `EXPORT_AUDIT`.
- Export memakai dataset scoped yang sedang tampil.

### 9.3 Settings

- Theme LIGHT/DARK/SYSTEM.
- Impersonate spinner (hanya jika `IMPERSONATE`).
- Sync Now (fake API).
- Run Escalation Pass **hidden** tanpa `FORCE_ESCALATE`.
- Logout: clear session + `replace` ke `/login`.

---

## 10. Fase 6 — PWA production shell

Kerjakan **setelah** alur utama jalan.

### 10.1 `manifest.webmanifest`

```json
{
  "name": "Wings ApprovalHub",
  "short_name": "ApprovalHub",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#F5F7F8",
  "theme_color": "#0F4C5C",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable" }
  ],
  "shortcuts": [
    { "name": "Inbox", "url": "/inbox" },
    { "name": "Buat request", "url": "/requests/new" }
  ]
}
```

### 10.2 Service worker

`vite-plugin-pwa` + Workbox:

- Precache shell (HTML/JS/CSS).
- IndexedDB **jangan** di-cache sebagai HTTP; Dexie tetap sumber data.
- Navigasi fallback ke `index.html` (SPA).
- Offline: login tetap perlu data Dexie lokal (sudah ada); tampilkan banner “Offline”.

### 10.3 Notifikasi

Port `ApprovalNotifier.notifyInbox` ke `Notification.requestPermission` + `new Notification(title, { body })` saat tab boleh. Jangan spam. Web Push terpusat = fase belakangan (butuh backend).

### 10.4 Escalation periodik

Parity WorkManager 6 jam:

1. Saat app foreground: cek overdue + (opsional) auto-run **hanya** sebagai job sistem, bukan tombol user tanpa permission.
2. Auto job di PWA **tanpa user** setara `EscalationWorker` (actor sistem). Bedakan dengan tombol Settings yang memakai `session.id`.
3. Dokumentasikan: tab tertutup = job tidak jalan, kecuali nanti ada server.

### 10.5 Installability checklist

- HTTPS atau localhost
- Manifest valid
- SW controlling
- Icon 192 + 512
- `display: standalone`

Prompt:

```text
Tambah PWA shell saja: vite-plugin-pwa, manifest, icons placeholder, register SW, offline banner.

Jangan ubah domain atau RBAC.
Verifikasi di Chrome Application panel: manifest + SW activated.
```

---

## 11. Fase 7 — Kualitas, a11y, performa

- Landmark: `<main>`, nav `aria-label="Primary"`.
- Kontras token sudah didefinisikan; jangan abu-abu di abu-abu.
- Form login: `<label>`, `autocomplete`.
- List request: keyboard (Enter membuka detail).
- Jangan bundle seluruh `jspdf` jika CSV cukup untuk slice awal; PDF menyusul.
- Lighthouse: PWA, a11y, best practices. Target installable + 0 error a11y pada login/dashboard.

Playwright e2e (setelah UI stabil):

1. staff login → create request → logout
2. supervisor login → inbox → approve
3. admin impersonate staff → escalate button hilang, inbox kosong
4. export audit hilang untuk staff

---

## 12. Checklist slice (cetak untuk setiap PR)

```text
[ ] Android files @-mentioned in the chat
[ ] Domain/tests first if logic changed
[ ] RBAC enforced in repository
[ ] No new npm deps without AGENTS.md update
[ ] Browser flow exercised (not screenshot-only)
[ ] /review-bugbot on PWA repo
[ ] Commit only if user asked
```

---

## 13. Prompt master — urutan chat yang disarankan

Salin satu per satu. Jangan gabungkan.

| # | Mode | Isi |
| --- | --- | --- |
| 1 | Plan | Arsitektur folder + Dexie schema + daftar slice. Tunggu approval. |
| 2 | Agent | Scaffold Vite + `AGENTS.md` + `.cursor/rules` + skills. |
| 3 | Agent | Port models + RBAC + tes. |
| 4 | Agent | Port workflow + amount rules + hasher + tes. |
| 5 | Agent | Dexie + seeder + AppRepository + tes. |
| 6 | Agent | Router, shell nav, login, session timeout. **Browser verify.** |
| 7 | Agent | Dashboard. **Browser verify.** |
| 8 | Agent | Inbox + list item. **Browser verify.** |
| 9 | Agent | Create + detail approve/reject/escalate. **Browser verify.** |
| 10 | Agent | Analytics (tulis pilihan scoped vs global). |
| 11 | Agent | Audit reload + export gate. **Impersonate then reopen Audit.** |
| 12 | Agent | Settings theme, impersonate, sync, escalation pass, logout. |
| 13 | Agent | PWA manifest + SW + offline banner + shortcuts. |
| 14 | Agent | Playwright happy paths + Lighthouse notes. |
| 15 | Ask | `/review-bugbot` lalu triase; fix hanya temuan yang Anda setujui. |

Prompt pembuka Plan mode:

```text
Saya akan mem-port Wings ApprovalHub Android ke PWA di repo ini (kosong).

Baca dulu:
@D:\fauzi\cursor\wings\android-approval\README.md
@D:\fauzi\cursor\wings\android-approval\docs\PORTING-PWA-CURSOR.md
@D:\fauzi\cursor\wings\android-approval\domain\src\main\java\com\fauzi\wings\domain

Buat rencana slice 0–N sesuai playbook. Jangan menulis kode aplikasi.
Tampilkan: struktur folder, schema Dexie, risiko parity, dan urutan tes.
Tunggu saya approve sebelum Agent mode.
```

---

## 14. Anti-pola (yang sering dilakukan agent)

| Jangan | Lakukan |
| --- | --- |
| Satu prompt “buat PWA lengkap” | Satu slice, file sumber `@` |
| Menyalin Java ke TypeScript di dalam komponen React | Domain murni + tes |
| Menyembunyikan tombol saja tanpa cek repository | RBAC di `appRepository` |
| `navigate('/login')` tanpa `replace` | Hapus history seperti `popUpTo` |
| Analytics/dashboard dari `COUNT(*)` global | Visible set |
| Menambah Next, Redux, Tailwind “karena standar” | Stack yang dikunci di AGENTS.md |
| Mengedit `android-approval` sambil generate PWA | Repo terpisah |
| Commit otomatis | Hanya jika user minta |
| Mengandalkan screenshot | Klik alur di browser |
| Mengabaikan Bugbot | Tabel temuan, fix terarah |

---

## 15. Definition of done (seluruh port)

Port selesai jika:

1. Semua akun demo login dengan password yang sama.
2. Workflow L1–L3 dan amount rules lulus tes vektor.
3. Staff tidak melihat / mengekspor audit global.
4. Impersonate: audit & export menyesuaikan **segera**, inbox kosong, tidak bisa decide.
5. Timeout 15 menit membawa ke login tanpa Back ke data.
6. Escalation pass manual butuh permission dan `actorId` = operator.
7. App installable (manifest + SW) di Chrome desktop.
8. Offline: buka dashboard dari cache + Dexie (tanpa network) setelah kunjungan pertama.
9. Bugbot pada repo PWA: no bugs pada slice terakhir, atau temuan tertutup.
10. README PWA menjelaskan cara `npm run dev`, akun demo, dan bahwa data hidup di IndexedDB browser.

---

## 16. Referensi cepat file Android

| Topik | Path |
| --- | --- |
| Arsitektur | `README.md` |
| Modul | `settings.gradle.kts` |
| RBAC | `domain/.../RbacPolicy.java` |
| Workflow | `domain/.../ApprovalWorkflow.java` |
| Amount | `domain/.../AmountBasedRules.java` |
| Hasher | `domain/.../PasswordHasher.java` |
| Repository | `data/.../AppRepository.java` |
| Seed | `core/database/.../DatabaseSeeder.java` |
| Nav | `app/src/main/res/navigation/nav_graph.xml` |
| Bottom nav | `app/src/main/res/menu/menu_bottom.xml` |
| Warna | `core/ui/src/main/res/values/colors.xml` |
| Worker | `app/.../work/EscalationWorker.java` |
| Fake API | `core/network/.../FakeRemoteApi.java` |

---

*Playbook ini mengikuti cara kerja Cursor: rencana dulu, rules/skills, slice kecil, sumber di-`@`, tes domain, verifikasi browser, lalu Bugbot. Implementasi PWA dimulai di repo terpisah, bukan dengan menyalin file ini ke dalam modul Gradle.*
