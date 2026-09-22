#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(r"D:\fauzi\cursor\wings\android")
PKG = "com.fauzi.wings"
P = PKG.replace(".", "/")


def w(rel: str, content: str) -> None:
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    print("wrote", rel)


# Login
w(f"feature/auth/src/main/java/{P}/feature/auth/LoginUiState.java", f'''
package {PKG}.feature.auth;
import {PKG}.core.model.DemoAccounts;
import {PKG}.core.model.User;
public class LoginUiState {{
    public final boolean loading; public final String error; public final User loggedInUser; public final String demoHint;
    public LoginUiState(boolean loading, String error, User loggedInUser, String demoHint) {{
        this.loading = loading; this.error = error; this.loggedInUser = loggedInUser; this.demoHint = demoHint;
    }}
    public static LoginUiState initial() {{
        StringBuilder sb = new StringBuilder();
        for (DemoAccounts.Demo d : DemoAccounts.ALL) {{
            if (sb.length() > 0) sb.append("\\n");
            sb.append(d.username).append(" / ").append(d.password).append(" · ").append(d.roleLabel);
        }}
        return new LoginUiState(false, null, null, sb.toString());
    }}
}}
''')

w(f"feature/auth/src/main/java/{P}/feature/auth/LoginViewModel.java", f'''
package {PKG}.feature.auth;
import androidx.lifecycle.LiveData; import androidx.lifecycle.MutableLiveData; import androidx.lifecycle.ViewModel;
import {PKG}.core.database.AppDatabase; import {PKG}.core.model.User; import {PKG}.domain.repository.SessionRepository;
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
                uiState.postValue(new LoginUiState(false, null, restored, cur.demoHint));
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

w(f"feature/auth/src/main/java/{P}/feature/auth/LoginFragment.java", f'''
package {PKG}.feature.auth;
import android.os.Bundle; import android.view.*; import android.widget.*;
import androidx.annotation.*; import androidx.fragment.app.Fragment;
import androidx.lifecycle.ViewModelProvider; import androidx.navigation.NavOptions; import androidx.navigation.Navigation;
import com.google.android.material.textfield.TextInputEditText;
import {PKG}.core.ui.NavRoutes; import {PKG}.data.di.HasAppContainer;
public class LoginFragment extends Fragment {{
    private LoginViewModel viewModel;
    @Nullable @Override public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {{
        return inflater.inflate(R.layout.fragment_login, container, false);
    }}
    @Override public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        viewModel = new ViewModelProvider(this, HasAppContainer.from(requireContext()).getViewModelFactory()).get(LoginViewModel.class);
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
            if (state.error != null) {{ textError.setVisibility(View.VISIBLE); textError.setText(state.error); }}
            else textError.setVisibility(View.GONE);
            if (state.loggedInUser != null) {{
                Navigation.findNavController(view).navigate(NavRoutes.DASHBOARD, new NavOptions.Builder().setLaunchSingleTop(true).build());
            }}
        }});
    }}
}}
''')

# Dashboard
w(f"feature/dashboard/src/main/java/{P}/feature/dashboard/DashboardViewModel.java", f'''
package {PKG}.feature.dashboard;
import androidx.lifecycle.*;
import {PKG}.core.model.*; import {PKG}.data.repository.AppRepository;
import {PKG}.domain.rbac.RbacPolicy; import {PKG}.domain.repository.*;
import java.util.List;
public class DashboardViewModel extends ViewModel {{
    private final AppRepository appRepository;
    private final MediatorLiveData<DashboardUiState> uiState = new MediatorLiveData<>(DashboardUiState.empty());
    public DashboardViewModel(SessionRepository sessionRepository, ApprovalRepository approvalRepository) {{
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
        RequestFilter f = new RequestFilter(); f.query = query; appRepository.updateFilter(f);
    }}
}}
''')

w(f"feature/dashboard/src/main/java/{P}/feature/dashboard/DashboardFragment.java", f'''
package {PKG}.feature.dashboard;
import android.os.Bundle; import android.text.*; import android.view.View;
import androidx.annotation.*; import androidx.lifecycle.ViewModelProvider;
import androidx.navigation.Navigation; import androidx.recyclerview.widget.LinearLayoutManager;
import {PKG}.core.ui.*; import {PKG}.data.di.HasAppContainer;
import {PKG}.feature.dashboard.databinding.FragmentDashboardBinding;
public class DashboardFragment extends BaseMvvmFragment<FragmentDashboardBinding, DashboardViewModel> {{
    private RequestListAdapter adapter;
    public DashboardFragment() {{ super(R.layout.fragment_dashboard); }}
    @NonNull @Override protected DashboardViewModel createViewModel() {{
        return new ViewModelProvider(this, HasAppContainer.from(requireContext()).getViewModelFactory()).get(DashboardViewModel.class);
    }}
    @Override public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        adapter = new RequestListAdapter(req -> Navigation.findNavController(view).navigate(NavRoutes.detail(req.id)));
        binding.recycler.setLayoutManager(new LinearLayoutManager(requireContext()));
        binding.recycler.setAdapter(adapter);
        binding.btnCreate.setOnClickListener(v -> Navigation.findNavController(view).navigate(NavRoutes.CREATE));
        if (binding.inputFilter != null) {{
            binding.inputFilter.addTextChangedListener(new TextWatcher() {{
                @Override public void beforeTextChanged(CharSequence s, int st, int c, int a) {{}}
                @Override public void onTextChanged(CharSequence s, int st, int b, int c) {{ viewModel.setFilterQuery(s == null ? "" : s.toString()); }}
                @Override public void afterTextChanged(Editable s) {{}}
            }});
        }}
        observe(viewModel.getUiState(), state -> {{
            binding.setTitle(state.title);
            binding.setUserLine(state.user == null ? "" : state.user.displayName + " · " + state.user.role + " · " + state.user.department);
            binding.setStats("Visible " + state.stats.totalVisible + " · Inbox " + state.stats.pendingInbox
                    + " · Approved " + state.stats.approved + " · Rejected " + state.stats.rejected + " · Pipeline " + state.stats.inPipeline);
            adapter.submitList(state.requests);
        }});
    }}
}}
''')

# Inbox
w(f"feature/inbox/src/main/java/{P}/feature/inbox/InboxViewModel.java", f'''
package {PKG}.feature.inbox;
import androidx.lifecycle.*;
import {PKG}.domain.repository.ApprovalRepository;
public class InboxViewModel extends ViewModel {{
    private final LiveData<InboxUiState> uiState;
    public InboxViewModel(ApprovalRepository approvalRepository) {{
        uiState = Transformations.map(approvalRepository.observeInbox(), InboxUiState::new);
    }}
    public LiveData<InboxUiState> getUiState() {{ return uiState; }}
}}
''')

w(f"feature/inbox/src/main/java/{P}/feature/inbox/InboxUiState.java", f'''
package {PKG}.feature.inbox;
import {PKG}.core.model.ApprovalRequest; import java.util.*;
public class InboxUiState {{
    public final List<ApprovalRequest> items;
    public InboxUiState(List<ApprovalRequest> items) {{ this.items = items == null ? Collections.emptyList() : items; }}
}}
''')

w(f"feature/inbox/src/main/java/{P}/feature/inbox/InboxFragment.java", f'''
package {PKG}.feature.inbox;
import android.os.Bundle; import android.view.View;
import androidx.annotation.*; import androidx.lifecycle.ViewModelProvider;
import androidx.navigation.Navigation; import androidx.recyclerview.widget.LinearLayoutManager;
import {PKG}.core.ui.*; import {PKG}.data.di.HasAppContainer;
import {PKG}.feature.inbox.databinding.FragmentInboxBinding;
public class InboxFragment extends BaseMvvmFragment<FragmentInboxBinding, InboxViewModel> {{
    private RequestListAdapter adapter;
    public InboxFragment() {{ super(R.layout.fragment_inbox); }}
    @NonNull @Override protected InboxViewModel createViewModel() {{
        return new ViewModelProvider(this, HasAppContainer.from(requireContext()).getViewModelFactory()).get(InboxViewModel.class);
    }}
    @Override public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        adapter = new RequestListAdapter(req -> Navigation.findNavController(view).navigate(NavRoutes.detail(req.id)));
        binding.recycler.setLayoutManager(new LinearLayoutManager(requireContext()));
        binding.recycler.setAdapter(adapter);
        observe(viewModel.getUiState(), state -> {{
            binding.setEmptyText(state.items.isEmpty() ? "Tidak ada item menunggu aksi Anda" : "");
            adapter.submitList(state.items);
        }});
    }}
}}
''')

print("auth/dashboard/inbox done")
