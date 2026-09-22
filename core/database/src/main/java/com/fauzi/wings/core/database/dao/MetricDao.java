package com.fauzi.wings.core.database.dao;

import androidx.lifecycle.LiveData;
import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;

import com.fauzi.wings.core.database.entity.MetricSnapshotEntity;

import java.util.List;

@Dao
public interface MetricDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void upsertAll(List<MetricSnapshotEntity> metrics);

    @Query("SELECT * FROM metric_snapshots ORDER BY recordedAt ASC")
    LiveData<List<MetricSnapshotEntity>> observeAll();

    @Query("SELECT * FROM metric_snapshots WHERE category = :category ORDER BY recordedAt ASC")
    LiveData<List<MetricSnapshotEntity>> observeByCategory(String category);

    @Query("SELECT COUNT(*) FROM metric_snapshots")
    int count();
}
