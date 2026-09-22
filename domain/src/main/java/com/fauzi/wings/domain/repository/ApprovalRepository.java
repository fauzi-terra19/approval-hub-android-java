package com.fauzi.wings.domain.repository;

import com.fauzi.wings.core.model.ApprovalAction;
import com.fauzi.wings.core.model.ApprovalRequest;
import com.fauzi.wings.core.model.DashboardStats;
import com.fauzi.wings.core.model.RequestType;
import com.fauzi.wings.core.model.StatusCount;
import com.fauzi.wings.core.model.SyncMeta;
import com.fauzi.wings.core.model.TypeStat;
import com.fauzi.wings.domain.analytics.BottleneckLevel;
import com.fauzi.wings.domain.analytics.SlaStats;

import androidx.lifecycle.LiveData;

import java.util.List;
import java.util.Map;

public interface ApprovalRepository {
    LiveData<List<ApprovalRequest>> observeRequestsForCurrentUser();
    LiveData<List<ApprovalRequest>> observeInbox();
    LiveData<List<ApprovalAction>> observeActions(long requestId);
    LiveData<DashboardStats> observeDashboardStats();
    LiveData<List<StatusCount>> observeStatusCounts();
    LiveData<List<TypeStat>> observeTypeStats();
    LiveData<SyncMeta> observeSyncMeta();
    LiveData<Integer> observePendingCount();

    ApprovalRequest getRequest(long requestId);
    long createRequest(String title, String description, RequestType type, double amount) throws Exception;
    void decide(long requestId, boolean approve, String comment) throws Exception;
    void forceEscalate(long requestId) throws Exception;
    int runEscalationPass() throws Exception;
    SyncMeta syncNow() throws Exception;
    List<ApprovalRequest> allRequests();
    List<ApprovalAction> allActions();
    List<ApprovalRequest> visibleRequestsSnapshot();
    List<ApprovalAction> visibleActionsSnapshot();
    Map<Long, String> buildUserNameMap();
    SlaStats computeSla();
    List<BottleneckLevel> computeBottleneck();
}
