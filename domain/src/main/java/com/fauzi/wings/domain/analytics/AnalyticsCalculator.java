package com.fauzi.wings.domain.analytics;

import com.fauzi.wings.core.model.ApprovalAction;
import com.fauzi.wings.core.model.ApprovalRequest;
import com.fauzi.wings.core.model.ApprovalStatus;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

public final class AnalyticsCalculator {
    private AnalyticsCalculator() {}

    public static SlaStats slaStats(List<ApprovalRequest> requests, long slaHours) {
        List<ApprovalRequest> completed = new ArrayList<>();
        for (ApprovalRequest r : requests) {
            if (r.status == ApprovalStatus.APPROVED || r.status == ApprovalStatus.REJECTED) {
                completed.add(r);
            }
        }
        long slaMs = TimeUnit.HOURS.toMillis(slaHours);
        int within = 0;
        for (ApprovalRequest r : completed) {
            if (r.updatedAt - r.createdAt <= slaMs) within++;
        }
        float percent = completed.isEmpty() ? 0f : within * 100f / completed.size();
        return new SlaStats(completed.size(), within, percent, slaHours);
    }

    public static List<BottleneckLevel> bottleneckHeatmap(List<ApprovalRequest> requests,
                                                          List<ApprovalAction> actions) {
        Map<Long, List<ApprovalAction>> byRequest = new HashMap<>();
        for (ApprovalAction a : actions) {
            byRequest.computeIfAbsent(a.requestId, k -> new ArrayList<>()).add(a);
        }
        Map<Integer, List<Long>> waits = new HashMap<>();
        long now = System.currentTimeMillis();
        for (ApprovalRequest req : requests) {
            List<ApprovalAction> list = new ArrayList<>(byRequest.getOrDefault(req.id, Collections.emptyList()));
            list.sort((a, b) -> Long.compare(a.createdAt, b.createdAt));
            long prev = req.createdAt;
            for (ApprovalAction action : list) {
                long wait = Math.max(0, action.createdAt - prev);
                waits.computeIfAbsent(action.level, k -> new ArrayList<>()).add(wait);
                prev = action.createdAt;
            }
            if (req.status != ApprovalStatus.APPROVED && req.status != ApprovalStatus.REJECTED) {
                Integer level = null;
                if (req.status == ApprovalStatus.PENDING_L1) level = 1;
                else if (req.status == ApprovalStatus.PENDING_L2) level = 2;
                else if (req.status == ApprovalStatus.PENDING_L3) level = 3;
                if (level != null) {
                    waits.computeIfAbsent(level, k -> new ArrayList<>())
                            .add(Math.max(0, now - req.updatedAt));
                }
            }
        }
        List<BottleneckLevel> result = new ArrayList<>();
        long hourMs = TimeUnit.HOURS.toMillis(1);
        for (int level = 1; level <= 3; level++) {
            List<Long> samples = waits.getOrDefault(level, Collections.emptyList());
            double avg = 0;
            if (!samples.isEmpty()) {
                long sum = 0;
                for (Long s : samples) sum += s;
                avg = (sum / (double) samples.size()) / hourMs;
            }
            result.add(new BottleneckLevel(level, avg, samples.size()));
        }
        return result;
    }
}
