package com.fauzi.wings.core.database.entity;

import androidx.room.Entity;
import androidx.room.ForeignKey;
import androidx.room.Index;
import androidx.room.PrimaryKey;

@Entity(
        tableName = "approval_actions",
        foreignKeys = {
                @ForeignKey(entity = ApprovalRequestEntity.class, parentColumns = "id",
                        childColumns = "requestId", onDelete = ForeignKey.CASCADE),
                @ForeignKey(entity = UserEntity.class, parentColumns = "id",
                        childColumns = "actorId", onDelete = ForeignKey.CASCADE)
        },
        indices = {@Index("requestId"), @Index("actorId")}
)
public class ApprovalActionEntity {
    @PrimaryKey(autoGenerate = true)
    public long id;
    public long requestId;
    public long actorId;
    public int level;
    public String decision;
    public String comment = "";
    public long createdAt;

    public ApprovalActionEntity() {}

    public ApprovalActionEntity(long requestId, long actorId, int level, String decision, String comment, long createdAt) {
        this.requestId = requestId;
        this.actorId = actorId;
        this.level = level;
        this.decision = decision;
        this.comment = comment;
        this.createdAt = createdAt;
    }
}
