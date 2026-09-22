package com.fauzi.wings.core.model;

public class DashboardStats {
    public final int totalVisible;
    public final int pendingInbox;
    public final int approved;
    public final int rejected;
    public final int inPipeline;

    public DashboardStats() {
        this(0, 0, 0, 0, 0);
    }

    public DashboardStats(int totalVisible, int pendingInbox, int approved, int rejected, int inPipeline) {
        this.totalVisible = totalVisible;
        this.pendingInbox = pendingInbox;
        this.approved = approved;
        this.rejected = rejected;
        this.inPipeline = inPipeline;
    }
}
