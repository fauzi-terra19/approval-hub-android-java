#!/usr/bin/env python3
"""Force-stabilize conflicting files to one coherent Java MVVM stack."""
from pathlib import Path

ROOT = Path(r"D:\fauzi\cursor\wings\android")
PKG = "com.fauzi.wings"
P = PKG.replace(".", "/")


def w(rel: str, content: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    print("wrote", rel)


# --- DI ---
w(f"data/src/main/java/{P}/data/di/HasAppContainer.java", f'''
package {PKG}.data.di;

import android.content.Context;
import androidx.lifecycle.ViewModelProvider;
import {PKG}.data.repository.AppRepository;
import java.util.concurrent.Executor;

public interface HasAppContainer {{
    AppRepository getRepository();
    Executor getIoExecutor();
    ViewModelProvider.Factory getViewModelFactory();

    static HasAppContainer from(Context context) {{
        Context app = context.getApplicationContext();
        if (app instanceof HasAppContainer) return (HasAppContainer) app;
        throw new IllegalStateException("Application must implement HasAppContainer");
    }}
}}
''')

w(f"app/src/main/java/{P}/app/AppContainer.java", f'''
package {PKG}.app;

import android.content.Context;
import androidx.lifecycle.ViewModelProvider;
import {PKG}.core.database.AppDatabase;
import {PKG}.core.network.FakeRemoteApi;
import {PKG}.core.preference.UserPreferences;
import {PKG}.data.repository.AppRepository;
import {PKG}.data.sync.SyncRepository;
import java.util.concurrent.Executor;

public class AppContainer {{
    public final AppDatabase database;
    public final UserPreferences preferences;
    public final SyncRepository syncRepository;
    public final AppRepository repository;
    public final Executor ioExecutor;
    public final ViewModelProvider.Factory viewModelFactory;

    public AppContainer(Context context) {{
        Context app = context.getApplicationContext();
        database = AppDatabase.get(app);
        preferences = new UserPreferences(app);
        syncRepository = new SyncRepository(database, new FakeRemoteApi());
        repository = new AppRepository(database, preferences, syncRepository, app);
        ioExecutor = AppDatabase.IO;
        viewModelFactory = new ViewModelFactory(this);
    }}
}}
''')

w(f"app/src/main/java/{P}/app/ViewModelFactory.java", f'''
package {PKG}.app;

import androidx.annotation.NonNull;
import androidx.lifecycle.ViewModel;
import androidx.lifecycle.ViewModelProvider;
import androidx.lifecycle.viewmodel.CreationExtras;
import {PKG}.feature.analytics.AnalyticsViewModel;
import {PKG}.feature.audit.AuditViewModel;
import {PKG}.feature.auth.LoginViewModel;
import {PKG}.feature.dashboard.DashboardViewModel;
import {PKG}.feature.inbox.InboxViewModel;
import {PKG}.feature.request.ApprovalDetailViewModel;
import {PKG}.feature.request.CreateRequestViewModel;
import {PKG}.feature.settings.SettingsViewModel;

public class ViewModelFactory implements ViewModelProvider.Factory {{
    public static final CreationExtras.Key<Long> REQUEST_ID_KEY = new CreationExtras.Key<Long>() {{}};
    private final AppContainer container;

    public ViewModelFactory(AppContainer container) {{ this.container = container; }}

    @NonNull @Override @SuppressWarnings("unchecked")
    public <T extends ViewModel> T create(@NonNull Class<T> modelClass, @NonNull CreationExtras extras) {{
        if (modelClass.isAssignableFrom(LoginViewModel.class))
            return (T) new LoginViewModel(container.repository);
        if (modelClass.isAssignableFrom(DashboardViewModel.class))
            return (T) new DashboardViewModel(container.repository, container.repository);
        if (modelClass.isAssignableFrom(InboxViewModel.class))
            return (T) new InboxViewModel(container.repository);
        if (modelClass.isAssignableFrom(CreateRequestViewModel.class))
            return (T) new CreateRequestViewModel(container.repository);
        if (modelClass.isAssignableFrom(ApprovalDetailViewModel.class)) {{
            Long id = extras.get(REQUEST_ID_KEY);
            return (T) new ApprovalDetailViewModel(id == null ? 0L : id, container.repository, container.repository);
        }}
        if (modelClass.isAssignableFrom(AnalyticsViewModel.class))
            return (T) new AnalyticsViewModel(container.repository);
        if (modelClass.isAssignableFrom(AuditViewModel.class))
            return (T) new AuditViewModel(container.repository);
        if (modelClass.isAssignableFrom(SettingsViewModel.class))
            return (T) new SettingsViewModel(container.repository, container.repository);
        throw new IllegalArgumentException("Unknown ViewModel: " + modelClass.getName());
    }}

    @NonNull @Override @SuppressWarnings("unchecked")
    public <T extends ViewModel> T create(@NonNull Class<T> modelClass) {{
        return create(modelClass, CreationExtras.Empty.INSTANCE);
    }}
}}
''')

w(f"app/src/main/java/{P}/app/WingsApp.java", f'''
package {PKG}.app;

import android.app.Application;
import androidx.lifecycle.ViewModelProvider;
import {PKG}.app.work.EscalationWorker;
import {PKG}.core.notification.ApprovalNotifier;
import {PKG}.data.di.HasAppContainer;
import {PKG}.data.repository.AppRepository;
import java.util.concurrent.Executor;

public class WingsApp extends Application implements HasAppContainer {{
    private AppContainer appContainer;

    @Override public void onCreate() {{
        super.onCreate();
        appContainer = new AppContainer(this);
        ApprovalNotifier.ensureChannel(this);
        EscalationWorker.schedule(this);
    }}

    public AppContainer getAppContainer() {{ return appContainer; }}
    @Override public AppRepository getRepository() {{ return appContainer.repository; }}
    @Override public Executor getIoExecutor() {{ return appContainer.ioExecutor; }}
    @Override public ViewModelProvider.Factory getViewModelFactory() {{ return appContainer.viewModelFactory; }}
}}
''')

w(f"app/src/main/java/{P}/app/MainActivity.java", f'''
package {PKG}.app;

import android.os.Bundle;
import android.view.View;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.app.AppCompatDelegate;
import androidx.navigation.NavController;
import androidx.navigation.fragment.NavHostFragment;
import androidx.navigation.ui.NavigationUI;
import com.google.android.material.bottomnavigation.BottomNavigationView;
import {PKG}.core.database.AppDatabase;
import {PKG}.core.model.ThemeMode;
import {PKG}.core.ui.NavRoutes;

public class MainActivity extends AppCompatActivity {{
    @Override protected void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        applyTheme(((WingsApp) getApplication()).getAppContainer().preferences.getThemeMode());
        NavHostFragment navHost = (NavHostFragment) getSupportFragmentManager().findFragmentById(R.id.nav_host);
        NavController navController = navHost.getNavController();
        BottomNavigationView bottomNav = findViewById(R.id.bottomNav);
        NavigationUI.setupWithNavController(bottomNav, navController);
        navController.addOnDestinationChangedListener((c, destination, a) -> {{
            int id = destination.getId();
            boolean hide = id == R.id.loginFragment || id == R.id.createRequestFragment || id == R.id.approvalDetailFragment;
            bottomNav.setVisibility(hide ? View.GONE : View.VISIBLE);
        }});
    }}

    @Override protected void onResume() {{
        super.onResume();
        AppContainer container = ((WingsApp) getApplication()).getAppContainer();
        AppDatabase.IO.execute(() -> {{
            if (container.repository.checkSessionTimeout()) {{
                runOnUiThread(() -> {{
                    NavHostFragment navHost = (NavHostFragment) getSupportFragmentManager().findFragmentById(R.id.nav_host);
                    if (navHost != null) navHost.getNavController().navigate(NavRoutes.LOGIN);
                }});
            }}
        }});
    }}

    private void applyTheme(ThemeMode mode) {{
        if (mode == null) mode = ThemeMode.SYSTEM;
        int night;
        switch (mode) {{
            case LIGHT: night = AppCompatDelegate.MODE_NIGHT_NO; break;
            case DARK: night = AppCompatDelegate.MODE_NIGHT_YES; break;
            default: night = AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM; break;
        }}
        AppCompatDelegate.setDefaultNightMode(night);
    }}
}}
''')

# Remove duplicate di AppContainer
dup = ROOT / f"app/src/main/java/{P}/app/di/AppContainer.java"
if dup.exists():
    dup.unlink()
    print("deleted di/AppContainer.java")

# Base + NavRoutes
w(f"core/ui/src/main/java/{P}/core/ui/BaseMvvmFragment.java", f'''
package {PKG}.core.ui;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import androidx.annotation.LayoutRes;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.databinding.DataBindingUtil;
import androidx.databinding.ViewDataBinding;
import androidx.fragment.app.Fragment;
import androidx.lifecycle.LiveData;
import androidx.lifecycle.Observer;
import androidx.lifecycle.ViewModel;

public abstract class BaseMvvmFragment<VB extends ViewDataBinding, VM extends ViewModel> extends Fragment {{
    protected VB binding;
    protected VM viewModel;
    private final int layoutId;

    protected BaseMvvmFragment(@LayoutRes int layoutId) {{ this.layoutId = layoutId; }}

    @NonNull protected abstract VM createViewModel();

    protected VB getBinding() {{ return binding; }}

    protected <T> void observe(LiveData<T> liveData, Observer<T> observer) {{
        liveData.observe(getViewLifecycleOwner(), observer);
    }}

    @Nullable @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {{
        binding = DataBindingUtil.inflate(inflater, layoutId, container, false);
        binding.setLifecycleOwner(getViewLifecycleOwner());
        viewModel = createViewModel();
        return binding.getRoot();
    }}

    @Override public void onDestroyView() {{
        super.onDestroyView();
        binding = null;
    }}
}}
''')

w(f"core/ui/src/main/java/{P}/core/ui/NavRoutes.java", f'''
package {PKG}.core.ui;
import android.net.Uri;
public final class NavRoutes {{
    public static final Uri LOGIN = Uri.parse("wings://login");
    public static final Uri DASHBOARD = Uri.parse("wings://dashboard");
    public static final Uri CREATE = Uri.parse("wings://create");
    private NavRoutes() {{}}
    public static Uri detail(long requestId) {{ return Uri.parse("wings://detail/" + requestId); }}
}}
''')

# Nav graph with deep links
w("app/src/main/res/navigation/nav_graph.xml", f'''<?xml version="1.0" encoding="utf-8"?>
<navigation xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:id="@+id/nav_graph"
    app:startDestination="@id/loginFragment">
    <fragment android:id="@+id/loginFragment" android:name="{PKG}.feature.auth.LoginFragment" android:label="Login">
        <deepLink app:uri="wings://login" />
        <action android:id="@+id/action_login_to_dashboard" app:destination="@id/dashboardFragment"
            app:popUpTo="@id/loginFragment" app:popUpToInclusive="true" />
    </fragment>
    <fragment android:id="@+id/dashboardFragment" android:name="{PKG}.feature.dashboard.DashboardFragment" android:label="Dashboard">
        <deepLink app:uri="wings://dashboard" />
    </fragment>
    <fragment android:id="@+id/inboxFragment" android:name="{PKG}.feature.inbox.InboxFragment" android:label="Inbox" />
    <fragment android:id="@+id/createRequestFragment" android:name="{PKG}.feature.request.CreateRequestFragment" android:label="Create">
        <deepLink app:uri="wings://create" />
    </fragment>
    <fragment android:id="@+id/approvalDetailFragment" android:name="{PKG}.feature.request.ApprovalDetailFragment" android:label="Detail">
        <argument android:name="requestId" app:argType="long" android:defaultValue="0L" />
        <deepLink app:uri="wings://detail/{{requestId}}" />
    </fragment>
    <fragment android:id="@+id/analyticsFragment" android:name="{PKG}.feature.analytics.AnalyticsFragment" android:label="Analytics" />
    <fragment android:id="@+id/auditFragment" android:name="{PKG}.feature.audit.AuditFragment" android:label="Audit" />
    <fragment android:id="@+id/settingsFragment" android:name="{PKG}.feature.settings.SettingsFragment" android:label="Settings" />
    <action android:id="@+id/action_global_to_detail" app:destination="@id/approvalDetailFragment" />
    <action android:id="@+id/action_global_to_create" app:destination="@id/createRequestFragment" />
    <action android:id="@+id/action_global_to_login" app:destination="@id/loginFragment"
        app:popUpTo="@id/nav_graph" app:popUpToInclusive="true" />
</navigation>
''')

print("core app wiring done — writing ViewModels/Fragments next")
