#!/usr/bin/env python3
"""Generate all remaining Java feature + app modules."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = "com.fauzi.wings"
P = PKG.replace(".", "/")


def w(rel: str, content: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip("\n") + "\n", encoding="utf-8")
    print("wrote", rel)


def empty_manifest() -> str:
    return '<?xml version="1.0" encoding="utf-8"?>\n<manifest xmlns:android="http://schemas.android.com/apk/res/android" />\n'


def feature_build(ns: str, extras: list[str] | None = None, databinding: bool = True) -> str:
    deps = [
        'api(project(":core:ui"))',
        'api(project(":core:model"))',
        'api(project(":domain"))',
        'implementation(project(":data"))',
        "api(libs.androidx.appcompat)",
        "api(libs.material)",
        "api(libs.androidx.lifecycle.viewmodel)",
        "api(libs.androidx.lifecycle.livedata)",
        "api(libs.androidx.fragment)",
        "api(libs.androidx.navigation.fragment)",
        "api(libs.androidx.recyclerview)",
        "api(libs.androidx.swiperefresh)",
    ]
    if extras:
        deps.extend(extras)
    feat = ""
    if databinding:
        feat = """
    buildFeatures {
        dataBinding = true
        viewBinding = true
    }
"""
    return f'''plugins {{
    alias(libs.plugins.android.library)
}}

android {{
    namespace = "{ns}"
    compileSdk = libs.versions.compileSdk.get().toInt()
    defaultConfig {{
        minSdk = libs.versions.minSdk.get().toInt()
        consumerProguardFiles("consumer-rules.pro")
    }}
    compileOptions {{
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }}{feat}}}

dependencies {{
{chr(10).join("    " + d for d in deps)}
}}
'''


def vm_boilerplate(class_name: str) -> str:
    return f'''
        HasAppContainer services = HasAppContainer.from(requireContext());
        viewModel = new ViewModelProvider(this, services.getViewModelFactory()).get({class_name}.class);
'''


def main() -> None:
    patch_db()
    di_and_export()
    nav_menu()
    auth()
    dashboard()
    inbox()
    request()
    analytics()
    audit()
    settings()
    widget()
    app()
    domain_test()
    for kt in ROOT.rglob("*.kt"):
        if "tools" in kt.parts:
            continue
        print("deleting", kt)
        kt.unlink()
    print("DONE")


def patch_db() -> None:
    w(f"core/database/src/main/java/{P}/core/database/AppDatabase.java", f'''
package {PKG}.core.database;

import android.content.Context;

import androidx.room.Database;
import androidx.room.Room;
import androidx.room.RoomDatabase;
import androidx.room.TypeConverters;

@Database(
        entities = {{
                UserEntity.class,
                ApprovalRequestEntity.class,
                ApprovalActionEntity.class,
                MetricSnapshotEntity.class,
                SyncMetaEntity.class
        }},
        version = 1,
        exportSchema = false
)
@TypeConverters(Converters.class)
public abstract class AppDatabase extends RoomDatabase {{
    private static volatile AppDatabase INSTANCE;

    public abstract UserDao userDao();
    public abstract ApprovalRequestDao approvalRequestDao();
    public abstract ApprovalActionDao approvalActionDao();
    public abstract MetricDao metricDao();
    public abstract SyncMetaDao syncMetaDao();

    public static AppDatabase get(Context context) {{
        if (INSTANCE == null) {{
            synchronized (AppDatabase.class) {{
                if (INSTANCE == null) {{
                    INSTANCE = build(context.getApplicationContext());
                }}
            }}
        }}
        return INSTANCE;
    }}

    public static AppDatabase build(Context context) {{
        return Room.databaseBuilder(context, AppDatabase.class, "wings_approval_hub.db")
                .build();
    }}
}}
''')


def di_and_export() -> None:
    w(f"data/src/main/java/{P}/data/di/HasAppContainer.java", f'''
package {PKG}.data.di;

import android.content.Context;

import androidx.lifecycle.ViewModelProvider;

import {PKG}.data.repository.AppRepository;

import java.util.concurrent.Executor;

public interface HasAppContainer {{
    AppRepository getRepository();

    Executor getIoExecutor();

    ViewModelProvider.Factory getViewModelFactory();

    static HasAppContainer from(Context context) {{
        Context app = context.getApplicationContext();
        if (app instanceof HasAppContainer) {{
            return (HasAppContainer) app;
        }}
        throw new IllegalStateException("Application must implement HasAppContainer");
    }}
}}
''')
    w(f"data/src/main/java/{P}/data/export/ExportUtils.java", f'''
package {PKG}.data.export;

import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.pdf.PdfDocument;
import android.net.Uri;

import androidx.core.content.FileProvider;

import {PKG}.core.model.ApprovalAction;
import {PKG}.core.model.ApprovalRequest;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

public final class ExportUtils {{
    private static final SimpleDateFormat SDF =
            new SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.getDefault());

    private ExportUtils() {{}}

    public static Uri exportAuditCsv(
            Context context,
            List<ApprovalRequest> requests,
            List<ApprovalAction> actions,
            Map<Long, String> userNames
    ) throws Exception {{
        StringBuilder sb = new StringBuilder();
        sb.append("requestId,title,status,type,amount,department,actionId,level,decision,actor,comment,createdAt\\n");
        Map<Long, List<ApprovalAction>> byReq = new HashMap<>();
        for (ApprovalAction a : actions) {{
            byReq.computeIfAbsent(a.getRequestId(), k -> new ArrayList<>()).add(a);
        }}
        for (ApprovalRequest req : requests) {{
            List<ApprovalAction> rows = byReq.getOrDefault(req.getId(), List.of());
            if (rows.isEmpty()) {{
                sb.append(req.getId()).append(",\\"").append(esc(req.getTitle())).append("\\",")
                        .append(req.getStatus()).append(',').append(req.getType()).append(',')
                        .append(req.getAmount()).append(',').append(req.getDepartment())
                        .append(",,,,,,\\n");
            }} else {{
                for (ApprovalAction a : rows) {{
                    String actor = userNames.containsKey(a.getActorId())
                            ? userNames.get(a.getActorId()) : String.valueOf(a.getActorId());
                    sb.append(req.getId()).append(",\\"").append(esc(req.getTitle())).append("\\",")
                            .append(req.getStatus()).append(',').append(req.getType()).append(',')
                            .append(req.getAmount()).append(',').append(req.getDepartment()).append(',')
                            .append(a.getId()).append(',').append(a.getLevel()).append(',')
                            .append(a.getDecision()).append(",\\"").append(esc(actor)).append("\\",\\"")
                            .append(esc(a.getComment())).append("\\",")
                            .append(SDF.format(new Date(a.getCreatedAt()))).append('\\n');
                }}
            }}
        }}
        File file = new File(context.getCacheDir(), "audit_" + System.currentTimeMillis() + ".csv");
        try (OutputStreamWriter writer = new OutputStreamWriter(
                new FileOutputStream(file), StandardCharsets.UTF_8)) {{
            writer.write(sb.toString());
        }}
        return FileProvider.getUriForFile(context, context.getPackageName() + ".fileprovider", file);
    }}

    public static Uri exportAuditPdf(
            Context context,
            List<ApprovalRequest> requests,
            List<ApprovalAction> actions,
            Map<Long, String> userNames
    ) throws Exception {{
        PdfDocument doc = new PdfDocument();
        Paint paint = new Paint();
        paint.setTextSize(10f);
        int pageNumber = 1;
        float y = 40f;
        PdfDocument.Page page = doc.startPage(new PdfDocument.PageInfo.Builder(595, 842, pageNumber).create());
        Canvas canvas = page.getCanvas();
        canvas.drawText("ApprovalHub Audit Trail", 40f, y, paint);
        y += 24f;

        int limit = Math.min(40, requests.size());
        for (int i = 0; i < limit; i++) {{
            ApprovalRequest req = requests.get(i);
            if (y + 60f > 800f) {{
                doc.finishPage(page);
                pageNumber++;
                page = doc.startPage(new PdfDocument.PageInfo.Builder(595, 842, pageNumber).create());
                canvas = page.getCanvas();
                y = 40f;
            }}
            canvas.drawText("#" + req.getId() + " " + req.getTitle() + " [" + req.getStatus() + "]", 40f, y, paint);
            y += 14f;
            canvas.drawText(req.getType() + " · " + req.getAmount() + " · " + req.getDepartment(), 48f, y, paint);
            y += 14f;
            for (ApprovalAction a : actions) {{
                if (a.getRequestId() != req.getId()) continue;
                if (y + 16f > 800f) {{
                    doc.finishPage(page);
                    pageNumber++;
                    page = doc.startPage(new PdfDocument.PageInfo.Builder(595, 842, pageNumber).create());
                    canvas = page.getCanvas();
                    y = 40f;
                }}
                String actor = userNames.containsKey(a.getActorId())
                        ? userNames.get(a.getActorId()) : String.valueOf(a.getActorId());
                canvas.drawText("L" + a.getLevel() + " " + a.getDecision() + " by " + actor
                        + " — " + a.getComment(), 56f, y, paint);
                y += 14f;
            }}
            y += 8f;
        }}
        doc.finishPage(page);
        File file = new File(context.getCacheDir(), "audit_" + System.currentTimeMillis() + ".pdf");
        try (FileOutputStream fos = new FileOutputStream(file)) {{
            doc.writeTo(fos);
        }}
        doc.close();
        return FileProvider.getUriForFile(context, context.getPackageName() + ".fileprovider", file);
    }}

    public static void shareUri(Context context, Uri uri, String mime, String title) {{
        Intent intent = new Intent(Intent.ACTION_SEND);
        intent.setType(mime);
        intent.putExtra(Intent.EXTRA_STREAM, uri);
        intent.putExtra(Intent.EXTRA_SUBJECT, title);
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        Intent chooser = Intent.createChooser(intent, title);
        chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        context.startActivity(chooser);
    }}

    public static void shareBitmap(Context context, Bitmap bitmap, String title) throws Exception {{
        File file = new File(context.getCacheDir(), "chart_" + System.currentTimeMillis() + ".png");
        try (FileOutputStream fos = new FileOutputStream(file)) {{
            bitmap.compress(Bitmap.CompressFormat.PNG, 95, fos);
        }}
        Uri uri = FileProvider.getUriForFile(context, context.getPackageName() + ".fileprovider", file);
        shareUri(context, uri, "image/png", title);
    }}

    public static Bitmap createSimpleChartBitmap(List<String> labels, List<Float> values, String title) {{
        int width = 1080;
        int height = 720;
        Bitmap bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
        Canvas canvas = new Canvas(bitmap);
        canvas.drawColor(0xFFFFFFFF);
        Paint titlePaint = new Paint();
        titlePaint.setTextSize(42f);
        titlePaint.setFakeBoldText(true);
        titlePaint.setColor(0xFF0F4C5C);
        Paint barPaint = new Paint();
        barPaint.setColor(0xFF2A9D8F);
        Paint textPaint = new Paint();
        textPaint.setTextSize(28f);
        textPaint.setColor(0xFF333333);
        canvas.drawText(title, 40f, 60f, titlePaint);
        float max = 1f;
        for (Float v : values) {{
            if (v != null && v > max) max = v;
        }}
        float chartTop = 120f;
        float chartBottom = height - 100f;
        float chartHeight = chartBottom - chartTop;
        float slot = (width - 80f) / Math.max(1, values.size());
        for (int i = 0; i < values.size(); i++) {{
            float v = values.get(i) == null ? 0f : values.get(i);
            float barH = (v / max) * chartHeight;
            float left = 40f + i * slot + slot * 0.2f;
            float right = left + slot * 0.6f;
            canvas.drawRect(left, chartBottom - barH, right, chartBottom, barPaint);
            String label = i < labels.size() ? labels.get(i) : "";
            if (label.length() > 8) label = label.substring(0, 8);
            canvas.drawText(label, left, chartBottom + 40f, textPaint);
        }}
        return bitmap;
    }}

    private static String esc(String value) {{
        return value == null ? "" : value.replace("\\"", "'");
    }}
}}
''')
    w("data/build.gradle.kts", '''
plugins {
    alias(libs.plugins.android.library)
}

android {
    namespace = "com.fauzi.wings.data"
    compileSdk = libs.versions.compileSdk.get().toInt()
    defaultConfig {
        minSdk = libs.versions.minSdk.get().toInt()
        consumerProguardFiles("consumer-rules.pro")
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    api(project(":domain"))
    api(project(":core:model"))
    api(project(":core:common"))
    api(project(":core:database"))
    api(project(":core:preference"))
    api(project(":core:network"))
    api(project(":core:notification"))
    api(libs.androidx.lifecycle.livedata)
    api(libs.androidx.lifecycle.viewmodel)
    implementation(libs.androidx.appcompat)
    implementation(libs.androidx.core)
}
''')


def nav_menu() -> None:
    w("core/ui/src/main/res/menu/menu_bottom.xml", '''
<?xml version="1.0" encoding="utf-8"?>
<menu xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:id="@+id/dashboardFragment" android:title="Home" android:icon="@android:drawable/ic_menu_compass" />
    <item android:id="@+id/inboxFragment" android:title="Inbox" android:icon="@android:drawable/ic_menu_agenda" />
    <item android:id="@+id/analyticsFragment" android:title="Charts" android:icon="@android:drawable/ic_menu_sort_by_size" />
    <item android:id="@+id/auditFragment" android:title="Audit" android:icon="@android:drawable/ic_menu_recent_history" />
    <item android:id="@+id/settingsFragment" android:title="Settings" android:icon="@android:drawable/ic_menu_preferences" />
</menu>
''')
    w("core/ui/src/main/res/navigation/nav_graph.xml", f'''
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
''')


def auth() -> None:
    w("feature/auth/build.gradle.kts", feature_build(f"{PKG}.feature.auth"))
    w("feature/auth/consumer-rules.pro", "#\n")
    w("feature/auth/src/main/AndroidManifest.xml", empty_manifest())
    w("feature/auth/src/main/res/layout/fragment_login.xml", '''
<?xml version="1.0" encoding="utf-8"?>
<ScrollView xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:fillViewport="true"
    android:background="@color/wings_surface">
    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="vertical"
        android:padding="24dp"
        android:gravity="center_horizontal">
        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="@string/login_title"
            android:textSize="28sp"
            android:textStyle="bold"
            android:textColor="@color/wings_primary"
            android:layout_marginTop="48dp" />
        <TextView
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:text="@string/login_subtitle"
            android:textColor="@color/wings_muted"
            android:layout_marginBottom="32dp" />
        <com.google.android.material.textfield.TextInputLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:hint="Username">
            <com.google.android.material.textfield.TextInputEditText
                android:id="@+id/inputUsername"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:inputType="text" />
        </com.google.android.material.textfield.TextInputLayout>
        <com.google.android.material.textfield.TextInputLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:hint="Password"
            android:layout_marginTop="12dp">
            <com.google.android.material.textfield.TextInputEditText
                android:id="@+id/inputPassword"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:inputType="textPassword" />
        </com.google.android.material.textfield.TextInputLayout>
        <TextView
            android:id="@+id/textError"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:textColor="@color/wings_danger"
            android:visibility="gone"
            android:layout_marginTop="8dp" />
        <com.google.android.material.button.MaterialButton
            android:id="@+id/btnLogin"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="@string/action_masuk"
            android:layout_marginTop="20dp" />
        <ProgressBar
            android:id="@+id/progress"
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:visibility="gone"
            android:layout_marginTop="16dp" />
        <TextView
            android:id="@+id/textDemoAccounts"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:layout_marginTop="24dp"
            android:textSize="12sp"
            android:textColor="@color/wings_muted" />
    </LinearLayout>
</ScrollView>
''')
    base = f"feature/auth/src/main/java/{P}/feature/auth"
    w(f"{base}/LoginUiState.java", f'''
package {PKG}.feature.auth;

import {PKG}.core.model.DemoAccounts;
import {PKG}.core.model.User;

public class LoginUiState {{
    public final boolean loading;
    public final String error;
    public final User loggedInUser;
    public final String demoHint;

    public LoginUiState(boolean loading, String error, User loggedInUser, String demoHint) {{
        this.loading = loading;
        this.error = error;
        this.loggedInUser = loggedInUser;
        this.demoHint = demoHint;
    }}

    public static LoginUiState initial() {{
        StringBuilder sb = new StringBuilder();
        for (DemoAccounts.DemoAccount d : DemoAccounts.ALL) {{
            if (sb.length() > 0) sb.append('\\n');
            sb.append(d.username).append(" / ").append(d.password).append(" · ").append(d.roleLabel);
        }}
        return new LoginUiState(false, null, null, sb.toString());
    }}

    public LoginUiState withLoading(boolean loading) {{
        return new LoginUiState(loading, null, loggedInUser, demoHint);
    }}

    public LoginUiState withError(String error) {{
        return new LoginUiState(false, error, null, demoHint);
    }}

    public LoginUiState withUser(User user) {{
        return new LoginUiState(false, null, user, demoHint);
    }}
}}
''')
    w(f"{base}/LoginViewModel.java", f'''
package {PKG}.feature.auth;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.Observer;
import androidx.lifecycle.ViewModel;

import {PKG}.core.model.User;
import {PKG}.data.repository.AppRepository;
import {PKG}.domain.repository.SessionRepository;

import java.util.concurrent.Executor;

public class LoginViewModel extends ViewModel {{
    private final AppRepository repository;
    private final Executor ioExecutor;
    private final MutableLiveData<LoginUiState> uiState = new MutableLiveData<>(LoginUiState.initial());
    private final Observer<User> sessionObserver = user -> {{
        if (user != null) {{
            LoginUiState cur = uiState.getValue();
            if (cur == null) cur = LoginUiState.initial();
            uiState.postValue(cur.withUser(user));
        }}
    }};

    public LoginViewModel(AppRepository repository, Executor ioExecutor) {{
        this.repository = repository;
        this.ioExecutor = ioExecutor;
        repository.ensureSeeded(ioExecutor, () -> repository.restoreSession(ioExecutor));
        repository.getSession().observeForever(sessionObserver);
    }}

    public LiveData<LoginUiState> getUiState() {{
        return uiState;
    }}

    public void login(String username, String password) {{
        LoginUiState cur = uiState.getValue();
        if (cur == null) cur = LoginUiState.initial();
        uiState.setValue(cur.withLoading(true));
        repository.login(username, password, ioExecutor, new SessionRepository.Callback<User>() {{
            @Override
            public void onSuccess(User value) {{
                LoginUiState s = uiState.getValue();
                if (s == null) s = LoginUiState.initial();
                uiState.postValue(s.withUser(value));
            }}

            @Override
            public void onError(Throwable error) {{
                LoginUiState s = uiState.getValue();
                if (s == null) s = LoginUiState.initial();
                uiState.postValue(s.withError(error.getMessage()));
            }}
        }});
    }}

    @Override
    protected void onCleared() {{
        repository.getSession().removeObserver(sessionObserver);
        super.onCleared();
    }}
}}
''')
    w(f"{base}/LoginFragment.java", f'''
package {PKG}.feature.auth;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.ProgressBar;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.lifecycle.ViewModelProvider;
import androidx.navigation.fragment.NavHostFragment;

import com.google.android.material.textfield.TextInputEditText;

import {PKG}.data.di.HasAppContainer;

public class LoginFragment extends Fragment {{
    private LoginViewModel viewModel;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {{
        return inflater.inflate(R.layout.fragment_login, container, false);
    }}

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        HasAppContainer services = HasAppContainer.from(requireContext());
        viewModel = new ViewModelProvider(this, services.getViewModelFactory()).get(LoginViewModel.class);

        // findViewById required for LoginFragment
        TextInputEditText inputUsername = view.findViewById(R.id.inputUsername);
        TextInputEditText inputPassword = view.findViewById(R.id.inputPassword);
        Button btnLogin = view.findViewById(R.id.btnLogin);
        TextView textError = view.findViewById(R.id.textError);
        ProgressBar progress = view.findViewById(R.id.progress);
        TextView textDemo = view.findViewById(R.id.textDemoAccounts);

        btnLogin.setOnClickListener(v -> viewModel.login(
                inputUsername.getText() == null ? "" : inputUsername.getText().toString(),
                inputPassword.getText() == null ? "" : inputPassword.getText().toString()
        ));

        viewModel.getUiState().observe(getViewLifecycleOwner(), state -> {{
            textDemo.setText(state.demoHint);
            progress.setVisibility(state.loading ? View.VISIBLE : View.GONE);
            btnLogin.setEnabled(!state.loading);
            if (state.error != null) {{
                textError.setVisibility(View.VISIBLE);
                textError.setText(state.error);
            }} else {{
                textError.setVisibility(View.GONE);
            }}
            if (state.loggedInUser != null) {{
                NavHostFragment.findNavController(this)
                        .navigate({PKG}.core.ui.R.id.action_login_to_dashboard);
            }}
        }});
    }}
}}
''')


def dashboard() -> None:
    w("feature/dashboard/build.gradle.kts", feature_build(f"{PKG}.feature.dashboard"))
    w("feature/dashboard/consumer-rules.pro", "#\n")
    w("feature/dashboard/src/main/AndroidManifest.xml", empty_manifest())
    w("feature/dashboard/src/main/res/layout/fragment_dashboard.xml", '''
<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android">
    <data>
        <variable name="title" type="String" />
        <variable name="stats" type="String" />
        <variable name="userLine" type="String" />
    </data>
    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:orientation="vertical"
        android:background="@color/wings_surface">
        <TextView
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:padding="16dp"
            android:text="@{title}"
            android:textSize="20sp"
            android:textStyle="bold"
            android:textColor="@color/wings_primary"
            android:background="@color/wings_card" />
        <TextView
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:paddingHorizontal="16dp"
            android:paddingBottom="8dp"
            android:text="@{userLine}"
            android:textColor="@color/wings_muted"
            android:background="@color/wings_card" />
        <TextView
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:padding="16dp"
            android:text="@{stats}"
            android:textSize="14sp" />
        <androidx.recyclerview.widget.RecyclerView
            android:id="@+id/recycler"
            android:layout_width="match_parent"
            android:layout_height="0dp"
            android:layout_weight="1" />
        <com.google.android.material.button.MaterialButton
            android:id="@+id/btnCreate"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="Buat Request"
            android:layout_margin="12dp" />
    </LinearLayout>
</layout>
''')
    base = f"feature/dashboard/src/main/java/{P}/feature/dashboard"
    w(f"{base}/DashboardUiState.java", f'''
package {PKG}.feature.dashboard;

import {PKG}.core.model.ApprovalRequest;
import {PKG}.core.model.DashboardStats;
import {PKG}.core.model.User;

import java.util.Collections;
import java.util.List;

public class DashboardUiState {{
    public final User user;
    public final String title;
    public final DashboardStats stats;
    public final List<ApprovalRequest> requests;

    public DashboardUiState(User user, String title, DashboardStats stats, List<ApprovalRequest> requests) {{
        this.user = user;
        this.title = title;
        this.stats = stats == null ? new DashboardStats() : stats;
        this.requests = requests == null ? Collections.emptyList() : requests;
    }}

    public static DashboardUiState empty() {{
        return new DashboardUiState(null, "Dashboard", new DashboardStats(), Collections.emptyList());
    }}
}}
''')
    w(f"{base}/DashboardViewModel.java", f'''
package {PKG}.feature.dashboard;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MediatorLiveData;
import androidx.lifecycle.ViewModel;

import {PKG}.core.model.ApprovalRequest;
import {PKG}.core.model.DashboardStats;
import {PKG}.core.model.Role;
import {PKG}.core.model.User;
import {PKG}.data.repository.AppRepository;
import {PKG}.domain.rbac.RbacPolicy;

import java.util.List;

public class DashboardViewModel extends ViewModel {{
    private final MediatorLiveData<DashboardUiState> uiState = new MediatorLiveData<>(DashboardUiState.empty());

    public DashboardViewModel(AppRepository repository) {{
        LiveData<User> session = repository.getSession();
        LiveData<Role> imp = repository.getImpersonateRole();
        LiveData<DashboardStats> stats = repository.observeDashboardStats();
        LiveData<List<ApprovalRequest>> requests = repository.observeRequestsForCurrentUser();
        Runnable recompute = () -> {{
            User user = session.getValue();
            Role roleImp = imp.getValue();
            Role role = roleImp != null ? roleImp : (user == null ? null : user.getRole());
            String title = role == null ? "Dashboard" : RbacPolicy.dashboardTitle(role);
            uiState.setValue(new DashboardUiState(
                    user, title, stats.getValue(), requests.getValue()));
        }};
        uiState.addSource(session, v -> recompute.run());
        uiState.addSource(imp, v -> recompute.run());
        uiState.addSource(stats, v -> recompute.run());
        uiState.addSource(requests, v -> recompute.run());
    }}

    public LiveData<DashboardUiState> getUiState() {{
        return uiState;
    }}
}}
''')
    w(f"{base}/DashboardFragment.java", f'''
package {PKG}.feature.dashboard;

import android.os.Bundle;
import android.view.View;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.lifecycle.ViewModelProvider;
import androidx.navigation.fragment.NavHostFragment;
import androidx.recyclerview.widget.LinearLayoutManager;

import {PKG}.core.ui.BaseMvvmFragment;
import {PKG}.core.ui.RequestListAdapter;
import {PKG}.data.di.HasAppContainer;
import {PKG}.feature.dashboard.databinding.FragmentDashboardBinding;

public class DashboardFragment extends BaseMvvmFragment<FragmentDashboardBinding> {{
    private DashboardViewModel viewModel;
    private RequestListAdapter adapter;

    public DashboardFragment() {{
        super(R.layout.fragment_dashboard);
    }}

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        HasAppContainer services = HasAppContainer.from(requireContext());
        viewModel = new ViewModelProvider(this, services.getViewModelFactory()).get(DashboardViewModel.class);
        adapter = new RequestListAdapter(req -> {{
            Bundle args = new Bundle();
            args.putLong("requestId", req.getId());
            NavHostFragment.findNavController(this)
                    .navigate({PKG}.core.ui.R.id.action_global_to_detail, args);
        }});
        getBinding().recycler.setLayoutManager(new LinearLayoutManager(requireContext()));
        getBinding().recycler.setAdapter(adapter);
        getBinding().btnCreate.setOnClickListener(v ->
                NavHostFragment.findNavController(this)
                        .navigate({PKG}.core.ui.R.id.action_global_to_create));
        observe(viewModel.getUiState(), state -> {{
            getBinding().setTitle(state.title);
            if (state.user != null) {{
                getBinding().setUserLine(state.user.getDisplayName() + " · "
                        + state.user.getRole() + " · " + state.user.getDepartment());
            }} else {{
                getBinding().setUserLine("");
            }}
            getBinding().setStats("Visible " + state.stats.getTotalVisible()
                    + " · Inbox " + state.stats.getPendingInbox()
                    + " · Approved " + state.stats.getApproved()
                    + " · Rejected " + state.stats.getRejected()
                    + " · Pipeline " + state.stats.getInPipeline());
            adapter.submitList(state.requests);
        }});
    }}
}}
''')


def inbox() -> None:
    w("feature/inbox/build.gradle.kts", feature_build(f"{PKG}.feature.inbox"))
    w("feature/inbox/consumer-rules.pro", "#\n")
    w("feature/inbox/src/main/AndroidManifest.xml", empty_manifest())
    w("feature/inbox/src/main/res/layout/fragment_inbox.xml", '''
<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android">
    <data>
        <variable name="emptyText" type="String" />
    </data>
    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:orientation="vertical"
        android:background="@color/wings_surface">
        <TextView
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:padding="16dp"
            android:text="Inbox Approval"
            android:textStyle="bold"
            android:textSize="20sp"
            android:textColor="@color/wings_primary" />
        <TextView
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:padding="16dp"
            android:text="@{emptyText}"
            android:textColor="@color/wings_muted" />
        <androidx.recyclerview.widget.RecyclerView
            android:id="@+id/recycler"
            android:layout_width="match_parent"
            android:layout_height="match_parent" />
    </LinearLayout>
</layout>
''')
    base = f"feature/inbox/src/main/java/{P}/feature/inbox"
    w(f"{base}/InboxViewModel.java", f'''
package {PKG}.feature.inbox;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.Transformations;
import androidx.lifecycle.ViewModel;

import {PKG}.core.model.ApprovalRequest;
import {PKG}.data.repository.AppRepository;

import java.util.Collections;
import java.util.List;

public class InboxViewModel extends ViewModel {{
    private final LiveData<List<ApprovalRequest>> items;

    public InboxViewModel(AppRepository repository) {{
        items = Transformations.map(repository.observeInbox(), list ->
                list == null ? Collections.emptyList() : list);
    }}

    public LiveData<List<ApprovalRequest>> getItems() {{
        return items;
    }}
}}
''')
    w(f"{base}/InboxFragment.java", f'''
package {PKG}.feature.inbox;

import android.os.Bundle;
import android.view.View;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.lifecycle.ViewModelProvider;
import androidx.navigation.fragment.NavHostFragment;
import androidx.recyclerview.widget.LinearLayoutManager;

import {PKG}.core.ui.BaseMvvmFragment;
import {PKG}.core.ui.RequestListAdapter;
import {PKG}.data.di.HasAppContainer;
import {PKG}.feature.inbox.databinding.FragmentInboxBinding;

public class InboxFragment extends BaseMvvmFragment<FragmentInboxBinding> {{
    private InboxViewModel viewModel;
    private RequestListAdapter adapter;

    public InboxFragment() {{
        super(R.layout.fragment_inbox);
    }}

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        HasAppContainer services = HasAppContainer.from(requireContext());
        viewModel = new ViewModelProvider(this, services.getViewModelFactory()).get(InboxViewModel.class);
        adapter = new RequestListAdapter(req -> {{
            Bundle args = new Bundle();
            args.putLong("requestId", req.getId());
            NavHostFragment.findNavController(this)
                    .navigate({PKG}.core.ui.R.id.action_global_to_detail, args);
        }});
        getBinding().recycler.setLayoutManager(new LinearLayoutManager(requireContext()));
        getBinding().recycler.setAdapter(adapter);
        observe(viewModel.getItems(), list -> {{
            getBinding().setEmptyText(list == null || list.isEmpty()
                    ? "Tidak ada item menunggu aksi Anda" : "");
            adapter.submitList(list);
        }});
    }}
}}
''')


def request() -> None:
    w("feature/request/build.gradle.kts", feature_build(f"{PKG}.feature.request"))
    w("feature/request/consumer-rules.pro", "#\n")
    w("feature/request/src/main/AndroidManifest.xml", empty_manifest())
    w("feature/request/src/main/res/layout/fragment_create_request.xml", '''
<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android">
    <data>
        <variable name="ruleHint" type="String" />
        <variable name="error" type="String" />
    </data>
    <ScrollView
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:background="@color/wings_surface">
        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="vertical"
            android:padding="16dp">
            <TextView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:text="Buat Request"
                android:textStyle="bold"
                android:textSize="20sp"
                android:textColor="@color/wings_primary" />
            <com.google.android.material.textfield.TextInputLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:hint="Judul"
                android:layout_marginTop="12dp">
                <com.google.android.material.textfield.TextInputEditText
                    android:id="@+id/inputTitle"
                    android:layout_width="match_parent"
                    android:layout_height="wrap_content" />
            </com.google.android.material.textfield.TextInputLayout>
            <com.google.android.material.textfield.TextInputLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:hint="Deskripsi"
                android:layout_marginTop="8dp">
                <com.google.android.material.textfield.TextInputEditText
                    android:id="@+id/inputDesc"
                    android:layout_width="match_parent"
                    android:layout_height="wrap_content" />
            </com.google.android.material.textfield.TextInputLayout>
            <Spinner
                android:id="@+id/spinnerType"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="12dp" />
            <com.google.android.material.textfield.TextInputLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:hint="Amount"
                android:layout_marginTop="8dp">
                <com.google.android.material.textfield.TextInputEditText
                    android:id="@+id/inputAmount"
                    android:layout_width="match_parent"
                    android:layout_height="wrap_content"
                    android:inputType="numberDecimal" />
            </com.google.android.material.textfield.TextInputLayout>
            <TextView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:text="@{ruleHint}"
                android:layout_marginTop="8dp"
                android:textColor="@color/wings_primary" />
            <TextView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:text="@{error}"
                android:textColor="@color/wings_danger"
                android:layout_marginTop="4dp" />
            <com.google.android.material.button.MaterialButton
                android:id="@+id/btnSubmit"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:text="Submit"
                android:layout_marginTop="16dp" />
        </LinearLayout>
    </ScrollView>
</layout>
''')
    w("feature/request/src/main/res/layout/fragment_approval_detail.xml", '''
<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android">
    <data>
        <variable name="detail" type="String" />
        <variable name="canAct" type="boolean" />
        <variable name="canEscalate" type="boolean" />
        <variable name="message" type="String" />
    </data>
    <ScrollView
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:background="@color/wings_surface">
        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="vertical"
            android:padding="16dp">
            <TextView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:text="@{detail}"
                android:textSize="14sp" />
            <com.google.android.material.textfield.TextInputLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:hint="Komentar"
                android:layout_marginTop="12dp">
                <com.google.android.material.textfield.TextInputEditText
                    android:id="@+id/inputComment"
                    android:layout_width="match_parent"
                    android:layout_height="wrap_content" />
            </com.google.android.material.textfield.TextInputLayout>
            <LinearLayout
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:orientation="horizontal"
                android:layout_marginTop="12dp">
                <com.google.android.material.button.MaterialButton
                    android:id="@+id/btnApprove"
                    android:layout_width="0dp"
                    android:layout_weight="1"
                    android:layout_height="wrap_content"
                    android:text="Approve"
                    android:enabled="@{canAct}" />
                <com.google.android.material.button.MaterialButton
                    android:id="@+id/btnReject"
                    android:layout_width="0dp"
                    android:layout_weight="1"
                    android:layout_height="wrap_content"
                    android:text="Reject"
                    android:enabled="@{canAct}"
                    style="@style/Widget.MaterialComponents.Button.OutlinedButton" />
            </LinearLayout>
            <com.google.android.material.button.MaterialButton
                android:id="@+id/btnEscalate"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:text="Force Escalate"
                android:enabled="@{canEscalate}"
                android:layout_marginTop="8dp" />
            <TextView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:text="@{message}"
                android:layout_marginTop="8dp"
                android:textColor="@color/wings_muted" />
            <TextView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:text="Riwayat aksi"
                android:textStyle="bold"
                android:layout_marginTop="16dp" />
            <TextView
                android:id="@+id/textActions"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="8dp" />
        </LinearLayout>
    </ScrollView>
</layout>
''')
    base = f"feature/request/src/main/java/{P}/feature/request"
    w(f"{base}/CreateRequestUiState.java", f'''
package {PKG}.feature.request;

public class CreateRequestUiState {{
    public final String ruleHint;
    public final String error;
    public final Long createdId;
    public final boolean loading;

    public CreateRequestUiState(String ruleHint, String error, Long createdId, boolean loading) {{
        this.ruleHint = ruleHint == null ? "" : ruleHint;
        this.error = error;
        this.createdId = createdId;
        this.loading = loading;
    }}

    public static CreateRequestUiState initial() {{
        return new CreateRequestUiState("", null, null, false);
    }}
}}
''')
    w(f"{base}/CreateRequestViewModel.java", f'''
package {PKG}.feature.request;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;

import {PKG}.core.model.RequestType;
import {PKG}.data.repository.AppRepository;
import {PKG}.domain.approval.AmountBasedRules;
import {PKG}.domain.repository.SessionRepository;

import java.util.concurrent.Executor;

public class CreateRequestViewModel extends ViewModel {{
    private final AppRepository repository;
    private final Executor ioExecutor;
    private final MutableLiveData<CreateRequestUiState> uiState =
            new MutableLiveData<>(CreateRequestUiState.initial());

    public CreateRequestViewModel(AppRepository repository, Executor ioExecutor) {{
        this.repository = repository;
        this.ioExecutor = ioExecutor;
    }}

    public LiveData<CreateRequestUiState> getUiState() {{
        return uiState;
    }}

    public void updateHint(RequestType type, double amount) {{
        CreateRequestUiState cur = uiState.getValue();
        if (cur == null) cur = CreateRequestUiState.initial();
        uiState.setValue(new CreateRequestUiState(
                AmountBasedRules.ruleLabel(type, amount), cur.error, cur.createdId, cur.loading));
    }}

    public void submit(String title, String description, RequestType type, double amount) {{
        CreateRequestUiState cur = uiState.getValue();
        if (cur == null) cur = CreateRequestUiState.initial();
        uiState.setValue(new CreateRequestUiState(cur.ruleHint, null, null, true));
        repository.createRequest(title, description, type, amount, ioExecutor,
                new SessionRepository.Callback<Long>() {{
                    @Override
                    public void onSuccess(Long value) {{
                        CreateRequestUiState s = uiState.getValue();
                        if (s == null) s = CreateRequestUiState.initial();
                        uiState.postValue(new CreateRequestUiState(s.ruleHint, null, value, false));
                    }}

                    @Override
                    public void onError(Throwable error) {{
                        CreateRequestUiState s = uiState.getValue();
                        if (s == null) s = CreateRequestUiState.initial();
                        uiState.postValue(new CreateRequestUiState(s.ruleHint, error.getMessage(), null, false));
                    }}
                }});
    }}
}}
''')
    w(f"{base}/CreateRequestFragment.java", f'''
package {PKG}.feature.request;

import android.os.Bundle;
import android.view.View;
import android.widget.ArrayAdapter;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.lifecycle.ViewModelProvider;
import androidx.navigation.fragment.NavHostFragment;

import {PKG}.core.model.RequestType;
import {PKG}.core.ui.BaseMvvmFragment;
import {PKG}.data.di.HasAppContainer;
import {PKG}.feature.request.databinding.FragmentCreateRequestBinding;

public class CreateRequestFragment extends BaseMvvmFragment<FragmentCreateRequestBinding> {{
    private CreateRequestViewModel viewModel;

    public CreateRequestFragment() {{
        super(R.layout.fragment_create_request);
    }}

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        HasAppContainer services = HasAppContainer.from(requireContext());
        viewModel = new ViewModelProvider(this, services.getViewModelFactory())
                .get(CreateRequestViewModel.class);
        RequestType[] types = RequestType.values();
        String[] names = new String[types.length];
        for (int i = 0; i < types.length; i++) names[i] = types[i].name();
        getBinding().spinnerType.setAdapter(new ArrayAdapter<>(
                requireContext(), android.R.layout.simple_spinner_dropdown_item, names));
        getBinding().btnSubmit.setOnClickListener(v -> {{
            RequestType type = types[getBinding().spinnerType.getSelectedItemPosition()];
            String amountText = getBinding().inputAmount.getText() == null
                    ? "0" : getBinding().inputAmount.getText().toString();
            double amount;
            try {{
                amount = Double.parseDouble(amountText);
            }} catch (Exception e) {{
                amount = 0;
            }}
            viewModel.updateHint(type, amount);
            viewModel.submit(
                    getBinding().inputTitle.getText() == null ? "" : getBinding().inputTitle.getText().toString(),
                    getBinding().inputDesc.getText() == null ? "" : getBinding().inputDesc.getText().toString(),
                    type, amount);
        }});
        observe(viewModel.getUiState(), state -> {{
            getBinding().setRuleHint(state.ruleHint);
            getBinding().setError(state.error == null ? "" : state.error);
            if (state.createdId != null) {{
                NavHostFragment.findNavController(this).navigateUp();
            }}
        }});
    }}
}}
''')
    w(f"{base}/ApprovalDetailUiState.java", f'''
package {PKG}.feature.request;

import {PKG}.core.model.ApprovalAction;
import {PKG}.core.model.ApprovalRequest;

import java.util.Collections;
import java.util.List;

public class ApprovalDetailUiState {{
    public final ApprovalRequest request;
    public final List<ApprovalAction> actions;
    public final boolean canAct;
    public final boolean canEscalate;
    public final String message;
    public final String detailText;

    public ApprovalDetailUiState(
            ApprovalRequest request, List<ApprovalAction> actions, boolean canAct,
            boolean canEscalate, String message, String detailText
    ) {{
        this.request = request;
        this.actions = actions == null ? Collections.emptyList() : actions;
        this.canAct = canAct;
        this.canEscalate = canEscalate;
        this.message = message == null ? "" : message;
        this.detailText = detailText == null ? "" : detailText;
    }}

    public static ApprovalDetailUiState loading() {{
        return new ApprovalDetailUiState(null, Collections.emptyList(), false, false, "", "Loading…");
    }}
}}
''')
    w(f"{base}/ApprovalDetailViewModel.java", f'''
package {PKG}.feature.request;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MediatorLiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;

import {PKG}.core.model.ApprovalAction;
import {PKG}.core.model.ApprovalRequest;
import {PKG}.core.model.Permission;
import {PKG}.core.model.Role;
import {PKG}.core.model.User;
import {PKG}.data.repository.AppRepository;
import {PKG}.domain.approval.ApprovalWorkflow;
import {PKG}.domain.repository.SessionRepository;

import java.util.List;
import java.util.concurrent.Executor;
import java.util.concurrent.atomic.AtomicReference;

public class ApprovalDetailViewModel extends ViewModel {{
    private final long requestId;
    private final AppRepository repository;
    private final Executor ioExecutor;
    private final MutableLiveData<String> message = new MutableLiveData<>("");
    private final MutableLiveData<ApprovalRequest> requestLive = new MutableLiveData<>();
    private final MediatorLiveData<ApprovalDetailUiState> uiState =
            new MediatorLiveData<>(ApprovalDetailUiState.loading());
    private final AtomicReference<ApprovalRequest> cached = new AtomicReference<>();

    public ApprovalDetailViewModel(long requestId, AppRepository repository, Executor ioExecutor) {{
        this.requestId = requestId;
        this.repository = repository;
        this.ioExecutor = ioExecutor;
        refreshRequest();
        LiveData<List<ApprovalAction>> actions = repository.observeActions(requestId);
        LiveData<User> session = repository.getSession();
        LiveData<Role> imp = repository.getImpersonateRole();
        Runnable recompute = () -> {{
            ApprovalRequest req = cached.get();
            if (req == null) req = requestLive.getValue();
            User user = session.getValue();
            Role role = user == null ? null : user.getRole();
            boolean readOnly = repository.isReadOnly();
            boolean canAct = req != null && role != null
                    && ApprovalWorkflow.canActOn(req.getStatus(), role, readOnly);
            boolean canEscalate = repository.hasPermission(Permission.FORCE_ESCALATE)
                    && req != null && !ApprovalWorkflow.isTerminal(req.getStatus());
            String detail = req == null ? "Loading…" :
                    "#" + req.getId() + " " + req.getTitle() + "\\n"
                            + req.getDescription() + "\\n"
                            + ApprovalWorkflow.levelLabel(req.getStatus()) + " · "
                            + req.getType() + " · " + req.getAmount() + "\\n"
                            + "Dept " + req.getDepartment() + " · Max L" + req.getRequiredMaxLevel()
                            + (req.isEscalated() ? " · ESCALATED" : "");
            uiState.setValue(new ApprovalDetailUiState(
                    req, actions.getValue(), canAct, canEscalate, message.getValue(), detail));
        }};
        uiState.addSource(requestLive, v -> {{
            cached.set(v);
            recompute.run();
        }});
        uiState.addSource(actions, v -> recompute.run());
        uiState.addSource(session, v -> recompute.run());
        uiState.addSource(imp, v -> recompute.run());
        uiState.addSource(message, v -> recompute.run());
    }}

    private void refreshRequest() {{
        repository.getRequest(requestId, ioExecutor, new SessionRepository.Callback<ApprovalRequest>() {{
            @Override
            public void onSuccess(ApprovalRequest value) {{
                requestLive.postValue(value);
            }}

            @Override
            public void onError(Throwable error) {{
                message.postValue(error.getMessage());
            }}
        }});
    }}

    public LiveData<ApprovalDetailUiState> getUiState() {{
        return uiState;
    }}

    public void decide(boolean approve, String comment) {{
        repository.decide(requestId, approve, comment, ioExecutor, new SessionRepository.Callback<Void>() {{
            @Override
            public void onSuccess(Void value) {{
                message.postValue("Berhasil");
                refreshRequest();
            }}

            @Override
            public void onError(Throwable error) {{
                message.postValue(error.getMessage());
            }}
        }});
    }}

    public void escalate() {{
        repository.forceEscalate(requestId, ioExecutor, new SessionRepository.Callback<Void>() {{
            @Override
            public void onSuccess(Void value) {{
                message.postValue("Escalated");
                refreshRequest();
            }}

            @Override
            public void onError(Throwable error) {{
                message.postValue(error.getMessage());
            }}
        }});
    }}
}}
''')
    w(f"{base}/ApprovalDetailFragment.java", f'''
package {PKG}.feature.request;

import android.os.Bundle;
import android.view.View;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.lifecycle.ViewModelProvider;

import {PKG}.core.common.DateFormatters;
import {PKG}.core.model.ApprovalAction;
import {PKG}.core.ui.BaseMvvmFragment;
import {PKG}.data.di.HasAppContainer;
import {PKG}.feature.request.databinding.FragmentApprovalDetailBinding;

public class ApprovalDetailFragment extends BaseMvvmFragment<FragmentApprovalDetailBinding> {{
    private ApprovalDetailViewModel viewModel;

    public ApprovalDetailFragment() {{
        super(R.layout.fragment_approval_detail);
    }}

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        long requestId = getArguments() == null ? 0L : getArguments().getLong("requestId", 0L);
        HasAppContainer services = HasAppContainer.from(requireContext());
        viewModel = new ViewModelProvider(this, services.getViewModelFactory())
                .get(ApprovalDetailViewModel.class);
        // Factory uses CreationExtras requestId via WingsApp factory keys — also re-get with key
        viewModel = new ViewModelProvider(this, services.getViewModelFactory())
                .get("detail-" + requestId, ApprovalDetailViewModel.class);

        getBinding().btnApprove.setOnClickListener(v -> viewModel.decide(true, comment()));
        getBinding().btnReject.setOnClickListener(v -> viewModel.decide(false, comment()));
        getBinding().btnEscalate.setOnClickListener(v -> viewModel.escalate());
        observe(viewModel.getUiState(), state -> {{
            getBinding().setDetail(state.detailText);
            getBinding().setCanAct(state.canAct);
            getBinding().setCanEscalate(state.canEscalate);
            getBinding().setMessage(state.message);
            StringBuilder sb = new StringBuilder();
            for (ApprovalAction a : state.actions) {{
                if (sb.length() > 0) sb.append('\\n');
                sb.append("L").append(a.getLevel()).append(" ").append(a.getDecision())
                        .append(" — ").append(a.getComment())
                        .append(" (").append(DateFormatters.full(a.getCreatedAt())).append(")");
            }}
            getBinding().textActions.setText(sb.toString());
        }});
    }}

    private String comment() {{
        return getBinding().inputComment.getText() == null
                ? "" : getBinding().inputComment.getText().toString();
    }}
}}
''')


# Continue in same file - analytics, audit, settings, widget, app, test
# Due to size, append via second write after reading... Actually keep writing functions below.

def analytics() -> None:
    w("feature/analytics/build.gradle.kts", feature_build(f"{PKG}.feature.analytics"))
    w("feature/analytics/consumer-rules.pro", "#\n")
    w("feature/analytics/src/main/AndroidManifest.xml", empty_manifest())
    w("feature/analytics/src/main/res/layout/fragment_analytics.xml", '''
<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android">
    <data>
        <variable name="content" type="String" />
    </data>
    <ScrollView
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:background="@color/wings_surface">
        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="vertical"
            android:padding="16dp">
            <TextView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:text="Analytics"
                android:textStyle="bold"
                android:textSize="20sp"
                android:textColor="@color/wings_primary" />
            <TextView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:text="@{content}"
                android:layout_marginTop="12dp"
                android:lineSpacingExtra="4dp" />
            <com.google.android.material.button.MaterialButton
                android:id="@+id/btnExportChart"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:text="Export Chart PNG"
                android:layout_marginTop="16dp" />
        </LinearLayout>
    </ScrollView>
</layout>
''')
    base = f"feature/analytics/src/main/java/{P}/feature/analytics"
    w(f"{base}/AnalyticsUiState.java", f'''
package {PKG}.feature.analytics;

import {PKG}.core.model.StatusCount;
import {PKG}.core.model.TypeStat;
import {PKG}.domain.analytics.AnalyticsCalculator;

import java.util.Collections;
import java.util.List;

public class AnalyticsUiState {{
    public final List<StatusCount> statusCounts;
    public final List<TypeStat> typeStats;
    public final AnalyticsCalculator.SlaStats sla;
    public final List<AnalyticsCalculator.BottleneckLevel> bottleneck;
    public final String content;

    public AnalyticsUiState(
            List<StatusCount> statusCounts, List<TypeStat> typeStats,
            AnalyticsCalculator.SlaStats sla,
            List<AnalyticsCalculator.BottleneckLevel> bottleneck,
            String content
    ) {{
        this.statusCounts = statusCounts == null ? Collections.emptyList() : statusCounts;
        this.typeStats = typeStats == null ? Collections.emptyList() : typeStats;
        this.sla = sla;
        this.bottleneck = bottleneck == null ? Collections.emptyList() : bottleneck;
        this.content = content == null ? "Loading…" : content;
    }}
}}
''')
    w(f"{base}/AnalyticsViewModel.java", f'''
package {PKG}.feature.analytics;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MediatorLiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;

import {PKG}.core.model.StatusCount;
import {PKG}.core.model.TypeStat;
import {PKG}.data.repository.AppRepository;
import {PKG}.domain.analytics.AnalyticsCalculator;
import {PKG}.domain.repository.SessionRepository;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.Executor;

public class AnalyticsViewModel extends ViewModel {{
    private final MutableLiveData<AnalyticsCalculator.SlaStats> sla = new MutableLiveData<>();
    private final MutableLiveData<List<AnalyticsCalculator.BottleneckLevel>> bn =
            new MutableLiveData<>(List.of());
    private final MediatorLiveData<AnalyticsUiState> uiState =
            new MediatorLiveData<>(new AnalyticsUiState(null, null, null, null, "Loading…"));

    public AnalyticsViewModel(AppRepository repository, Executor ioExecutor) {{
        repository.computeSla(ioExecutor, new SessionRepository.Callback<>() {{
            @Override public void onSuccess(AnalyticsCalculator.SlaStats value) {{ sla.postValue(value); }}
            @Override public void onError(Throwable error) {{ }}
        }});
        repository.computeBottleneck(ioExecutor, new SessionRepository.Callback<>() {{
            @Override public void onSuccess(List<AnalyticsCalculator.BottleneckLevel> value) {{ bn.postValue(value); }}
            @Override public void onError(Throwable error) {{ }}
        }});
        LiveData<List<StatusCount>> status = repository.observeStatusCounts();
        LiveData<List<TypeStat>> types = repository.observeTypeStats();
        Runnable recompute = () -> {{
            List<StatusCount> sc = status.getValue();
            List<TypeStat> ts = types.getValue();
            AnalyticsCalculator.SlaStats s = sla.getValue();
            List<AnalyticsCalculator.BottleneckLevel> b = bn.getValue();
            StringBuilder text = new StringBuilder();
            text.append("Status counts:\\n");
            if (sc != null) for (StatusCount c : sc) {{
                text.append(" · ").append(c.status).append(": ").append(c.count).append('\\n');
            }}
            text.append("\\nBy type:\\n");
            if (ts != null) for (TypeStat t : ts) {{
                text.append(" · ").append(t.type).append(": ").append(t.count)
                        .append(" (sum ").append(t.totalAmount).append(")\\n");
            }}
            text.append('\\n');
            if (s != null) {{
                text.append("SLA ").append(s.slaHours).append("h: ")
                        .append(s.withinSlaCount).append('/').append(s.completedCount)
                        .append(String.format(Locale.US, " (%.1f%%)\\n", s.withinSlaPercent));
            }}
            text.append("\\nBottleneck (avg wait hours):\\n");
            if (b != null) for (AnalyticsCalculator.BottleneckLevel bl : b) {{
                text.append(String.format(Locale.US, " · L%d: %.1fh (n=%d)\\n",
                        bl.level, bl.avgWaitHours, bl.sampleCount));
            }}
            uiState.setValue(new AnalyticsUiState(sc, ts, s, b, text.toString()));
        }};
        uiState.addSource(status, v -> recompute.run());
        uiState.addSource(types, v -> recompute.run());
        uiState.addSource(sla, v -> recompute.run());
        uiState.addSource(bn, v -> recompute.run());
    }}

    public LiveData<AnalyticsUiState> getUiState() {{
        return uiState;
    }}

    public List<String> chartLabels() {{
        AnalyticsUiState s = uiState.getValue();
        List<String> labels = new ArrayList<>();
        if (s != null) for (StatusCount c : s.statusCounts) labels.add(c.status.name());
        return labels;
    }}

    public List<Float> chartValues() {{
        AnalyticsUiState s = uiState.getValue();
        List<Float> values = new ArrayList<>();
        if (s != null) for (StatusCount c : s.statusCounts) values.add((float) c.count);
        return values;
    }}
}}
''')
    w(f"{base}/AnalyticsFragment.java", f'''
package {PKG}.feature.analytics;

import android.os.Bundle;
import android.view.View;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.lifecycle.ViewModelProvider;

import {PKG}.core.ui.BaseMvvmFragment;
import {PKG}.data.di.HasAppContainer;
import {PKG}.data.export.ExportUtils;
import {PKG}.feature.analytics.databinding.FragmentAnalyticsBinding;

import java.util.List;

public class AnalyticsFragment extends BaseMvvmFragment<FragmentAnalyticsBinding> {{
    private AnalyticsViewModel viewModel;

    public AnalyticsFragment() {{
        super(R.layout.fragment_analytics);
    }}

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        HasAppContainer services = HasAppContainer.from(requireContext());
        viewModel = new ViewModelProvider(this, services.getViewModelFactory()).get(AnalyticsViewModel.class);
        getBinding().btnExportChart.setOnClickListener(v -> {{
            try {{
                List<String> labels = viewModel.chartLabels();
                List<Float> values = viewModel.chartValues();
                if (!values.isEmpty()) {{
                    ExportUtils.shareBitmap(requireContext(),
                            ExportUtils.createSimpleChartBitmap(labels, values, "Status distribution"),
                            "ApprovalHub Chart");
                }}
            }} catch (Exception e) {{
                Toast.makeText(requireContext(), e.getMessage(), Toast.LENGTH_SHORT).show();
            }}
        }});
        observe(viewModel.getUiState(), state -> getBinding().setContent(state.content));
    }}
}}
''')


def audit() -> None:
    w("feature/audit/build.gradle.kts", feature_build(f"{PKG}.feature.audit"))
    w("feature/audit/consumer-rules.pro", "#\n")
    w("feature/audit/src/main/AndroidManifest.xml", empty_manifest())
    w("feature/audit/src/main/res/layout/fragment_audit.xml", '''
<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android">
    <data>
        <variable name="content" type="String" />
    </data>
    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:orientation="vertical"
        android:padding="16dp"
        android:background="@color/wings_surface">
        <TextView
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="Audit Trail"
            android:textStyle="bold"
            android:textSize="20sp"
            android:textColor="@color/wings_primary" />
        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="horizontal"
            android:layout_marginTop="12dp">
            <com.google.android.material.button.MaterialButton
                android:id="@+id/btnCsv"
                android:layout_width="0dp"
                android:layout_weight="1"
                android:layout_height="wrap_content"
                android:text="Export CSV" />
            <com.google.android.material.button.MaterialButton
                android:id="@+id/btnPdf"
                android:layout_width="0dp"
                android:layout_weight="1"
                android:layout_height="wrap_content"
                android:text="Export PDF" />
        </LinearLayout>
        <ScrollView
            android:layout_width="match_parent"
            android:layout_height="match_parent"
            android:layout_marginTop="12dp">
            <TextView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:text="@{content}"
                android:textSize="13sp" />
        </ScrollView>
    </LinearLayout>
</layout>
''')
    base = f"feature/audit/src/main/java/{P}/feature/audit"
    w(f"{base}/AuditUiState.java", f'''
package {PKG}.feature.audit;

import {PKG}.core.model.ApprovalAction;
import {PKG}.core.model.ApprovalRequest;

import java.util.Collections;
import java.util.List;
import java.util.Map;

public class AuditUiState {{
    public final List<ApprovalRequest> requests;
    public final List<ApprovalAction> actions;
    public final Map<Long, String> names;
    public final String content;

    public AuditUiState(
            List<ApprovalRequest> requests, List<ApprovalAction> actions,
            Map<Long, String> names, String content
    ) {{
        this.requests = requests == null ? Collections.emptyList() : requests;
        this.actions = actions == null ? Collections.emptyList() : actions;
        this.names = names == null ? Collections.emptyMap() : names;
        this.content = content == null ? "Loading…" : content;
    }}
}}
''')
    w(f"{base}/AuditViewModel.java", f'''
package {PKG}.feature.audit;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;

import {PKG}.core.model.ApprovalAction;
import {PKG}.core.model.ApprovalRequest;
import {PKG}.data.repository.AppRepository;
import {PKG}.domain.repository.SessionRepository;

import java.util.List;
import java.util.Map;
import java.util.concurrent.Executor;
import java.util.concurrent.atomic.AtomicReference;

public class AuditViewModel extends ViewModel {{
    private final MutableLiveData<AuditUiState> uiState =
            new MutableLiveData<>(new AuditUiState(null, null, null, "Loading…"));
    private final AtomicReference<List<ApprovalRequest>> reqs = new AtomicReference<>();
    private final AtomicReference<List<ApprovalAction>> acts = new AtomicReference<>();
    private final AtomicReference<Map<Long, String>> names = new AtomicReference<>();

    public AuditViewModel(AppRepository repository, Executor ioExecutor) {{
        repository.allRequests(ioExecutor, new SessionRepository.Callback<>() {{
            @Override public void onSuccess(List<ApprovalRequest> value) {{
                reqs.set(value);
                maybePublish();
            }}
            @Override public void onError(Throwable error) {{
                uiState.postValue(new AuditUiState(null, null, null, error.getMessage()));
            }}
        }});
        repository.allActions(ioExecutor, new SessionRepository.Callback<>() {{
            @Override public void onSuccess(List<ApprovalAction> value) {{
                acts.set(value);
                maybePublish();
            }}
            @Override public void onError(Throwable error) {{ }}
        }});
        repository.buildUserNameMap(ioExecutor, new SessionRepository.Callback<>() {{
            @Override public void onSuccess(Map<Long, String> value) {{
                names.set(value);
                maybePublish();
            }}
            @Override public void onError(Throwable error) {{ }}
        }});
    }}

    private void maybePublish() {{
        List<ApprovalRequest> requests = reqs.get();
        List<ApprovalAction> actions = acts.get();
        Map<Long, String> map = names.get();
        if (requests == null || actions == null || map == null) return;
        StringBuilder text = new StringBuilder();
        int limit = Math.min(30, requests.size());
        for (int i = 0; i < limit; i++) {{
            ApprovalRequest r = requests.get(i);
            text.append('#').append(r.getId()).append(' ').append(r.getTitle())
                    .append(" [").append(r.getStatus()).append("]\\n");
            for (ApprovalAction a : actions) {{
                if (a.getRequestId() != r.getId()) continue;
                String actor = map.containsKey(a.getActorId())
                        ? map.get(a.getActorId()) : String.valueOf(a.getActorId());
                text.append("  L").append(a.getLevel()).append(' ').append(a.getDecision())
                        .append(" by ").append(actor).append(" — ").append(a.getComment()).append('\\n');
            }}
        }}
        uiState.postValue(new AuditUiState(requests, actions, map, text.toString()));
    }}

    public LiveData<AuditUiState> getUiState() {{
        return uiState;
    }}
}}
''')
    w(f"{base}/AuditFragment.java", f'''
package {PKG}.feature.audit;

import android.os.Bundle;
import android.view.View;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.lifecycle.ViewModelProvider;

import {PKG}.core.ui.BaseMvvmFragment;
import {PKG}.data.di.HasAppContainer;
import {PKG}.data.export.ExportUtils;
import {PKG}.feature.audit.databinding.FragmentAuditBinding;

public class AuditFragment extends BaseMvvmFragment<FragmentAuditBinding> {{
    private AuditViewModel viewModel;

    public AuditFragment() {{
        super(R.layout.fragment_audit);
    }}

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        HasAppContainer services = HasAppContainer.from(requireContext());
        viewModel = new ViewModelProvider(this, services.getViewModelFactory()).get(AuditViewModel.class);
        getBinding().btnCsv.setOnClickListener(v -> {{
            AuditUiState s = viewModel.getUiState().getValue();
            if (s == null) return;
            try {{
                ExportUtils.shareUri(requireContext(),
                        ExportUtils.exportAuditCsv(requireContext(), s.requests, s.actions, s.names),
                        "text/csv", "Audit CSV");
            }} catch (Exception e) {{
                Toast.makeText(requireContext(), e.getMessage(), Toast.LENGTH_SHORT).show();
            }}
        }});
        getBinding().btnPdf.setOnClickListener(v -> {{
            AuditUiState s = viewModel.getUiState().getValue();
            if (s == null) return;
            try {{
                ExportUtils.shareUri(requireContext(),
                        ExportUtils.exportAuditPdf(requireContext(), s.requests, s.actions, s.names),
                        "application/pdf", "Audit PDF");
            }} catch (Exception e) {{
                Toast.makeText(requireContext(), e.getMessage(), Toast.LENGTH_SHORT).show();
            }}
        }});
        observe(viewModel.getUiState(), state -> getBinding().setContent(state.content));
    }}
}}
''')


def settings() -> None:
    w("feature/settings/build.gradle.kts", feature_build(f"{PKG}.feature.settings"))
    w("feature/settings/consumer-rules.pro", "#\n")
    w("feature/settings/src/main/AndroidManifest.xml", empty_manifest())
    w("feature/settings/src/main/res/layout/fragment_settings.xml", '''
<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android">
    <data>
        <variable name="info" type="String" />
        <variable name="syncInfo" type="String" />
    </data>
    <ScrollView
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:background="@color/wings_surface">
        <LinearLayout
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:orientation="vertical"
            android:padding="16dp">
            <TextView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:text="Settings"
                android:textStyle="bold"
                android:textSize="20sp"
                android:textColor="@color/wings_primary" />
            <TextView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:text="@{info}"
                android:layout_marginTop="12dp" />
            <TextView
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:text="@{syncInfo}"
                android:layout_marginTop="8dp"
                android:textColor="@color/wings_muted" />
            <Spinner
                android:id="@+id/spinnerTheme"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="12dp" />
            <Spinner
                android:id="@+id/spinnerImpersonate"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:layout_marginTop="8dp" />
            <com.google.android.material.button.MaterialButton
                android:id="@+id/btnSync"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:text="Sync Now"
                android:layout_marginTop="12dp" />
            <com.google.android.material.button.MaterialButton
                android:id="@+id/btnEscalate"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:text="Run Escalation Pass"
                android:layout_marginTop="8dp" />
            <com.google.android.material.button.MaterialButton
                android:id="@+id/btnLogout"
                android:layout_width="match_parent"
                android:layout_height="wrap_content"
                android:text="Logout"
                android:layout_marginTop="8dp"
                style="@style/Widget.MaterialComponents.Button.OutlinedButton" />
        </LinearLayout>
    </ScrollView>
</layout>
''')
    base = f"feature/settings/src/main/java/{P}/feature/settings"
    w(f"{base}/SettingsUiState.java", f'''
package {PKG}.feature.settings;

import {PKG}.core.model.Role;
import {PKG}.core.model.User;

public class SettingsUiState {{
    public final User user;
    public final Role impersonate;
    public final String syncInfo;
    public final String message;
    public final boolean loggedOut;

    public SettingsUiState(User user, Role impersonate, String syncInfo, String message, boolean loggedOut) {{
        this.user = user;
        this.impersonate = impersonate;
        this.syncInfo = syncInfo == null ? "" : syncInfo;
        this.message = message == null ? "" : message;
        this.loggedOut = loggedOut;
    }}
}}
''')
    w(f"{base}/SettingsViewModel.java", f'''
package {PKG}.feature.settings;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MediatorLiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;

import {PKG}.core.common.DateFormatters;
import {PKG}.core.model.Role;
import {PKG}.core.model.SyncMeta;
import {PKG}.core.model.ThemeMode;
import {PKG}.core.model.User;
import {PKG}.data.repository.AppRepository;
import {PKG}.domain.repository.SessionRepository;

import java.util.concurrent.Executor;

public class SettingsViewModel extends ViewModel {{
    private final AppRepository repository;
    private final Executor ioExecutor;
    private final MutableLiveData<String> message = new MutableLiveData<>("");
    private final MutableLiveData<Boolean> loggedOut = new MutableLiveData<>(false);
    private final MediatorLiveData<SettingsUiState> uiState =
            new MediatorLiveData<>(new SettingsUiState(null, null, "", "", false));

    public SettingsViewModel(AppRepository repository, Executor ioExecutor) {{
        this.repository = repository;
        this.ioExecutor = ioExecutor;
        LiveData<User> session = repository.getSession();
        LiveData<Role> imp = repository.getImpersonateRole();
        LiveData<SyncMeta> sync = repository.observeSyncMeta();
        Runnable recompute = () -> {{
            SyncMeta meta = sync.getValue();
            String syncInfo = meta == null ? "No sync meta" :
                    "Last sync: " + (meta.getLastSyncedAt() == 0L ? "never"
                            : DateFormatters.full(meta.getLastSyncedAt()))
                            + " · " + meta.getLastSyncStatus()
                            + " · pending " + meta.getPendingPushCount();
            uiState.setValue(new SettingsUiState(
                    session.getValue(), imp.getValue(), syncInfo,
                    message.getValue(), Boolean.TRUE.equals(loggedOut.getValue())));
        }};
        uiState.addSource(session, v -> recompute.run());
        uiState.addSource(imp, v -> recompute.run());
        uiState.addSource(sync, v -> recompute.run());
        uiState.addSource(message, v -> recompute.run());
        uiState.addSource(loggedOut, v -> recompute.run());
    }}

    public LiveData<SettingsUiState> getUiState() {{
        return uiState;
    }}

    public void setTheme(ThemeMode mode) {{
        repository.setThemeMode(mode, ioExecutor);
    }}

    public void setImpersonate(Role role) {{
        repository.setImpersonateRole(role);
    }}

    public void sync() {{
        repository.syncNow(ioExecutor, new SessionRepository.Callback<>() {{
            @Override public void onSuccess(SyncMeta value) {{ message.postValue("Sync OK"); }}
            @Override public void onError(Throwable error) {{
                message.postValue(error.getMessage() == null ? "Sync failed" : error.getMessage());
            }}
        }});
    }}

    public void runEscalation() {{
        repository.runEscalationPass(ioExecutor, new SessionRepository.Callback<>() {{
            @Override public void onSuccess(Integer value) {{
                message.postValue("Escalated " + value + " request(s)");
            }}
            @Override public void onError(Throwable error) {{
                message.postValue(error.getMessage());
            }}
        }});
    }}

    public void logout() {{
        repository.logoutAndClear(ioExecutor, () -> loggedOut.postValue(true));
    }}
}}
''')
    w(f"{base}/SettingsFragment.java", f'''
package {PKG}.feature.settings;

import android.os.Bundle;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatDelegate;
import androidx.lifecycle.ViewModelProvider;
import androidx.navigation.fragment.NavHostFragment;

import {PKG}.core.model.Role;
import {PKG}.core.model.ThemeMode;
import {PKG}.core.ui.BaseMvvmFragment;
import {PKG}.data.di.HasAppContainer;
import {PKG}.feature.settings.databinding.FragmentSettingsBinding;

public class SettingsFragment extends BaseMvvmFragment<FragmentSettingsBinding> {{
    private SettingsViewModel viewModel;
    private boolean themeReady;
    private boolean impReady;

    public SettingsFragment() {{
        super(R.layout.fragment_settings);
    }}

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        HasAppContainer services = HasAppContainer.from(requireContext());
        viewModel = new ViewModelProvider(this, services.getViewModelFactory()).get(SettingsViewModel.class);

        ThemeMode[] themes = ThemeMode.values();
        String[] themeNames = new String[themes.length];
        for (int i = 0; i < themes.length; i++) themeNames[i] = themes[i].name();
        getBinding().spinnerTheme.setAdapter(new ArrayAdapter<>(
                requireContext(), android.R.layout.simple_spinner_dropdown_item, themeNames));

        Role[] roles = Role.values();
        String[] roleNames = new String[roles.length + 1];
        roleNames[0] = "(none)";
        for (int i = 0; i < roles.length; i++) roleNames[i + 1] = roles[i].name();
        getBinding().spinnerImpersonate.setAdapter(new ArrayAdapter<>(
                requireContext(), android.R.layout.simple_spinner_dropdown_item, roleNames));

        getBinding().spinnerTheme.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {{
            @Override
            public void onItemSelected(AdapterView<?> parent, View v, int pos, long id) {{
                if (!themeReady) {{ themeReady = true; return; }}
                ThemeMode mode = themes[pos];
                viewModel.setTheme(mode);
                int night;
                switch (mode) {{
                    case LIGHT: night = AppCompatDelegate.MODE_NIGHT_NO; break;
                    case DARK: night = AppCompatDelegate.MODE_NIGHT_YES; break;
                    default: night = AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM; break;
                }}
                AppCompatDelegate.setDefaultNightMode(night);
            }}
            @Override public void onNothingSelected(AdapterView<?> parent) {{ }}
        }});
        getBinding().spinnerImpersonate.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {{
            @Override
            public void onItemSelected(AdapterView<?> parent, View v, int pos, long id) {{
                if (!impReady) {{ impReady = true; return; }}
                viewModel.setImpersonate(pos == 0 ? null : roles[pos - 1]);
            }}
            @Override public void onNothingSelected(AdapterView<?> parent) {{ }}
        }});
        getBinding().btnSync.setOnClickListener(v -> viewModel.sync());
        getBinding().btnEscalate.setOnClickListener(v -> viewModel.runEscalation());
        getBinding().btnLogout.setOnClickListener(v -> viewModel.logout());

        observe(viewModel.getUiState(), state -> {{
            if (state.user != null) {{
                String info = state.user.getDisplayName() + " (" + state.user.getUsername() + ") · "
                        + state.user.getRole()
                        + (state.impersonate == null ? "" : " · impersonate " + state.impersonate)
                        + "\\n" + state.message;
                getBinding().setInfo(info);
            }} else {{
                getBinding().setInfo(state.message);
            }}
            getBinding().setSyncInfo(state.syncInfo);
            if (state.loggedOut) {{
                NavHostFragment.findNavController(this)
                        .navigate({PKG}.core.ui.R.id.action_global_to_login);
            }}
        }});
    }}
}}
''')


def widget() -> None:
    w("feature/widget/build.gradle.kts", '''
plugins {
    alias(libs.plugins.android.library)
}

android {
    namespace = "com.fauzi.wings.feature.widget"
    compileSdk = libs.versions.compileSdk.get().toInt()
    defaultConfig {
        minSdk = libs.versions.minSdk.get().toInt()
        consumerProguardFiles("consumer-rules.pro")
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    implementation(project(":core:database"))
    implementation(libs.androidx.core)
}
''')
    w("feature/widget/consumer-rules.pro", "#\n")
    w("feature/widget/src/main/AndroidManifest.xml", f'''
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application>
        <receiver
            android:name="{PKG}.feature.widget.PendingWidgetReceiver"
            android:exported="true">
            <intent-filter>
                <action android:name="android.appwidget.action.APPWIDGET_UPDATE" />
            </intent-filter>
            <meta-data
                android:name="android.appwidget.provider"
                android:resource="@xml/pending_widget_info" />
        </receiver>
    </application>
</manifest>
''')
    w("feature/widget/src/main/res/layout/widget_pending_placeholder.xml", '''
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:padding="12dp"
    android:background="@color/wings_primary"
    android:gravity="center">
    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Pending"
        android:textColor="#FFFFFF"
        android:textSize="12sp" />
    <TextView
        android:id="@+id/widget_pending_count"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="0"
        android:textColor="#FFFFFF"
        android:textSize="28sp"
        android:textStyle="bold" />
</LinearLayout>
''')
    w("feature/widget/src/main/res/xml/pending_widget_info.xml", '''
<?xml version="1.0" encoding="utf-8"?>
<appwidget-provider xmlns:android="http://schemas.android.com/apk/res/android"
    android:minWidth="110dp"
    android:minHeight="40dp"
    android:updatePeriodMillis="1800000"
    android:initialLayout="@layout/widget_pending_placeholder"
    android:resizeMode="horizontal|vertical"
    android:widgetCategory="home_screen" />
''')
    w("feature/widget/src/main/res/values/colors.xml", '''
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="wings_primary">#0F4C5C</color>
</resources>
''')
    w(f"feature/widget/src/main/java/{P}/feature/widget/PendingWidgetReceiver.java", f'''
package {PKG}.feature.widget;

import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.widget.RemoteViews;

import {PKG}.core.database.AppDatabase;

import java.util.concurrent.Executors;

public class PendingWidgetReceiver extends AppWidgetProvider {{
    @Override
    public void onUpdate(Context context, AppWidgetManager appWidgetManager, int[] appWidgetIds) {{
        Executors.newSingleThreadExecutor().execute(() -> {{
            int count = 0;
            try {{
                Integer live = AppDatabase.get(context).approvalRequestDao()
                        .observePendingCount().getValue();
                if (live != null) {{
                    count = live;
                }} else {{
                    count = AppDatabase.get(context).approvalRequestDao().getAll().stream()
                            .mapToInt(r -> r.status.name().startsWith("PENDING") ? 1 : 0)
                            .sum();
                }}
            }} catch (Exception ignored) {{
            }}
            int finalCount = count;
            new Handler(Looper.getMainLooper()).post(() -> {{
                for (int id : appWidgetIds) {{
                    RemoteViews views = new RemoteViews(context.getPackageName(),
                            R.layout.widget_pending_placeholder);
                    views.setTextViewText(R.id.widget_pending_count, String.valueOf(finalCount));
                    appWidgetManager.updateAppWidget(id, views);
                }}
            }});
        }});
    }}
}}
''')


def app() -> None:
    w("app/build.gradle.kts", f'''
plugins {{
    alias(libs.plugins.android.application)
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
    implementation(project(":core:preference"))
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

    implementation(libs.androidx.core)
    implementation(libs.androidx.appcompat)
    implementation(libs.material)
    implementation(libs.androidx.constraintlayout)
    implementation(libs.androidx.activity)
    implementation(libs.androidx.fragment)
    implementation(libs.androidx.navigation.fragment)
    implementation(libs.androidx.navigation.ui)
    implementation(libs.androidx.lifecycle.runtime)
    implementation(libs.androidx.lifecycle.viewmodel)
    implementation(libs.androidx.lifecycle.livedata)
    implementation(libs.androidx.work)
}}
''')
    w("app/proguard-rules.pro", "# app proguard\n")
    w("app/src/main/AndroidManifest.xml", f'''
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />

    <application
        android:name=".WingsApp"
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.WingsApprovalHub">

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
''')
    # Also copy nav into app as required by user
    w("app/src/main/res/navigation/nav_graph.xml", open(ROOT / "core/ui/src/main/res/navigation/nav_graph.xml").read() if (ROOT / "core/ui/src/main/res/navigation/nav_graph.xml").exists() else "<!-- placeholder -->")
    # Will rewrite after nav_menu writes - call nav rewrite
    w("app/src/main/res/xml/file_paths.xml", '''
<?xml version="1.0" encoding="utf-8"?>
<paths>
    <cache-path name="cache" path="." />
</paths>
''')
    w("app/src/main/res/values/strings.xml", '''
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">ApprovalHub</string>
</resources>
''')
    w("app/src/main/res/values/colors.xml", '''
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="wings_primary">#0F4C5C</color>
    <color name="wings_surface">#F7F4EF</color>
</resources>
''')
    w("app/src/main/res/layout/activity_main.xml", '''
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
        android:background="@color/wings_surface"
        app:menu="@menu/menu_bottom"
        app:layout_constraintBottom_toBottomOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent" />
</androidx.constraintlayout.widget.ConstraintLayout>
''')
    # menu in app too for activity reference - or use core:ui transitive. Non-transitive R means app needs own menu or depend and use core.ui R.
    # activity uses @menu/menu_bottom — copy to app
    w("app/src/main/res/menu/menu_bottom.xml", '''
<?xml version="1.0" encoding="utf-8"?>
<menu xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:id="@+id/dashboardFragment" android:title="Home" android:icon="@android:drawable/ic_menu_compass" />
    <item android:id="@+id/inboxFragment" android:title="Inbox" android:icon="@android:drawable/ic_menu_agenda" />
    <item android:id="@+id/analyticsFragment" android:title="Charts" android:icon="@android:drawable/ic_menu_sort_by_size" />
    <item android:id="@+id/auditFragment" android:title="Audit" android:icon="@android:drawable/ic_menu_recent_history" />
    <item android:id="@+id/settingsFragment" android:title="Settings" android:icon="@android:drawable/ic_menu_preferences" />
</menu>
''')
    w("app/src/main/res/drawable/ic_launcher_foreground.xml", '''
<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:fillColor="#2A9D8F"
        android:pathData="M54,30c-10,0 -18,8 -18,18v8h-6v24h48V56h-6v-8c0,-10 -8,-18 -18,-18zM46,56v-8c0,-4.4 3.6,-8 8,-8s8,3.6 8,8v8H46z" />
</vector>
''')
    w("app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml", '''
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/wings_primary" />
    <foreground android:drawable="@drawable/ic_launcher_foreground" />
</adaptive-icon>
''')
    w("app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml", '''
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/wings_primary" />
    <foreground android:drawable="@drawable/ic_launcher_foreground" />
</adaptive-icon>
''')

    base = f"app/src/main/java/{P}/app"
    w(f"{base}/AppContainer.java", f'''
package {PKG}.app;

import android.content.Context;

import androidx.lifecycle.ViewModelProvider;

import {PKG}.core.database.AppDatabase;
import {PKG}.core.network.FakeRemoteApi;
import {PKG}.core.preference.UserPreferences;
import {PKG}.data.repository.AppRepository;
import {PKG}.data.sync.SyncRepository;

import java.util.concurrent.Executor;
import java.util.concurrent.Executors;

public class AppContainer {{
    public final AppDatabase database;
    public final UserPreferences preferences;
    public final SyncRepository syncRepository;
    public final AppRepository repository;
    public final Executor ioExecutor;
    public final ViewModelProvider.Factory viewModelFactory;

    public AppContainer(Context context) {{
        Context app = context.getApplicationContext();
        database = AppDatabase.get(app);
        preferences = new UserPreferences(app);
        syncRepository = new SyncRepository(database, new FakeRemoteApi());
        repository = new AppRepository(database, preferences, syncRepository, app);
        ioExecutor = Executors.newFixedThreadPool(4);
        viewModelFactory = new ViewModelFactory(this);
    }}
}}
''')
    w(f"{base}/ViewModelFactory.java", f'''
package {PKG}.app;

import androidx.annotation.NonNull;
import androidx.lifecycle.ViewModel;
import androidx.lifecycle.ViewModelProvider;
import androidx.lifecycle.viewmodel.CreationExtras;

import {PKG}.feature.analytics.AnalyticsViewModel;
import {PKG}.feature.audit.AuditViewModel;
import {PKG}.feature.auth.LoginViewModel;
import {PKG}.feature.dashboard.DashboardViewModel;
import {PKG}.feature.inbox.InboxViewModel;
import {PKG}.feature.request.ApprovalDetailViewModel;
import {PKG}.feature.request.CreateRequestViewModel;
import {PKG}.feature.settings.SettingsViewModel;

public class ViewModelFactory implements ViewModelProvider.Factory {{
    public static final CreationExtras.Key<Long> REQUEST_ID_KEY = new CreationExtras.Key<>() {{ }};

    private final AppContainer container;

    public ViewModelFactory(AppContainer container) {{
        this.container = container;
    }}

    @NonNull
    @Override
    @SuppressWarnings("unchecked")
    public <T extends ViewModel> T create(@NonNull Class<T> modelClass, @NonNull CreationExtras extras) {{
        if (modelClass.isAssignableFrom(LoginViewModel.class)) {{
            return (T) new LoginViewModel(container.repository, container.ioExecutor);
        }}
        if (modelClass.isAssignableFrom(DashboardViewModel.class)) {{
            return (T) new DashboardViewModel(container.repository);
        }}
        if (modelClass.isAssignableFrom(InboxViewModel.class)) {{
            return (T) new InboxViewModel(container.repository);
        }}
        if (modelClass.isAssignableFrom(CreateRequestViewModel.class)) {{
            return (T) new CreateRequestViewModel(container.repository, container.ioExecutor);
        }}
        if (modelClass.isAssignableFrom(ApprovalDetailViewModel.class)) {{
            Long id = extras.get(REQUEST_ID_KEY);
            long requestId = id == null ? 0L : id;
            return (T) new ApprovalDetailViewModel(requestId, container.repository, container.ioExecutor);
        }}
        if (modelClass.isAssignableFrom(AnalyticsViewModel.class)) {{
            return (T) new AnalyticsViewModel(container.repository, container.ioExecutor);
        }}
        if (modelClass.isAssignableFrom(AuditViewModel.class)) {{
            return (T) new AuditViewModel(container.repository, container.ioExecutor);
        }}
        if (modelClass.isAssignableFrom(SettingsViewModel.class)) {{
            return (T) new SettingsViewModel(container.repository, container.ioExecutor);
        }}
        throw new IllegalArgumentException("Unknown ViewModel: " + modelClass.getName());
    }}

    @NonNull
    @Override
    @SuppressWarnings("unchecked")
    public <T extends ViewModel> T create(@NonNull Class<T> modelClass) {{
        return create(modelClass, CreationExtras.Empty.INSTANCE);
    }}
}}
''')
    w(f"{base}/WingsApp.java", f'''
package {PKG}.app;

import android.app.Application;

import androidx.lifecycle.ViewModelProvider;

import {PKG}.app.work.EscalationWorker;
import {PKG}.core.notification.ApprovalNotifier;
import {PKG}.data.di.HasAppContainer;
import {PKG}.data.repository.AppRepository;

import java.util.concurrent.Executor;

public class WingsApp extends Application implements HasAppContainer {{
    private AppContainer appContainer;

    @Override
    public void onCreate() {{
        super.onCreate();
        appContainer = new AppContainer(this);
        ApprovalNotifier.ensureChannel(this);
        EscalationWorker.schedule(this);
    }}

    public AppContainer getAppContainer() {{
        return appContainer;
    }}

    @Override
    public AppRepository getRepository() {{
        return appContainer.repository;
    }}

    @Override
    public Executor getIoExecutor() {{
        return appContainer.ioExecutor;
    }}

    @Override
    public ViewModelProvider.Factory getViewModelFactory() {{
        return appContainer.viewModelFactory;
    }}
}}
''')
    w(f"{base}/MainActivity.java", f'''
package {PKG}.app;

import android.os.Bundle;
import android.view.View;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.app.AppCompatDelegate;
import androidx.navigation.NavController;
import androidx.navigation.fragment.NavHostFragment;
import androidx.navigation.ui.NavigationUI;

import com.google.android.material.bottomnavigation.BottomNavigationView;

import {PKG}.core.model.ThemeMode;
import {PKG}.core.model.User;
import {PKG}.data.repository.AppRepository;
import {PKG}.domain.repository.SessionRepository;

public class MainActivity extends AppCompatActivity {{
    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        AppContainer container = ((WingsApp) getApplication()).getAppContainer();
        applyTheme(container.preferences.readTheme());

        NavHostFragment navHost = (NavHostFragment) getSupportFragmentManager()
                .findFragmentById(R.id.nav_host);
        if (navHost == null) return;
        NavController navController = navHost.getNavController();
        BottomNavigationView bottomNav = findViewById(R.id.bottomNav);
        NavigationUI.setupWithNavController(bottomNav, navController);
        navController.addOnDestinationChangedListener((controller, destination, args) -> {{
            int id = destination.getId();
            boolean hide = id == {PKG}.core.ui.R.id.loginFragment
                    || id == {PKG}.core.ui.R.id.createRequestFragment
                    || id == {PKG}.core.ui.R.id.approvalDetailFragment
                    || id == R.id.loginFragment
                    || id == R.id.createRequestFragment
                    || id == R.id.approvalDetailFragment;
            bottomNav.setVisibility(hide ? View.GONE : View.VISIBLE);
        }});

        container.repository.getSession().observe(this, this::onSession);
        container.preferences.getThemeMode().observe(this, this::applyTheme);
    }}

    @Override
    protected void onResume() {{
        super.onResume();
        AppContainer container = ((WingsApp) getApplication()).getAppContainer();
        container.repository.checkSessionTimeout(container.ioExecutor,
                new SessionRepository.Callback<Boolean>() {{
                    @Override
                    public void onSuccess(Boolean timedOut) {{
                        if (Boolean.TRUE.equals(timedOut)) {{
                            runOnUiThread(() -> {{
                                NavHostFragment navHost = (NavHostFragment) getSupportFragmentManager()
                                        .findFragmentById(R.id.nav_host);
                                if (navHost != null) {{
                                    navHost.getNavController()
                                            .navigate({PKG}.core.ui.R.id.action_global_to_login);
                                }}
                            }});
                        }}
                    }}

                    @Override
                    public void onError(Throwable error) {{ }}
                }});
        container.repository.touchActivity(container.ioExecutor);
    }}

    private void onSession(User user) {{
        // no-op hook for future session UI
    }}

    private void applyTheme(ThemeMode mode) {{
        if (mode == null) mode = ThemeMode.SYSTEM;
        int night;
        switch (mode) {{
            case LIGHT: night = AppCompatDelegate.MODE_NIGHT_NO; break;
            case DARK: night = AppCompatDelegate.MODE_NIGHT_YES; break;
            default: night = AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM; break;
        }}
        AppCompatDelegate.setDefaultNightMode(night);
    }}
}}
''')
    w(f"{base}/work/EscalationWorker.java", f'''
package {PKG}.app.work;

import android.content.Context;

import androidx.annotation.NonNull;
import androidx.work.ExistingPeriodicWorkPolicy;
import androidx.work.PeriodicWorkRequest;
import androidx.work.Worker;
import androidx.work.WorkerParameters;
import androidx.work.WorkManager;

import {PKG}.core.database.ApprovalActionEntity;
import {PKG}.core.database.ApprovalRequestEntity;
import {PKG}.core.database.AppDatabase;
import {PKG}.core.model.ApprovalStatus;
import {PKG}.core.notification.ApprovalNotifier;
import {PKG}.domain.approval.ApprovalWorkflow;

import java.util.List;
import java.util.concurrent.TimeUnit;

public class EscalationWorker extends Worker {{
    private static final String UNIQUE = "escalation_periodic";

    public EscalationWorker(@NonNull Context context, @NonNull WorkerParameters params) {{
        super(context, params);
    }}

    @NonNull
    @Override
    public Result doWork() {{
        AppDatabase db = AppDatabase.get(getApplicationContext());
        long now = System.currentTimeMillis();
        long threshold = now - ApprovalWorkflow.IDLE_BEFORE_ESCALATE_MS;
        List<ApprovalRequestEntity> overdue = db.approvalRequestDao().getOverdue(threshold);
        int escalatedCount = 0;
        for (ApprovalRequestEntity request : overdue) {{
            ApprovalStatus next = ApprovalWorkflow.escalateStatus(request.status, request.requiredMaxLevel);
            if (next == null) continue;
            Integer level = ApprovalWorkflow.requiredLevel(next);
            if (level == null) continue;
            request.status = next;
            request.currentLevel = level;
            request.escalated = true;
            request.updatedAt = now;
            db.approvalRequestDao().update(request);
            db.approvalActionDao().insert(new ApprovalActionEntity(
                    0, request.id, 1, request.currentLevel, "ESCALATE",
                    "Auto-escalate karena idle > 2 hari", now));
            escalatedCount++;
        }}
        int pending = 0;
        for (ApprovalRequestEntity r : db.approvalRequestDao().getAll()) {{
            if (r.status.name().startsWith("PENDING")) pending++;
        }}
        if (pending > 0 || escalatedCount > 0) {{
            String title = escalatedCount > 0 ? "Escalation & Inbox" : "Approval Inbox";
            StringBuilder body = new StringBuilder();
            if (escalatedCount > 0) body.append(escalatedCount).append(" request di-escalate. ");
            body.append(pending).append(" request masih pending.");
            ApprovalNotifier.notifyInbox(getApplicationContext(), title, body.toString(), 2001);
        }}
        return Result.success();
    }}

    public static void schedule(Context context) {{
        PeriodicWorkRequest request = new PeriodicWorkRequest.Builder(
                EscalationWorker.class, 6, TimeUnit.HOURS).build();
        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                UNIQUE, ExistingPeriodicWorkPolicy.UPDATE, request);
    }}
}}
''')

    # Write app nav graph (same as core ui)
    w("app/src/main/res/navigation/nav_graph.xml", f'''
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
''')


def domain_test() -> None:
    w(f"domain/src/test/java/{P}/domain/DomainLogicTest.java", f'''
package {PKG}.domain;

import static com.google.common.truth.Truth.assertThat;

import {PKG}.core.model.ApprovalStatus;
import {PKG}.core.model.RequestType;
import {PKG}.core.model.Role;
import {PKG}.domain.approval.AmountBasedRules;
import {PKG}.domain.approval.ApprovalWorkflow;
import {PKG}.domain.rbac.RbacPolicy;

import org.junit.Test;

public class DomainLogicTest {{
    @Test
    public void purchaseAmountRules() {{
        assertThat(AmountBasedRules.requiredMaxLevel(RequestType.PURCHASE, 1_000_000)).isEqualTo(1);
        assertThat(AmountBasedRules.requiredMaxLevel(RequestType.PURCHASE, 3_000_000)).isEqualTo(2);
        assertThat(AmountBasedRules.requiredMaxLevel(RequestType.PURCHASE, 12_000_000)).isEqualTo(3);
    }}

    @Test
    public void workflowApproveAndEscalate() {{
        assertThat(ApprovalWorkflow.nextStatusOnApprove(ApprovalStatus.PENDING_L1, 2))
                .isEqualTo(ApprovalStatus.PENDING_L2);
        assertThat(ApprovalWorkflow.nextStatusOnApprove(ApprovalStatus.PENDING_L2, 2))
                .isEqualTo(ApprovalStatus.APPROVED);
        assertThat(ApprovalWorkflow.escalateStatus(ApprovalStatus.PENDING_L1, 3))
                .isEqualTo(ApprovalStatus.PENDING_L2);
        assertThat(ApprovalWorkflow.canActOn(ApprovalStatus.PENDING_L1, Role.SUPERVISOR, false)).isTrue();
        assertThat(ApprovalWorkflow.canActOn(ApprovalStatus.PENDING_L1, Role.STAFF, false)).isFalse();
    }}

    @Test
    public void rbacPermissions() {{
        assertThat(RbacPolicy.hasPermission(Role.ADMIN, {PKG}.core.model.Permission.FORCE_ESCALATE)).isTrue();
        assertThat(RbacPolicy.hasPermission(Role.STAFF, {PKG}.core.model.Permission.CREATE_REQUEST)).isTrue();
        assertThat(RbacPolicy.canApproveLevel(Role.MANAGER, 2)).isTrue();
    }}
}}
''')


if __name__ == "__main__":
    main()
