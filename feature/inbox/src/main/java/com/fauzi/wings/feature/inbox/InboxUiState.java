package com.fauzi.wings.feature.inbox;
import com.fauzi.wings.core.model.ApprovalRequest; import java.util.*;
public class InboxUiState {
    public final List<ApprovalRequest> items;
    public InboxUiState(List<ApprovalRequest> items) { this.items = items == null ? Collections.emptyList() : items; }
}
