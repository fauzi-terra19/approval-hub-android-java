package com.fauzi.wings.feature.request;
public class CreateRequestUiState {
    public final String ruleHint; public final String error; public final Long createdId; public final boolean loading;
    public CreateRequestUiState(String ruleHint, String error, Long createdId, boolean loading) {
        this.ruleHint = ruleHint == null ? "" : ruleHint; this.error = error; this.createdId = createdId; this.loading = loading;
    }
}
