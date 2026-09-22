package com.fauzi.wings.core.model;

public class StatusCount {
    public final ApprovalStatus status;
    public final int count;

    public StatusCount(ApprovalStatus status, int count) {
        this.status = status;
        this.count = count;
    }
}
