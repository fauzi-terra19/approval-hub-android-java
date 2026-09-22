package com.fauzi.wings.feature.settings;
import androidx.lifecycle.*;
import com.fauzi.wings.core.common.DateFormatters; import com.fauzi.wings.core.database.AppDatabase; import com.fauzi.wings.core.model.*;
import com.fauzi.wings.domain.repository.*;
public class SettingsViewModel extends ViewModel {
    private final SessionRepository sessionRepository; private final ApprovalRepository approvalRepository;
    private final MutableLiveData<String> message = new MutableLiveData<>("");
    private final MutableLiveData<Boolean> loggedOut = new MutableLiveData<>(false);
    private final MediatorLiveData<SettingsUiState> uiState = new MediatorLiveData<>();
    public SettingsViewModel(SessionRepository sessionRepository, ApprovalRepository approvalRepository) {
        this.sessionRepository = sessionRepository; this.approvalRepository = approvalRepository;
        LiveData<User> session = sessionRepository.observeSession();
        LiveData<Role> imp = sessionRepository.observeImpersonateRole();
        LiveData<SyncMeta> meta = approvalRepository.observeSyncMeta();
        Runnable compute = () -> {
            SyncMeta m = meta.getValue();
            String syncInfo = m == null ? "No sync meta" : "Last sync: " + (m.lastSyncedAt == 0L ? "never" : DateFormatters.full(m.lastSyncedAt))
                    + " · " + m.lastSyncStatus + " · pending " + m.pendingPushCount;
            uiState.setValue(new SettingsUiState(session.getValue(), imp.getValue(), syncInfo, message.getValue(),
                    Boolean.TRUE.equals(loggedOut.getValue()), sessionRepository.hasPermission(Permission.FORCE_ESCALATE)));
        };
        uiState.addSource(session, v -> compute.run()); uiState.addSource(imp, v -> compute.run());
        uiState.addSource(meta, v -> compute.run()); uiState.addSource(message, v -> compute.run()); uiState.addSource(loggedOut, v -> compute.run());
    }
    public LiveData<SettingsUiState> getUiState() { return uiState; }
    public void setTheme(ThemeMode mode) { sessionRepository.setThemeMode(mode); }
    public void setImpersonate(Role role) { sessionRepository.setImpersonateRole(role); }
    public void sync() { AppDatabase.IO.execute(() -> { try { approvalRepository.syncNow(); message.postValue("Sync OK"); } catch (Exception e) { message.postValue(e.getMessage() == null ? "Sync failed" : e.getMessage()); } }); }
    public void runEscalation() {
        AppDatabase.IO.execute(() -> {
            try { message.postValue("Escalated " + approvalRepository.runEscalationPass() + " request(s)"); }
            catch (Exception e) { message.postValue(e.getMessage() == null ? "Escalation failed" : e.getMessage()); }
        });
    }
    public void logout() { AppDatabase.IO.execute(() -> { sessionRepository.logoutAndClear(); loggedOut.postValue(true); }); }
}
