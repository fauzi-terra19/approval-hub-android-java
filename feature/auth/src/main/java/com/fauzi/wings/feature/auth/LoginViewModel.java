package com.fauzi.wings.feature.auth;
import androidx.lifecycle.LiveData; import androidx.lifecycle.MutableLiveData; import androidx.lifecycle.ViewModel;
import com.fauzi.wings.core.database.AppDatabase; import com.fauzi.wings.core.model.User; import com.fauzi.wings.domain.repository.SessionRepository;
public class LoginViewModel extends ViewModel {
    private final SessionRepository sessionRepository;
    private final MutableLiveData<LoginUiState> uiState = new MutableLiveData<>(LoginUiState.initial());
    public LoginViewModel(SessionRepository sessionRepository) {
        this.sessionRepository = sessionRepository;
        AppDatabase.IO.execute(() -> {
            sessionRepository.ensureSeeded();
            User restored = sessionRepository.restoreSession();
            if (restored != null) {
                LoginUiState cur = uiState.getValue();
                uiState.postValue(new LoginUiState(false, null, restored, cur.demoHint));
            }
        });
    }
    public LiveData<LoginUiState> getUiState() { return uiState; }
    public void login(String username, String password) {
        LoginUiState cur = uiState.getValue();
        uiState.setValue(new LoginUiState(true, null, null, cur.demoHint));
        AppDatabase.IO.execute(() -> {
            try {
                User user = sessionRepository.login(username, password);
                uiState.postValue(new LoginUiState(false, null, user, cur.demoHint));
            } catch (Exception e) {
                uiState.postValue(new LoginUiState(false, e.getMessage(), null, cur.demoHint));
            }
        });
    }
}
