package com.fauzi.wings.feature.request;
import com.fauzi.wings.core.model.*; import java.util.*;
public class ApprovalDetailUiState {
    public final ApprovalRequest request; public final List<ApprovalAction> actions;
    public final boolean canAct; public final boolean canEscalate; public final String message; public final String detailText;
    public ApprovalDetailUiState(ApprovalRequest request, List<ApprovalAction> actions, boolean canAct, boolean canEscalate, String message, String detailText) {
        this.request = request; this.actions = actions == null ? Collections.emptyList() : actions;
        this.canAct = canAct; this.canEscalate = canEscalate;
        this.message = message == null ? "" : message; this.detailText = detailText == null ? "" : detailText;
    }
}
