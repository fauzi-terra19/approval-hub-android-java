package com.fauzi.wings.data.mapper;

import com.fauzi.wings.core.database.dao.StatusCountRow;
import com.fauzi.wings.core.database.dao.TypeStatRow;
import com.fauzi.wings.core.database.entity.ApprovalActionEntity;
import com.fauzi.wings.core.database.entity.ApprovalRequestEntity;
import com.fauzi.wings.core.database.entity.SyncMetaEntity;
import com.fauzi.wings.core.database.entity.UserEntity;
import com.fauzi.wings.core.model.ApprovalAction;
import com.fauzi.wings.core.model.ApprovalRequest;
import com.fauzi.wings.core.model.StatusCount;
import com.fauzi.wings.core.model.SyncMeta;
import com.fauzi.wings.core.model.TypeStat;
import com.fauzi.wings.core.model.User;

import java.util.ArrayList;
import java.util.List;

public final class Mappers {
    private Mappers() {}

    public static User toUser(UserEntity e) {
        if (e == null) return null;
        return new User(e.id, e.username, e.displayName, e.role, e.department);
    }

    public static ApprovalRequest toRequest(ApprovalRequestEntity e) {
        if (e == null) return null;
        return new ApprovalRequest(e.id, e.title, e.description, e.type, e.amount, e.requesterId,
                e.department, e.status, e.currentLevel, e.requiredMaxLevel, e.escalated, e.createdAt, e.updatedAt);
    }

    public static List<ApprovalRequest> toRequests(List<ApprovalRequestEntity> list) {
        List<ApprovalRequest> out = new ArrayList<>();
        if (list == null) return out;
        for (ApprovalRequestEntity e : list) out.add(toRequest(e));
        return out;
    }

    public static ApprovalAction toAction(ApprovalActionEntity e) {
        return new ApprovalAction(e.id, e.requestId, e.actorId, e.level, e.decision, e.comment, e.createdAt);
    }

    public static List<ApprovalAction> toActions(List<ApprovalActionEntity> list) {
        List<ApprovalAction> out = new ArrayList<>();
        if (list == null) return out;
        for (ApprovalActionEntity e : list) out.add(toAction(e));
        return out;
    }

    public static StatusCount toStatusCount(StatusCountRow r) {
        return new StatusCount(r.status, r.count);
    }

    public static TypeStat toTypeStat(TypeStatRow r) {
        return new TypeStat(r.type, r.count, r.totalAmount);
    }

    public static SyncMeta toSyncMeta(SyncMetaEntity e) {
        if (e == null) return null;
        return new SyncMeta(e.lastSyncedAt, e.lastSyncStatus, e.pendingPushCount);
    }
}
