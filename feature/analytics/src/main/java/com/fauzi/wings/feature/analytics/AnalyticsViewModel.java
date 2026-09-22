package com.fauzi.wings.feature.analytics;
import androidx.lifecycle.*;
import com.fauzi.wings.core.database.AppDatabase; import com.fauzi.wings.core.model.*;
import com.fauzi.wings.domain.analytics.*; import com.fauzi.wings.domain.repository.ApprovalRepository;
import java.util.*;
public class AnalyticsViewModel extends ViewModel {
    private final MutableLiveData<SlaStats> sla = new MutableLiveData<>();
    private final MutableLiveData<List<BottleneckLevel>> bn = new MutableLiveData<>();
    private final MediatorLiveData<AnalyticsUiState> uiState = new MediatorLiveData<>();
    public AnalyticsViewModel(ApprovalRepository approvalRepository) {
        AppDatabase.IO.execute(() -> { sla.postValue(approvalRepository.computeSla()); bn.postValue(approvalRepository.computeBottleneck()); });
        LiveData<List<StatusCount>> status = approvalRepository.observeStatusCounts();
        LiveData<List<TypeStat>> types = approvalRepository.observeTypeStats();
        Runnable compute = () -> {
            StringBuilder text = new StringBuilder("Status counts:\n");
            List<StatusCount> s = status.getValue(); List<TypeStat> t = types.getValue();
            if (s != null) for (StatusCount sc : s) text.append(" · ").append(sc.status).append(": ").append(sc.count).append("\n");
            text.append("\nBy type:\n");
            if (t != null) for (TypeStat ts : t) text.append(" · ").append(ts.type).append(": ").append(ts.count).append(" (sum ").append(ts.totalAmount).append(")\n");
            SlaStats slaVal = sla.getValue();
            if (slaVal != null) text.append("\nSLA ").append(slaVal.slaHours).append("h: ").append(slaVal.withinSlaCount).append("/").append(slaVal.completedCount)
                    .append(String.format(Locale.US, " (%.1f%%)\n", slaVal.withinSlaPercent));
            text.append("\nBottleneck:\n");
            List<BottleneckLevel> bnVal = bn.getValue();
            if (bnVal != null) for (BottleneckLevel b : bnVal) text.append(String.format(Locale.US, " · L%d: %.1fh (n=%d)\n", b.level, b.avgWaitHours, b.sampleCount));
            uiState.postValue(new AnalyticsUiState(s, text.toString()));
        };
        uiState.addSource(status, v -> compute.run()); uiState.addSource(types, v -> compute.run());
        uiState.addSource(sla, v -> compute.run()); uiState.addSource(bn, v -> compute.run());
    }
    public LiveData<AnalyticsUiState> getUiState() { return uiState; }
    public List<String> chartLabels() { List<String> out = new ArrayList<>(); AnalyticsUiState s = uiState.getValue(); if (s != null) for (StatusCount c : s.statusCounts) out.add(c.status.name()); return out; }
    public List<Float> chartValues() { List<Float> out = new ArrayList<>(); AnalyticsUiState s = uiState.getValue(); if (s != null) for (StatusCount c : s.statusCounts) out.add((float) c.count); return out; }
}
