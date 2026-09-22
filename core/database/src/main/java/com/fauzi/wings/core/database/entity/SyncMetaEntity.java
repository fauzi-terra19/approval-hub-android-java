package com.fauzi.wings.core.database.entity;

import androidx.room.Entity;
import androidx.room.PrimaryKey;

@Entity(tableName = "sync_meta")
public class SyncMetaEntity {
    @PrimaryKey
    public int id = 1;
    public long lastSyncedAt;
    public String lastSyncStatus;
    public int pendingPushCount;

    public SyncMetaEntity() {}

    public SyncMetaEntity(int id, long lastSyncedAt, String lastSyncStatus, int pendingPushCount) {
        this.id = id;
        this.lastSyncedAt = lastSyncedAt;
        this.lastSyncStatus = lastSyncStatus;
        this.pendingPushCount = pendingPushCount;
    }
}
