package com.fauzi.wings.domain.approval;

import com.fauzi.wings.core.model.ApprovalStatus;
import com.fauzi.wings.core.model.Role;
import com.fauzi.wings.domain.rbac.RbacPolicy;

import java.util.concurrent.TimeUnit;

public final class ApprovalWorkflow {
    public static final int MAX_LEVEL = 3;
    public static final long IDLE_BEFORE_ESCALATE_MS = TimeUnit.DAYS.toMillis(2);

    private ApprovalWorkflow() {}

    public static ApprovalStatus initialStatusAfterSubmit() {
        return ApprovalStatus.PENDING_L1;
    }

    public static Integer requiredLevel(ApprovalStatus status) {
        switch (status) {
            case PENDING_L1: return 1;
            case PENDING_L2: return 2;
            case PENDING_L3: return 3;
            default: return null;
        }
    }

    public static boolean canActOn(ApprovalStatus status, Role actorRole, boolean readOnly) {
        if (readOnly) return false;
        Integer level = requiredLevel(status);
        if (level == null) return false;
        return RbacPolicy.canApproveLevel(actorRole, level);
    }

    public static ApprovalStatus nextStatusOnApprove(ApprovalStatus current, int requiredMaxLevel) {
        Integer currentLevel = requiredLevel(current);
        if (currentLevel == null) return current;
        int max = Math.max(1, Math.min(MAX_LEVEL, requiredMaxLevel));
        if (currentLevel >= max) return ApprovalStatus.APPROVED;
        switch (current) {
            case PENDING_L1: return ApprovalStatus.PENDING_L2;
            case PENDING_L2: return ApprovalStatus.PENDING_L3;
            case PENDING_L3: return ApprovalStatus.APPROVED;
            default: return current;
        }
    }

    public static ApprovalStatus statusOnReject() {
        return ApprovalStatus.REJECTED;
    }

    public static boolean isTerminal(ApprovalStatus status) {
        return status == ApprovalStatus.APPROVED
                || status == ApprovalStatus.REJECTED
                || status == ApprovalStatus.CANCELLED;
    }

    public static String levelLabel(ApprovalStatus status) {
        switch (status) {
            case DRAFT: return "Draft";
            case PENDING_L1: return "Menunggu Supervisor (L1)";
            case PENDING_L2: return "Menunggu Manager (L2)";
            case PENDING_L3: return "Menunggu Director (L3)";
            case APPROVED: return "Disetujui";
            case REJECTED: return "Ditolak";
            case CANCELLED: return "Dibatalkan";
            default: return status.name();
        }
    }

    public static boolean isOverdue(long updatedAt, long now) {
        return now - updatedAt >= IDLE_BEFORE_ESCALATE_MS;
    }

    public static ApprovalStatus escalateStatus(ApprovalStatus current, int requiredMaxLevel) {
        if (isTerminal(current)) return null;
        Integer level = requiredLevel(current);
        if (level == null) return null;
        int max = Math.max(1, Math.min(MAX_LEVEL, requiredMaxLevel));
        if (level >= max) return null;
        switch (current) {
            case PENDING_L1: return ApprovalStatus.PENDING_L2;
            case PENDING_L2: return ApprovalStatus.PENDING_L3;
            default: return null;
        }
    }

    public static ApprovalStatus statusFromLevel(int level) {
        int l = Math.max(1, Math.min(3, level));
        if (l == 1) return ApprovalStatus.PENDING_L1;
        if (l == 2) return ApprovalStatus.PENDING_L2;
        return ApprovalStatus.PENDING_L3;
    }
}
