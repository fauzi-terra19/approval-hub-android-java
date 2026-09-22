package com.fauzi.wings.data.sync;

import com.fauzi.wings.core.database.AppDatabase;
import com.fauzi.wings.core.database.entity.ApprovalRequestEntity;
import com.fauzi.wings.core.database.entity.SyncMetaEntity;
import com.fauzi.wings.core.model.SyncMeta;
import com.fauzi.wings.core.network.RemoteApi;
import com.fauzi.wings.data.mapper.Mappers;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.Transformations;

public class SyncRepository {
    private final AppDatabase db;
    private final RemoteApi remoteApi;

    public SyncRepository(AppDatabase db, RemoteApi remoteApi) {
        this.db = db;
        this.remoteApi = remoteApi;
    }

    public LiveData<SyncMeta> observeMeta() {
        return Transformations.map(db.syncMetaDao().observe(), Mappers::toSyncMeta);
    }

    public SyncMeta syncNow() throws Exception {
        int pending = 0;
        for (ApprovalRequestEntity r : db.approvalRequestDao().getAll()) {
            if (r.status.name().startsWith("PENDING")) pending++;
        }
        try {
            remoteApi.pushPending(pending);
            remoteApi.pullRequestCount();
            SyncMetaEntity meta = new SyncMetaEntity(1, System.currentTimeMillis(), "OK", pending);
            db.syncMetaDao().upsert(meta);
            return Mappers.toSyncMeta(meta);
        } catch (Exception error) {
            SyncMetaEntity meta = new SyncMetaEntity(1, System.currentTimeMillis(),
                    "ERROR: " + error.getMessage(), 0);
            db.syncMetaDao().upsert(meta);
            throw error;
        }
    }
}
