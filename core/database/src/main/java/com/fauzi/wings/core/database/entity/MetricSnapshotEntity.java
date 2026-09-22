package com.fauzi.wings.core.database.entity;

import androidx.room.Entity;
import androidx.room.PrimaryKey;

@Entity(tableName = "metric_snapshots")
public class MetricSnapshotEntity {
    @PrimaryKey(autoGenerate = true)
    public long id;
    public String label;
    public String category;
    public double value;
    public long recordedAt;

    public MetricSnapshotEntity() {}

    public MetricSnapshotEntity(String label, String category, double value, long recordedAt) {
        this.label = label;
        this.category = category;
        this.value = value;
        this.recordedAt = recordedAt;
    }
}
