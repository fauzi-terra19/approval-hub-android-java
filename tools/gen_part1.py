# -*- coding: utf-8 -*-
"""Generate remaining Java modules for Wings ApprovalHub."""
from pathlib import Path

ROOT = Path(r"D:/fauzi/cursor/wings/android")


def w(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if content.startswith("\n"):
        content = content[1:]
    p.write_text(content, encoding="utf-8")
    print(rel)


def android_lib(ns, deps, databinding=False):
    bf = ""
    if databinding:
        bf = """
    buildFeatures {
        dataBinding = true
        viewBinding = true
    }
"""
    dep = "\n".join("    " + d for d in deps)
    return f"""plugins {{
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
    }}
{bf}}}

dependencies {{
{dep}
}}
"""


def empty_manifest():
    return '<?xml version="1.0" encoding="utf-8"?>\n<manifest />\n'


def feature_deps():
    return [
        'api(project(":core:ui"))',
        'api(project(":core:model"))',
        'api(project(":core:common"))',
        'api(project(":domain"))',
        'implementation(project(":data"))',
        "api(libs.androidx.appcompat)",
        "api(libs.material)",
        "api(libs.androidx.recyclerview)",
        "api(libs.androidx.lifecycle.viewmodel)",
        "api(libs.androidx.lifecycle.livedata)",
        "api(libs.androidx.fragment)",
        "api(libs.androidx.navigation.fragment)",
    ]


def gen_preference():
    w("core/preference/build.gradle.kts", android_lib("com.fauzi.wings.core.preference", [
        'api(project(":core:model"))',
        "implementation(libs.androidx.appcompat)",
        "api(libs.androidx.lifecycle.livedata)",
    ]))
    w("core/preference/consumer-rules.pro", "#\n")
    w("core/preference/src/main/AndroidManifest.xml", empty_manifest())
    w("core/preference/src/main/java/com/fauzi/wings/core/preference/UserPreferences.java", """
package com.fauzi.wings.core.preference;

import android.content.Context;
import android.content.SharedPreferences;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;

import com.fauzi.wings.core.model.ThemeMode;

public class UserPreferences {
    private static final String PREFS = "wings_approval_hub_prefs";
    private static final String KEY_THEME = "theme_mode";
    private static final String KEY_ACTIVITY = "last_activity_at";
    private static final String KEY_SESSION = "session_user_id";

    private final SharedPreferences prefs;
    private final MutableLiveData<ThemeMode> themeLive = new MutableLiveData<>(ThemeMode.SYSTEM);

    public UserPreferences(Context context) {
        prefs = context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        themeLive.setValue(readTheme());
    }

    public LiveData<ThemeMode> getThemeMode() { return themeLive; }

    public ThemeMode readTheme() {
        try {
            return ThemeMode.valueOf(prefs.getString(KEY_THEME, ThemeMode.SYSTEM.name()));
        } catch (Exception e) {
            return ThemeMode.SYSTEM;
        }
    }

    public void setThemeMode(ThemeMode mode) {
        prefs.edit().putString(KEY_THEME, mode.name()).apply();
        themeLive.postValue(mode);
    }

    public long getLastActivityAt() {
        return prefs.getLong(KEY_ACTIVITY, 0L);
    }

    public void touchActivity() {
        prefs.edit().putLong(KEY_ACTIVITY, System.currentTimeMillis()).apply();
    }

    public Long getSessionUserId() {
        if (!prefs.contains(KEY_SESSION)) return null;
        return prefs.getLong(KEY_SESSION, -1L);
    }

    public void saveSessionUserId(Long userId) {
        SharedPreferences.Editor ed = prefs.edit();
        if (userId == null) ed.remove(KEY_SESSION);
        else ed.putLong(KEY_SESSION, userId);
        ed.apply();
    }
}
""")


def gen_network():
    w("core/network/build.gradle.kts", android_lib("com.fauzi.wings.core.network", [
        "implementation(libs.androidx.annotation)",
    ]))
    w("core/network/consumer-rules.pro", "#\n")
    w("core/network/src/main/AndroidManifest.xml", empty_manifest())
    w("core/network/src/main/java/com/fauzi/wings/core/network/RemoteApi.java", """
package com.fauzi.wings.core.network;

public interface RemoteApi {
    int pullRequestCount() throws InterruptedException;
    int pushPending(int localPending) throws InterruptedException;
}
""")
    w("core/network/src/main/java/com/fauzi/wings/core/network/FakeRemoteApi.java", """
package com.fauzi.wings.core.network;

public class FakeRemoteApi implements RemoteApi {
    @Override
    public int pullRequestCount() throws InterruptedException {
        Thread.sleep(400);
        return 2;
    }

    @Override
    public int pushPending(int localPending) throws InterruptedException {
        Thread.sleep(400);
        return localPending;
    }
}
""")


def gen_notification():
    w("core/notification/build.gradle.kts", android_lib("com.fauzi.wings.core.notification", [
        "implementation(libs.androidx.core)",
        "implementation(libs.androidx.appcompat)",
    ]))
    w("core/notification/consumer-rules.pro", "#\n")
    w("core/notification/src/main/AndroidManifest.xml", empty_manifest())
    w("core/notification/src/main/java/com/fauzi/wings/core/notification/ApprovalNotifier.java", """
package com.fauzi.wings.core.notification;

import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.Context;
import android.os.Build;

import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;

public final class ApprovalNotifier {
    public static final String CHANNEL_ID = "approval_inbox";

    private ApprovalNotifier() {}

    public static void ensureChannel(Context context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID, "Approval Inbox", NotificationManager.IMPORTANCE_DEFAULT);
            NotificationManager nm = context.getSystemService(NotificationManager.class);
            if (nm != null) nm.createNotificationChannel(channel);
        }
    }

    public static void notifyInbox(Context context, String title, String body, int notificationId) {
        ensureChannel(context);
        NotificationCompat.Builder builder = new NotificationCompat.Builder(context, CHANNEL_ID)
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentTitle(title)
                .setContentText(body)
                .setAutoCancel(true);
        try {
            NotificationManagerCompat.from(context).notify(notificationId, builder.build());
        } catch (SecurityException ignored) {
        }
    }
}
""")


print("part1 helpers loaded")
