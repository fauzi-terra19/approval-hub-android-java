"""App module: MainActivity, Koin, Workers, nav host, manifests, launcher."""
from __future__ import annotations


def gen_app(w, PKG, P):
    w("app/build.gradle.kts", f"""
plugins {{
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.ksp)
}}

android {{
    namespace = "{PKG}.app"
    compileSdk = libs.versions.compileSdk.get().toInt()

    defaultConfig {{
        applicationId = "{PKG}"
        minSdk = libs.versions.minSdk.get().toInt()
        targetSdk = libs.versions.targetSdk.get().toInt()
        versionCode = 1
        versionName = "1.0"
    }}

    buildTypes {{
        release {{
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }}
    }}
    compileOptions {{
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }}
    kotlinOptions {{ jvmTarget = "17" }}
    buildFeatures {{
        dataBinding = true
        viewBinding = true
    }}
}}

dependencies {{
    implementation(project(":core:ui"))
    implementation(project(":core:model"))
    implementation(project(":core:common"))
    implementation(project(":core:database"))
    implementation(project(":core:datastore"))
    implementation(project(":core:network"))
    implementation(project(":core:notification"))
    implementation(project(":domain"))
    implementation(project(":data"))
    implementation(project(":feature:auth"))
    implementation(project(":feature:dashboard"))
    implementation(project(":feature:inbox"))
    implementation(project(":feature:request"))
    implementation(project(":feature:analytics"))
    implementation(project(":feature:audit"))
    implementation(project(":feature:settings"))
    implementation(project(":feature:widget"))

    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.appcompat)
    implementation(libs.material)
    implementation(libs.androidx.constraintlayout)
    implementation(libs.androidx.activity)
    implementation(libs.androidx.fragment)
    implementation(libs.androidx.navigation.fragment)
    implementation(libs.androidx.navigation.ui)
    implementation(libs.androidx.lifecycle.runtime)
    implementation(libs.androidx.lifecycle.viewmodel)
    implementation(libs.androidx.work)
    implementation(libs.koin.android)
    implementation(libs.koin.workmanager)
    implementation(libs.coroutines.android)
}}
""")
    w("app/proguard-rules.pro", "# app proguard\n")
    w("app/src/main/AndroidManifest.xml", f"""
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />

    <application
        android:name=".ApprovalHubApp"
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.ApprovalHub">

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:windowSoftInputMode="adjustResize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="${{applicationId}}.fileprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/file_paths" />
        </provider>
    </application>
</manifest>
""")
    w("app/src/main/res/xml/file_paths.xml", """
<?xml version="1.0" encoding="utf-8"?>
<paths>
    <cache-path name="cache" path="." />
</paths>
""")
    w("app/src/main/res/values/strings.xml", """
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">ApprovalHub</string>
</resources>
""")
    w("app/src/main/res/layout/activity_main.xml", """
<?xml version="1.0" encoding="utf-8"?>
<androidx.constraintlayout.widget.ConstraintLayout
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:layout_width="match_parent"
    android:layout_height="match_parent">

    <androidx.fragment.app.FragmentContainerView
        android:id="@+id/nav_host"
        android:name="androidx.navigation.fragment.NavHostFragment"
        android:layout_width="0dp"
        android:layout_height="0dp"
        app:defaultNavHost="true"
        app:navGraph="@navigation/nav_graph"
        app:layout_constraintTop_toTopOf="parent"
        app:layout_constraintBottom_toTopOf="@id/bottomNav"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent" />

    <com.google.android.material.bottomnavigation.BottomNavigationView
        android:id="@+id/bottomNav"
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:background="@color/ah_surface"
        app:menu="@menu/menu_bottom"
        app:layout_constraintBottom_toBottomOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent" />
</androidx.constraintlayout.widget.ConstraintLayout>
""")
    # Shared nav + bottom menu in core:ui so feature modules share the same R ids
    w("core/ui/src/main/res/menu/menu_bottom.xml", """
<?xml version="1.0" encoding="utf-8"?>
<menu xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:id="@+id/dashboardFragment" android:title="Home" android:icon="@android:drawable/ic_menu_compass" />
    <item android:id="@+id/inboxFragment" android:title="Inbox" android:icon="@android:drawable/ic_menu_agenda" />
    <item android:id="@+id/analyticsFragment" android:title="Charts" android:icon="@android:drawable/ic_menu_sort_by_size" />
    <item android:id="@+id/auditFragment" android:title="Audit" android:icon="@android:drawable/ic_menu_recent_history" />
    <item android:id="@+id/settingsFragment" android:title="Settings" android:icon="@android:drawable/ic_menu_preferences" />
</menu>
""")
    w("core/ui/src/main/res/navigation/nav_graph.xml", f"""
<?xml version="1.0" encoding="utf-8"?>
<navigation xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:id="@+id/nav_graph"
    app:startDestination="@id/loginFragment">

    <fragment
        android:id="@+id/loginFragment"
        android:name="{PKG}.feature.auth.LoginFragment"
        android:label="Login">
        <action
            android:id="@+id/action_login_to_dashboard"
            app:destination="@id/dashboardFragment"
            app:popUpTo="@id/loginFragment"
            app:popUpToInclusive="true" />
    </fragment>

    <fragment
        android:id="@+id/dashboardFragment"
        android:name="{PKG}.feature.dashboard.DashboardFragment"
        android:label="Dashboard" />

    <fragment
        android:id="@+id/inboxFragment"
        android:name="{PKG}.feature.inbox.InboxFragment"
        android:label="Inbox" />

    <fragment
        android:id="@+id/createRequestFragment"
        android:name="{PKG}.feature.request.CreateRequestFragment"
        android:label="Create" />

    <fragment
        android:id="@+id/approvalDetailFragment"
        android:name="{PKG}.feature.request.ApprovalDetailFragment"
        android:label="Detail">
        <argument android:name="requestId" app:argType="long" android:defaultValue="0L" />
    </fragment>

    <fragment
        android:id="@+id/analyticsFragment"
        android:name="{PKG}.feature.analytics.AnalyticsFragment"
        android:label="Analytics" />

    <fragment
        android:id="@+id/auditFragment"
        android:name="{PKG}.feature.audit.AuditFragment"
        android:label="Audit" />

    <fragment
        android:id="@+id/settingsFragment"
        android:name="{PKG}.feature.settings.SettingsFragment"
        android:label="Settings" />

    <action android:id="@+id/action_global_to_detail" app:destination="@id/approvalDetailFragment" />
    <action android:id="@+id/action_global_to_create" app:destination="@id/createRequestFragment" />
    <action
        android:id="@+id/action_global_to_login"
        app:destination="@id/loginFragment"
        app:popUpTo="@id/nav_graph"
        app:popUpToInclusive="true" />
</navigation>
""")
    # launcher assets
    w("app/src/main/res/drawable/ic_launcher_foreground.xml", """
<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
    <path android:fillColor="#2A9D8F"
        android:pathData="M54,30c-10,0 -18,8 -18,18v8h-6v24h48V56h-6v-8c0,-10 -8,-18 -18,-18zM46,56v-8c0,-4.4 3.6,-8 8,-8s8,3.6 8,8v8H46z"/>
</vector>
""")
    w("app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml", """
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ah_primary"/>
    <foreground android:drawable="@drawable/ic_launcher_foreground"/>
</adaptive-icon>
""")
    w("app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml", """
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ah_primary"/>
    <foreground android:drawable="@drawable/ic_launcher_foreground"/>
</adaptive-icon>
""")
    w("app/src/main/res/values/colors.xml", """
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ah_primary">#0F4C5C</color>
    <color name="ah_surface">#FFFFFF</color>
</resources>
""")
    # Also need Theme in app or rely on core:ui - app theme references Theme.ApprovalHub from core:ui via dependency. Non-transitive R might block color from core:ui in mipmap. We duplicated ah_primary in app.

    base = f"app/src/main/java/{P}/app"
    w(f"{base}/ApprovalHubApp.kt", f"""
package {PKG}.app

import android.app.Application
import {PKG}.app.di.appModule
import {PKG}.app.work.EscalationWorker
import {PKG}.core.notification.ApprovalNotifier
import org.koin.android.ext.koin.androidContext
import org.koin.android.ext.koin.androidLogger
import org.koin.androidx.workmanager.koin.workManagerFactory
import org.koin.core.context.startKoin

class ApprovalHubApp : Application() {{
    override fun onCreate() {{
        super.onCreate()
        ApprovalNotifier.ensureChannel(this)
        startKoin {{
            androidLogger()
            androidContext(this@ApprovalHubApp)
            workManagerFactory()
            modules(appModule)
        }}
        EscalationWorker.schedule(this)
    }}
}}
""")
    w(f"{base}/MainActivity.kt", f"""
package {PKG}.app

import android.os.Bundle
import android.view.View
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.isVisible
import androidx.navigation.fragment.NavHostFragment
import androidx.navigation.ui.setupWithNavController
import com.google.android.material.bottomnavigation.BottomNavigationView

class MainActivity : AppCompatActivity() {{
    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        val navHost = supportFragmentManager.findFragmentById(R.id.nav_host) as NavHostFragment
        val navController = navHost.navController
        val bottomNav = findViewById<BottomNavigationView>(R.id.bottomNav)
        bottomNav.setupWithNavController(navController)
        navController.addOnDestinationChangedListener {{ _, destination, _ ->
            val uiR = {PKG}.core.ui.R.id
            val hide = destination.id == uiR.loginFragment ||
                destination.id == uiR.createRequestFragment ||
                destination.id == uiR.approvalDetailFragment
            bottomNav.isVisible = !hide
        }}
    }}
}}
""")
    w(f"{base}/di/AppModule.kt", f"""
package {PKG}.app.di

import {PKG}.core.database.AppDatabase
import {PKG}.core.datastore.UserPreferences
import {PKG}.core.network.FakeRemoteApi
import {PKG}.core.network.RemoteApi
import {PKG}.data.repository.AppRepository
import {PKG}.data.sync.SyncRepository
import {PKG}.domain.repository.ApprovalRepository
import {PKG}.domain.repository.SessionRepository
import {PKG}.feature.analytics.AnalyticsViewModel
import {PKG}.feature.audit.AuditViewModel
import {PKG}.feature.auth.LoginViewModel
import {PKG}.feature.dashboard.DashboardViewModel
import {PKG}.feature.inbox.InboxViewModel
import {PKG}.feature.request.ApprovalDetailViewModel
import {PKG}.feature.request.CreateRequestViewModel
import {PKG}.feature.settings.SettingsViewModel
import org.koin.android.ext.koin.androidContext
import org.koin.androidx.viewmodel.dsl.viewModel
import org.koin.dsl.module

val appModule = module {{
    single {{ AppDatabase.get(androidContext()) }}
    single {{ UserPreferences(androidContext()) }}
    single<RemoteApi> {{ FakeRemoteApi() }}
    single {{ SyncRepository(get(), get()) }}
    single {{ AppRepository(get(), get(), get(), androidContext()) }}
    single<SessionRepository> {{ get<AppRepository>() }}
    single<ApprovalRepository> {{ get<AppRepository>() }}

    viewModel {{ LoginViewModel(get()) }}
    viewModel {{ DashboardViewModel(get(), get()) }}
    viewModel {{ InboxViewModel(get()) }}
    viewModel {{ CreateRequestViewModel(get()) }}
    viewModel {{ (requestId: Long) -> ApprovalDetailViewModel(requestId, get(), get()) }}
    viewModel {{ AnalyticsViewModel(get()) }}
    viewModel {{ AuditViewModel(get()) }}
    viewModel {{ SettingsViewModel(get(), get()) }}
}}
""")
    w(f"{base}/work/Workers.kt", f"""
package {PKG}.app.work

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import {PKG}.core.database.AppDatabase
import {PKG}.core.database.entity.ApprovalActionEntity
import {PKG}.core.network.FakeRemoteApi
import {PKG}.core.notification.ApprovalNotifier
import {PKG}.data.sync.SyncRepository
import {PKG}.domain.approval.ApprovalWorkflow
import java.util.concurrent.TimeUnit

class EscalationWorker(
    appContext: Context,
    params: WorkerParameters
) : CoroutineWorker(appContext, params) {{

    override suspend fun doWork(): Result {{
        val db = AppDatabase.get(applicationContext)
        val now = System.currentTimeMillis()
        val threshold = now - ApprovalWorkflow.IDLE_BEFORE_ESCALATE_MS
        val overdue = db.approvalRequestDao().getOverdue(threshold)
        var escalatedCount = 0
        overdue.forEach {{ request ->
            val next = ApprovalWorkflow.escalateStatus(request.status, request.requiredMaxLevel) ?: return@forEach
            val level = ApprovalWorkflow.requiredLevel(next) ?: return@forEach
            db.approvalRequestDao().update(
                request.copy(status = next, currentLevel = level, escalated = true, updatedAt = now)
            )
            db.approvalActionDao().insert(
                ApprovalActionEntity(
                    requestId = request.id, actorId = 1, level = request.currentLevel,
                    decision = "ESCALATE", comment = "Auto-escalate karena idle > 2 hari", createdAt = now
                )
            )
            escalatedCount++
        }}
        val pending = db.approvalRequestDao().getAll().count {{ it.status.name.startsWith("PENDING") }}
        if (pending > 0 || escalatedCount > 0) {{
            ApprovalNotifier.notifyInbox(
                applicationContext,
                title = if (escalatedCount > 0) "Escalation & Inbox" else "Approval Inbox",
                body = buildString {{
                    if (escalatedCount > 0) append("$escalatedCount request di-escalate. ")
                    append("$pending request masih pending.")
                }},
                notificationId = 2001
            )
        }}
        return Result.success()
    }}

    companion object {{
        private const val UNIQUE = "escalation_periodic"
        fun schedule(context: Context) {{
            val request = PeriodicWorkRequestBuilder<EscalationWorker>(6, TimeUnit.HOURS).build()
            WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                UNIQUE, ExistingPeriodicWorkPolicy.UPDATE, request
            )
        }}
    }}
}}

class SyncWorker(
    appContext: Context,
    params: WorkerParameters
) : CoroutineWorker(appContext, params) {{
    override suspend fun doWork(): Result = try {{
        val db = AppDatabase.get(applicationContext)
        SyncRepository(db, FakeRemoteApi()).syncNow()
        Result.success()
    }} catch (_: Exception) {{
        Result.retry()
    }}

    companion object {{
        fun enqueueOnce(context: Context) {{
            WorkManager.getInstance(context).enqueue(OneTimeWorkRequestBuilder<SyncWorker>().build())
        }}
    }}
}}
""")
