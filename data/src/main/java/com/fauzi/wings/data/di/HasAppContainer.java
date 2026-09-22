package com.fauzi.wings.data.di;

import android.content.Context;
import androidx.lifecycle.ViewModelProvider;
import com.fauzi.wings.data.repository.AppRepository;
import java.util.concurrent.Executor;

public interface HasAppContainer {
    AppRepository getRepository();
    Executor getIoExecutor();
    ViewModelProvider.Factory getViewModelFactory();

    static HasAppContainer from(Context context) {
        Context app = context.getApplicationContext();
        if (app instanceof HasAppContainer) return (HasAppContainer) app;
        throw new IllegalStateException("Application must implement HasAppContainer");
    }
}
