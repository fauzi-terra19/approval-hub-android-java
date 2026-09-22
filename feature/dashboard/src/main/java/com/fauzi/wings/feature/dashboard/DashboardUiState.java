package com.fauzi.wings.feature.dashboard;

import com.fauzi.wings.core.model.ApprovalRequest;
import com.fauzi.wings.core.model.DashboardStats;
import com.fauzi.wings.core.model.User;

import java.util.Collections;
import java.util.List;

public class DashboardUiState {
    public final User user;
    public final String title;
    public final DashboardStats stats;
    public final List<ApprovalRequest> requests;

    public DashboardUiState(User user, String title, DashboardStats stats, List<ApprovalRequest> requests) {
        this.user = user;
        this.title = title;
        this.stats = stats == null ? new DashboardStats() : stats;
        this.requests = requests == null ? Collections.emptyList() : requests;
    }

    public static DashboardUiState empty() {
        return new DashboardUiState(null, "Dashboard", new DashboardStats(), Collections.emptyList());
    }
}
