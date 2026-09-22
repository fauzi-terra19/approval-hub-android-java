package com.fauzi.wings.app;

import androidx.annotation.NonNull;
import androidx.lifecycle.ViewModel;
import androidx.lifecycle.ViewModelProvider;
import androidx.lifecycle.viewmodel.CreationExtras;

import com.fauzi.wings.feature.analytics.AnalyticsViewModel;
import com.fauzi.wings.feature.audit.AuditViewModel;
import com.fauzi.wings.feature.auth.LoginViewModel;
import com.fauzi.wings.feature.dashboard.DashboardViewModel;
import com.fauzi.wings.feature.inbox.InboxViewModel;
import com.fauzi.wings.feature.request.ApprovalDetailViewModel;
import com.fauzi.wings.feature.request.CreateRequestViewModel;
import com.fauzi.wings.feature.settings.SettingsViewModel;

public class ViewModelFactory implements ViewModelProvider.Factory {
    public static final CreationExtras.Key<Long> REQUEST_ID_KEY = new CreationExtras.Key<Long>() {};

    private final AppContainer container;

    public ViewModelFactory(AppContainer container) {
        this.container = container;
    }

    @NonNull
    @Override
    @SuppressWarnings("unchecked")
    public <T extends ViewModel> T create(@NonNull Class<T> modelClass, @NonNull CreationExtras extras) {
        if (modelClass.isAssignableFrom(LoginViewModel.class)) {
            return (T) new LoginViewModel(container.repository);
        }
        if (modelClass.isAssignableFrom(DashboardViewModel.class)) {
            return (T) new DashboardViewModel(container.repository);
        }
        if (modelClass.isAssignableFrom(InboxViewModel.class)) {
            return (T) new InboxViewModel(container.repository);
        }
        if (modelClass.isAssignableFrom(CreateRequestViewModel.class)) {
            return (T) new CreateRequestViewModel(container.repository);
        }
        if (modelClass.isAssignableFrom(ApprovalDetailViewModel.class)) {
            Long id = extras.get(REQUEST_ID_KEY);
            return (T) new ApprovalDetailViewModel(
                    id == null ? 0L : id, container.repository, container.repository);
        }
        if (modelClass.isAssignableFrom(AnalyticsViewModel.class)) {
            return (T) new AnalyticsViewModel(container.repository);
        }
        if (modelClass.isAssignableFrom(AuditViewModel.class)) {
            return (T) new AuditViewModel(container.repository, container.repository);
        }
        if (modelClass.isAssignableFrom(SettingsViewModel.class)) {
            return (T) new SettingsViewModel(container.repository, container.repository);
        }
        throw new IllegalArgumentException("Unknown ViewModel: " + modelClass.getName());
    }

    @NonNull
    @Override
    @SuppressWarnings("unchecked")
    public <T extends ViewModel> T create(@NonNull Class<T> modelClass) {
        return create(modelClass, CreationExtras.Empty.INSTANCE);
    }
}
