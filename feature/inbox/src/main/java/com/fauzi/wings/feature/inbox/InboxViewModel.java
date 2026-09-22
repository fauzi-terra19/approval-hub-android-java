package com.fauzi.wings.feature.inbox;
import androidx.lifecycle.*;
import com.fauzi.wings.domain.repository.ApprovalRepository;
public class InboxViewModel extends ViewModel {
    private final LiveData<InboxUiState> uiState;
    public InboxViewModel(ApprovalRepository approvalRepository) {
        uiState = Transformations.map(approvalRepository.observeInbox(), InboxUiState::new);
    }
    public LiveData<InboxUiState> getUiState() { return uiState; }
}
