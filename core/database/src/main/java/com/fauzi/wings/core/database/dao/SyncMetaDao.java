package com.fauzi.wings.core.database.dao;

import androidx.lifecycle.LiveData;
import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;

import com.fauzi.wings.core.database.entity.SyncMetaEntity;

@Dao
public interface SyncMetaDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void upsert(SyncMetaEntity meta);

    @Query("SELECT * FROM sync_meta WHERE id = 1 LIMIT 1")
    LiveData<SyncMetaEntity> observe();

    @Query("SELECT * FROM sync_meta WHERE id = 1 LIMIT 1")
    SyncMetaEntity get();
}
