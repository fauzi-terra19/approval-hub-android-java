package com.fauzi.wings.domain.analytics;

public class SlaStats {
    public final int completedCount;
    public final int withinSlaCount;
    public final float withinSlaPercent;
    public final long slaHours;

    public SlaStats(int completedCount, int withinSlaCount, float withinSlaPercent, long slaHours) {
        this.completedCount = completedCount;
        this.withinSlaCount = withinSlaCount;
        this.withinSlaPercent = withinSlaPercent;
        this.slaHours = slaHours;
    }
}
