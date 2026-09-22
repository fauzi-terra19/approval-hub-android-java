package com.fauzi.wings.feature.request;
import androidx.lifecycle.*;
import com.fauzi.wings.core.database.AppDatabase; import com.fauzi.wings.core.model.*;
import com.fauzi.wings.domain.approval.ApprovalWorkflow; import com.fauzi.wings.domain.repository.*;
import java.util.List;
public class ApprovalDetailViewModel extends ViewModel {
    private final long requestId; private final SessionRepository sessionRepository; private final ApprovalRepository approvalRepository;
    private final MutableLiveData<String> message = new MutableLiveData<>("");
    private final MediatorLiveData<ApprovalDetailUiState> uiState = new MediatorLiveData<>();
    public ApprovalDetailViewModel(long requestId, SessionRepository sessionRepository, ApprovalRepository approvalRepository) {
        this.requestId = requestId; this.sessionRepository = sessionRepository; this.approvalRepository = approvalRepository;
        LiveData<List<ApprovalAction>> actions = approvalRepository.observeActions(requestId);
        LiveData<User> session = sessionRepository.observeSession();
        LiveData<Role> imp = sessionRepository.observeImpersonateRole();
        Runnable compute = () -> {
            ApprovalRequest req = approvalRepository.getRequest(requestId);
            User user = session.getValue();
            Role role = user == null ? null : user.role;
            boolean canAct = req != null && role != null && ApprovalWorkflow.canActOn(req.status, role, imp.getValue() != null);
            boolean canEscalate = sessionRepository.hasPermission(Permission.FORCE_ESCALATE) && req != null && !ApprovalWorkflow.isTerminal(req.status);
            String detail = req == null ? "Loading…" : "#" + req.id + " " + req.title + "\n" + req.description + "\n"
                    + ApprovalWorkflow.levelLabel(req.status) + " · " + req.type + " · " + req.amount + "\n"
                    + "Dept " + req.department + " · Max L" + req.requiredMaxLevel + (req.escalated ? " · ESCALATED" : "");
            uiState.postValue(new ApprovalDetailUiState(req, actions.getValue(), canAct, canEscalate, message.getValue(), detail));
        };
        uiState.addSource(actions, v -> AppDatabase.IO.execute(compute));
        uiState.addSource(session, v -> AppDatabase.IO.execute(compute));
        uiState.addSource(imp, v -> AppDatabase.IO.execute(compute));
        uiState.addSource(message, v -> AppDatabase.IO.execute(compute));
        AppDatabase.IO.execute(compute);
    }
    public LiveData<ApprovalDetailUiState> getUiState() { return uiState; }
    public void decide(boolean approve, String comment) {
        AppDatabase.IO.execute(() -> {
            try { approvalRepository.decide(requestId, approve, comment); message.postValue("Berhasil"); }
            catch (Exception e) { message.postValue(e.getMessage() == null ? "Gagal" : e.getMessage()); }
        });
    }
    public void escalate() {
        AppDatabase.IO.execute(() -> {
            try { approvalRepository.forceEscalate(requestId); message.postValue("Escalated"); }
            catch (Exception e) { message.postValue(e.getMessage() == null ? "Gagal" : e.getMessage()); }
        });
    }
}
