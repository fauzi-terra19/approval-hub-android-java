package com.fauzi.wings.feature.audit;
import com.fauzi.wings.core.model.*; import java.util.*;
public class AuditUiState {
    public final List<ApprovalRequest> requests; public final List<ApprovalAction> actions;
    public final Map<Long, String> names; public final String content; public final boolean canExport;
    public AuditUiState(List<ApprovalRequest> requests, List<ApprovalAction> actions, Map<Long, String> names, String content, boolean canExport) {
        this.requests = requests == null ? Collections.emptyList() : requests;
        this.actions = actions == null ? Collections.emptyList() : actions;
        this.names = names == null ? Collections.emptyMap() : names;
        this.content = content == null ? "" : content;
        this.canExport = canExport;
    }
}
