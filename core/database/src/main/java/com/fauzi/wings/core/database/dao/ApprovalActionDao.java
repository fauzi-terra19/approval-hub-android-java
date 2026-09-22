package com.fauzi.wings.core.database.dao;

import androidx.lifecycle.LiveData;
import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;

import com.fauzi.wings.core.database.entity.ApprovalActionEntity;

import java.util.List;

@Dao
public interface ApprovalActionDao {
    @Insert
    long insert(ApprovalActionEntity action);

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void upsertAll(List<ApprovalActionEntity> actions);

    @Query("SELECT * FROM approval_actions WHERE requestId = :requestId ORDER BY createdAt ASC")
    LiveData<List<ApprovalActionEntity>> observeByRequest(long requestId);

    @Query("SELECT * FROM approval_actions ORDER BY createdAt DESC")
    LiveData<List<ApprovalActionEntity>> observeAll();

    @Query("SELECT * FROM approval_actions ORDER BY createdAt DESC")
    List<ApprovalActionEntity> getAll();
}
