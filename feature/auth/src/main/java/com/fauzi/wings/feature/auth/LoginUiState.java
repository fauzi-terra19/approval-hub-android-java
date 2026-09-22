package com.fauzi.wings.feature.auth;
import com.fauzi.wings.core.model.DemoAccounts;
import com.fauzi.wings.core.model.User;
public class LoginUiState {
    public final boolean loading; public final String error; public final User loggedInUser; public final String demoHint;
    public LoginUiState(boolean loading, String error, User loggedInUser, String demoHint) {
        this.loading = loading; this.error = error; this.loggedInUser = loggedInUser; this.demoHint = demoHint;
    }
    public static LoginUiState initial() {
        StringBuilder sb = new StringBuilder();
        for (DemoAccounts.Demo d : DemoAccounts.ALL) {
            if (sb.length() > 0) sb.append("\n");
            sb.append(d.username).append(" / ").append(d.password).append(" · ").append(d.roleLabel);
        }
        return new LoginUiState(false, null, null, sb.toString());
    }
}
