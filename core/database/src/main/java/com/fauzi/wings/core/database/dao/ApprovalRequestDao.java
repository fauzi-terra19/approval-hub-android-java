package com.fauzi.wings.core.database.dao;

import androidx.lifecycle.LiveData;
import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;
import androidx.room.Update;

import com.fauzi.wings.core.database.entity.ApprovalRequestEntity;

import java.util.List;

@Dao
public interface ApprovalRequestDao {
    @Insert
    long insert(ApprovalRequestEntity request);

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void upsertAll(List<ApprovalRequestEntity> requests);

    @Update
    void update(ApprovalRequestEntity request);

    @Query("SELECT * FROM approval_requests WHERE id = :id")
    ApprovalRequestEntity getById(long id);

    @Query("SELECT * FROM approval_requests ORDER BY updatedAt DESC")
    LiveData<List<ApprovalRequestEntity>> observeAll();

    @Query("SELECT * FROM approval_requests ORDER BY updatedAt DESC")
    List<ApprovalRequestEntity> getAll();

    @Query("SELECT * FROM approval_requests WHERE status IN ('PENDING_L1','PENDING_L2','PENDING_L3') AND updatedAt <= :before ORDER BY updatedAt ASC")
    List<ApprovalRequestEntity> getOverdue(long before);

    @Query("SELECT status AS status, COUNT(*) AS count FROM approval_requests GROUP BY status")
    LiveData<List<StatusCountRow>> observeStatusCounts();

    @Query("SELECT type AS type, COUNT(*) AS count, SUM(amount) AS totalAmount FROM approval_requests GROUP BY type")
    LiveData<List<TypeStatRow>> observeTypeStats();

    @Query("SELECT COUNT(*) FROM approval_requests WHERE status IN ('PENDING_L1','PENDING_L2','PENDING_L3')")
    LiveData<Integer> observePendingCount();

    @Query("SELECT COUNT(*) FROM approval_requests WHERE status IN ('PENDING_L1','PENDING_L2','PENDING_L3')")
    int pendingCountSync();

    @Query("SELECT COUNT(*) FROM approval_requests")
    int count();
}
