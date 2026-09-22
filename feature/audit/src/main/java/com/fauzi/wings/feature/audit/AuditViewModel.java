package com.fauzi.wings.feature.audit;
import androidx.lifecycle.*;
import com.fauzi.wings.core.database.AppDatabase; import com.fauzi.wings.core.model.*;
import com.fauzi.wings.domain.repository.ApprovalRepository; import com.fauzi.wings.domain.repository.SessionRepository;
import java.util.*;
public class AuditViewModel extends ViewModel {
    private final MutableLiveData<AuditUiState> uiState = new MutableLiveData<>(new AuditUiState(null, null, null, "Loading…", false));
    public AuditViewModel(SessionRepository sessionRepository, ApprovalRepository approvalRepository) {
        AppDatabase.IO.execute(() -> {
            if (sessionRepository.getSession() == null) {
                uiState.postValue(new AuditUiState(null, null, null, "Not authorized", false));
                return;
            }
            boolean canExport = sessionRepository.hasPermission(Permission.EXPORT_AUDIT);
            List<ApprovalRequest> requests = approvalRepository.visibleRequestsSnapshot();
            List<ApprovalAction> actions = approvalRepository.visibleActionsSnapshot();
            Map<Long, String> names = approvalRepository.buildUserNameMap();
            StringBuilder text = new StringBuilder();
            int take = Math.min(30, requests.size());
            for (int i = 0; i < take; i++) {
                ApprovalRequest r = requests.get(i);
                text.append("#").append(r.id).append(" ").append(r.title).append(" [").append(r.status).append("]\n");
                for (ApprovalAction a : actions) if (a.requestId == r.id)
                    text.append("  L").append(a.level).append(" ").append(a.decision).append(" by ")
                            .append(names.getOrDefault(a.actorId, String.valueOf(a.actorId))).append(" — ").append(a.comment).append("\n");
            }
            if (take == 0) text.append("No requests in your audit scope.");
            uiState.postValue(new AuditUiState(requests, actions, names, text.toString(), canExport));
        });
    }
    public LiveData<AuditUiState> getUiState() { return uiState; }
}
