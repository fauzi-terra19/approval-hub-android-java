package com.fauzi.wings.app.work;

import android.content.Context;

import androidx.annotation.NonNull;
import androidx.work.ExistingPeriodicWorkPolicy;
import androidx.work.PeriodicWorkRequest;
import androidx.work.Worker;
import androidx.work.WorkerParameters;
import androidx.work.WorkManager;

import com.fauzi.wings.core.database.AppDatabase;
import com.fauzi.wings.core.database.entity.ApprovalActionEntity;
import com.fauzi.wings.core.database.entity.ApprovalRequestEntity;
import com.fauzi.wings.core.model.ApprovalStatus;
import com.fauzi.wings.core.notification.ApprovalNotifier;
import com.fauzi.wings.domain.approval.ApprovalWorkflow;

import java.util.List;
import java.util.concurrent.TimeUnit;

public class EscalationWorker extends Worker {
    private static final String UNIQUE = "escalation_periodic";

    public EscalationWorker(@NonNull Context context, @NonNull WorkerParameters params) {
        super(context, params);
    }

    @NonNull
    @Override
    public Result doWork() {
        AppDatabase db = AppDatabase.get(getApplicationContext());
        long now = System.currentTimeMillis();
        long threshold = now - ApprovalWorkflow.IDLE_BEFORE_ESCALATE_MS;
        List<ApprovalRequestEntity> overdue = db.approvalRequestDao().getOverdue(threshold);
        int escalatedCount = 0;
        for (ApprovalRequestEntity request : overdue) {
            ApprovalStatus next = ApprovalWorkflow.escalateStatus(request.status, request.requiredMaxLevel);
            if (next == null) continue;
            Integer level = ApprovalWorkflow.requiredLevel(next);
            if (level == null) continue;
            request.status = next;
            request.currentLevel = level;
            request.escalated = true;
            request.updatedAt = now;
            db.approvalRequestDao().update(request);
            db.approvalActionDao().insert(new ApprovalActionEntity(
                    request.id, 1, request.currentLevel, "ESCALATE",
                    "Auto-escalate karena idle > 2 hari", now));
            escalatedCount++;
        }
        int pending = db.approvalRequestDao().pendingCountSync();
        if (pending > 0 || escalatedCount > 0) {
            String title = escalatedCount > 0 ? "Escalation & Inbox" : "Approval Inbox";
            StringBuilder body = new StringBuilder();
            if (escalatedCount > 0) body.append(escalatedCount).append(" request di-escalate. ");
            body.append(pending).append(" request masih pending.");
            ApprovalNotifier.notifyInbox(getApplicationContext(), title, body.toString(), 2001);
        }
        return Result.success();
    }

    public static void schedule(Context context) {
        PeriodicWorkRequest request = new PeriodicWorkRequest.Builder(
                EscalationWorker.class, 6, TimeUnit.HOURS).build();
        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                UNIQUE, ExistingPeriodicWorkPolicy.UPDATE, request);
    }
}
