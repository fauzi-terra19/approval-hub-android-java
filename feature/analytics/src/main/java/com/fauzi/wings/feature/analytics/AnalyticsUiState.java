package com.fauzi.wings.feature.analytics;
import com.fauzi.wings.core.model.StatusCount; import java.util.*;
public class AnalyticsUiState {
    public final List<StatusCount> statusCounts; public final String content;
    public AnalyticsUiState(List<StatusCount> statusCounts, String content) {
        this.statusCounts = statusCounts == null ? Collections.emptyList() : statusCounts;
        this.content = content == null ? "" : content;
    }
}
