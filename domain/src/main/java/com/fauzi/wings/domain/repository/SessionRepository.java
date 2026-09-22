package com.fauzi.wings.domain.repository;

import com.fauzi.wings.core.model.Permission;
import com.fauzi.wings.core.model.Role;
import com.fauzi.wings.core.model.ThemeMode;
import com.fauzi.wings.core.model.User;

import androidx.lifecycle.LiveData;

public interface SessionRepository {
    LiveData<User> observeSession();
    LiveData<Role> observeImpersonateRole();
    User getSession();
    Role getImpersonateRole();
    void ensureSeeded();
    User restoreSession();
    User login(String username, String password) throws Exception;
    void logoutAndClear();
    void touchActivity();
    boolean checkSessionTimeout();
    boolean hasPermission(Permission permission);
    void setImpersonateRole(Role role);
    void setThemeMode(ThemeMode mode);
    ThemeMode getThemeMode();
}
