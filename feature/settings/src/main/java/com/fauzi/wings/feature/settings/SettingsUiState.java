package com.fauzi.wings.feature.settings;
import com.fauzi.wings.core.model.*;
public class SettingsUiState {
    public final User user; public final Role impersonate; public final String syncInfo; public final String message;
    public final boolean loggedOut; public final boolean canForceEscalate;
    public SettingsUiState(User user, Role impersonate, String syncInfo, String message, boolean loggedOut, boolean canForceEscalate) {
        this.user = user; this.impersonate = impersonate; this.syncInfo = syncInfo == null ? "" : syncInfo;
        this.message = message == null ? "" : message; this.loggedOut = loggedOut;
        this.canForceEscalate = canForceEscalate;
    }
}
