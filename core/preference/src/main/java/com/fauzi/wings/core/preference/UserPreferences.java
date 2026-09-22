package com.fauzi.wings.core.preference;

import android.content.Context;
import android.content.SharedPreferences;

import com.fauzi.wings.core.model.ThemeMode;

public class UserPreferences {
    private static final String PREFS = "approval_hub_prefs";
    private static final String KEY_THEME = "theme_mode";
    private static final String KEY_LAST_ACTIVITY = "last_activity_at";
    private static final String KEY_SESSION_USER = "session_user_id";

    private final SharedPreferences prefs;

    public UserPreferences(Context context) {
        prefs = context.getApplicationContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public ThemeMode getThemeMode() {
        try {
            return ThemeMode.valueOf(prefs.getString(KEY_THEME, ThemeMode.SYSTEM.name()));
        } catch (Exception e) {
            return ThemeMode.SYSTEM;
        }
    }

    public void setThemeMode(ThemeMode mode) {
        prefs.edit().putString(KEY_THEME, mode.name()).apply();
    }

    public long getLastActivityAt() {
        return prefs.getLong(KEY_LAST_ACTIVITY, 0L);
    }

    public void touchActivity() {
        prefs.edit().putLong(KEY_LAST_ACTIVITY, System.currentTimeMillis()).apply();
    }

    public void saveSessionUserId(Long userId) {
        SharedPreferences.Editor ed = prefs.edit();
        if (userId == null) ed.remove(KEY_SESSION_USER);
        else ed.putLong(KEY_SESSION_USER, userId);
        ed.apply();
    }

    public Long getSessionUserId() {
        if (!prefs.contains(KEY_SESSION_USER)) return null;
        return prefs.getLong(KEY_SESSION_USER, 0L);
    }
}
