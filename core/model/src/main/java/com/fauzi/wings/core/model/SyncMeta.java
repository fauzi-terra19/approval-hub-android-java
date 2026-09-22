package com.fauzi.wings.core.model;

public class SyncMeta {
    public final long lastSyncedAt;
    public final String lastSyncStatus;
    public final int pendingPushCount;

    public SyncMeta(long lastSyncedAt, String lastSyncStatus, int pendingPushCount) {
        this.lastSyncedAt = lastSyncedAt;
        this.lastSyncStatus = lastSyncStatus;
        this.pendingPushCount = pendingPushCount;
    }
}
