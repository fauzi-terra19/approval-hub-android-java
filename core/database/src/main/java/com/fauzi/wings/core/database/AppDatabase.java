package com.fauzi.wings.core.database;

import android.content.Context;

import androidx.room.Database;
import androidx.room.Room;
import androidx.room.RoomDatabase;
import androidx.room.TypeConverters;

import com.fauzi.wings.core.database.dao.ApprovalActionDao;
import com.fauzi.wings.core.database.dao.ApprovalRequestDao;
import com.fauzi.wings.core.database.dao.MetricDao;
import com.fauzi.wings.core.database.dao.SyncMetaDao;
import com.fauzi.wings.core.database.dao.UserDao;
import com.fauzi.wings.core.database.entity.ApprovalActionEntity;
import com.fauzi.wings.core.database.entity.ApprovalRequestEntity;
import com.fauzi.wings.core.database.entity.MetricSnapshotEntity;
import com.fauzi.wings.core.database.entity.SyncMetaEntity;
import com.fauzi.wings.core.database.entity.UserEntity;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@Database(
        entities = {
                UserEntity.class,
                ApprovalRequestEntity.class,
                ApprovalActionEntity.class,
                MetricSnapshotEntity.class,
                SyncMetaEntity.class
        },
        version = 1,
        exportSchema = false
)
@TypeConverters(Converters.class)
public abstract class AppDatabase extends RoomDatabase {
    public static final ExecutorService IO = Executors.newFixedThreadPool(4);

    private static volatile AppDatabase INSTANCE;

    public abstract UserDao userDao();
    public abstract ApprovalRequestDao approvalRequestDao();
    public abstract ApprovalActionDao approvalActionDao();
    public abstract MetricDao metricDao();
    public abstract SyncMetaDao syncMetaDao();

    public static AppDatabase get(Context context) {
        if (INSTANCE == null) {
            synchronized (AppDatabase.class) {
                if (INSTANCE == null) {
                    INSTANCE = build(context.getApplicationContext());
                }
            }
        }
        return INSTANCE;
    }

    public static AppDatabase build(Context context) {
        return Room.databaseBuilder(context, AppDatabase.class, "wings_approval_hub.db")
                .build();
    }

    public static void seed(AppDatabase db) {
        DatabaseSeeder.seedIfNeeded(db);
    }
}
