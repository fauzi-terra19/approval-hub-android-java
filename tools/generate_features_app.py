#!/usr/bin/env python3
"""Feature modules + app module generator (Java MVVM)."""
from __future__ import annotations

from generate_all import PKG, P, w, empty_consumer, empty_manifest, lib_build


def feature_deps(extra=None):
    deps = [
        'api(project(":core:ui"))',
        'api(project(":domain"))',
        'implementation(project(":data"))',
        "implementation(libs.androidx.lifecycle.livedata)",
        "implementation(libs.androidx.lifecycle.viewmodel)",
        "implementation(libs.androidx.lifecycle.common.java8)",
        "implementation(libs.material)",
        "implementation(libs.androidx.swiperefresh)",
    ]
    if extra:
        deps.extend(extra)
    return deps


def gen_features():
    _auth()
    _dashboard()
    _inbox()
    _request()
    _analytics()
    _audit()
    _settings()
    _widget()


def _vm_helper():
    """Shared snippet: resolve AppContainer from Application."""
    return f'''
    private {PKG}.data.di.AppContainer container() {{
        return (({PKG}.data.di.AppContainerHolder) requireActivity().getApplication()).getAppContainer();
    }}
'''


def _auth():
    empty_consumer("feature/auth")
    w("feature/auth/build.gradle.kts", lib_build(f"{PKG}.feature.auth", feature_deps(), True))
    w("feature/auth/src/main/AndroidManifest.xml", empty_manifest(f"{PKG}.feature.auth"))
    w("feature/auth/src/main/res/layout/fragment_login.xml", '''<?xml version="1.0" encoding="utf-8"?>
<ScrollView xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:fillViewport="true" android:background="@color/ah_bg">
    <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
        android:orientation="vertical" android:padding="24dp" android:gravity="center_horizontal">
        <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="ApprovalHub" android:textSize="28sp" android:textStyle="bold"
            android:textColor="@color/ah_primary" android:layout_marginTop="48dp" />
        <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
            android:text="Multi-level approval · Wings" android:textColor="@color/ah_muted"
            android:layout_marginBottom="32dp" />
        <com.google.android.material.textfield.TextInputLayout
            android:layout_width="match_parent" android:layout_height="wrap_content"
            android:hint="Username">
            <com.google.android.material.textfield.TextInputEditText
                android:id="@+id/inputUsername" android:layout_width="match_parent"
                android:layout_height="wrap_content" android:inputType="text" />
        </com.google.android.material.textfield.TextInputLayout>
        <com.google.android.material.textfield.TextInputLayout
            android:layout_width="match_parent" android:layout_height="wrap_content"
            android:hint="Password" android:layout_marginTop="12dp">
            <com.google.android.material.textfield.TextInputEditText
                android:id="@+id/inputPassword" android:layout_width="match_parent"
                android:layout_height="wrap_content" android:inputType="textPassword" />
        </com.google.android.material.textfield.TextInputLayout>
        <TextView android:id="@+id/textError" android:layout_width="match_parent"
            android:layout_height="wrap_content" android:textColor="@color/ah_danger"
            android:visibility="gone" android:layout_marginTop="8dp" />
        <com.google.android.material.button.MaterialButton
            android:id="@+id/btnLogin" android:layout_width="match_parent"
            android:layout_height="wrap_content" android:text="Login"
            android:layout_marginTop="20dp" />
        <ProgressBar android:id="@+id/progress" android:layout_width="wrap_content"
            android:layout_height="wrap_content" android:visibility="gone"
            android:layout_marginTop="16dp" />
        <TextView android:id="@+id/textDemoAccounts" android:layout_width="match_parent"
            android:layout_height="wrap_content" android:layout_marginTop="24dp"
            android:textSize="12sp" android:textColor="@color/ah_muted" />
    </LinearLayout>
</ScrollView>
''')
    base = f"feature/auth/src/main/java/{P}/feature/auth"
    w(f"{base}/LoginUiState.java", f'''
package {PKG}.feature.auth;

import {PKG}.core.model.DemoAccounts;
import {PKG}.core.model.User;

public class LoginUiState {{
    public final boolean loading;
    public final String error;
    public final User loggedInUser;
    public final String demoHint;

    public LoginUiState(boolean loading, String error, User loggedInUser, String demoHint) {{
        this.loading = loading;
        this.error = error;
        this.loggedInUser = loggedInUser;
        this.demoHint = demoHint;
    }}

    public static LoginUiState initial() {{
        StringBuilder sb = new StringBuilder();
        for (DemoAccounts.Demo d : DemoAccounts.ALL) {{
            if (sb.length() > 0) sb.append("\\n");
            sb.append(d.username).append(" / ").append(d.password).append(" · ").append(d.roleLabel);
        }}
        return new LoginUiState(false, null, null, sb.toString());
    }}

    public LoginUiState copy(Boolean loading, String error, User loggedInUser) {{
        return new LoginUiState(
                loading != null ? loading : this.loading,
                error,
                loggedInUser != null ? loggedInUser : this.loggedInUser,
                this.demoHint);
    }}
}}
''')
    w(f"{base}/LoginViewModel.java", f'''
package {PKG}.feature.auth;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;

import {PKG}.core.database.AppDatabase;
import {PKG}.core.model.User;
import {PKG}.domain.repository.SessionRepository;

public class LoginViewModel extends ViewModel {{
    private final SessionRepository sessionRepository;
    private final MutableLiveData<LoginUiState> uiState = new MutableLiveData<>(LoginUiState.initial());

    public LoginViewModel(SessionRepository sessionRepository) {{
        this.sessionRepository = sessionRepository;
        AppDatabase.IO.execute(() -> {{
            sessionRepository.ensureSeeded();
            User restored = sessionRepository.restoreSession();
            if (restored != null) {{
                LoginUiState cur = uiState.getValue();
                uiState.postValue(cur.copy(false, null, restored));
            }}
        }});
    }}

    public LiveData<LoginUiState> getUiState() {{ return uiState; }}

    public void login(String username, String password) {{
        LoginUiState cur = uiState.getValue();
        uiState.setValue(new LoginUiState(true, null, null, cur.demoHint));
        AppDatabase.IO.execute(() -> {{
            try {{
                User user = sessionRepository.login(username, password);
                uiState.postValue(new LoginUiState(false, null, user, cur.demoHint));
            }} catch (Exception e) {{
                uiState.postValue(new LoginUiState(false, e.getMessage(), null, cur.demoHint));
            }}
        }});
    }}
}}
''')
    w(f"{base}/LoginFragment.java", f'''
package {PKG}.feature.auth;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.ProgressBar;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.lifecycle.ViewModelProvider;
import androidx.navigation.NavOptions;
import androidx.navigation.Navigation;

import com.google.android.material.textfield.TextInputEditText;

import {PKG}.core.ui.NavRoutes;
import {PKG}.data.di.AppContainerHolder;

public class LoginFragment extends Fragment {{
    private LoginViewModel viewModel;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {{
        return inflater.inflate(R.layout.fragment_login, container, false);
    }}

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        viewModel = new ViewModelProvider(this,
                ((AppContainerHolder) requireActivity().getApplication()).getAppContainer().factory)
                .get(LoginViewModel.class);

        TextInputEditText inputUsername = view.findViewById(R.id.inputUsername);
        TextInputEditText inputPassword = view.findViewById(R.id.inputPassword);
        Button btnLogin = view.findViewById(R.id.btnLogin);
        TextView textError = view.findViewById(R.id.textError);
        ProgressBar progress = view.findViewById(R.id.progress);
        TextView textDemo = view.findViewById(R.id.textDemoAccounts);

        btnLogin.setOnClickListener(v -> viewModel.login(
                inputUsername.getText() == null ? "" : inputUsername.getText().toString(),
                inputPassword.getText() == null ? "" : inputPassword.getText().toString()));

        viewModel.getUiState().observe(getViewLifecycleOwner(), state -> {{
            textDemo.setText(state.demoHint);
            progress.setVisibility(state.loading ? View.VISIBLE : View.GONE);
            btnLogin.setEnabled(!state.loading);
            if (state.error != null) {{
                textError.setVisibility(View.VISIBLE);
                textError.setText(state.error);
            }} else {{
                textError.setVisibility(View.GONE);
            }}
            if (state.loggedInUser != null) {{
                NavOptions opts = new NavOptions.Builder()
                        .setPopUpTo(R.id.loginFragment, true)
                        .build();
                // Prefer deep link so we don't rely on app R ids from this module
                try {{
                    Navigation.findNavController(view).navigate(NavRoutes.DASHBOARD);
                }} catch (Exception e) {{
                    Navigation.findNavController(view).navigate(NavRoutes.DASHBOARD, null, opts);
                }}
            }}
        }});
    }}
}}
''')
    # Fix LoginFragment - loginFragment R.id won't exist in feature module. Use only deep link.
    w(f"{base}/LoginFragment.java", f'''
package {PKG}.feature.auth;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.ProgressBar;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.lifecycle.ViewModelProvider;
import androidx.navigation.NavOptions;
import androidx.navigation.Navigation;

import com.google.android.material.textfield.TextInputEditText;

import {PKG}.core.ui.NavRoutes;
import {PKG}.data.di.AppContainerHolder;

public class LoginFragment extends Fragment {{
    private LoginViewModel viewModel;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {{
        return inflater.inflate(R.layout.fragment_login, container, false);
    }}

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        viewModel = new ViewModelProvider(this,
                ((AppContainerHolder) requireActivity().getApplication()).getAppContainer().factory)
                .get(LoginViewModel.class);

        // findViewById as required for LoginFragment
        TextInputEditText inputUsername = view.findViewById(R.id.inputUsername);
        TextInputEditText inputPassword = view.findViewById(R.id.inputPassword);
        Button btnLogin = view.findViewById(R.id.btnLogin);
        TextView textError = view.findViewById(R.id.textError);
        ProgressBar progress = view.findViewById(R.id.progress);
        TextView textDemo = view.findViewById(R.id.textDemoAccounts);

        btnLogin.setOnClickListener(v -> viewModel.login(
                inputUsername.getText() == null ? "" : inputUsername.getText().toString(),
                inputPassword.getText() == null ? "" : inputPassword.getText().toString()));

        viewModel.getUiState().observe(getViewLifecycleOwner(), state -> {{
            textDemo.setText(state.demoHint);
            progress.setVisibility(state.loading ? View.VISIBLE : View.GONE);
            btnLogin.setEnabled(!state.loading);
            if (state.error != null) {{
                textError.setVisibility(View.VISIBLE);
                textError.setText(state.error);
            }} else {{
                textError.setVisibility(View.GONE);
            }}
            if (state.loggedInUser != null) {{
                NavOptions opts = new NavOptions.Builder().setLaunchSingleTop(true).build();
                Navigation.findNavController(view).navigate(NavRoutes.DASHBOARD, opts);
            }}
        }});
    }}
}}
''')


def _simple_feature(name, class_prefix, title, layout_extra="", has_list=True):
    pass


def _dashboard():
    empty_consumer("feature/dashboard")
    w("feature/dashboard/build.gradle.kts", lib_build(f"{PKG}.feature.dashboard", feature_deps(), True))
    w("feature/dashboard/src/main/AndroidManifest.xml", empty_manifest(f"{PKG}.feature.dashboard"))
    w("feature/dashboard/src/main/res/layout/fragment_dashboard.xml", '''<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android">
    <data>
        <variable name="title" type="String" />
        <variable name="stats" type="String" />
        <variable name="userLine" type="String" />
    </data>
    <LinearLayout android:layout_width="match_parent" android:layout_height="match_parent"
        android:orientation="vertical" android:background="@color/ah_bg">
        <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
            android:padding="16dp" android:text="@{title}" android:textSize="20sp"
            android:textStyle="bold" android:textColor="@color/ah_primary"
            android:background="@color/ah_surface" />
        <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
            android:paddingHorizontal="16dp" android:paddingBottom="8dp"
            android:text="@{userLine}" android:textColor="@color/ah_muted" android:background="@color/ah_surface" />
        <com.google.android.material.textfield.TextInputLayout android:layout_width="match_parent"
            android:layout_height="wrap_content" android:hint="Filter query" android:layout_margin="12dp">
            <com.google.android.material.textfield.TextInputEditText android:id="@+id/inputFilter"
                android:layout_width="match_parent" android:layout_height="wrap_content" />
        </com.google.android.material.textfield.TextInputLayout>
        <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
            android:padding="16dp" android:text="@{stats}" android:textSize="14sp" />
        <androidx.recyclerview.widget.RecyclerView
            android:id="@+id/recycler" android:layout_width="match_parent"
            android:layout_height="0dp" android:layout_weight="1" />
        <com.google.android.material.button.MaterialButton
            android:id="@+id/btnCreate" android:layout_width="match_parent"
            android:layout_height="wrap_content" android:text="Buat Request"
            android:layout_margin="12dp" />
    </LinearLayout>
</layout>
''')
    base = f"feature/dashboard/src/main/java/{P}/feature/dashboard"
    w(f"{base}/DashboardUiState.java", f'''
package {PKG}.feature.dashboard;

import {PKG}.core.model.ApprovalRequest;
import {PKG}.core.model.DashboardStats;
import {PKG}.core.model.User;

import java.util.Collections;
import java.util.List;

public class DashboardUiState {{
    public final User user;
    public final String title;
    public final DashboardStats stats;
    public final List<ApprovalRequest> requests;

    public DashboardUiState(User user, String title, DashboardStats stats, List<ApprovalRequest> requests) {{
        this.user = user;
        this.title = title;
        this.stats = stats == null ? new DashboardStats() : stats;
        this.requests = requests == null ? Collections.emptyList() : requests;
    }}
}}
''')
    w(f"{base}/DashboardViewModel.java", f'''
package {PKG}.feature.dashboard;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MediatorLiveData;
import androidx.lifecycle.ViewModel;

import {PKG}.core.model.ApprovalRequest;
import {PKG}.core.model.DashboardStats;
import {PKG}.core.model.RequestFilter;
import {PKG}.core.model.Role;
import {PKG}.core.model.User;
import {PKG}.data.repository.AppRepository;
import {PKG}.domain.rbac.RbacPolicy;
import {PKG}.domain.repository.ApprovalRepository;
import {PKG}.domain.repository.SessionRepository;

import java.util.List;

public class DashboardViewModel extends ViewModel {{
    private final SessionRepository sessionRepository;
    private final ApprovalRepository approvalRepository;
    private final AppRepository appRepository;
    private final MediatorLiveData<DashboardUiState> uiState = new MediatorLiveData<>();

    public DashboardViewModel(SessionRepository sessionRepository, ApprovalRepository approvalRepository) {{
        this.sessionRepository = sessionRepository;
        this.approvalRepository = approvalRepository;
        this.appRepository = (AppRepository) approvalRepository;
        LiveData<User> session = sessionRepository.observeSession();
        LiveData<Role> imp = sessionRepository.observeImpersonateRole();
        LiveData<DashboardStats> stats = approvalRepository.observeDashboardStats();
        LiveData<List<ApprovalRequest>> requests = approvalRepository.observeRequestsForCurrentUser();
        Runnable compute = () -> {{
            User user = session.getValue();
            Role role = imp.getValue() != null ? imp.getValue() : (user == null ? null : user.role);
            String title = role == null ? "Dashboard" : RbacPolicy.dashboardTitle(role);
            uiState.setValue(new DashboardUiState(user, title, stats.getValue(), requests.getValue()));
        }};
        uiState.addSource(session, v -> compute.run());
        uiState.addSource(imp, v -> compute.run());
        uiState.addSource(stats, v -> compute.run());
        uiState.addSource(requests, v -> compute.run());
    }}

    public LiveData<DashboardUiState> getUiState() {{ return uiState; }}

    public void setFilterQuery(String query) {{
        RequestFilter f = new RequestFilter();
        f.query = query;
        appRepository.updateFilter(f);
    }}
}}
''')
    w(f"{base}/DashboardFragment.java", f'''
package {PKG}.feature.dashboard;

import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.View;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.lifecycle.ViewModelProvider;
import androidx.navigation.Navigation;
import androidx.recyclerview.widget.LinearLayoutManager;

import {PKG}.core.ui.BaseMvvmFragment;
import {PKG}.core.ui.NavRoutes;
import {PKG}.core.ui.RequestListAdapter;
import {PKG}.data.di.AppContainerHolder;
import {PKG}.feature.dashboard.databinding.FragmentDashboardBinding;

public class DashboardFragment extends BaseMvvmFragment<FragmentDashboardBinding, DashboardViewModel> {{
    private RequestListAdapter adapter;

    public DashboardFragment() {{
        super(R.layout.fragment_dashboard);
    }}

    @NonNull
    @Override
    protected DashboardViewModel createViewModel() {{
        return new ViewModelProvider(this,
                ((AppContainerHolder) requireActivity().getApplication()).getAppContainer().factory)
                .get(DashboardViewModel.class);
    }}

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        adapter = new RequestListAdapter(req ->
                Navigation.findNavController(view).navigate(NavRoutes.detail(req.id)));
        binding.recycler.setLayoutManager(new LinearLayoutManager(requireContext()));
        binding.recycler.setAdapter(adapter);
        binding.btnCreate.setOnClickListener(v ->
                Navigation.findNavController(view).navigate(NavRoutes.CREATE));
        binding.inputFilter.addTextChangedListener(new TextWatcher() {{
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {{}}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {{
                viewModel.setFilterQuery(s == null ? "" : s.toString());
            }}
            @Override public void afterTextChanged(Editable s) {{}}
        }});
        viewModel.getUiState().observe(getViewLifecycleOwner(), state -> {{
            binding.setTitle(state.title);
            binding.setUserLine(state.user == null ? "" :
                    state.user.displayName + " · " + state.user.role + " · " + state.user.department);
            binding.setStats("Visible " + state.stats.totalVisible + " · Inbox " + state.stats.pendingInbox
                    + " · Approved " + state.stats.approved + " · Rejected " + state.stats.rejected
                    + " · Pipeline " + state.stats.inPipeline);
            adapter.submitList(state.requests);
        }});
    }}
}}
''')


def _inbox():
    empty_consumer("feature/inbox")
    w("feature/inbox/build.gradle.kts", lib_build(f"{PKG}.feature.inbox", feature_deps(), True))
    w("feature/inbox/src/main/AndroidManifest.xml", empty_manifest(f"{PKG}.feature.inbox"))
    w("feature/inbox/src/main/res/layout/fragment_inbox.xml", '''<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android">
    <data><variable name="emptyText" type="String" /></data>
    <LinearLayout android:layout_width="match_parent" android:layout_height="match_parent"
        android:orientation="vertical" android:background="@color/ah_bg">
        <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
            android:padding="16dp" android:text="Inbox Approval" android:textStyle="bold"
            android:textSize="20sp" android:textColor="@color/ah_primary" />
        <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
            android:padding="16dp" android:text="@{emptyText}" android:textColor="@color/ah_muted" />
        <androidx.recyclerview.widget.RecyclerView
            android:id="@+id/recycler" android:layout_width="match_parent"
            android:layout_height="match_parent" />
    </LinearLayout>
</layout>
''')
    base = f"feature/inbox/src/main/java/{P}/feature/inbox"
    w(f"{base}/InboxUiState.java", f'''
package {PKG}.feature.inbox;

import {PKG}.core.model.ApprovalRequest;
import java.util.Collections;
import java.util.List;

public class InboxUiState {{
    public final List<ApprovalRequest> items;
    public InboxUiState(List<ApprovalRequest> items) {{
        this.items = items == null ? Collections.emptyList() : items;
    }}
}}
''')
    w(f"{base}/InboxViewModel.java", f'''
package {PKG}.feature.inbox;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.Transformations;
import androidx.lifecycle.ViewModel;
import {PKG}.domain.repository.ApprovalRepository;

public class InboxViewModel extends ViewModel {{
    private final LiveData<InboxUiState> uiState;

    public InboxViewModel(ApprovalRepository approvalRepository) {{
        uiState = Transformations.map(approvalRepository.observeInbox(), InboxUiState::new);
    }}

    public LiveData<InboxUiState> getUiState() {{ return uiState; }}
}}
''')
    w(f"{base}/InboxFragment.java", f'''
package {PKG}.feature.inbox;

import android.os.Bundle;
import android.view.View;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.lifecycle.ViewModelProvider;
import androidx.navigation.Navigation;
import androidx.recyclerview.widget.LinearLayoutManager;
import {PKG}.core.ui.BaseMvvmFragment;
import {PKG}.core.ui.NavRoutes;
import {PKG}.core.ui.RequestListAdapter;
import {PKG}.data.di.AppContainerHolder;
import {PKG}.feature.inbox.databinding.FragmentInboxBinding;

public class InboxFragment extends BaseMvvmFragment<FragmentInboxBinding, InboxViewModel> {{
    private RequestListAdapter adapter;

    public InboxFragment() {{ super(R.layout.fragment_inbox); }}

    @NonNull
    @Override
    protected InboxViewModel createViewModel() {{
        return new ViewModelProvider(this,
                ((AppContainerHolder) requireActivity().getApplication()).getAppContainer().factory)
                .get(InboxViewModel.class);
    }}

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        adapter = new RequestListAdapter(req ->
                Navigation.findNavController(view).navigate(NavRoutes.detail(req.id)));
        binding.recycler.setLayoutManager(new LinearLayoutManager(requireContext()));
        binding.recycler.setAdapter(adapter);
        viewModel.getUiState().observe(getViewLifecycleOwner(), state -> {{
            binding.setEmptyText(state.items.isEmpty() ? "Tidak ada item menunggu aksi Anda" : "");
            adapter.submitList(state.items);
        }});
    }}
}}
''')


def _request():
    empty_consumer("feature/request")
    w("feature/request/build.gradle.kts", lib_build(f"{PKG}.feature.request", feature_deps(), True))
    w("feature/request/src/main/AndroidManifest.xml", empty_manifest(f"{PKG}.feature.request"))
    w("feature/request/src/main/res/layout/fragment_create_request.xml", '''<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android">
    <data>
        <variable name="ruleHint" type="String" />
        <variable name="error" type="String" />
    </data>
    <ScrollView android:layout_width="match_parent" android:layout_height="match_parent"
        android:background="@color/ah_bg">
        <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
            android:orientation="vertical" android:padding="16dp">
            <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
                android:text="Buat Request" android:textStyle="bold" android:textSize="20sp"
                android:textColor="@color/ah_primary" />
            <com.google.android.material.textfield.TextInputLayout android:layout_width="match_parent"
                android:layout_height="wrap_content" android:hint="Judul" android:layout_marginTop="12dp">
                <com.google.android.material.textfield.TextInputEditText android:id="@+id/inputTitle"
                    android:layout_width="match_parent" android:layout_height="wrap_content" />
            </com.google.android.material.textfield.TextInputLayout>
            <com.google.android.material.textfield.TextInputLayout android:layout_width="match_parent"
                android:layout_height="wrap_content" android:hint="Deskripsi" android:layout_marginTop="8dp">
                <com.google.android.material.textfield.TextInputEditText android:id="@+id/inputDesc"
                    android:layout_width="match_parent" android:layout_height="wrap_content" />
            </com.google.android.material.textfield.TextInputLayout>
            <Spinner android:id="@+id/spinnerType" android:layout_width="match_parent"
                android:layout_height="wrap_content" android:layout_marginTop="12dp" />
            <com.google.android.material.textfield.TextInputLayout android:layout_width="match_parent"
                android:layout_height="wrap_content" android:hint="Amount" android:layout_marginTop="8dp">
                <com.google.android.material.textfield.TextInputEditText android:id="@+id/inputAmount"
                    android:layout_width="match_parent" android:layout_height="wrap_content"
                    android:inputType="numberDecimal" />
            </com.google.android.material.textfield.TextInputLayout>
            <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
                android:text="@{ruleHint}" android:layout_marginTop="8dp" android:textColor="@color/ah_primary" />
            <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
                android:text="@{error}" android:textColor="@color/ah_danger" android:layout_marginTop="4dp" />
            <com.google.android.material.button.MaterialButton android:id="@+id/btnSubmit"
                android:layout_width="match_parent" android:layout_height="wrap_content"
                android:text="Submit" android:layout_marginTop="16dp" />
        </LinearLayout>
    </ScrollView>
</layout>
''')
    w("feature/request/src/main/res/layout/fragment_approval_detail.xml", '''<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android">
    <data>
        <variable name="detail" type="String" />
        <variable name="canAct" type="boolean" />
        <variable name="canEscalate" type="boolean" />
        <variable name="message" type="String" />
    </data>
    <ScrollView android:layout_width="match_parent" android:layout_height="match_parent"
        android:background="@color/ah_bg">
        <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
            android:orientation="vertical" android:padding="16dp">
            <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
                android:text="@{detail}" android:textSize="14sp" />
            <com.google.android.material.textfield.TextInputLayout android:layout_width="match_parent"
                android:layout_height="wrap_content" android:hint="Komentar" android:layout_marginTop="12dp">
                <com.google.android.material.textfield.TextInputEditText android:id="@+id/inputComment"
                    android:layout_width="match_parent" android:layout_height="wrap_content" />
            </com.google.android.material.textfield.TextInputLayout>
            <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
                android:orientation="horizontal" android:layout_marginTop="12dp">
                <com.google.android.material.button.MaterialButton android:id="@+id/btnApprove"
                    android:layout_width="0dp" android:layout_weight="1" android:layout_height="wrap_content"
                    android:text="Approve" android:enabled="@{canAct}" />
                <com.google.android.material.button.MaterialButton android:id="@+id/btnReject"
                    android:layout_width="0dp" android:layout_weight="1" android:layout_height="wrap_content"
                    android:text="Reject" android:enabled="@{canAct}"
                    style="@style/Widget.MaterialComponents.Button.OutlinedButton" />
            </LinearLayout>
            <com.google.android.material.button.MaterialButton android:id="@+id/btnEscalate"
                android:layout_width="match_parent" android:layout_height="wrap_content"
                android:text="Force Escalate" android:enabled="@{canEscalate}" android:layout_marginTop="8dp" />
            <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
                android:text="@{message}" android:layout_marginTop="8dp" android:textColor="@color/ah_muted" />
            <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
                android:text="Riwayat aksi" android:textStyle="bold" android:layout_marginTop="16dp" />
            <TextView android:id="@+id/textActions" android:layout_width="match_parent"
                android:layout_height="wrap_content" android:layout_marginTop="8dp" />
        </LinearLayout>
    </ScrollView>
</layout>
''')
    base = f"feature/request/src/main/java/{P}/feature/request"
    w(f"{base}/CreateRequestUiState.java", f'''
package {PKG}.feature.request;

public class CreateRequestUiState {{
    public final String ruleHint;
    public final String error;
    public final Long createdId;
    public final boolean loading;

    public CreateRequestUiState(String ruleHint, String error, Long createdId, boolean loading) {{
        this.ruleHint = ruleHint == null ? "" : ruleHint;
        this.error = error;
        this.createdId = createdId;
        this.loading = loading;
    }}
}}
''')
    w(f"{base}/CreateRequestViewModel.java", f'''
package {PKG}.feature.request;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;
import {PKG}.core.database.AppDatabase;
import {PKG}.core.model.RequestType;
import {PKG}.domain.approval.AmountBasedRules;
import {PKG}.domain.repository.ApprovalRepository;

public class CreateRequestViewModel extends ViewModel {{
    private final ApprovalRepository approvalRepository;
    private final MutableLiveData<CreateRequestUiState> uiState =
            new MutableLiveData<>(new CreateRequestUiState("", null, null, false));

    public CreateRequestViewModel(ApprovalRepository approvalRepository) {{
        this.approvalRepository = approvalRepository;
    }}

    public LiveData<CreateRequestUiState> getUiState() {{ return uiState; }}

    public void updateHint(RequestType type, double amount) {{
        CreateRequestUiState cur = uiState.getValue();
        uiState.setValue(new CreateRequestUiState(AmountBasedRules.ruleLabel(type, amount),
                cur == null ? null : cur.error, null, false));
    }}

    public void submit(String title, String description, RequestType type, double amount) {{
        uiState.setValue(new CreateRequestUiState(AmountBasedRules.ruleLabel(type, amount), null, null, true));
        AppDatabase.IO.execute(() -> {{
            try {{
                long id = approvalRepository.createRequest(title, description, type, amount);
                uiState.postValue(new CreateRequestUiState(AmountBasedRules.ruleLabel(type, amount), null, id, false));
            }} catch (Exception e) {{
                uiState.postValue(new CreateRequestUiState(AmountBasedRules.ruleLabel(type, amount), e.getMessage(), null, false));
            }}
        }});
    }}
}}
''')
    w(f"{base}/CreateRequestFragment.java", f'''
package {PKG}.feature.request;

import android.os.Bundle;
import android.view.View;
import android.widget.ArrayAdapter;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.lifecycle.ViewModelProvider;
import androidx.navigation.Navigation;
import {PKG}.core.model.RequestType;
import {PKG}.core.ui.BaseMvvmFragment;
import {PKG}.data.di.AppContainerHolder;
import {PKG}.feature.request.databinding.FragmentCreateRequestBinding;

public class CreateRequestFragment extends BaseMvvmFragment<FragmentCreateRequestBinding, CreateRequestViewModel> {{
    public CreateRequestFragment() {{ super(R.layout.fragment_create_request); }}

    @NonNull
    @Override
    protected CreateRequestViewModel createViewModel() {{
        return new ViewModelProvider(this,
                ((AppContainerHolder) requireActivity().getApplication()).getAppContainer().factory)
                .get(CreateRequestViewModel.class);
    }}

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        RequestType[] types = RequestType.values();
        String[] names = new String[types.length];
        for (int i = 0; i < types.length; i++) names[i] = types[i].name();
        binding.spinnerType.setAdapter(new ArrayAdapter<>(requireContext(),
                android.R.layout.simple_spinner_dropdown_item, names));
        binding.btnSubmit.setOnClickListener(v -> {{
            RequestType type = types[binding.spinnerType.getSelectedItemPosition()];
            double amount = 0;
            try {{
                String t = binding.inputAmount.getText() == null ? "0" : binding.inputAmount.getText().toString();
                amount = Double.parseDouble(t.isEmpty() ? "0" : t);
            }} catch (Exception ignored) {{}}
            viewModel.updateHint(type, amount);
            viewModel.submit(
                    binding.inputTitle.getText() == null ? "" : binding.inputTitle.getText().toString(),
                    binding.inputDesc.getText() == null ? "" : binding.inputDesc.getText().toString(),
                    type, amount);
        }});
        viewModel.getUiState().observe(getViewLifecycleOwner(), state -> {{
            binding.setRuleHint(state.ruleHint);
            binding.setError(state.error == null ? "" : state.error);
            if (state.createdId != null) Navigation.findNavController(view).navigateUp();
        }});
    }}
}}
''')
    w(f"{base}/ApprovalDetailUiState.java", f'''
package {PKG}.feature.request;

import {PKG}.core.model.ApprovalAction;
import {PKG}.core.model.ApprovalRequest;
import java.util.Collections;
import java.util.List;

public class ApprovalDetailUiState {{
    public final ApprovalRequest request;
    public final List<ApprovalAction> actions;
    public final boolean canAct;
    public final boolean canEscalate;
    public final String message;
    public final String detailText;

    public ApprovalDetailUiState(ApprovalRequest request, List<ApprovalAction> actions,
                                 boolean canAct, boolean canEscalate, String message, String detailText) {{
        this.request = request;
        this.actions = actions == null ? Collections.emptyList() : actions;
        this.canAct = canAct;
        this.canEscalate = canEscalate;
        this.message = message == null ? "" : message;
        this.detailText = detailText == null ? "" : detailText;
    }}
}}
''')
    w(f"{base}/ApprovalDetailViewModel.java", f'''
package {PKG}.feature.request;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MediatorLiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;
import {PKG}.core.database.AppDatabase;
import {PKG}.core.model.ApprovalAction;
import {PKG}.core.model.ApprovalRequest;
import {PKG}.core.model.Permission;
import {PKG}.core.model.Role;
import {PKG}.core.model.User;
import {PKG}.domain.approval.ApprovalWorkflow;
import {PKG}.domain.repository.ApprovalRepository;
import {PKG}.domain.repository.SessionRepository;
import java.util.List;

public class ApprovalDetailViewModel extends ViewModel {{
    private final long requestId;
    private final SessionRepository sessionRepository;
    private final ApprovalRepository approvalRepository;
    private final MutableLiveData<String> message = new MutableLiveData<>("");
    private final MediatorLiveData<ApprovalDetailUiState> uiState = new MediatorLiveData<>();

    public ApprovalDetailViewModel(long requestId, SessionRepository sessionRepository,
                                   ApprovalRepository approvalRepository) {{
        this.requestId = requestId;
        this.sessionRepository = sessionRepository;
        this.approvalRepository = approvalRepository;
        LiveData<List<ApprovalAction>> actions = approvalRepository.observeActions(requestId);
        LiveData<User> session = sessionRepository.observeSession();
        LiveData<Role> imp = sessionRepository.observeImpersonateRole();
        Runnable compute = () -> {{
            ApprovalRequest req = approvalRepository.getRequest(requestId);
            User user = session.getValue();
            Role role = user == null ? null : user.role;
            boolean canAct = req != null && role != null
                    && ApprovalWorkflow.canActOn(req.status, role, imp.getValue() != null);
            boolean canEscalate = sessionRepository.hasPermission(Permission.FORCE_ESCALATE)
                    && req != null && !ApprovalWorkflow.isTerminal(req.status);
            String detail = req == null ? "Loading…" :
                    "#" + req.id + " " + req.title + "\\n" + req.description + "\\n"
                            + ApprovalWorkflow.levelLabel(req.status) + " · " + req.type + " · " + req.amount + "\\n"
                            + "Dept " + req.department + " · Max L" + req.requiredMaxLevel
                            + (req.escalated ? " · ESCALATED" : "");
            uiState.postValue(new ApprovalDetailUiState(req, actions.getValue(), canAct, canEscalate,
                    message.getValue(), detail));
        }};
        uiState.addSource(actions, v -> AppDatabase.IO.execute(compute));
        uiState.addSource(session, v -> AppDatabase.IO.execute(compute));
        uiState.addSource(imp, v -> AppDatabase.IO.execute(compute));
        uiState.addSource(message, v -> AppDatabase.IO.execute(compute));
        AppDatabase.IO.execute(compute);
    }}

    public LiveData<ApprovalDetailUiState> getUiState() {{ return uiState; }}

    public void decide(boolean approve, String comment) {{
        AppDatabase.IO.execute(() -> {{
            try {{
                approvalRepository.decide(requestId, approve, comment);
                message.postValue("Berhasil");
            }} catch (Exception e) {{
                message.postValue(e.getMessage() == null ? "Gagal" : e.getMessage());
            }}
        }});
    }}

    public void escalate() {{
        AppDatabase.IO.execute(() -> {{
            try {{
                approvalRepository.forceEscalate(requestId);
                message.postValue("Escalated");
            }} catch (Exception e) {{
                message.postValue(e.getMessage() == null ? "Gagal" : e.getMessage());
            }}
        }});
    }}
}}
''')
    w(f"{base}/ApprovalDetailFragment.java", f'''
package {PKG}.feature.request;

import android.os.Bundle;
import android.view.View;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.lifecycle.ViewModelProvider;
import {PKG}.core.common.DateFormatters;
import {PKG}.core.model.ApprovalAction;
import {PKG}.core.ui.BaseMvvmFragment;
import {PKG}.data.di.AppContainer;
import {PKG}.data.di.AppContainerHolder;
import {PKG}.feature.request.databinding.FragmentApprovalDetailBinding;

public class ApprovalDetailFragment extends BaseMvvmFragment<FragmentApprovalDetailBinding, ApprovalDetailViewModel> {{
    public ApprovalDetailFragment() {{ super(R.layout.fragment_approval_detail); }}

    @NonNull
    @Override
    protected ApprovalDetailViewModel createViewModel() {{
        long requestId = getArguments() == null ? 0L : getArguments().getLong("requestId", 0L);
        AppContainer c = ((AppContainerHolder) requireActivity().getApplication()).getAppContainer();
        return new ViewModelProvider(this, c.factoryForDetail(requestId)).get(ApprovalDetailViewModel.class);
    }}

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        binding.btnApprove.setOnClickListener(v -> viewModel.decide(true,
                binding.inputComment.getText() == null ? "" : binding.inputComment.getText().toString()));
        binding.btnReject.setOnClickListener(v -> viewModel.decide(false,
                binding.inputComment.getText() == null ? "" : binding.inputComment.getText().toString()));
        binding.btnEscalate.setOnClickListener(v -> viewModel.escalate());
        viewModel.getUiState().observe(getViewLifecycleOwner(), state -> {{
            binding.setDetail(state.detailText);
            binding.setCanAct(state.canAct);
            binding.setCanEscalate(state.canEscalate);
            binding.setMessage(state.message);
            StringBuilder sb = new StringBuilder();
            for (ApprovalAction a : state.actions) {{
                if (sb.length() > 0) sb.append("\\n");
                sb.append("L").append(a.level).append(" ").append(a.decision).append(" — ")
                        .append(a.comment).append(" (").append(DateFormatters.full(a.createdAt)).append(")");
            }}
            binding.textActions.setText(sb.toString());
        }});
    }}
}}
''')


def _analytics():
    empty_consumer("feature/analytics")
    w("feature/analytics/build.gradle.kts", lib_build(f"{PKG}.feature.analytics", feature_deps(), True))
    w("feature/analytics/src/main/AndroidManifest.xml", empty_manifest(f"{PKG}.feature.analytics"))
    w("feature/analytics/src/main/res/layout/fragment_analytics.xml", '''<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android">
    <data><variable name="content" type="String" /></data>
    <ScrollView android:layout_width="match_parent" android:layout_height="match_parent"
        android:background="@color/ah_bg">
        <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
            android:orientation="vertical" android:padding="16dp">
            <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
                android:text="Analytics" android:textStyle="bold" android:textSize="20sp"
                android:textColor="@color/ah_primary" />
            <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
                android:text="@{content}" android:layout_marginTop="12dp" android:lineSpacingExtra="4dp" />
            <com.google.android.material.button.MaterialButton android:id="@+id/btnExportChart"
                android:layout_width="match_parent" android:layout_height="wrap_content"
                android:text="Export Chart PNG" android:layout_marginTop="16dp" />
        </LinearLayout>
    </ScrollView>
</layout>
''')
    base = f"feature/analytics/src/main/java/{P}/feature/analytics"
    w(f"{base}/AnalyticsUiState.java", f'''
package {PKG}.feature.analytics;

import {PKG}.core.model.StatusCount;
import java.util.Collections;
import java.util.List;

public class AnalyticsUiState {{
    public final List<StatusCount> statusCounts;
    public final String content;

    public AnalyticsUiState(List<StatusCount> statusCounts, String content) {{
        this.statusCounts = statusCounts == null ? Collections.emptyList() : statusCounts;
        this.content = content == null ? "" : content;
    }}
}}
''')
    w(f"{base}/AnalyticsViewModel.java", f'''
package {PKG}.feature.analytics;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MediatorLiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;
import {PKG}.core.database.AppDatabase;
import {PKG}.core.model.StatusCount;
import {PKG}.core.model.TypeStat;
import {PKG}.domain.analytics.BottleneckLevel;
import {PKG}.domain.analytics.SlaStats;
import {PKG}.domain.repository.ApprovalRepository;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

public class AnalyticsViewModel extends ViewModel {{
    private final ApprovalRepository approvalRepository;
    private final MutableLiveData<SlaStats> sla = new MutableLiveData<>();
    private final MutableLiveData<List<BottleneckLevel>> bn = new MutableLiveData<>();
    private final MediatorLiveData<AnalyticsUiState> uiState = new MediatorLiveData<>();

    public AnalyticsViewModel(ApprovalRepository approvalRepository) {{
        this.approvalRepository = approvalRepository;
        AppDatabase.IO.execute(() -> {{
            sla.postValue(approvalRepository.computeSla());
            bn.postValue(approvalRepository.computeBottleneck());
        }});
        LiveData<List<StatusCount>> status = approvalRepository.observeStatusCounts();
        LiveData<List<TypeStat>> types = approvalRepository.observeTypeStats();
        Runnable compute = () -> {{
            List<StatusCount> s = status.getValue();
            List<TypeStat> t = types.getValue();
            SlaStats slaVal = sla.getValue();
            List<BottleneckLevel> bnVal = bn.getValue();
            StringBuilder text = new StringBuilder();
            text.append("Status counts:\\n");
            if (s != null) for (StatusCount sc : s) text.append(" · ").append(sc.status).append(": ").append(sc.count).append("\\n");
            text.append("\\nBy type:\\n");
            if (t != null) for (TypeStat ts : t) text.append(" · ").append(ts.type).append(": ").append(ts.count)
                    .append(" (sum ").append(ts.totalAmount).append(")\\n");
            text.append("\\n");
            if (slaVal != null) {{
                text.append("SLA ").append(slaVal.slaHours).append("h: ")
                        .append(slaVal.withinSlaCount).append("/").append(slaVal.completedCount)
                        .append(String.format(Locale.US, " (%.1f%%)\\n", slaVal.withinSlaPercent));
            }}
            text.append("\\nBottleneck (avg wait hours):\\n");
            if (bnVal != null) for (BottleneckLevel b : bnVal) {{
                text.append(String.format(Locale.US, " · L%d: %.1fh (n=%d)\\n", b.level, b.avgWaitHours, b.sampleCount));
            }}
            uiState.postValue(new AnalyticsUiState(s, text.toString()));
        }};
        uiState.addSource(status, v -> compute.run());
        uiState.addSource(types, v -> compute.run());
        uiState.addSource(sla, v -> compute.run());
        uiState.addSource(bn, v -> compute.run());
    }}

    public LiveData<AnalyticsUiState> getUiState() {{ return uiState; }}

    public List<String> chartLabels() {{
        AnalyticsUiState s = uiState.getValue();
        List<String> labels = new ArrayList<>();
        if (s != null) for (StatusCount c : s.statusCounts) labels.add(c.status.name());
        return labels;
    }}

    public List<Float> chartValues() {{
        AnalyticsUiState s = uiState.getValue();
        List<Float> values = new ArrayList<>();
        if (s != null) for (StatusCount c : s.statusCounts) values.add((float) c.count);
        return values;
    }}
}}
''')
    w(f"{base}/AnalyticsFragment.java", f'''
package {PKG}.feature.analytics;

import android.os.Bundle;
import android.view.View;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.lifecycle.ViewModelProvider;
import {PKG}.core.ui.BaseMvvmFragment;
import {PKG}.data.di.AppContainerHolder;
import {PKG}.data.export.ExportUtils;
import {PKG}.feature.analytics.databinding.FragmentAnalyticsBinding;
import java.util.List;

public class AnalyticsFragment extends BaseMvvmFragment<FragmentAnalyticsBinding, AnalyticsViewModel> {{
    public AnalyticsFragment() {{ super(R.layout.fragment_analytics); }}

    @NonNull
    @Override
    protected AnalyticsViewModel createViewModel() {{
        return new ViewModelProvider(this,
                ((AppContainerHolder) requireActivity().getApplication()).getAppContainer().factory)
                .get(AnalyticsViewModel.class);
    }}

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        binding.btnExportChart.setOnClickListener(v -> {{
            List<String> labels = viewModel.chartLabels();
            List<Float> values = viewModel.chartValues();
            if (!values.isEmpty()) {{
                try {{
                    ExportUtils.shareBitmap(requireContext(),
                            ExportUtils.createSimpleChartBitmap(labels, values, "Status distribution"),
                            "ApprovalHub Chart");
                }} catch (Exception ignored) {{}}
            }}
        }});
        viewModel.getUiState().observe(getViewLifecycleOwner(), state -> binding.setContent(state.content));
    }}
}}
''')


def _audit():
    empty_consumer("feature/audit")
    w("feature/audit/build.gradle.kts", lib_build(f"{PKG}.feature.audit", feature_deps(), True))
    w("feature/audit/src/main/AndroidManifest.xml", empty_manifest(f"{PKG}.feature.audit"))
    w("feature/audit/src/main/res/layout/fragment_audit.xml", '''<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android">
    <data><variable name="content" type="String" /></data>
    <LinearLayout android:layout_width="match_parent" android:layout_height="match_parent"
        android:orientation="vertical" android:padding="16dp" android:background="@color/ah_bg">
        <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
            android:text="Audit Trail" android:textStyle="bold" android:textSize="20sp"
            android:textColor="@color/ah_primary" />
        <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
            android:orientation="horizontal" android:layout_marginTop="12dp">
            <com.google.android.material.button.MaterialButton android:id="@+id/btnCsv"
                android:layout_width="0dp" android:layout_weight="1" android:layout_height="wrap_content"
                android:text="Export CSV" />
            <com.google.android.material.button.MaterialButton android:id="@+id/btnPdf"
                android:layout_width="0dp" android:layout_weight="1" android:layout_height="wrap_content"
                android:text="Export PDF" />
        </LinearLayout>
        <ScrollView android:layout_width="match_parent" android:layout_height="match_parent"
            android:layout_marginTop="12dp">
            <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
                android:text="@{content}" android:textSize="13sp" />
        </ScrollView>
    </LinearLayout>
</layout>
''')
    base = f"feature/audit/src/main/java/{P}/feature/audit"
    w(f"{base}/AuditUiState.java", f'''
package {PKG}.feature.audit;

import {PKG}.core.model.ApprovalAction;
import {PKG}.core.model.ApprovalRequest;
import java.util.Collections;
import java.util.List;
import java.util.Map;

public class AuditUiState {{
    public final List<ApprovalRequest> requests;
    public final List<ApprovalAction> actions;
    public final Map<Long, String> names;
    public final String content;

    public AuditUiState(List<ApprovalRequest> requests, List<ApprovalAction> actions,
                        Map<Long, String> names, String content) {{
        this.requests = requests == null ? Collections.emptyList() : requests;
        this.actions = actions == null ? Collections.emptyList() : actions;
        this.names = names == null ? Collections.emptyMap() : names;
        this.content = content == null ? "" : content;
    }}
}}
''')
    w(f"{base}/AuditViewModel.java", f'''
package {PKG}.feature.audit;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;
import {PKG}.core.database.AppDatabase;
import {PKG}.core.model.ApprovalAction;
import {PKG}.core.model.ApprovalRequest;
import {PKG}.domain.repository.ApprovalRepository;
import java.util.List;
import java.util.Map;

public class AuditViewModel extends ViewModel {{
    private final MutableLiveData<AuditUiState> uiState = new MutableLiveData<>(
            new AuditUiState(null, null, null, "Loading…"));

    public AuditViewModel(ApprovalRepository approvalRepository) {{
        AppDatabase.IO.execute(() -> {{
            List<ApprovalRequest> requests = approvalRepository.allRequests();
            List<ApprovalAction> actions = approvalRepository.allActions();
            Map<Long, String> names = approvalRepository.buildUserNameMap();
            StringBuilder text = new StringBuilder();
            int take = Math.min(30, requests.size());
            for (int i = 0; i < take; i++) {{
                ApprovalRequest r = requests.get(i);
                text.append("#").append(r.id).append(" ").append(r.title).append(" [").append(r.status).append("]\\n");
                for (ApprovalAction a : actions) {{
                    if (a.requestId != r.id) continue;
                    String name = names.getOrDefault(a.actorId, String.valueOf(a.actorId));
                    text.append("  L").append(a.level).append(" ").append(a.decision).append(" by ")
                            .append(name).append(" — ").append(a.comment).append("\\n");
                }}
            }}
            uiState.postValue(new AuditUiState(requests, actions, names, text.toString()));
        }});
    }}

    public LiveData<AuditUiState> getUiState() {{ return uiState; }}
}}
''')
    w(f"{base}/AuditFragment.java", f'''
package {PKG}.feature.audit;

import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.lifecycle.ViewModelProvider;
import {PKG}.core.ui.BaseMvvmFragment;
import {PKG}.data.di.AppContainerHolder;
import {PKG}.data.export.ExportUtils;
import {PKG}.feature.audit.databinding.FragmentAuditBinding;

public class AuditFragment extends BaseMvvmFragment<FragmentAuditBinding, AuditViewModel> {{
    public AuditFragment() {{ super(R.layout.fragment_audit); }}

    @NonNull
    @Override
    protected AuditViewModel createViewModel() {{
        return new ViewModelProvider(this,
                ((AppContainerHolder) requireActivity().getApplication()).getAppContainer().factory)
                .get(AuditViewModel.class);
    }}

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        binding.btnCsv.setOnClickListener(v -> {{
            AuditUiState s = viewModel.getUiState().getValue();
            if (s == null) return;
            try {{
                Uri uri = ExportUtils.exportAuditCsv(requireContext(), s.requests, s.actions, s.names);
                ExportUtils.shareUri(requireContext(), uri, "text/csv", "Audit CSV");
            }} catch (Exception ignored) {{}}
        }});
        binding.btnPdf.setOnClickListener(v -> {{
            AuditUiState s = viewModel.getUiState().getValue();
            if (s == null) return;
            try {{
                Uri uri = ExportUtils.exportAuditPdf(requireContext(), s.requests, s.actions, s.names);
                ExportUtils.shareUri(requireContext(), uri, "application/pdf", "Audit PDF");
            }} catch (Exception ignored) {{}}
        }});
        viewModel.getUiState().observe(getViewLifecycleOwner(), state -> binding.setContent(state.content));
    }}
}}
''')


def _settings():
    empty_consumer("feature/settings")
    w("feature/settings/build.gradle.kts", lib_build(f"{PKG}.feature.settings", feature_deps(), True))
    w("feature/settings/src/main/AndroidManifest.xml", empty_manifest(f"{PKG}.feature.settings"))
    w("feature/settings/src/main/res/layout/fragment_settings.xml", '''<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android">
    <data>
        <variable name="info" type="String" />
        <variable name="syncInfo" type="String" />
    </data>
    <ScrollView android:layout_width="match_parent" android:layout_height="match_parent"
        android:background="@color/ah_bg">
        <LinearLayout android:layout_width="match_parent" android:layout_height="wrap_content"
            android:orientation="vertical" android:padding="16dp">
            <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
                android:text="Settings" android:textStyle="bold" android:textSize="20sp"
                android:textColor="@color/ah_primary" />
            <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
                android:text="@{info}" android:layout_marginTop="12dp" />
            <TextView android:layout_width="match_parent" android:layout_height="wrap_content"
                android:text="@{syncInfo}" android:layout_marginTop="8dp" android:textColor="@color/ah_muted" />
            <Spinner android:id="@+id/spinnerTheme" android:layout_width="match_parent"
                android:layout_height="wrap_content" android:layout_marginTop="12dp" />
            <Spinner android:id="@+id/spinnerImpersonate" android:layout_width="match_parent"
                android:layout_height="wrap_content" android:layout_marginTop="8dp" />
            <com.google.android.material.button.MaterialButton android:id="@+id/btnSync"
                android:layout_width="match_parent" android:layout_height="wrap_content"
                android:text="Sync Now" android:layout_marginTop="12dp" />
            <com.google.android.material.button.MaterialButton android:id="@+id/btnEscalate"
                android:layout_width="match_parent" android:layout_height="wrap_content"
                android:text="Run Escalation Pass" android:layout_marginTop="8dp" />
            <com.google.android.material.button.MaterialButton android:id="@+id/btnLogout"
                android:layout_width="match_parent" android:layout_height="wrap_content"
                android:text="Logout" android:layout_marginTop="8dp"
                style="@style/Widget.MaterialComponents.Button.OutlinedButton" />
        </LinearLayout>
    </ScrollView>
</layout>
''')
    base = f"feature/settings/src/main/java/{P}/feature/settings"
    w(f"{base}/SettingsUiState.java", f'''
package {PKG}.feature.settings;

import {PKG}.core.model.Role;
import {PKG}.core.model.User;

public class SettingsUiState {{
    public final User user;
    public final Role impersonate;
    public final String syncInfo;
    public final String message;
    public final boolean loggedOut;

    public SettingsUiState(User user, Role impersonate, String syncInfo, String message, boolean loggedOut) {{
        this.user = user;
        this.impersonate = impersonate;
        this.syncInfo = syncInfo == null ? "" : syncInfo;
        this.message = message == null ? "" : message;
        this.loggedOut = loggedOut;
    }}
}}
''')
    w(f"{base}/SettingsViewModel.java", f'''
package {PKG}.feature.settings;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MediatorLiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.ViewModel;
import {PKG}.core.common.DateFormatters;
import {PKG}.core.database.AppDatabase;
import {PKG}.core.model.Role;
import {PKG}.core.model.SyncMeta;
import {PKG}.core.model.ThemeMode;
import {PKG}.core.model.User;
import {PKG}.domain.repository.ApprovalRepository;
import {PKG}.domain.repository.SessionRepository;

public class SettingsViewModel extends ViewModel {{
    private final SessionRepository sessionRepository;
    private final ApprovalRepository approvalRepository;
    private final MutableLiveData<String> message = new MutableLiveData<>("");
    private final MutableLiveData<Boolean> loggedOut = new MutableLiveData<>(false);
    private final MediatorLiveData<SettingsUiState> uiState = new MediatorLiveData<>();

    public SettingsViewModel(SessionRepository sessionRepository, ApprovalRepository approvalRepository) {{
        this.sessionRepository = sessionRepository;
        this.approvalRepository = approvalRepository;
        LiveData<User> session = sessionRepository.observeSession();
        LiveData<Role> imp = sessionRepository.observeImpersonateRole();
        LiveData<SyncMeta> meta = approvalRepository.observeSyncMeta();
        Runnable compute = () -> {{
            SyncMeta m = meta.getValue();
            String syncInfo = m == null ? "No sync meta" :
                    "Last sync: " + (m.lastSyncedAt == 0L ? "never" : DateFormatters.full(m.lastSyncedAt))
                            + " · " + m.lastSyncStatus + " · pending " + m.pendingPushCount;
            uiState.setValue(new SettingsUiState(session.getValue(), imp.getValue(), syncInfo,
                    message.getValue(), Boolean.TRUE.equals(loggedOut.getValue())));
        }};
        uiState.addSource(session, v -> compute.run());
        uiState.addSource(imp, v -> compute.run());
        uiState.addSource(meta, v -> compute.run());
        uiState.addSource(message, v -> compute.run());
        uiState.addSource(loggedOut, v -> compute.run());
    }}

    public LiveData<SettingsUiState> getUiState() {{ return uiState; }}

    public void setTheme(ThemeMode mode) {{ sessionRepository.setThemeMode(mode); }}
    public void setImpersonate(Role role) {{ sessionRepository.setImpersonateRole(role); }}

    public void sync() {{
        AppDatabase.IO.execute(() -> {{
            try {{
                approvalRepository.syncNow();
                message.postValue("Sync OK");
            }} catch (Exception e) {{
                message.postValue(e.getMessage() == null ? "Sync failed" : e.getMessage());
            }}
        }});
    }}

    public void runEscalation() {{
        AppDatabase.IO.execute(() -> {{
            int n = approvalRepository.runEscalationPass();
            message.postValue("Escalated " + n + " request(s)");
        }});
    }}

    public void logout() {{
        AppDatabase.IO.execute(() -> {{
            sessionRepository.logoutAndClear();
            loggedOut.postValue(true);
        }});
    }}
}}
''')
    w(f"{base}/SettingsFragment.java", f'''
package {PKG}.feature.settings;

import android.os.Bundle;
import android.view.View;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatDelegate;
import androidx.lifecycle.ViewModelProvider;
import androidx.navigation.NavOptions;
import androidx.navigation.Navigation;
import {PKG}.core.model.Role;
import {PKG}.core.model.ThemeMode;
import {PKG}.core.ui.BaseMvvmFragment;
import {PKG}.core.ui.NavRoutes;
import {PKG}.data.di.AppContainerHolder;
import {PKG}.feature.settings.databinding.FragmentSettingsBinding;

public class SettingsFragment extends BaseMvvmFragment<FragmentSettingsBinding, SettingsViewModel> {{
    public SettingsFragment() {{ super(R.layout.fragment_settings); }}

    @NonNull
    @Override
    protected SettingsViewModel createViewModel() {{
        return new ViewModelProvider(this,
                ((AppContainerHolder) requireActivity().getApplication()).getAppContainer().factory)
                .get(SettingsViewModel.class);
    }}

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        ThemeMode[] themes = ThemeMode.values();
        String[] themeNames = new String[themes.length];
        for (int i = 0; i < themes.length; i++) themeNames[i] = themes[i].name();
        binding.spinnerTheme.setAdapter(new ArrayAdapter<>(requireContext(),
                android.R.layout.simple_spinner_dropdown_item, themeNames));

        Role[] rolesEnum = Role.values();
        String[] roleNames = new String[rolesEnum.length + 1];
        roleNames[0] = "(none)";
        for (int i = 0; i < rolesEnum.length; i++) roleNames[i + 1] = rolesEnum[i].name();
        binding.spinnerImpersonate.setAdapter(new ArrayAdapter<>(requireContext(),
                android.R.layout.simple_spinner_dropdown_item, roleNames));

        binding.spinnerTheme.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {{
            @Override public void onItemSelected(AdapterView<?> parent, View v, int pos, long id) {{
                ThemeMode mode = themes[pos];
                viewModel.setTheme(mode);
                int night;
                if (mode == ThemeMode.LIGHT) night = AppCompatDelegate.MODE_NIGHT_NO;
                else if (mode == ThemeMode.DARK) night = AppCompatDelegate.MODE_NIGHT_YES;
                else night = AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM;
                AppCompatDelegate.setDefaultNightMode(night);
            }}
            @Override public void onNothingSelected(AdapterView<?> parent) {{}}
        }});
        binding.spinnerImpersonate.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {{
            @Override public void onItemSelected(AdapterView<?> parent, View v, int pos, long id) {{
                viewModel.setImpersonate(pos == 0 ? null : rolesEnum[pos - 1]);
            }}
            @Override public void onNothingSelected(AdapterView<?> parent) {{}}
        }});
        binding.btnSync.setOnClickListener(v -> viewModel.sync());
        binding.btnEscalate.setOnClickListener(v -> viewModel.runEscalation());
        binding.btnLogout.setOnClickListener(v -> viewModel.logout());
        viewModel.getUiState().observe(getViewLifecycleOwner(), state -> {{
            if (state.user != null) {{
                String info = state.user.displayName + " (" + state.user.username + ") · " + state.user.role;
                if (state.impersonate != null) info += " · impersonate " + state.impersonate;
                info += "\\n" + state.message;
                binding.setInfo(info);
            }} else binding.setInfo("");
            binding.setSyncInfo(state.syncInfo);
            if (state.loggedOut) {{
                NavOptions opts = new NavOptions.Builder().setPopUpTo(NavRoutes.LOGIN, true).build();
                Navigation.findNavController(view).navigate(NavRoutes.LOGIN, opts);
            }}
        }});
    }}
}}
''')


def _widget():
    empty_consumer("feature/widget")
    w("feature/widget/build.gradle.kts", lib_build(f"{PKG}.feature.widget", [
        'implementation(project(":core:database"))',
        "implementation(libs.androidx.core)",
    ], False))
    w("feature/widget/src/main/AndroidManifest.xml", f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application>
        <receiver
            android:name="{PKG}.feature.widget.PendingWidgetReceiver"
            android:exported="true">
            <intent-filter>
                <action android:name="android.appwidget.action.APPWIDGET_UPDATE" />
            </intent-filter>
            <meta-data
                android:name="android.appwidget.provider"
                android:resource="@xml/pending_widget_info" />
        </receiver>
    </application>
</manifest>
''')
    w("feature/widget/src/main/res/layout/widget_pending_placeholder.xml", '''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent"
    android:orientation="vertical" android:padding="12dp"
    android:background="@color/ah_primary" android:gravity="center">
    <TextView android:layout_width="wrap_content" android:layout_height="wrap_content"
        android:text="Pending" android:textColor="#FFFFFF" android:textSize="12sp" />
    <TextView android:id="@+id/widget_pending_count" android:layout_width="wrap_content"
        android:layout_height="wrap_content" android:text="0" android:textColor="#FFFFFF"
        android:textSize="28sp" android:textStyle="bold" />
</LinearLayout>
''')
    w("feature/widget/src/main/res/xml/pending_widget_info.xml", '''<?xml version="1.0" encoding="utf-8"?>
<appwidget-provider xmlns:android="http://schemas.android.com/apk/res/android"
    android:minWidth="110dp" android:minHeight="40dp"
    android:updatePeriodMillis="1800000"
    android:initialLayout="@layout/widget_pending_placeholder"
    android:resizeMode="horizontal|vertical"
    android:widgetCategory="home_screen" />
''')
    w("feature/widget/src/main/res/values/colors.xml", '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ah_primary">#0F4C5C</color>
</resources>
''')
    w(f"feature/widget/src/main/java/{P}/feature/widget/PendingWidgetReceiver.java", f'''
package {PKG}.feature.widget;

import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.Context;
import android.widget.RemoteViews;
import {PKG}.core.database.AppDatabase;

public class PendingWidgetReceiver extends AppWidgetProvider {{
    @Override
    public void onUpdate(Context context, AppWidgetManager appWidgetManager, int[] appWidgetIds) {{
        AppDatabase.IO.execute(() -> {{
            int count = 0;
            try {{
                count = AppDatabase.get(context).approvalRequestDao().pendingCountSync();
            }} catch (Exception ignored) {{}}
            for (int id : appWidgetIds) {{
                RemoteViews views = new RemoteViews(context.getPackageName(), R.layout.widget_pending_placeholder);
                views.setTextViewText(R.id.widget_pending_count, String.valueOf(count));
                appWidgetManager.updateAppWidget(id, views);
            }}
        }});
    }}
}}
''')


def gen_app():
    w("app/build.gradle.kts", f'''
plugins {{
    alias(libs.plugins.android.application)
}}

android {{
    namespace = "{PKG}.app"
    compileSdk = libs.versions.compileSdk.get().toInt()

    defaultConfig {{
        applicationId = "{PKG}"
        minSdk = libs.versions.minSdk.get().toInt()
        targetSdk = libs.versions.targetSdk.get().toInt()
        versionCode = 1
        versionName = "1.0"
    }}

    buildTypes {{
        release {{
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }}
    }}
    compileOptions {{
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }}
    buildFeatures {{
        dataBinding = true
    }}
}}

dependencies {{
    implementation(project(":core:ui"))
    implementation(project(":core:model"))
    implementation(project(":core:common"))
    implementation(project(":core:database"))
    implementation(project(":core:preference"))
    implementation(project(":core:network"))
    implementation(project(":core:notification"))
    implementation(project(":domain"))
    implementation(project(":data"))
    implementation(project(":feature:auth"))
    implementation(project(":feature:dashboard"))
    implementation(project(":feature:inbox"))
    implementation(project(":feature:request"))
    implementation(project(":feature:analytics"))
    implementation(project(":feature:audit"))
    implementation(project(":feature:settings"))
    implementation(project(":feature:widget"))

    implementation(libs.androidx.core)
    implementation(libs.androidx.appcompat)
    implementation(libs.material)
    implementation(libs.androidx.constraintlayout)
    implementation(libs.androidx.activity)
    implementation(libs.androidx.fragment)
    implementation(libs.androidx.navigation.fragment)
    implementation(libs.androidx.navigation.ui)
    implementation(libs.androidx.lifecycle.runtime)
    implementation(libs.androidx.lifecycle.viewmodel)
    implementation(libs.androidx.lifecycle.livedata)
    implementation(libs.androidx.work)
}}
''')
    w("app/proguard-rules.pro", "# app proguard\\n")
    w("app/src/main/AndroidManifest.xml", f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />

    <application
        android:name=".WingsApp"
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.ApprovalHub">

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:windowSoftInputMode="adjustResize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="${{applicationId}}.fileprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/file_paths" />
        </provider>
    </application>
</manifest>
''')
    w("app/src/main/res/xml/file_paths.xml", '''<?xml version="1.0" encoding="utf-8"?>
<paths>
    <cache-path name="cache" path="." />
</paths>
''')
    w("app/src/main/res/values/strings.xml", '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">ApprovalHub</string>
</resources>
''')
    w("app/src/main/res/values/colors.xml", '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ah_primary">#0F4C5C</color>
    <color name="ah_surface">#FFFFFF</color>
</resources>
''')
    w("app/src/main/res/menu/menu_bottom.xml", '''<?xml version="1.0" encoding="utf-8"?>
<menu xmlns:android="http://schemas.android.com/apk/res/android">
    <item android:id="@+id/dashboardFragment" android:title="Home" android:icon="@android:drawable/ic_menu_compass" />
    <item android:id="@+id/inboxFragment" android:title="Inbox" android:icon="@android:drawable/ic_menu_agenda" />
    <item android:id="@+id/analyticsFragment" android:title="Charts" android:icon="@android:drawable/ic_menu_sort_by_size" />
    <item android:id="@+id/auditFragment" android:title="Audit" android:icon="@android:drawable/ic_menu_recent_history" />
    <item android:id="@+id/settingsFragment" android:title="Settings" android:icon="@android:drawable/ic_menu_preferences" />
</menu>
''')
    w("app/src/main/res/navigation/nav_graph.xml", f'''<?xml version="1.0" encoding="utf-8"?>
<navigation xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:id="@+id/nav_graph"
    app:startDestination="@id/loginFragment">

    <fragment
        android:id="@+id/loginFragment"
        android:name="{PKG}.feature.auth.LoginFragment"
        android:label="Login">
        <deepLink app:uri="wings://login" />
    </fragment>

    <fragment
        android:id="@+id/dashboardFragment"
        android:name="{PKG}.feature.dashboard.DashboardFragment"
        android:label="Dashboard">
        <deepLink app:uri="wings://dashboard" />
    </fragment>

    <fragment
        android:id="@+id/inboxFragment"
        android:name="{PKG}.feature.inbox.InboxFragment"
        android:label="Inbox" />

    <fragment
        android:id="@+id/createRequestFragment"
        android:name="{PKG}.feature.request.CreateRequestFragment"
        android:label="Create">
        <deepLink app:uri="wings://create" />
    </fragment>

    <fragment
        android:id="@+id/approvalDetailFragment"
        android:name="{PKG}.feature.request.ApprovalDetailFragment"
        android:label="Detail">
        <argument android:name="requestId" app:argType="long" android:defaultValue="0L" />
        <deepLink app:uri="wings://detail/{{requestId}}" />
    </fragment>

    <fragment
        android:id="@+id/analyticsFragment"
        android:name="{PKG}.feature.analytics.AnalyticsFragment"
        android:label="Analytics" />

    <fragment
        android:id="@+id/auditFragment"
        android:name="{PKG}.feature.audit.AuditFragment"
        android:label="Audit" />

    <fragment
        android:id="@+id/settingsFragment"
        android:name="{PKG}.feature.settings.SettingsFragment"
        android:label="Settings" />
</navigation>
''')
    w("app/src/main/res/layout/activity_main.xml", '''<?xml version="1.0" encoding="utf-8"?>
<androidx.constraintlayout.widget.ConstraintLayout
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:layout_width="match_parent"
    android:layout_height="match_parent">

    <androidx.fragment.app.FragmentContainerView
        android:id="@+id/nav_host"
        android:name="androidx.navigation.fragment.NavHostFragment"
        android:layout_width="0dp"
        android:layout_height="0dp"
        app:defaultNavHost="true"
        app:navGraph="@navigation/nav_graph"
        app:layout_constraintTop_toTopOf="parent"
        app:layout_constraintBottom_toTopOf="@id/bottomNav"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent" />

    <com.google.android.material.bottomnavigation.BottomNavigationView
        android:id="@+id/bottomNav"
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:background="@color/ah_surface"
        app:menu="@menu/menu_bottom"
        app:layout_constraintBottom_toBottomOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent" />
</androidx.constraintlayout.widget.ConstraintLayout>
''')
    w("app/src/main/res/drawable/ic_launcher_foreground.xml", '''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp"
    android:viewportWidth="108" android:viewportHeight="108">
    <path android:fillColor="#2A9D8F"
        android:pathData="M54,30c-10,0 -18,8 -18,18v8h-6v24h48V56h-6v-8c0,-10 -8,-18 -18,-18zM46,56v-8c0,-4.4 3.6,-8 8,-8s8,3.6 8,8v8H46z"/>
</vector>
''')
    w("app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml", '''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ah_primary"/>
    <foreground android:drawable="@drawable/ic_launcher_foreground"/>
</adaptive-icon>
''')
    w("app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml", '''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ah_primary"/>
    <foreground android:drawable="@drawable/ic_launcher_foreground"/>
</adaptive-icon>
''')
    base = f"app/src/main/java/{P}/app"
    w(f"{base}/WingsApp.java", f'''
package {PKG}.app;

import android.app.Application;
import {PKG}.app.work.EscalationWorker;
import {PKG}.core.notification.ApprovalNotifier;
import {PKG}.data.di.AppContainer;
import {PKG}.data.di.AppContainerHolder;

public class WingsApp extends Application implements AppContainerHolder {{
    private AppContainer appContainer;

    @Override
    public void onCreate() {{
        super.onCreate();
        appContainer = new AppContainer(this);
        ApprovalNotifier.ensureChannel(this);
        EscalationWorker.schedule(this);
    }}

    @Override
    public AppContainer getAppContainer() {{
        return appContainer;
    }}
}}
''')
    w(f"{base}/MainActivity.java", f'''
package {PKG}.app;

import android.os.Bundle;
import android.view.View;
import androidx.appcompat.app.AppCompatActivity;
import androidx.navigation.NavController;
import androidx.navigation.fragment.NavHostFragment;
import androidx.navigation.ui.NavigationUI;
import com.google.android.material.bottomnavigation.BottomNavigationView;
import {PKG}.core.database.AppDatabase;
import {PKG}.core.ui.NavRoutes;
import {PKG}.data.di.AppContainerHolder;
import {PKG}.domain.repository.SessionRepository;

public class MainActivity extends AppCompatActivity {{
    @Override
    protected void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        NavHostFragment navHost = (NavHostFragment) getSupportFragmentManager().findFragmentById(R.id.nav_host);
        NavController navController = navHost.getNavController();
        BottomNavigationView bottomNav = findViewById(R.id.bottomNav);
        NavigationUI.setupWithNavController(bottomNav, navController);
        navController.addOnDestinationChangedListener((controller, destination, arguments) -> {{
            int id = destination.getId();
            boolean hide = id == R.id.loginFragment
                    || id == R.id.createRequestFragment
                    || id == R.id.approvalDetailFragment;
            bottomNav.setVisibility(hide ? View.GONE : View.VISIBLE);
        }});
    }}

    @Override
    protected void onResume() {{
        super.onResume();
        SessionRepository session = ((AppContainerHolder) getApplication()).getAppContainer().sessionRepository;
        AppDatabase.IO.execute(() -> {{
            if (session.checkSessionTimeout()) {{
                runOnUiThread(() -> {{
                    NavHostFragment navHost = (NavHostFragment) getSupportFragmentManager().findFragmentById(R.id.nav_host);
                    if (navHost != null) navHost.getNavController().navigate(NavRoutes.LOGIN);
                }});
            }}
        }});
    }}
}}
''')
    w(f"{base}/work/EscalationWorker.java", f'''
package {PKG}.app.work;

import android.content.Context;
import androidx.annotation.NonNull;
import androidx.work.ExistingPeriodicWorkPolicy;
import androidx.work.OneTimeWorkRequest;
import androidx.work.PeriodicWorkRequest;
import androidx.work.WorkManager;
import androidx.work.Worker;
import androidx.work.WorkerParameters;
import {PKG}.core.database.AppDatabase;
import {PKG}.core.database.entity.ApprovalActionEntity;
import {PKG}.core.database.entity.ApprovalRequestEntity;
import {PKG}.core.network.FakeRemoteApi;
import {PKG}.core.notification.ApprovalNotifier;
import {PKG}.core.model.ApprovalStatus;
import {PKG}.data.sync.SyncRepository;
import {PKG}.domain.approval.ApprovalWorkflow;
import java.util.List;
import java.util.concurrent.TimeUnit;

public class EscalationWorker extends Worker {{
    private static final String UNIQUE = "escalation_periodic";

    public EscalationWorker(@NonNull Context context, @NonNull WorkerParameters params) {{
        super(context, params);
    }}

    @NonNull
    @Override
    public Result doWork() {{
        AppDatabase db = AppDatabase.get(getApplicationContext());
        long now = System.currentTimeMillis();
        long threshold = now - ApprovalWorkflow.IDLE_BEFORE_ESCALATE_MS;
        List<ApprovalRequestEntity> overdue = db.approvalRequestDao().getOverdue(threshold);
        int escalatedCount = 0;
        for (ApprovalRequestEntity request : overdue) {{
            ApprovalStatus next = ApprovalWorkflow.escalateStatus(request.status, request.requiredMaxLevel);
            if (next == null) continue;
            Integer level = ApprovalWorkflow.requiredLevel(next);
            if (level == null) continue;
            request.status = next;
            request.currentLevel = level;
            request.escalated = true;
            request.updatedAt = now;
            db.approvalRequestDao().update(request);
            db.approvalActionDao().insert(new ApprovalActionEntity(
                    request.id, 1, request.currentLevel, "ESCALATE",
                    "Auto-escalate karena idle > 2 hari", now));
            escalatedCount++;
        }}
        int pending = db.approvalRequestDao().pendingCountSync();
        if (pending > 0 || escalatedCount > 0) {{
            String body = (escalatedCount > 0 ? escalatedCount + " request di-escalate. " : "")
                    + pending + " request masih pending.";
            ApprovalNotifier.notifyInbox(getApplicationContext(),
                    escalatedCount > 0 ? "Escalation & Inbox" : "Approval Inbox",
                    body, 2001);
        }}
        return Result.success();
    }}

    public static void schedule(Context context) {{
        PeriodicWorkRequest request = new PeriodicWorkRequest.Builder(EscalationWorker.class, 6, TimeUnit.HOURS).build();
        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                UNIQUE, ExistingPeriodicWorkPolicy.UPDATE, request);
    }}
}}

class SyncWorker extends Worker {{
    public SyncWorker(@NonNull Context context, @NonNull WorkerParameters params) {{
        super(context, params);
    }}

    @NonNull
    @Override
    public Result doWork() {{
        try {{
            AppDatabase db = AppDatabase.get(getApplicationContext());
            new SyncRepository(db, new FakeRemoteApi()).syncNow();
            return Result.success();
        }} catch (Exception e) {{
            return Result.retry();
        }}
    }}

    public static void enqueueOnce(Context context) {{
        WorkManager.getInstance(context).enqueue(new OneTimeWorkRequest.Builder(SyncWorker.class).build());
    }}
}}
''')

    # DI holder lives in data; AppContainer implementation lives in :app (avoids cycles)
    w(f"data/src/main/java/{P}/data/di/AppContainerHolder.java", f'''
package {PKG}.data.di;

import {PKG}.domain.repository.ApprovalRepository;
import {PKG}.domain.repository.SessionRepository;

public interface AppContainerHolder {{
    SessionRepository getSessionRepository();
    ApprovalRepository getApprovalRepository();
}}
''')
    w(f"{base}/di/AppContainer.java", f'''
package {PKG}.app.di;

import android.content.Context;
import androidx.annotation.NonNull;
import androidx.lifecycle.ViewModel;
import androidx.lifecycle.ViewModelProvider;
import {PKG}.core.database.AppDatabase;
import {PKG}.core.network.FakeRemoteApi;
import {PKG}.core.preference.UserPreferences;
import {PKG}.data.repository.AppRepository;
import {PKG}.data.sync.SyncRepository;
import {PKG}.domain.repository.ApprovalRepository;
import {PKG}.domain.repository.SessionRepository;
import {PKG}.feature.analytics.AnalyticsViewModel;
import {PKG}.feature.audit.AuditViewModel;
import {PKG}.feature.auth.LoginViewModel;
import {PKG}.feature.dashboard.DashboardViewModel;
import {PKG}.feature.inbox.InboxViewModel;
import {PKG}.feature.request.ApprovalDetailViewModel;
import {PKG}.feature.request.CreateRequestViewModel;
import {PKG}.feature.settings.SettingsViewModel;

public class AppContainer {{
    public final SessionRepository sessionRepository;
    public final ApprovalRepository approvalRepository;
    public final ViewModelProvider.Factory factory;

    public AppContainer(Context context) {{
        Context app = context.getApplicationContext();
        AppDatabase database = AppDatabase.get(app);
        UserPreferences preferences = new UserPreferences(app);
        SyncRepository syncRepository = new SyncRepository(database, new FakeRemoteApi());
        AppRepository appRepository = new AppRepository(database, preferences, syncRepository, app);
        sessionRepository = appRepository;
        approvalRepository = appRepository;
        factory = new ViewModelProvider.Factory() {{
            @NonNull
            @Override
            @SuppressWarnings("unchecked")
            public <T extends ViewModel> T create(@NonNull Class<T> modelClass) {{
                if (modelClass.isAssignableFrom(LoginViewModel.class)) {{
                    return (T) new LoginViewModel(sessionRepository);
                }}
                if (modelClass.isAssignableFrom(DashboardViewModel.class)) {{
                    return (T) new DashboardViewModel(sessionRepository, approvalRepository);
                }}
                if (modelClass.isAssignableFrom(InboxViewModel.class)) {{
                    return (T) new InboxViewModel(approvalRepository);
                }}
                if (modelClass.isAssignableFrom(CreateRequestViewModel.class)) {{
                    return (T) new CreateRequestViewModel(approvalRepository);
                }}
                if (modelClass.isAssignableFrom(AnalyticsViewModel.class)) {{
                    return (T) new AnalyticsViewModel(approvalRepository);
                }}
                if (modelClass.isAssignableFrom(AuditViewModel.class)) {{
                    return (T) new AuditViewModel(approvalRepository);
                }}
                if (modelClass.isAssignableFrom(SettingsViewModel.class)) {{
                    return (T) new SettingsViewModel(sessionRepository, approvalRepository);
                }}
                throw new IllegalArgumentException("Unknown ViewModel: " + modelClass.getName());
            }}
        }};
    }}

    public ViewModelProvider.Factory factoryForDetail(long requestId) {{
        return new ViewModelProvider.Factory() {{
            @NonNull
            @Override
            @SuppressWarnings("unchecked")
            public <T extends ViewModel> T create(@NonNull Class<T> modelClass) {{
                if (modelClass.isAssignableFrom(ApprovalDetailViewModel.class)) {{
                    return (T) new ApprovalDetailViewModel(requestId, sessionRepository, approvalRepository);
                }}
                throw new IllegalArgumentException("Unknown ViewModel: " + modelClass.getName());
            }}
        }};
    }}
}}
''')
    w(f"{base}/WingsApp.java", f'''
package {PKG}.app;

import android.app.Application;
import {PKG}.app.di.AppContainer;
import {PKG}.app.work.EscalationWorker;
import {PKG}.core.notification.ApprovalNotifier;
import {PKG}.data.di.AppContainerHolder;
import {PKG}.domain.repository.ApprovalRepository;
import {PKG}.domain.repository.SessionRepository;

public class WingsApp extends Application implements AppContainerHolder {{
    private AppContainer appContainer;

    @Override
    public void onCreate() {{
        super.onCreate();
        appContainer = new AppContainer(this);
        ApprovalNotifier.ensureChannel(this);
        EscalationWorker.schedule(this);
    }}

    public AppContainer getAppContainer() {{
        return appContainer;
    }}

    @Override
    public SessionRepository getSessionRepository() {{
        return appContainer.sessionRepository;
    }}

    @Override
    public ApprovalRepository getApprovalRepository() {{
        return appContainer.approvalRepository;
    }}
}}
''')


print("features/app generators ready")
