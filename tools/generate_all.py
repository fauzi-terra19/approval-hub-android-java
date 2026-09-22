#!/usr/bin/env python3
"""Generate complete Java multi-module Wings ApprovalHub project."""
from __future__ import annotations
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = "com.fauzi.wings"
P = PKG.replace(".", "/")


def w(rel: str, content: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    text = content.strip("\n") + "\n"
    if text.startswith("<?xml") or text.lstrip().startswith("<"):
        # strip leading blank from triple-quoted XML
        pass
    path.write_text(text, encoding="utf-8")
    print("wrote", rel)


def empty_manifest(module_ns: str) -> str:
    return f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android" />
'''


def empty_consumer(mod: str) -> None:
    w(f"{mod}/consumer-rules.pro", "# consumer rules\n")
    w(f"{mod}/proguard-rules.pro", "# proguard\n")


def lib_build(namespace: str, deps: list[str], databinding: bool = False, room: bool = False) -> str:
    features = ""
    if databinding:
        features = """
    buildFeatures {
        dataBinding = true
    }
"""
    room_dep = ""
    if room:
        room_dep = """
    implementation(libs.androidx.room.runtime)
    annotationProcessor(libs.androidx.room.compiler)
"""
    dep_block = "\n".join(f"    {d}" for d in deps)
    return f'''plugins {{
    alias(libs.plugins.android.library)
}}

android {{
    namespace = "{namespace}"
    compileSdk = libs.versions.compileSdk.get().toInt()

    defaultConfig {{
        minSdk = libs.versions.minSdk.get().toInt()
        consumerProguardFiles("consumer-rules.pro")
    }}

    compileOptions {{
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }}
{features}}}

dependencies {{
{dep_block}{room_dep}
}}
'''


def main() -> None:
    from generate_domain_data import gen_domain, gen_core_database, gen_data
    from generate_features_app import gen_features, gen_app

    gen_core_model()
    gen_core_common()
    gen_core_preference()
    gen_core_network()
    gen_core_notification()
    gen_domain()
    gen_core_database()
    gen_data()
    gen_core_ui()  # after domain (depends on it)
    gen_features()
    gen_app()
    for kt in ROOT.rglob("*.kt"):
        if "tools" in str(kt):
            continue
        print("deleting leftover", kt)
        kt.unlink()
    print("DONE")


if __name__ == "__main__" and False:
    main()


def gen_core_model() -> None:
    empty_consumer("core/model")
    w("core/model/build.gradle.kts", lib_build(f"{PKG}.core.model", [
        "implementation(libs.androidx.annotation)",
    ]))
    w("core/model/src/main/AndroidManifest.xml", empty_manifest(f"{PKG}.core.model"))
    base = f"core/model/src/main/java/{P}/core/model"

    w(f"{base}/Role.java", f'''
package {PKG}.core.model;

public enum Role {{
    ADMIN, DIRECTOR, MANAGER, SUPERVISOR, STAFF
}}
''')
    w(f"{base}/Permission.java", f'''
package {PKG}.core.model;

public enum Permission {{
    VIEW_ADMIN_DASHBOARD,
    VIEW_EXECUTIVE_DASHBOARD,
    VIEW_MANAGER_DASHBOARD,
    VIEW_SUPERVISOR_DASHBOARD,
    VIEW_STAFF_DASHBOARD,
    MANAGE_USERS,
    CREATE_REQUEST,
    VIEW_REQUESTS,
    VIEW_DEPARTMENT_REQUESTS,
    VIEW_ALL_REQUESTS,
    APPROVE_LEVEL_1,
    APPROVE_LEVEL_2,
    APPROVE_LEVEL_3,
    VIEW_ANALYTICS,
    VIEW_TEAM_ANALYTICS,
    EXPORT_AUDIT,
    EXPORT_CHART,
    IMPERSONATE,
    SYNC_DATA,
    FORCE_ESCALATE
}}
''')
    w(f"{base}/ApprovalStatus.java", f'''
package {PKG}.core.model;

public enum ApprovalStatus {{
    DRAFT, PENDING_L1, PENDING_L2, PENDING_L3, APPROVED, REJECTED, CANCELLED
}}
''')
    w(f"{base}/RequestType.java", f'''
package {PKG}.core.model;

public enum RequestType {{
    PURCHASE, LEAVE, EXPENSE, ACCESS
}}
''')
    w(f"{base}/ThemeMode.java", f'''
package {PKG}.core.model;

public enum ThemeMode {{
    SYSTEM, LIGHT, DARK
}}
''')
    w(f"{base}/User.java", f'''
package {PKG}.core.model;

public class User {{
    public final long id;
    public final String username;
    public final String displayName;
    public final Role role;
    public final String department;

    public User(long id, String username, String displayName, Role role, String department) {{
        this.id = id;
        this.username = username;
        this.displayName = displayName;
        this.role = role;
        this.department = department;
    }}
}}
''')
    w(f"{base}/ApprovalRequest.java", f'''
package {PKG}.core.model;

public class ApprovalRequest {{
    public final long id;
    public final String title;
    public final String description;
    public final RequestType type;
    public final double amount;
    public final long requesterId;
    public final String department;
    public final ApprovalStatus status;
    public final int currentLevel;
    public final int requiredMaxLevel;
    public final boolean escalated;
    public final long createdAt;
    public final long updatedAt;

    public ApprovalRequest(long id, String title, String description, RequestType type, double amount,
                           long requesterId, String department, ApprovalStatus status, int currentLevel,
                           int requiredMaxLevel, boolean escalated, long createdAt, long updatedAt) {{
        this.id = id;
        this.title = title;
        this.description = description;
        this.type = type;
        this.amount = amount;
        this.requesterId = requesterId;
        this.department = department;
        this.status = status;
        this.currentLevel = currentLevel;
        this.requiredMaxLevel = requiredMaxLevel;
        this.escalated = escalated;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }}
}}
''')
    w(f"{base}/ApprovalAction.java", f'''
package {PKG}.core.model;

public class ApprovalAction {{
    public final long id;
    public final long requestId;
    public final long actorId;
    public final int level;
    public final String decision;
    public final String comment;
    public final long createdAt;

    public ApprovalAction(long id, long requestId, long actorId, int level,
                          String decision, String comment, long createdAt) {{
        this.id = id;
        this.requestId = requestId;
        this.actorId = actorId;
        this.level = level;
        this.decision = decision;
        this.comment = comment;
        this.createdAt = createdAt;
    }}
}}
''')
    w(f"{base}/DashboardStats.java", f'''
package {PKG}.core.model;

public class DashboardStats {{
    public final int totalVisible;
    public final int pendingInbox;
    public final int approved;
    public final int rejected;
    public final int inPipeline;

    public DashboardStats() {{
        this(0, 0, 0, 0, 0);
    }}

    public DashboardStats(int totalVisible, int pendingInbox, int approved, int rejected, int inPipeline) {{
        this.totalVisible = totalVisible;
        this.pendingInbox = pendingInbox;
        this.approved = approved;
        this.rejected = rejected;
        this.inPipeline = inPipeline;
    }}
}}
''')
    w(f"{base}/StatusCount.java", f'''
package {PKG}.core.model;

public class StatusCount {{
    public final ApprovalStatus status;
    public final int count;

    public StatusCount(ApprovalStatus status, int count) {{
        this.status = status;
        this.count = count;
    }}
}}
''')
    w(f"{base}/TypeStat.java", f'''
package {PKG}.core.model;

public class TypeStat {{
    public final RequestType type;
    public final int count;
    public final double totalAmount;

    public TypeStat(RequestType type, int count, double totalAmount) {{
        this.type = type;
        this.count = count;
        this.totalAmount = totalAmount;
    }}
}}
''')
    w(f"{base}/SyncMeta.java", f'''
package {PKG}.core.model;

public class SyncMeta {{
    public final long lastSyncedAt;
    public final String lastSyncStatus;
    public final int pendingPushCount;

    public SyncMeta(long lastSyncedAt, String lastSyncStatus, int pendingPushCount) {{
        this.lastSyncedAt = lastSyncedAt;
        this.lastSyncStatus = lastSyncStatus;
        this.pendingPushCount = pendingPushCount;
    }}
}}
''')
    w(f"{base}/RequestFilter.java", f'''
package {PKG}.core.model;

public class RequestFilter {{
    public String query = "";
    public ApprovalStatus status;
    public RequestType type;
    public Double minAmount;
    public Double maxAmount;
    public String department;

    public boolean matches(ApprovalRequest request, String requesterName) {{
        String q = query == null ? "" : query.trim();
        if (!q.isEmpty()) {{
            String hay = (request.title + " " + request.description + " " + request.department + " " + requesterName).toLowerCase();
            if (!hay.contains(q.toLowerCase())) return false;
        }}
        if (status != null && request.status != status) return false;
        if (type != null && request.type != type) return false;
        if (minAmount != null && request.amount < minAmount) return false;
        if (maxAmount != null && request.amount > maxAmount) return false;
        if (department != null && !department.isBlank() && !request.department.equalsIgnoreCase(department)) return false;
        return true;
    }}
}}
''')
    w(f"{base}/DemoAccounts.java", f'''
package {PKG}.core.model;

import java.util.Arrays;
import java.util.List;

public final class DemoAccounts {{
    public static final class Demo {{
        public final String username;
        public final String password;
        public final String roleLabel;

        public Demo(String username, String password, String roleLabel) {{
            this.username = username;
            this.password = password;
            this.roleLabel = roleLabel;
        }}
    }}

    public static final List<Demo> ALL = Arrays.asList(
            new Demo("staff", "staff123", "STAFF"),
            new Demo("staff2", "staff123", "STAFF"),
            new Demo("supervisor", "spv123", "SUPERVISOR"),
            new Demo("manager", "mgr123", "MANAGER"),
            new Demo("director", "dir123", "DIRECTOR"),
            new Demo("admin", "admin123", "ADMIN")
    );

    private DemoAccounts() {{}}
}}
''')


def gen_core_common() -> None:
    empty_consumer("core/common")
    w("core/common/build.gradle.kts", lib_build(f"{PKG}.core.common", [
        "implementation(libs.androidx.annotation)",
    ]))
    w("core/common/src/main/AndroidManifest.xml", empty_manifest(f"{PKG}.core.common"))
    base = f"core/common/src/main/java/{P}/core/common"
    w(f"{base}/DateFormatters.java", f'''
package {PKG}.core.common;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public final class DateFormatters {{
    private static final SimpleDateFormat FULL =
            new SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.getDefault());

    private DateFormatters() {{}}

    public static String full(long epochMs) {{
        return FULL.format(new Date(epochMs));
    }}
}}
''')
    w(f"{base}/MoneyFormatters.java", f'''
package {PKG}.core.common;

import java.text.NumberFormat;
import java.util.Locale;

public final class MoneyFormatters {{
    private MoneyFormatters() {{}}

    public static String idr(double amount) {{
        NumberFormat nf = NumberFormat.getCurrencyInstance(new Locale("id", "ID"));
        return nf.format(amount);
    }}
}}
''')


def gen_core_ui() -> None:
    empty_consumer("core/ui")
    w("core/ui/build.gradle.kts", lib_build(f"{PKG}.core.ui", [
        'api(project(":core:model"))',
        'api(project(":core:common"))',
        'api(project(":domain"))',
        "api(libs.androidx.appcompat)",
        "api(libs.material)",
        "api(libs.androidx.constraintlayout)",
        "api(libs.androidx.recyclerview)",
        "api(libs.androidx.fragment)",
        "api(libs.androidx.lifecycle.livedata)",
        "api(libs.androidx.lifecycle.viewmodel)",
        "api(libs.androidx.navigation.fragment)",
        "api(libs.androidx.navigation.ui)",
    ], databinding=True))
    w("core/ui/src/main/AndroidManifest.xml", empty_manifest(f"{PKG}.core.ui"))
    w("core/ui/src/main/res/values/colors.xml", '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ah_primary">#0F4C5C</color>
    <color name="ah_accent">#2A9D8F</color>
    <color name="ah_bg">#F5F7F8</color>
    <color name="ah_surface">#FFFFFF</color>
    <color name="ah_muted">#6B7280</color>
    <color name="ah_danger">#C62828</color>
    <color name="ah_on_primary">#FFFFFF</color>
</resources>
''')
    w("core/ui/src/main/res/values/themes.xml", '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.ApprovalHub" parent="Theme.MaterialComponents.DayNight.NoActionBar">
        <item name="colorPrimary">@color/ah_primary</item>
        <item name="colorPrimaryVariant">@color/ah_primary</item>
        <item name="colorSecondary">@color/ah_accent</item>
        <item name="android:statusBarColor">@color/ah_primary</item>
        <item name="android:windowBackground">@color/ah_bg</item>
    </style>
</resources>
''')
    w("core/ui/src/main/res/layout/item_request.xml", '''<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android">
    <data>
        <variable name="title" type="String" />
        <variable name="subtitle" type="String" />
        <variable name="meta" type="String" />
    </data>
    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="vertical"
        android:padding="12dp"
        android:layout_marginHorizontal="12dp"
        android:layout_marginVertical="6dp"
        android:background="@color/ah_surface">
        <TextView
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="@{title}"
            android:textStyle="bold"
            android:textColor="@color/ah_primary"
            android:textSize="16sp" />
        <TextView
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="@{subtitle}"
            android:textColor="@color/ah_muted"
            android:layout_marginTop="2dp" />
        <TextView
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:text="@{meta}"
            android:textSize="12sp"
            android:layout_marginTop="4dp" />
    </LinearLayout>
</layout>
''')
    base = f"core/ui/src/main/java/{P}/core/ui"
    w(f"{base}/NavRoutes.java", f'''
package {PKG}.core.ui;

import android.net.Uri;

public final class NavRoutes {{
    public static final String SCHEME = "wings";
    public static final Uri LOGIN = Uri.parse("wings://login");
    public static final Uri DASHBOARD = Uri.parse("wings://dashboard");
    public static final Uri CREATE = Uri.parse("wings://create");

    private NavRoutes() {{}}

    public static Uri detail(long requestId) {{
        return Uri.parse("wings://detail/" + requestId);
    }}
}}
''')
    w(f"{base}/BaseMvvmFragment.java", f'''
package {PKG}.core.ui;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.LayoutRes;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.databinding.DataBindingUtil;
import androidx.databinding.ViewDataBinding;
import androidx.fragment.app.Fragment;
import androidx.lifecycle.ViewModel;

public abstract class BaseMvvmFragment<VB extends ViewDataBinding, VM extends ViewModel> extends Fragment {{
    protected VB binding;
    protected VM viewModel;
    private final int layoutId;

    protected BaseMvvmFragment(@LayoutRes int layoutId) {{
        this.layoutId = layoutId;
    }}

    @NonNull
    protected abstract VM createViewModel();

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {{
        binding = DataBindingUtil.inflate(inflater, layoutId, container, false);
        binding.setLifecycleOwner(getViewLifecycleOwner());
        viewModel = createViewModel();
        return binding.getRoot();
    }}

    @Override
    public void onDestroyView() {{
        super.onDestroyView();
        binding = null;
    }}
}}
''')
    w(f"{base}/RequestListAdapter.java", f'''
package {PKG}.core.ui;

import android.view.LayoutInflater;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.DiffUtil;
import androidx.recyclerview.widget.ListAdapter;
import androidx.recyclerview.widget.RecyclerView;

import {PKG}.core.common.MoneyFormatters;
import {PKG}.core.model.ApprovalRequest;
import {PKG}.core.ui.databinding.ItemRequestBinding;
import {PKG}.domain.approval.ApprovalWorkflow;

public class RequestListAdapter extends ListAdapter<ApprovalRequest, RequestListAdapter.Holder> {{

    public interface OnClick {{
        void onClick(ApprovalRequest request);
    }}

    private final OnClick onClick;

    public RequestListAdapter(OnClick onClick) {{
        super(DIFF);
        this.onClick = onClick;
    }}

    private static final DiffUtil.ItemCallback<ApprovalRequest> DIFF = new DiffUtil.ItemCallback<ApprovalRequest>() {{
        @Override
        public boolean areItemsTheSame(@NonNull ApprovalRequest a, @NonNull ApprovalRequest b) {{
            return a.id == b.id;
        }}

        @Override
        public boolean areContentsTheSame(@NonNull ApprovalRequest a, @NonNull ApprovalRequest b) {{
            return a.updatedAt == b.updatedAt && a.status == b.status && a.title.equals(b.title);
        }}
    }};

    @NonNull
    @Override
    public Holder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {{
        ItemRequestBinding b = ItemRequestBinding.inflate(LayoutInflater.from(parent.getContext()), parent, false);
        return new Holder(b);
    }}

    @Override
    public void onBindViewHolder(@NonNull Holder holder, int position) {{
        ApprovalRequest r = getItem(position);
        holder.binding.setTitle("#" + r.id + " " + r.title);
        holder.binding.setSubtitle(ApprovalWorkflow.levelLabel(r.status) + (r.escalated ? " · ESCALATED" : ""));
        holder.binding.setMeta(r.type.name() + " · " + MoneyFormatters.idr(r.amount) + " · " + r.department);
        holder.binding.getRoot().setOnClickListener(v -> onClick.onClick(r));
        holder.binding.executePendingBindings();
    }}

    static class Holder extends RecyclerView.ViewHolder {{
        final ItemRequestBinding binding;

        Holder(ItemRequestBinding binding) {{
            super(binding.getRoot());
            this.binding = binding;
        }}
    }}
}}
''')


def gen_core_preference() -> None:
    empty_consumer("core/preference")
    w("core/preference/build.gradle.kts", lib_build(f"{PKG}.core.preference", [
        'api(project(":core:model"))',
        "implementation(libs.androidx.appcompat)",
    ]))
    w("core/preference/src/main/AndroidManifest.xml", empty_manifest(f"{PKG}.core.preference"))
    base = f"core/preference/src/main/java/{P}/core/preference"
    w(f"{base}/UserPreferences.java", f'''
package {PKG}.core.preference;

import android.content.Context;
import android.content.SharedPreferences;

import {PKG}.core.model.ThemeMode;

public class UserPreferences {{
    private static final String PREFS = "approval_hub_prefs";
    private static final String KEY_THEME = "theme_mode";
    private static final String KEY_LAST_ACTIVITY = "last_activity_at";
    private static final String KEY_SESSION_USER = "session_user_id";

    private final SharedPreferences prefs;

    public UserPreferences(Context context) {{
        prefs = context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }}

    public ThemeMode getThemeMode() {{
        try {{
            return ThemeMode.valueOf(prefs.getString(KEY_THEME, ThemeMode.SYSTEM.name()));
        }} catch (Exception e) {{
            return ThemeMode.SYSTEM;
        }}
    }}

    public void setThemeMode(ThemeMode mode) {{
        prefs.edit().putString(KEY_THEME, mode.name()).apply();
    }}

    public long getLastActivityAt() {{
        return prefs.getLong(KEY_LAST_ACTIVITY, 0L);
    }}

    public void touchActivity() {{
        prefs.edit().putLong(KEY_LAST_ACTIVITY, System.currentTimeMillis()).apply();
    }}

    public void saveSessionUserId(Long userId) {{
        SharedPreferences.Editor ed = prefs.edit();
        if (userId == null) ed.remove(KEY_SESSION_USER);
        else ed.putLong(KEY_SESSION_USER, userId);
        ed.apply();
    }}

    public Long getSessionUserId() {{
        if (!prefs.contains(KEY_SESSION_USER)) return null;
        return prefs.getLong(KEY_SESSION_USER, 0L);
    }}
}}
''')


def gen_core_network() -> None:
    empty_consumer("core/network")
    w("core/network/build.gradle.kts", lib_build(f"{PKG}.core.network", [
        "implementation(libs.androidx.annotation)",
    ]))
    w("core/network/src/main/AndroidManifest.xml", empty_manifest(f"{PKG}.core.network"))
    base = f"core/network/src/main/java/{P}/core/network"
    w(f"{base}/RemoteApi.java", f'''
package {PKG}.core.network;

public interface RemoteApi {{
    int pullRequestCount() throws Exception;
    int pushPending(int localPending) throws Exception;
}}
''')
    w(f"{base}/FakeRemoteApi.java", f'''
package {PKG}.core.network;

public class FakeRemoteApi implements RemoteApi {{
    @Override
    public int pullRequestCount() throws Exception {{
        Thread.sleep(400);
        return 2;
    }}

    @Override
    public int pushPending(int localPending) throws Exception {{
        Thread.sleep(400);
        return localPending;
    }}
}}
''')


def gen_core_notification() -> None:
    empty_consumer("core/notification")
    w("core/notification/build.gradle.kts", lib_build(f"{PKG}.core.notification", [
        "implementation(libs.androidx.core)",
        "implementation(libs.androidx.appcompat)",
    ]))
    w("core/notification/src/main/AndroidManifest.xml", empty_manifest(f"{PKG}.core.notification"))
    w("core/notification/src/main/res/drawable/ic_notification.xml", '''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp" android:height="24dp"
    android:viewportWidth="24" android:viewportHeight="24">
    <path android:fillColor="#FFFFFF"
        android:pathData="M12,2A2,2 0 0,0 10,4V5.08C7.16,5.57 5,8.03 5,11V16L3,18V19H21V18L19,16V11C19,8.03 16.84,5.57 14,5.08V4A2,2 0 0,0 12,2M10,21A2,2 0 0,0 12,23A2,2 0 0,0 14,21"/>
</vector>
''')
    base = f"core/notification/src/main/java/{P}/core/notification"
    w(f"{base}/ApprovalNotifier.java", f'''
package {PKG}.core.notification;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.os.Build;

import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;

public final class ApprovalNotifier {{
    public static final String CHANNEL_ID = "approval_inbox";
    private static final String CHANNEL_NAME = "Approval Inbox";
    private static final String LAUNCH_ACTION = "com.fauzi.wings.OPEN_APP";

    private ApprovalNotifier() {{}}

    public static void ensureChannel(Context context) {{
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {{
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID, CHANNEL_NAME, NotificationManager.IMPORTANCE_DEFAULT);
            channel.setDescription("Notifikasi request menunggu approval");
            NotificationManager nm = context.getSystemService(NotificationManager.class);
            if (nm != null) nm.createNotificationChannel(channel);
        }}
    }}

    public static void notifyInbox(Context context, String title, String body, int notificationId) {{
        ensureChannel(context);
        Intent intent = context.getPackageManager().getLaunchIntentForPackage(context.getPackageName());
        if (intent == null) {{
            intent = new Intent(LAUNCH_ACTION);
            intent.setPackage(context.getPackageName());
        }}
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent pending = PendingIntent.getActivity(
                context, 0, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        NotificationCompat.Builder builder = new NotificationCompat.Builder(context, CHANNEL_ID)
                .setSmallIcon(R.drawable.ic_notification)
                .setContentTitle(title)
                .setContentText(body)
                .setContentIntent(pending)
                .setAutoCancel(true)
                .setPriority(NotificationCompat.PRIORITY_DEFAULT);
        try {{
            NotificationManagerCompat.from(context).notify(notificationId, builder.build());
        }} catch (SecurityException ignored) {{
        }}
    }}
}}
''')


if __name__ == "__main__":
    # Partial — continued in generate_all2
    print("Part1 helpers loaded — run generate via generate_runner")
