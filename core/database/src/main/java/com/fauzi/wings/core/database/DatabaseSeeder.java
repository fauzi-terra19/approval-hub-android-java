package com.fauzi.wings.core.database;

import com.fauzi.wings.core.database.entity.ApprovalActionEntity;
import com.fauzi.wings.core.database.entity.ApprovalRequestEntity;
import com.fauzi.wings.core.database.entity.MetricSnapshotEntity;
import com.fauzi.wings.core.database.entity.SyncMetaEntity;
import com.fauzi.wings.core.database.entity.UserEntity;
import com.fauzi.wings.core.model.ApprovalStatus;
import com.fauzi.wings.core.model.RequestType;
import com.fauzi.wings.core.model.Role;
import com.fauzi.wings.domain.approval.AmountBasedRules;
import com.fauzi.wings.domain.security.PasswordHasher;

import java.util.Arrays;
import java.util.List;
import java.util.concurrent.TimeUnit;

public final class DatabaseSeeder {
    private DatabaseSeeder() {}

    public static void seedIfNeeded(AppDatabase db) {
        if (db.userDao().count() > 0) return;
        long now = System.currentTimeMillis();
        List<UserEntity> users = Arrays.asList(
                new UserEntity(1, "admin", "Admin Wings", PasswordHasher.hash("admin123"), Role.ADMIN, "IT"),
                new UserEntity(2, "director", "Dewi Director", PasswordHasher.hash("dir123"), Role.DIRECTOR, "Executive"),
                new UserEntity(3, "manager", "Mira Manager", PasswordHasher.hash("mgr123"), Role.MANAGER, "Operations"),
                new UserEntity(4, "supervisor", "Surya Supervisor", PasswordHasher.hash("spv123"), Role.SUPERVISOR, "Operations"),
                new UserEntity(5, "staff", "Rina Staff", PasswordHasher.hash("staff123"), Role.STAFF, "Operations"),
                new UserEntity(6, "staff2", "Budi Finance", PasswordHasher.hash("staff123"), Role.STAFF, "Finance")
        );
        db.userDao().upsertAll(users);

        ApprovalRequestEntity r1 = new ApprovalRequestEntity(
                "Laptop procurement", "MacBook untuk design team", RequestType.PURCHASE, 15_000_000,
                5, "Operations", ApprovalStatus.PENDING_L1, 1,
                AmountBasedRules.requiredMaxLevel(RequestType.PURCHASE, 15_000_000),
                false, now - TimeUnit.DAYS.toMillis(3), now - TimeUnit.DAYS.toMillis(3));
        ApprovalRequestEntity r2 = new ApprovalRequestEntity(
                "Travel expense Q3", "Client visit Surabaya", RequestType.EXPENSE, 3_500_000,
                6, "Finance", ApprovalStatus.PENDING_L2, 2,
                AmountBasedRules.requiredMaxLevel(RequestType.EXPENSE, 3_500_000),
                false, now - TimeUnit.DAYS.toMillis(1), now - TimeUnit.HOURS.toMillis(6));
        ApprovalRequestEntity r3 = new ApprovalRequestEntity(
                "Leave 3 days", "Cuti keluarga", RequestType.LEAVE, 0,
                5, "Operations", ApprovalStatus.APPROVED, 2,
                AmountBasedRules.requiredMaxLevel(RequestType.LEAVE, 0),
                false, now - TimeUnit.DAYS.toMillis(10), now - TimeUnit.DAYS.toMillis(8));
        ApprovalRequestEntity r4 = new ApprovalRequestEntity(
                "VPN access", "Akses staging VPN", RequestType.ACCESS, 0,
                6, "Finance", ApprovalStatus.PENDING_L1, 1,
                AmountBasedRules.requiredMaxLevel(RequestType.ACCESS, 0),
                true, now - TimeUnit.DAYS.toMillis(5), now - TimeUnit.DAYS.toMillis(4));

        long id1 = db.approvalRequestDao().insert(r1);
        long id2 = db.approvalRequestDao().insert(r2);
        long id3 = db.approvalRequestDao().insert(r3);
        long id4 = db.approvalRequestDao().insert(r4);

        db.approvalActionDao().upsertAll(Arrays.asList(
                new ApprovalActionEntity(id2, 4, 1, "APPROVE", "OK for L1", now - TimeUnit.HOURS.toMillis(12)),
                new ApprovalActionEntity(id3, 4, 1, "APPROVE", "Approved leave", now - TimeUnit.DAYS.toMillis(9)),
                new ApprovalActionEntity(id3, 3, 2, "APPROVE", "Manager OK", now - TimeUnit.DAYS.toMillis(8)),
                new ApprovalActionEntity(id4, 1, 1, "ESCALATE", "Auto escalate idle", now - TimeUnit.DAYS.toMillis(4))
        ));

        db.metricDao().upsertAll(Arrays.asList(
                new MetricSnapshotEntity("SLA 48h", "sla", 86.5, now - TimeUnit.DAYS.toMillis(2)),
                new MetricSnapshotEntity("Pending pipeline", "ops", 12, now - TimeUnit.DAYS.toMillis(1)),
                new MetricSnapshotEntity("Avg L1 hours", "bottleneck", 18.2, now)
        ));

        db.syncMetaDao().upsert(new SyncMetaEntity(1, 0, "NEVER", 0));
    }
}
