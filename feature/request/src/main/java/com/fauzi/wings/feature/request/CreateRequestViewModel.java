package com.fauzi.wings.feature.request;
import androidx.lifecycle.*;
import com.fauzi.wings.core.database.AppDatabase; import com.fauzi.wings.core.model.RequestType;
import com.fauzi.wings.domain.approval.AmountBasedRules; import com.fauzi.wings.domain.repository.ApprovalRepository;
public class CreateRequestViewModel extends ViewModel {
    private final ApprovalRepository approvalRepository;
    private final MutableLiveData<CreateRequestUiState> uiState = new MutableLiveData<>(new CreateRequestUiState("", null, null, false));
    public CreateRequestViewModel(ApprovalRepository approvalRepository) { this.approvalRepository = approvalRepository; }
    public LiveData<CreateRequestUiState> getUiState() { return uiState; }
    public void updateHint(RequestType type, double amount) {
        uiState.setValue(new CreateRequestUiState(AmountBasedRules.ruleLabel(type, amount), null, null, false));
    }
    public void submit(String title, String description, RequestType type, double amount) {
        uiState.setValue(new CreateRequestUiState(AmountBasedRules.ruleLabel(type, amount), null, null, true));
        AppDatabase.IO.execute(() -> {
            try {
                long id = approvalRepository.createRequest(title, description, type, amount);
                uiState.postValue(new CreateRequestUiState(AmountBasedRules.ruleLabel(type, amount), null, id, false));
            } catch (Exception e) {
                uiState.postValue(new CreateRequestUiState(AmountBasedRules.ruleLabel(type, amount), e.getMessage(), null, false));
            }
        });
    }
}
