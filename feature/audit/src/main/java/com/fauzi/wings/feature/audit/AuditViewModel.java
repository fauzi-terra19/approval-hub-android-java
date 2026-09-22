package com.fauzi.wings.feature.audit;
import androidx.lifecycle.*;
import com.fauzi.wings.core.database.AppDatabase; import com.fauzi.wings.core.model.*;
import com.fauzi.wings.domain.repository.ApprovalRepository; import com.fauzi.wings.domain.repository.SessionRepository;
import java.util.*; import java.util.concurrent.atomic.AtomicInteger;
public class AuditViewModel extends ViewModel {
    private final SessionRepository sessionRepository;
    private final ApprovalRepository approvalRepository;
    private final MediatorLiveData<AuditUiState> uiState = new MediatorLiveData<>();
    private final AtomicInteger generation = new AtomicInteger();
    public AuditViewModel(SessionRepository sessionRepository, ApprovalRepository approvalRepository) {
        this.sessionRepository = sessionRepository;
        this.approvalRepository = approvalRepository;
        uiState.setValue(new AuditUiState(null, null, null, "Loading…", false));
        uiState.addSource(sessionRepository.observeSession(), v -> reload(true));
        uiState.addSource(sessionRepository.observeImpersonateRole(), v -> reload(true));
        uiState.addSource(approvalRepository.observeRequestsForCurrentUser(), v -> reload(false));
    }
    private void reload(boolean clearPrivilegedState) {
        final int gen = generation.incrementAndGet();
        if (clearPrivilegedState) {
            uiState.setValue(new AuditUiState(null, null, null, "Loading…", false));
        }
        AppDatabase.IO.execute(() -> {
            if (gen != generation.get()) return;
            if (sessionRepository.getSession() == null) {
                if (gen == generation.get()) {
                    uiState.postValue(new AuditUiState(null, null, null, "Not authorized", false));
                }
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
            if (gen != generation.get()) return;
            uiState.postValue(new AuditUiState(requests, actions, names, text.toString(), canExport));
        });
    }
    public LiveData<AuditUiState> getUiState() { return uiState; }
}
