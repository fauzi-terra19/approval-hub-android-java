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


# Create request
w(f"feature/request/src/main/java/{P}/feature/request/CreateRequestUiState.java", f'''
package {PKG}.feature.request;
public class CreateRequestUiState {{
    public final String ruleHint; public final String error; public final Long createdId; public final boolean loading;
    public CreateRequestUiState(String ruleHint, String error, Long createdId, boolean loading) {{
        this.ruleHint = ruleHint == null ? "" : ruleHint; this.error = error; this.createdId = createdId; this.loading = loading;
    }}
}}
''')

w(f"feature/request/src/main/java/{P}/feature/request/CreateRequestViewModel.java", f'''
package {PKG}.feature.request;
import androidx.lifecycle.*;
import {PKG}.core.database.AppDatabase; import {PKG}.core.model.RequestType;
import {PKG}.domain.approval.AmountBasedRules; import {PKG}.domain.repository.ApprovalRepository;
public class CreateRequestViewModel extends ViewModel {{
    private final ApprovalRepository approvalRepository;
    private final MutableLiveData<CreateRequestUiState> uiState = new MutableLiveData<>(new CreateRequestUiState("", null, null, false));
    public CreateRequestViewModel(ApprovalRepository approvalRepository) {{ this.approvalRepository = approvalRepository; }}
    public LiveData<CreateRequestUiState> getUiState() {{ return uiState; }}
    public void updateHint(RequestType type, double amount) {{
        uiState.setValue(new CreateRequestUiState(AmountBasedRules.ruleLabel(type, amount), null, null, false));
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

w(f"feature/request/src/main/java/{P}/feature/request/CreateRequestFragment.java", f'''
package {PKG}.feature.request;
import android.os.Bundle; import android.view.View; import android.widget.ArrayAdapter;
import androidx.annotation.*; import androidx.lifecycle.ViewModelProvider; import androidx.navigation.Navigation;
import {PKG}.core.model.RequestType; import {PKG}.core.ui.BaseMvvmFragment; import {PKG}.data.di.HasAppContainer;
import {PKG}.feature.request.databinding.FragmentCreateRequestBinding;
public class CreateRequestFragment extends BaseMvvmFragment<FragmentCreateRequestBinding, CreateRequestViewModel> {{
    public CreateRequestFragment() {{ super(R.layout.fragment_create_request); }}
    @NonNull @Override protected CreateRequestViewModel createViewModel() {{
        return new ViewModelProvider(this, HasAppContainer.from(requireContext()).getViewModelFactory()).get(CreateRequestViewModel.class);
    }}
    @Override public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        RequestType[] types = RequestType.values();
        String[] names = new String[types.length];
        for (int i = 0; i < types.length; i++) names[i] = types[i].name();
        binding.spinnerType.setAdapter(new ArrayAdapter<>(requireContext(), android.R.layout.simple_spinner_dropdown_item, names));
        binding.btnSubmit.setOnClickListener(v -> {{
            RequestType type = types[binding.spinnerType.getSelectedItemPosition()];
            double amount = 0;
            try {{ String t = binding.inputAmount.getText() == null ? "0" : binding.inputAmount.getText().toString();
                amount = Double.parseDouble(t.isEmpty() ? "0" : t); }} catch (Exception ignored) {{}}
            viewModel.updateHint(type, amount);
            viewModel.submit(binding.inputTitle.getText() == null ? "" : binding.inputTitle.getText().toString(),
                    binding.inputDesc.getText() == null ? "" : binding.inputDesc.getText().toString(), type, amount);
        }});
        observe(viewModel.getUiState(), state -> {{
            binding.setRuleHint(state.ruleHint);
            binding.setError(state.error == null ? "" : state.error);
            if (state.createdId != null) Navigation.findNavController(view).navigateUp();
        }});
    }}
}}
''')

w(f"feature/request/src/main/java/{P}/feature/request/ApprovalDetailUiState.java", f'''
package {PKG}.feature.request;
import {PKG}.core.model.*; import java.util.*;
public class ApprovalDetailUiState {{
    public final ApprovalRequest request; public final List<ApprovalAction> actions;
    public final boolean canAct; public final boolean canEscalate; public final String message; public final String detailText;
    public ApprovalDetailUiState(ApprovalRequest request, List<ApprovalAction> actions, boolean canAct, boolean canEscalate, String message, String detailText) {{
        this.request = request; this.actions = actions == null ? Collections.emptyList() : actions;
        this.canAct = canAct; this.canEscalate = canEscalate;
        this.message = message == null ? "" : message; this.detailText = detailText == null ? "" : detailText;
    }}
}}
''')

w(f"feature/request/src/main/java/{P}/feature/request/ApprovalDetailViewModel.java", f'''
package {PKG}.feature.request;
import androidx.lifecycle.*;
import {PKG}.core.database.AppDatabase; import {PKG}.core.model.*;
import {PKG}.domain.approval.ApprovalWorkflow; import {PKG}.domain.repository.*;
import java.util.List;
public class ApprovalDetailViewModel extends ViewModel {{
    private final long requestId; private final SessionRepository sessionRepository; private final ApprovalRepository approvalRepository;
    private final MutableLiveData<String> message = new MutableLiveData<>("");
    private final MediatorLiveData<ApprovalDetailUiState> uiState = new MediatorLiveData<>();
    public ApprovalDetailViewModel(long requestId, SessionRepository sessionRepository, ApprovalRepository approvalRepository) {{
        this.requestId = requestId; this.sessionRepository = sessionRepository; this.approvalRepository = approvalRepository;
        LiveData<List<ApprovalAction>> actions = approvalRepository.observeActions(requestId);
        LiveData<User> session = sessionRepository.observeSession();
        LiveData<Role> imp = sessionRepository.observeImpersonateRole();
        Runnable compute = () -> {{
            ApprovalRequest req = approvalRepository.getRequest(requestId);
            User user = session.getValue();
            Role role = user == null ? null : user.role;
            boolean canAct = req != null && role != null && ApprovalWorkflow.canActOn(req.status, role, imp.getValue() != null);
            boolean canEscalate = sessionRepository.hasPermission(Permission.FORCE_ESCALATE) && req != null && !ApprovalWorkflow.isTerminal(req.status);
            String detail = req == null ? "Loading…" : "#" + req.id + " " + req.title + "\\n" + req.description + "\\n"
                    + ApprovalWorkflow.levelLabel(req.status) + " · " + req.type + " · " + req.amount + "\\n"
                    + "Dept " + req.department + " · Max L" + req.requiredMaxLevel + (req.escalated ? " · ESCALATED" : "");
            uiState.postValue(new ApprovalDetailUiState(req, actions.getValue(), canAct, canEscalate, message.getValue(), detail));
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
            try {{ approvalRepository.decide(requestId, approve, comment); message.postValue("Berhasil"); }}
            catch (Exception e) {{ message.postValue(e.getMessage() == null ? "Gagal" : e.getMessage()); }}
        }});
    }}
    public void escalate() {{
        AppDatabase.IO.execute(() -> {{
            try {{ approvalRepository.forceEscalate(requestId); message.postValue("Escalated"); }}
            catch (Exception e) {{ message.postValue(e.getMessage() == null ? "Gagal" : e.getMessage()); }}
        }});
    }}
}}
''')

w(f"feature/request/src/main/java/{P}/feature/request/ApprovalDetailFragment.java", f'''
package {PKG}.feature.request;
import android.os.Bundle; import android.view.View;
import androidx.annotation.*; import androidx.lifecycle.ViewModelProvider; import androidx.lifecycle.viewmodel.MutableCreationExtras;
import {PKG}.core.common.DateFormatters; import {PKG}.core.model.ApprovalAction;
import {PKG}.core.ui.BaseMvvmFragment; import {PKG}.data.di.HasAppContainer;
import {PKG}.app.ViewModelFactory;
import {PKG}.feature.request.databinding.FragmentApprovalDetailBinding;
public class ApprovalDetailFragment extends BaseMvvmFragment<FragmentApprovalDetailBinding, ApprovalDetailViewModel> {{
    public ApprovalDetailFragment() {{ super(R.layout.fragment_approval_detail); }}
    @NonNull @Override protected ApprovalDetailViewModel createViewModel() {{
        long requestId = getArguments() == null ? 0L : getArguments().getLong("requestId", 0L);
        MutableCreationExtras extras = new MutableCreationExtras();
        extras.set(ViewModelFactory.REQUEST_ID_KEY, requestId);
        return new ViewModelProvider(getViewModelStore(), HasAppContainer.from(requireContext()).getViewModelFactory(), extras)
                .get(ApprovalDetailViewModel.class);
    }}
    @Override public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        binding.btnApprove.setOnClickListener(v -> viewModel.decide(true, binding.inputComment.getText() == null ? "" : binding.inputComment.getText().toString()));
        binding.btnReject.setOnClickListener(v -> viewModel.decide(false, binding.inputComment.getText() == null ? "" : binding.inputComment.getText().toString()));
        binding.btnEscalate.setOnClickListener(v -> viewModel.escalate());
        observe(viewModel.getUiState(), state -> {{
            binding.setDetail(state.detailText); binding.setCanAct(state.canAct);
            binding.setCanEscalate(state.canEscalate); binding.setMessage(state.message);
            StringBuilder sb = new StringBuilder();
            for (ApprovalAction a : state.actions) {{
                if (sb.length() > 0) sb.append("\\n");
                sb.append("L").append(a.level).append(" ").append(a.decision).append(" — ").append(a.comment)
                        .append(" (").append(DateFormatters.full(a.createdAt)).append(")");
            }}
            binding.textActions.setText(sb.toString());
        }});
    }}
}}
''')

# Analytics, Audit, Settings - compact
w(f"feature/analytics/src/main/java/{P}/feature/analytics/AnalyticsUiState.java", f'''
package {PKG}.feature.analytics;
import {PKG}.core.model.StatusCount; import java.util.*;
public class AnalyticsUiState {{
    public final List<StatusCount> statusCounts; public final String content;
    public AnalyticsUiState(List<StatusCount> statusCounts, String content) {{
        this.statusCounts = statusCounts == null ? Collections.emptyList() : statusCounts;
        this.content = content == null ? "" : content;
    }}
}}
''')

w(f"feature/analytics/src/main/java/{P}/feature/analytics/AnalyticsViewModel.java", f'''
package {PKG}.feature.analytics;
import androidx.lifecycle.*;
import {PKG}.core.database.AppDatabase; import {PKG}.core.model.*;
import {PKG}.domain.analytics.*; import {PKG}.domain.repository.ApprovalRepository;
import java.util.*;
public class AnalyticsViewModel extends ViewModel {{
    private final MutableLiveData<SlaStats> sla = new MutableLiveData<>();
    private final MutableLiveData<List<BottleneckLevel>> bn = new MutableLiveData<>();
    private final MediatorLiveData<AnalyticsUiState> uiState = new MediatorLiveData<>();
    public AnalyticsViewModel(ApprovalRepository approvalRepository) {{
        AppDatabase.IO.execute(() -> {{ sla.postValue(approvalRepository.computeSla()); bn.postValue(approvalRepository.computeBottleneck()); }});
        LiveData<List<StatusCount>> status = approvalRepository.observeStatusCounts();
        LiveData<List<TypeStat>> types = approvalRepository.observeTypeStats();
        Runnable compute = () -> {{
            StringBuilder text = new StringBuilder("Status counts:\\n");
            List<StatusCount> s = status.getValue(); List<TypeStat> t = types.getValue();
            if (s != null) for (StatusCount sc : s) text.append(" · ").append(sc.status).append(": ").append(sc.count).append("\\n");
            text.append("\\nBy type:\\n");
            if (t != null) for (TypeStat ts : t) text.append(" · ").append(ts.type).append(": ").append(ts.count).append(" (sum ").append(ts.totalAmount).append(")\\n");
            SlaStats slaVal = sla.getValue();
            if (slaVal != null) text.append("\\nSLA ").append(slaVal.slaHours).append("h: ").append(slaVal.withinSlaCount).append("/").append(slaVal.completedCount)
                    .append(String.format(Locale.US, " (%.1f%%)\\n", slaVal.withinSlaPercent));
            text.append("\\nBottleneck:\\n");
            List<BottleneckLevel> bnVal = bn.getValue();
            if (bnVal != null) for (BottleneckLevel b : bnVal) text.append(String.format(Locale.US, " · L%d: %.1fh (n=%d)\\n", b.level, b.avgWaitHours, b.sampleCount));
            uiState.postValue(new AnalyticsUiState(s, text.toString()));
        }};
        uiState.addSource(status, v -> compute.run()); uiState.addSource(types, v -> compute.run());
        uiState.addSource(sla, v -> compute.run()); uiState.addSource(bn, v -> compute.run());
    }}
    public LiveData<AnalyticsUiState> getUiState() {{ return uiState; }}
    public List<String> chartLabels() {{ List<String> out = new ArrayList<>(); AnalyticsUiState s = uiState.getValue(); if (s != null) for (StatusCount c : s.statusCounts) out.add(c.status.name()); return out; }}
    public List<Float> chartValues() {{ List<Float> out = new ArrayList<>(); AnalyticsUiState s = uiState.getValue(); if (s != null) for (StatusCount c : s.statusCounts) out.add((float) c.count); return out; }}
}}
''')

w(f"feature/analytics/src/main/java/{P}/feature/analytics/AnalyticsFragment.java", f'''
package {PKG}.feature.analytics;
import android.os.Bundle; import android.view.View;
import androidx.annotation.*; import androidx.lifecycle.ViewModelProvider;
import {PKG}.core.ui.BaseMvvmFragment; import {PKG}.data.di.HasAppContainer; import {PKG}.data.export.ExportUtils;
import {PKG}.feature.analytics.databinding.FragmentAnalyticsBinding;
public class AnalyticsFragment extends BaseMvvmFragment<FragmentAnalyticsBinding, AnalyticsViewModel> {{
    public AnalyticsFragment() {{ super(R.layout.fragment_analytics); }}
    @NonNull @Override protected AnalyticsViewModel createViewModel() {{
        return new ViewModelProvider(this, HasAppContainer.from(requireContext()).getViewModelFactory()).get(AnalyticsViewModel.class);
    }}
    @Override public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        binding.btnExportChart.setOnClickListener(v -> {{
            try {{ if (!viewModel.chartValues().isEmpty())
                ExportUtils.shareBitmap(requireContext(), ExportUtils.createSimpleChartBitmap(viewModel.chartLabels(), viewModel.chartValues(), "Status distribution"), "ApprovalHub Chart");
            }} catch (Exception ignored) {{}}
        }});
        observe(viewModel.getUiState(), state -> binding.setContent(state.content));
    }}
}}
''')

w(f"feature/audit/src/main/java/{P}/feature/audit/AuditUiState.java", f'''
package {PKG}.feature.audit;
import {PKG}.core.model.*; import java.util.*;
public class AuditUiState {{
    public final List<ApprovalRequest> requests; public final List<ApprovalAction> actions;
    public final Map<Long, String> names; public final String content;
    public AuditUiState(List<ApprovalRequest> requests, List<ApprovalAction> actions, Map<Long, String> names, String content) {{
        this.requests = requests == null ? Collections.emptyList() : requests;
        this.actions = actions == null ? Collections.emptyList() : actions;
        this.names = names == null ? Collections.emptyMap() : names;
        this.content = content == null ? "" : content;
    }}
}}
''')

w(f"feature/audit/src/main/java/{P}/feature/audit/AuditViewModel.java", f'''
package {PKG}.feature.audit;
import androidx.lifecycle.*;
import {PKG}.core.database.AppDatabase; import {PKG}.core.model.*; import {PKG}.domain.repository.ApprovalRepository;
import java.util.*;
public class AuditViewModel extends ViewModel {{
    private final MutableLiveData<AuditUiState> uiState = new MutableLiveData<>(new AuditUiState(null, null, null, "Loading…"));
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
                for (ApprovalAction a : actions) if (a.requestId == r.id)
                    text.append("  L").append(a.level).append(" ").append(a.decision).append(" by ")
                            .append(names.getOrDefault(a.actorId, String.valueOf(a.actorId))).append(" — ").append(a.comment).append("\\n");
            }}
            uiState.postValue(new AuditUiState(requests, actions, names, text.toString()));
        }});
    }}
    public LiveData<AuditUiState> getUiState() {{ return uiState; }}
}}
''')

w(f"feature/audit/src/main/java/{P}/feature/audit/AuditFragment.java", f'''
package {PKG}.feature.audit;
import android.net.Uri; import android.os.Bundle; import android.view.View;
import androidx.annotation.*; import androidx.lifecycle.ViewModelProvider;
import {PKG}.core.ui.BaseMvvmFragment; import {PKG}.data.di.HasAppContainer; import {PKG}.data.export.ExportUtils;
import {PKG}.feature.audit.databinding.FragmentAuditBinding;
public class AuditFragment extends BaseMvvmFragment<FragmentAuditBinding, AuditViewModel> {{
    public AuditFragment() {{ super(R.layout.fragment_audit); }}
    @NonNull @Override protected AuditViewModel createViewModel() {{
        return new ViewModelProvider(this, HasAppContainer.from(requireContext()).getViewModelFactory()).get(AuditViewModel.class);
    }}
    @Override public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        binding.btnCsv.setOnClickListener(v -> {{ try {{ AuditUiState s = viewModel.getUiState().getValue(); if (s == null) return;
            Uri uri = ExportUtils.exportAuditCsv(requireContext(), s.requests, s.actions, s.names);
            ExportUtils.shareUri(requireContext(), uri, "text/csv", "Audit CSV"); }} catch (Exception ignored) {{}} }});
        binding.btnPdf.setOnClickListener(v -> {{ try {{ AuditUiState s = viewModel.getUiState().getValue(); if (s == null) return;
            Uri uri = ExportUtils.exportAuditPdf(requireContext(), s.requests, s.actions, s.names);
            ExportUtils.shareUri(requireContext(), uri, "application/pdf", "Audit PDF"); }} catch (Exception ignored) {{}} }});
        observe(viewModel.getUiState(), state -> binding.setContent(state.content));
    }}
}}
''')

w(f"feature/settings/src/main/java/{P}/feature/settings/SettingsUiState.java", f'''
package {PKG}.feature.settings;
import {PKG}.core.model.*;
public class SettingsUiState {{
    public final User user; public final Role impersonate; public final String syncInfo; public final String message; public final boolean loggedOut;
    public SettingsUiState(User user, Role impersonate, String syncInfo, String message, boolean loggedOut) {{
        this.user = user; this.impersonate = impersonate; this.syncInfo = syncInfo == null ? "" : syncInfo;
        this.message = message == null ? "" : message; this.loggedOut = loggedOut;
    }}
}}
''')

w(f"feature/settings/src/main/java/{P}/feature/settings/SettingsViewModel.java", f'''
package {PKG}.feature.settings;
import androidx.lifecycle.*;
import {PKG}.core.common.DateFormatters; import {PKG}.core.database.AppDatabase; import {PKG}.core.model.*;
import {PKG}.domain.repository.*;
public class SettingsViewModel extends ViewModel {{
    private final SessionRepository sessionRepository; private final ApprovalRepository approvalRepository;
    private final MutableLiveData<String> message = new MutableLiveData<>("");
    private final MutableLiveData<Boolean> loggedOut = new MutableLiveData<>(false);
    private final MediatorLiveData<SettingsUiState> uiState = new MediatorLiveData<>();
    public SettingsViewModel(SessionRepository sessionRepository, ApprovalRepository approvalRepository) {{
        this.sessionRepository = sessionRepository; this.approvalRepository = approvalRepository;
        LiveData<User> session = sessionRepository.observeSession();
        LiveData<Role> imp = sessionRepository.observeImpersonateRole();
        LiveData<SyncMeta> meta = approvalRepository.observeSyncMeta();
        Runnable compute = () -> {{
            SyncMeta m = meta.getValue();
            String syncInfo = m == null ? "No sync meta" : "Last sync: " + (m.lastSyncedAt == 0L ? "never" : DateFormatters.full(m.lastSyncedAt))
                    + " · " + m.lastSyncStatus + " · pending " + m.pendingPushCount;
            uiState.setValue(new SettingsUiState(session.getValue(), imp.getValue(), syncInfo, message.getValue(), Boolean.TRUE.equals(loggedOut.getValue())));
        }};
        uiState.addSource(session, v -> compute.run()); uiState.addSource(imp, v -> compute.run());
        uiState.addSource(meta, v -> compute.run()); uiState.addSource(message, v -> compute.run()); uiState.addSource(loggedOut, v -> compute.run());
    }}
    public LiveData<SettingsUiState> getUiState() {{ return uiState; }}
    public void setTheme(ThemeMode mode) {{ sessionRepository.setThemeMode(mode); }}
    public void setImpersonate(Role role) {{ sessionRepository.setImpersonateRole(role); }}
    public void sync() {{ AppDatabase.IO.execute(() -> {{ try {{ approvalRepository.syncNow(); message.postValue("Sync OK"); }} catch (Exception e) {{ message.postValue(e.getMessage() == null ? "Sync failed" : e.getMessage()); }} }}); }}
    public void runEscalation() {{ AppDatabase.IO.execute(() -> message.postValue("Escalated " + approvalRepository.runEscalationPass() + " request(s)")); }}
    public void logout() {{ AppDatabase.IO.execute(() -> {{ sessionRepository.logoutAndClear(); loggedOut.postValue(true); }}); }}
}}
''')

w(f"feature/settings/src/main/java/{P}/feature/settings/SettingsFragment.java", f'''
package {PKG}.feature.settings;
import android.os.Bundle; import android.view.View; import android.widget.*;
import androidx.annotation.*; import androidx.appcompat.app.AppCompatDelegate;
import androidx.lifecycle.ViewModelProvider; import androidx.navigation.NavOptions; import androidx.navigation.Navigation;
import {PKG}.core.model.*; import {PKG}.core.ui.*; import {PKG}.data.di.HasAppContainer;
import {PKG}.feature.settings.databinding.FragmentSettingsBinding;
public class SettingsFragment extends BaseMvvmFragment<FragmentSettingsBinding, SettingsViewModel> {{
    public SettingsFragment() {{ super(R.layout.fragment_settings); }}
    @NonNull @Override protected SettingsViewModel createViewModel() {{
        return new ViewModelProvider(this, HasAppContainer.from(requireContext()).getViewModelFactory()).get(SettingsViewModel.class);
    }}
    @Override public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {{
        super.onViewCreated(view, savedInstanceState);
        ThemeMode[] themes = ThemeMode.values();
        String[] themeNames = new String[themes.length];
        for (int i = 0; i < themes.length; i++) themeNames[i] = themes[i].name();
        binding.spinnerTheme.setAdapter(new ArrayAdapter<>(requireContext(), android.R.layout.simple_spinner_dropdown_item, themeNames));
        Role[] rolesEnum = Role.values();
        String[] roleNames = new String[rolesEnum.length + 1]; roleNames[0] = "(none)";
        for (int i = 0; i < rolesEnum.length; i++) roleNames[i + 1] = rolesEnum[i].name();
        binding.spinnerImpersonate.setAdapter(new ArrayAdapter<>(requireContext(), android.R.layout.simple_spinner_dropdown_item, roleNames));
        binding.spinnerTheme.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {{
            @Override public void onItemSelected(AdapterView<?> p, View v, int pos, long id) {{
                ThemeMode mode = themes[pos]; viewModel.setTheme(mode);
                int night = mode == ThemeMode.LIGHT ? AppCompatDelegate.MODE_NIGHT_NO : mode == ThemeMode.DARK ? AppCompatDelegate.MODE_NIGHT_YES : AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM;
                AppCompatDelegate.setDefaultNightMode(night);
            }}
            @Override public void onNothingSelected(AdapterView<?> p) {{}}
        }});
        binding.spinnerImpersonate.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {{
            @Override public void onItemSelected(AdapterView<?> p, View v, int pos, long id) {{ viewModel.setImpersonate(pos == 0 ? null : rolesEnum[pos - 1]); }}
            @Override public void onNothingSelected(AdapterView<?> p) {{}}
        }});
        binding.btnSync.setOnClickListener(v -> viewModel.sync());
        binding.btnEscalate.setOnClickListener(v -> viewModel.runEscalation());
        binding.btnLogout.setOnClickListener(v -> viewModel.logout());
        observe(viewModel.getUiState(), state -> {{
            if (state.user != null) {{
                String info = state.user.displayName + " (" + state.user.username + ") · " + state.user.role;
                if (state.impersonate != null) info += " · impersonate " + state.impersonate;
                binding.setInfo(info + "\\n" + state.message);
            }} else binding.setInfo("");
            binding.setSyncInfo(state.syncInfo);
            if (state.loggedOut) {{
                Navigation.findNavController(view).navigate(NavRoutes.LOGIN, new NavOptions.Builder()
                        .setPopUpTo(Navigation.findNavController(view).getGraph().getStartDestinationId(), true).build());
            }}
        }});
    }}
}}
''')

print("request/analytics/audit/settings done")
