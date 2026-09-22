package com.fauzi.wings.app;

import android.app.Application;
import androidx.lifecycle.ViewModelProvider;
import com.fauzi.wings.app.work.EscalationWorker;
import com.fauzi.wings.core.notification.ApprovalNotifier;
import com.fauzi.wings.data.di.HasAppContainer;
import com.fauzi.wings.data.repository.AppRepository;
import java.util.concurrent.Executor;

public class WingsApp extends Application implements HasAppContainer {
    private AppContainer appContainer;

    @Override public void onCreate() {
        super.onCreate();
        appContainer = new AppContainer(this);
        ApprovalNotifier.ensureChannel(this);
        EscalationWorker.schedule(this);
    }

    public AppContainer getAppContainer() { return appContainer; }
    @Override public AppRepository getRepository() { return appContainer.repository; }
    @Override public Executor getIoExecutor() { return appContainer.ioExecutor; }
    @Override public ViewModelProvider.Factory getViewModelFactory() { return appContainer.viewModelFactory; }
}
