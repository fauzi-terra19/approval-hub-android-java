package com.fauzi.wings.app;

import android.content.Context;
import androidx.lifecycle.ViewModelProvider;
import com.fauzi.wings.core.database.AppDatabase;
import com.fauzi.wings.core.network.FakeRemoteApi;
import com.fauzi.wings.core.preference.UserPreferences;
import com.fauzi.wings.data.repository.AppRepository;
import com.fauzi.wings.data.sync.SyncRepository;
import java.util.concurrent.Executor;

public class AppContainer {
    public final AppDatabase database;
    public final UserPreferences preferences;
    public final SyncRepository syncRepository;
    public final AppRepository repository;
    public final Executor ioExecutor;
    public final ViewModelProvider.Factory viewModelFactory;

    public AppContainer(Context context) {
        Context app = context.getApplicationContext();
        database = AppDatabase.get(app);
        preferences = new UserPreferences(app);
        syncRepository = new SyncRepository(database, new FakeRemoteApi());
        repository = new AppRepository(database, preferences, syncRepository, app);
        ioExecutor = AppDatabase.IO;
        viewModelFactory = new ViewModelFactory(this);
    }
}
