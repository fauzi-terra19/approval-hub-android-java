package com.fauzi.wings.feature.dashboard;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MediatorLiveData;
import androidx.lifecycle.ViewModel;

import com.fauzi.wings.core.model.ApprovalRequest;
import com.fauzi.wings.core.model.DashboardStats;
import com.fauzi.wings.core.model.RequestFilter;
import com.fauzi.wings.core.model.Role;
import com.fauzi.wings.core.model.User;
import com.fauzi.wings.data.repository.AppRepository;
import com.fauzi.wings.domain.rbac.RbacPolicy;

import java.util.List;

public class DashboardViewModel extends ViewModel {
    private final AppRepository appRepository;
    private final MediatorLiveData<DashboardUiState> uiState =
            new MediatorLiveData<>(DashboardUiState.empty());

    public DashboardViewModel(AppRepository repository) {
        this.appRepository = repository;
        LiveData<User> session = repository.observeSession();
        LiveData<Role> imp = repository.observeImpersonateRole();
        LiveData<DashboardStats> stats = repository.observeDashboardStats();
        LiveData<List<ApprovalRequest>> requests = repository.observeRequestsForCurrentUser();
        Runnable compute = () -> {
            User user = session.getValue();
            Role role = imp.getValue() != null ? imp.getValue() : (user == null ? null : user.role);
            String title = role == null ? "Dashboard" : RbacPolicy.dashboardTitle(role);
            uiState.setValue(new DashboardUiState(user, title, stats.getValue(), requests.getValue()));
        };
        uiState.addSource(session, v -> compute.run());
        uiState.addSource(imp, v -> compute.run());
        uiState.addSource(stats, v -> compute.run());
        uiState.addSource(requests, v -> compute.run());
    }

    public LiveData<DashboardUiState> getUiState() {
        return uiState;
    }

    public void setFilterQuery(String query) {
        RequestFilter f = new RequestFilter();
        f.query = query;
        appRepository.updateFilter(f);
    }
}
