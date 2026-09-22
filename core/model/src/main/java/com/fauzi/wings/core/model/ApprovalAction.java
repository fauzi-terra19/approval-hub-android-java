package com.fauzi.wings.core.model;

public class ApprovalAction {
    public final long id;
    public final long requestId;
    public final long actorId;
    public final int level;
    public final String decision;
    public final String comment;
    public final long createdAt;

    public ApprovalAction(long id, long requestId, long actorId, int level,
                          String decision, String comment, long createdAt) {
        this.id = id;
        this.requestId = requestId;
        this.actorId = actorId;
        this.level = level;
        this.decision = decision;
        this.comment = comment;
        this.createdAt = createdAt;
    }
}
