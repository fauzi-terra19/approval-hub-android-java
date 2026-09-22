"""Feature modules: auth, dashboard, inbox, request, analytics, audit, settings, widget."""
from __future__ import annotations


def feature_deps(extra: list[str] | None = None) -> list[str]:
    deps = [
        'api(project(":core:ui"))',
        'api(project(":domain"))',
        "implementation(libs.koin.android)",
        "implementation(libs.coroutines.android)",
        "implementation(libs.androidx.lifecycle.runtime)",
        "implementation(libs.androidx.lifecycle.viewmodel)",
        "implementation(libs.androidx.swiperefresh)",
    ]
    if extra:
        deps.extend(extra)
    return deps


def gen_features(w, lib_build, empty_consumer, PKG, P):
    _auth(w, lib_build, empty_consumer, PKG, P)
    _dashboard(w, lib_build, empty_consumer, PKG, P)
    _inbox(w, lib_build, empty_consumer, PKG, P)
    _request(w, lib_build, empty_consumer, PKG, P)
    _analytics(w, lib_build, empty_consumer, PKG, P)
    _audit(w, lib_build, empty_consumer, PKG, P)
    _settings(w, lib_build, empty_consumer, PKG, P)
    _widget(w, lib_build, empty_consumer, PKG, P)


def _auth(w, lib_build, empty_consumer, PKG, P):
    empty_consumer("feature/auth")
    w("feature/auth/build.gradle.kts", lib_build(f"{PKG}.feature.auth", feature_deps(), True, False))
    w("feature/auth/src/main/res/layout/fragment_login.xml", """
<?xml version="1.0" encoding="utf-8"?>
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
""")
    base = f"feature/auth/src/main/java/{P}/feature/auth"
    w(f"{base}/LoginViewModel.kt", f"""
package {PKG}.feature.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import {PKG}.core.model.DemoAccounts
import {PKG}.core.model.User
import {PKG}.domain.repository.SessionRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class LoginUiState(
    val loading: Boolean = false,
    val error: String? = null,
    val loggedInUser: User? = null,
    val demoHint: String = DemoAccounts.all.joinToString("\\n") {{
        "${{it.username}} / ${{it.password}} · ${{it.roleLabel}}"
    }}
)

class LoginViewModel(
    private val sessionRepository: SessionRepository
) : ViewModel() {{
    private val _uiState = MutableStateFlow(LoginUiState())
    val uiState: StateFlow<LoginUiState> = _uiState.asStateFlow()

    init {{
        viewModelScope.launch {{
            sessionRepository.ensureSeeded()
            sessionRepository.restoreSession()?.let {{ user ->
                _uiState.update {{ it.copy(loggedInUser = user) }}
            }}
        }}
    }}

    fun login(username: String, password: String) {{
        viewModelScope.launch {{
            _uiState.update {{ it.copy(loading = true, error = null) }}
            val result = sessionRepository.login(username, password)
            _uiState.update {{
                result.fold(
                    onSuccess = {{ user -> it.copy(loading = false, loggedInUser = user, error = null) }},
                    onFailure = {{ err -> it.copy(loading = false, error = err.message) }}
                )
            }}
        }}
    }}
}}
""")
    w(f"{base}/LoginFragment.kt", f"""
package {PKG}.feature.auth

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.ProgressBar
import android.widget.TextView
import androidx.fragment.app.Fragment
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import com.google.android.material.textfield.TextInputEditText
import kotlinx.coroutines.launch
import org.koin.androidx.viewmodel.ext.android.viewModel

class LoginFragment : Fragment() {{
    private val viewModel: LoginViewModel by viewModel()

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {{
        return inflater.inflate(R.layout.fragment_login, container, false)
    }}

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {{
        super.onViewCreated(view, savedInstanceState)
        // findViewById as required for LoginFragment
        val inputUsername = view.findViewById<TextInputEditText>(R.id.inputUsername)
        val inputPassword = view.findViewById<TextInputEditText>(R.id.inputPassword)
        val btnLogin = view.findViewById<Button>(R.id.btnLogin)
        val textError = view.findViewById<TextView>(R.id.textError)
        val progress = view.findViewById<ProgressBar>(R.id.progress)
        val textDemo = view.findViewById<TextView>(R.id.textDemoAccounts)

        btnLogin.setOnClickListener {{
            viewModel.login(
                inputUsername.text?.toString().orEmpty(),
                inputPassword.text?.toString().orEmpty()
            )
        }}

        viewLifecycleOwner.lifecycleScope.launch {{
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {{
                viewModel.uiState.collect {{ state ->
                    textDemo.text = state.demoHint
                    progress.visibility = if (state.loading) View.VISIBLE else View.GONE
                    btnLogin.isEnabled = !state.loading
                    if (state.error != null) {{
                        textError.visibility = View.VISIBLE
                        textError.text = state.error
                    }} else {{
                        textError.visibility = View.GONE
                    }}
                    if (state.loggedInUser != null) {{
                        findNavController().navigate({PKG}.core.ui.R.id.action_login_to_dashboard)
                    }}
                }}
            }}
        }}
    }}
}}
""")


def _dashboard(w, lib_build, empty_consumer, PKG, P):
    empty_consumer("feature/dashboard")
    w("feature/dashboard/build.gradle.kts", lib_build(f"{PKG}.feature.dashboard", feature_deps(), True, False))
    w("feature/dashboard/src/main/res/layout/fragment_dashboard.xml", """
<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto">
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
""")
    base = f"feature/dashboard/src/main/java/{P}/feature/dashboard"
    w(f"{base}/DashboardViewModel.kt", f"""
package {PKG}.feature.dashboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import {PKG}.core.model.ApprovalRequest
import {PKG}.core.model.DashboardStats
import {PKG}.core.model.User
import {PKG}.domain.rbac.RbacPolicy
import {PKG}.domain.repository.ApprovalRepository
import {PKG}.domain.repository.SessionRepository
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn

data class DashboardUiState(
    val user: User? = null,
    val title: String = "Dashboard",
    val stats: DashboardStats = DashboardStats(),
    val requests: List<ApprovalRequest> = emptyList()
)

class DashboardViewModel(
    sessionRepository: SessionRepository,
    approvalRepository: ApprovalRepository
) : ViewModel() {{
    val uiState: StateFlow<DashboardUiState> = combine(
        sessionRepository.session,
        sessionRepository.impersonateRole,
        approvalRepository.observeDashboardStats(),
        approvalRepository.observeRequestsForCurrentUser()
    ) {{ user, imp, stats, requests ->
        val role = imp ?: user?.role
        DashboardUiState(
            user = user,
            title = role?.let {{ RbacPolicy.dashboardTitle(it) }} ?: "Dashboard",
            stats = stats,
            requests = requests
        )
    }}.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), DashboardUiState())
}}
""")
    w(f"{base}/DashboardFragment.kt", f"""
package {PKG}.feature.dashboard

import android.os.Bundle
import android.view.View
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.LinearLayoutManager
import {PKG}.core.ui.BaseFragment
import {PKG}.core.ui.RequestListAdapter
import {PKG}.feature.dashboard.databinding.FragmentDashboardBinding
import kotlinx.coroutines.launch
import org.koin.androidx.viewmodel.ext.android.viewModel

class DashboardFragment : BaseFragment<FragmentDashboardBinding>(R.layout.fragment_dashboard) {{
    private val viewModel: DashboardViewModel by viewModel()
    private val adapter = RequestListAdapter {{ req ->
        findNavController().navigate(
            {PKG}.core.ui.R.id.action_global_to_detail,
            Bundle().apply {{ putLong("requestId", req.id) }}
        )
    }}

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {{
        super.onViewCreated(view, savedInstanceState)
        binding.recycler.layoutManager = LinearLayoutManager(requireContext())
        binding.recycler.adapter = adapter
        binding.btnCreate.setOnClickListener {{
            findNavController().navigate({PKG}.core.ui.R.id.action_global_to_create)
        }}
        viewLifecycleOwner.lifecycleScope.launch {{
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {{
                viewModel.uiState.collect {{ state ->
                    binding.title = state.title
                    binding.userLine = state.user?.let {{ "${{it.displayName}} · ${{it.role}} · ${{it.department}}" }} ?: ""
                    binding.stats = "Visible ${{state.stats.totalVisible}} · Inbox ${{state.stats.pendingInbox}} · " +
                        "Approved ${{state.stats.approved}} · Rejected ${{state.stats.rejected}} · Pipeline ${{state.stats.inPipeline}}"
                    adapter.submitList(state.requests)
                }}
            }}
        }}
    }}
}}
""")


def _inbox(w, lib_build, empty_consumer, PKG, P):
    empty_consumer("feature/inbox")
    w("feature/inbox/build.gradle.kts", lib_build(f"{PKG}.feature.inbox", feature_deps(), True, False))
    w("feature/inbox/src/main/res/layout/fragment_inbox.xml", """
<?xml version="1.0" encoding="utf-8"?>
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
""")
    base = f"feature/inbox/src/main/java/{P}/feature/inbox"
    w(f"{base}/InboxViewModel.kt", f"""
package {PKG}.feature.inbox

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import {PKG}.core.model.ApprovalRequest
import {PKG}.domain.repository.ApprovalRepository
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn

data class InboxUiState(val items: List<ApprovalRequest> = emptyList())

class InboxViewModel(approvalRepository: ApprovalRepository) : ViewModel() {{
    val uiState: StateFlow<InboxUiState> = approvalRepository.observeInbox()
        .map {{ InboxUiState(it) }}
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), InboxUiState())
}}
""")
    w(f"{base}/InboxFragment.kt", f"""
package {PKG}.feature.inbox

import android.os.Bundle
import android.view.View
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.LinearLayoutManager
import {PKG}.core.ui.BaseFragment
import {PKG}.core.ui.RequestListAdapter
import {PKG}.feature.inbox.databinding.FragmentInboxBinding
import kotlinx.coroutines.launch
import org.koin.androidx.viewmodel.ext.android.viewModel

class InboxFragment : BaseFragment<FragmentInboxBinding>(R.layout.fragment_inbox) {{
    private val viewModel: InboxViewModel by viewModel()
    private val adapter = RequestListAdapter {{ req ->
        findNavController().navigate(
            {PKG}.core.ui.R.id.action_global_to_detail,
            Bundle().apply {{ putLong("requestId", req.id) }}
        )
    }}

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {{
        super.onViewCreated(view, savedInstanceState)
        binding.recycler.layoutManager = LinearLayoutManager(requireContext())
        binding.recycler.adapter = adapter
        viewLifecycleOwner.lifecycleScope.launch {{
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {{
                viewModel.uiState.collect {{ state ->
                    binding.emptyText = if (state.items.isEmpty()) "Tidak ada item menunggu aksi Anda" else ""
                    adapter.submitList(state.items)
                }}
            }}
        }}
    }}
}}
""")


def _request(w, lib_build, empty_consumer, PKG, P):
    empty_consumer("feature/request")
    w("feature/request/build.gradle.kts", lib_build(f"{PKG}.feature.request", feature_deps(), True, False))
    w("feature/request/src/main/res/layout/fragment_create_request.xml", """
<?xml version="1.0" encoding="utf-8"?>
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
""")
    w("feature/request/src/main/res/layout/fragment_approval_detail.xml", """
<?xml version="1.0" encoding="utf-8"?>
<layout xmlns:android="http://schemas.android.com/apk/res/android">
    <data>
        <variable name="detail" type="String" />
        <variable name="canAct" type="Boolean" />
        <variable name="canEscalate" type="Boolean" />
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
""")
    base = f"feature/request/src/main/java/{P}/feature/request"
    w(f"{base}/CreateRequestViewModel.kt", f"""
package {PKG}.feature.request

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import {PKG}.core.model.RequestType
import {PKG}.domain.approval.AmountBasedRules
import {PKG}.domain.repository.ApprovalRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class CreateRequestUiState(
    val ruleHint: String = "",
    val error: String? = null,
    val createdId: Long? = null,
    val loading: Boolean = false
)

class CreateRequestViewModel(
    private val approvalRepository: ApprovalRepository
) : ViewModel() {{
    private val _uiState = MutableStateFlow(CreateRequestUiState())
    val uiState: StateFlow<CreateRequestUiState> = _uiState.asStateFlow()

    fun updateHint(type: RequestType, amount: Double) {{
        _uiState.update {{ it.copy(ruleHint = AmountBasedRules.ruleLabel(type, amount)) }}
    }}

    fun submit(title: String, description: String, type: RequestType, amount: Double) {{
        viewModelScope.launch {{
            _uiState.update {{ it.copy(loading = true, error = null) }}
            val result = approvalRepository.createRequest(title, description, type, amount)
            _uiState.update {{
                result.fold(
                    onSuccess = {{ id -> it.copy(loading = false, createdId = id) }},
                    onFailure = {{ e -> it.copy(loading = false, error = e.message) }}
                )
            }}
        }}
    }}
}}
""")
    w(f"{base}/CreateRequestFragment.kt", f"""
package {PKG}.feature.request

import android.os.Bundle
import android.view.View
import android.widget.ArrayAdapter
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import {PKG}.core.model.RequestType
import {PKG}.core.ui.BaseFragment
import {PKG}.feature.request.databinding.FragmentCreateRequestBinding
import kotlinx.coroutines.launch
import org.koin.androidx.viewmodel.ext.android.viewModel

class CreateRequestFragment : BaseFragment<FragmentCreateRequestBinding>(R.layout.fragment_create_request) {{
    private val viewModel: CreateRequestViewModel by viewModel()

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {{
        super.onViewCreated(view, savedInstanceState)
        val types = RequestType.entries
        binding.spinnerType.adapter = ArrayAdapter(
            requireContext(), android.R.layout.simple_spinner_dropdown_item, types.map {{ it.name }}
        )
        binding.btnSubmit.setOnClickListener {{
            val type = types[binding.spinnerType.selectedItemPosition]
            val amount = binding.inputAmount.text?.toString()?.toDoubleOrNull() ?: 0.0
            viewModel.updateHint(type, amount)
            viewModel.submit(
                binding.inputTitle.text?.toString().orEmpty(),
                binding.inputDesc.text?.toString().orEmpty(),
                type, amount
            )
        }}
        viewLifecycleOwner.lifecycleScope.launch {{
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {{
                viewModel.uiState.collect {{ state ->
                    binding.ruleHint = state.ruleHint
                    binding.error = state.error.orEmpty()
                    if (state.createdId != null) findNavController().navigateUp()
                }}
            }}
        }}
    }}
}}
""")
    w(f"{base}/ApprovalDetailViewModel.kt", f"""
package {PKG}.feature.request

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import {PKG}.core.model.ApprovalAction
import {PKG}.core.model.ApprovalRequest
import {PKG}.core.model.Permission
import {PKG}.domain.approval.ApprovalWorkflow
import {PKG}.domain.repository.ApprovalRepository
import {PKG}.domain.repository.SessionRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class ApprovalDetailUiState(
    val request: ApprovalRequest? = null,
    val actions: List<ApprovalAction> = emptyList(),
    val canAct: Boolean = false,
    val canEscalate: Boolean = false,
    val message: String = "",
    val detailText: String = ""
)

class ApprovalDetailViewModel(
    private val requestId: Long,
    private val sessionRepository: SessionRepository,
    private val approvalRepository: ApprovalRepository
) : ViewModel() {{
    private val _message = MutableStateFlow("")
    private val _refresh = MutableStateFlow(0)

    val uiState: StateFlow<ApprovalDetailUiState> = combine(
        _refresh,
        approvalRepository.observeActions(requestId),
        sessionRepository.session,
        sessionRepository.impersonateRole,
        _message
    ) {{ _, actions, user, imp, msg ->
        Triple(actions, user to imp, msg)
    }}.let {{ upstream ->
        kotlinx.coroutines.flow.channelFlow {{
            upstream.collect {{ (actions, userImp, msg) ->
                val (user, imp) = userImp
                val req = approvalRepository.getRequest(requestId)
                val role = user?.role
                val canAct = req != null && role != null && ApprovalWorkflow.canActOn(req.status, role, imp != null)
                val canEscalate = sessionRepository.hasPermission(Permission.FORCE_ESCALATE) && req != null &&
                    !ApprovalWorkflow.isTerminal(req.status)
                send(
                    ApprovalDetailUiState(
                        request = req,
                        actions = actions,
                        canAct = canAct,
                        canEscalate = canEscalate,
                        message = msg,
                        detailText = req?.let {{
                            "#${{it.id}} ${{it.title}}\\n${{it.description}}\\n" +
                                "${{ApprovalWorkflow.levelLabel(it.status)}} · ${{it.type}} · ${{it.amount}}\\n" +
                                "Dept ${{it.department}} · Max L${{it.requiredMaxLevel}}" +
                                if (it.escalated) " · ESCALATED" else ""
                        }} ?: "Loading…"
                    )
                )
            }}
        }}
    }}.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), ApprovalDetailUiState())

    fun decide(approve: Boolean, comment: String) {{
        viewModelScope.launch {{
            val result = approvalRepository.decide(requestId, approve, comment)
            _message.update {{
                result.fold(onSuccess = {{ "Berhasil" }}, onFailure = {{ e -> e.message ?: "Gagal" }})
            }}
            _refresh.update {{ it + 1 }}
        }}
    }}

    fun escalate() {{
        viewModelScope.launch {{
            val result = approvalRepository.forceEscalate(requestId)
            _message.update {{
                result.fold(onSuccess = {{ "Escalated" }}, onFailure = {{ e -> e.message ?: "Gagal" }})
            }}
            _refresh.update {{ it + 1 }}
        }}
    }}
}}
""")
    w(f"{base}/ApprovalDetailFragment.kt", f"""
package {PKG}.feature.request

import android.os.Bundle
import android.view.View
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import {PKG}.core.common.DateFormatters
import {PKG}.core.ui.BaseFragment
import {PKG}.feature.request.databinding.FragmentApprovalDetailBinding
import kotlinx.coroutines.launch
import org.koin.androidx.viewmodel.ext.android.viewModel
import org.koin.core.parameter.parametersOf

class ApprovalDetailFragment : BaseFragment<FragmentApprovalDetailBinding>(R.layout.fragment_approval_detail) {{
    private val requestId: Long by lazy {{ arguments?.getLong("requestId") ?: 0L }}
    private val viewModel: ApprovalDetailViewModel by viewModel {{ parametersOf(requestId) }}

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {{
        super.onViewCreated(view, savedInstanceState)
        binding.btnApprove.setOnClickListener {{
            viewModel.decide(true, binding.inputComment.text?.toString().orEmpty())
        }}
        binding.btnReject.setOnClickListener {{
            viewModel.decide(false, binding.inputComment.text?.toString().orEmpty())
        }}
        binding.btnEscalate.setOnClickListener {{ viewModel.escalate() }}
        viewLifecycleOwner.lifecycleScope.launch {{
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {{
                viewModel.uiState.collect {{ state ->
                    binding.detail = state.detailText
                    binding.canAct = state.canAct
                    binding.canEscalate = state.canEscalate
                    binding.message = state.message
                    binding.textActions.text = state.actions.joinToString("\\n") {{
                        "L${{it.level}} ${{it.decision}} — ${{it.comment}} (${{DateFormatters.full(it.createdAt)}})"
                    }}
                }}
            }}
        }}
    }}
}}
""")


def _analytics(w, lib_build, empty_consumer, PKG, P):
    empty_consumer("feature/analytics")
    w("feature/analytics/build.gradle.kts", lib_build(
        f"{PKG}.feature.analytics",
        feature_deps(['implementation(project(":data"))']),
        True, False,
    ))
    w("feature/analytics/src/main/res/layout/fragment_analytics.xml", """
<?xml version="1.0" encoding="utf-8"?>
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
""")
    base = f"feature/analytics/src/main/java/{P}/feature/analytics"
    w(f"{base}/AnalyticsViewModel.kt", f"""
package {PKG}.feature.analytics

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import {PKG}.core.model.StatusCount
import {PKG}.core.model.TypeStat
import {PKG}.domain.analytics.BottleneckLevel
import {PKG}.domain.analytics.SlaStats
import {PKG}.domain.repository.ApprovalRepository
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.update

data class AnalyticsUiState(
    val statusCounts: List<StatusCount> = emptyList(),
    val typeStats: List<TypeStat> = emptyList(),
    val sla: SlaStats? = null,
    val bottleneck: List<BottleneckLevel> = emptyList(),
    val content: String = "Loading…"
)

class AnalyticsViewModel(
    private val approvalRepository: ApprovalRepository
) : ViewModel() {{
    private val _sla = MutableStateFlow<SlaStats?>(null)
    private val _bn = MutableStateFlow<List<BottleneckLevel>>(emptyList())

    init {{
        viewModelScope.launch {{
            _sla.value = approvalRepository.computeSla()
            _bn.value = approvalRepository.computeBottleneck()
        }}
    }}

    val uiState: StateFlow<AnalyticsUiState> = combine(
        approvalRepository.observeStatusCounts(),
        approvalRepository.observeTypeStats(),
        _sla,
        _bn
    ) {{ status, types, sla, bn ->
        val text = buildString {{
            appendLine("Status counts:")
            status.forEach {{ appendLine(" · ${{it.status}}: ${{it.count}}") }}
            appendLine()
            appendLine("By type:")
            types.forEach {{ appendLine(" · ${{it.type}}: ${{it.count}} (sum ${{it.totalAmount}})") }}
            appendLine()
            sla?.let {{
                appendLine("SLA ${{it.slaHours}}h: ${{it.withinSlaCount}}/${{it.completedCount}} (${{"%.1f".format(it.withinSlaPercent)}}%)")
            }}
            appendLine()
            appendLine("Bottleneck (avg wait hours):")
            bn.forEach {{ appendLine(" · L${{it.level}}: ${{"%.1f".format(it.avgWaitHours)}}h (n=${{it.sampleCount}})") }}
        }}
        AnalyticsUiState(status, types, sla, bn, text)
    }}.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), AnalyticsUiState())

    fun chartData(): Pair<List<String>, List<Float>> {{
        val s = uiState.value.statusCounts
        return s.map {{ it.status.name }} to s.map {{ it.count.toFloat() }}
    }}
}}
""")
    w(f"{base}/AnalyticsFragment.kt", f"""
package {PKG}.feature.analytics

import android.os.Bundle
import android.view.View
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import {PKG}.core.ui.BaseFragment
import {PKG}.data.export.ExportUtils
import {PKG}.feature.analytics.databinding.FragmentAnalyticsBinding
import kotlinx.coroutines.launch
import org.koin.androidx.viewmodel.ext.android.viewModel

class AnalyticsFragment : BaseFragment<FragmentAnalyticsBinding>(R.layout.fragment_analytics) {{
    private val viewModel: AnalyticsViewModel by viewModel()

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {{
        super.onViewCreated(view, savedInstanceState)
        binding.btnExportChart.setOnClickListener {{
            val (labels, values) = viewModel.chartData()
            if (values.isNotEmpty()) {{
                val bmp = ExportUtils.createSimpleChartBitmap(labels, values, "Status distribution")
                ExportUtils.shareBitmap(requireContext(), bmp, "ApprovalHub Chart")
            }}
        }}
        viewLifecycleOwner.lifecycleScope.launch {{
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {{
                viewModel.uiState.collect {{ binding.content = it.content }}
            }}
        }}
    }}
}}
""")


def _audit(w, lib_build, empty_consumer, PKG, P):
    empty_consumer("feature/audit")
    w("feature/audit/build.gradle.kts", lib_build(
        f"{PKG}.feature.audit",
        feature_deps(['implementation(project(":data"))']),
        True, False,
    ))
    w("feature/audit/src/main/res/layout/fragment_audit.xml", """
<?xml version="1.0" encoding="utf-8"?>
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
""")
    base = f"feature/audit/src/main/java/{P}/feature/audit"
    w(f"{base}/AuditViewModel.kt", f"""
package {PKG}.feature.audit

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import {PKG}.core.model.ApprovalAction
import {PKG}.core.model.ApprovalRequest
import {PKG}.domain.repository.ApprovalRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class AuditUiState(
    val requests: List<ApprovalRequest> = emptyList(),
    val actions: List<ApprovalAction> = emptyList(),
    val names: Map<Long, String> = emptyMap(),
    val content: String = "Loading…"
)

class AuditViewModel(
    private val approvalRepository: ApprovalRepository
) : ViewModel() {{
    private val _uiState = MutableStateFlow(AuditUiState())
    val uiState: StateFlow<AuditUiState> = _uiState.asStateFlow()

    init {{
        viewModelScope.launch {{
            val requests = approvalRepository.allRequests()
            val actions = approvalRepository.allActions()
            val names = approvalRepository.buildUserNameMap()
            val text = buildString {{
                requests.take(30).forEach {{ r ->
                    appendLine("#${{r.id}} ${{r.title}} [${{r.status}}]")
                    actions.filter {{ it.requestId == r.id }}.forEach {{ a ->
                        appendLine("  L${{a.level}} ${{a.decision}} by ${{names[a.actorId] ?: a.actorId}} — ${{a.comment}}")
                    }}
                }}
            }}
            _uiState.update {{ AuditUiState(requests, actions, names, text) }}
        }}
    }}
}}
""")
    w(f"{base}/AuditFragment.kt", f"""
package {PKG}.feature.audit

import android.os.Bundle
import android.view.View
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import {PKG}.core.ui.BaseFragment
import {PKG}.data.export.ExportUtils
import {PKG}.feature.audit.databinding.FragmentAuditBinding
import kotlinx.coroutines.launch
import org.koin.androidx.viewmodel.ext.android.viewModel

class AuditFragment : BaseFragment<FragmentAuditBinding>(R.layout.fragment_audit) {{
    private val viewModel: AuditViewModel by viewModel()

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {{
        super.onViewCreated(view, savedInstanceState)
        binding.btnCsv.setOnClickListener {{
            val s = viewModel.uiState.value
            val uri = ExportUtils.exportAuditCsv(requireContext(), s.requests, s.actions, s.names)
            ExportUtils.shareUri(requireContext(), uri, "text/csv", "Audit CSV")
        }}
        binding.btnPdf.setOnClickListener {{
            val s = viewModel.uiState.value
            val uri = ExportUtils.exportAuditPdf(requireContext(), s.requests, s.actions, s.names)
            ExportUtils.shareUri(requireContext(), uri, "application/pdf", "Audit PDF")
        }}
        viewLifecycleOwner.lifecycleScope.launch {{
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {{
                viewModel.uiState.collect {{ binding.content = it.content }}
            }}
        }}
    }}
}}
""")


def _settings(w, lib_build, empty_consumer, PKG, P):
    empty_consumer("feature/settings")
    w("feature/settings/build.gradle.kts", lib_build(f"{PKG}.feature.settings", feature_deps(), True, False))
    w("feature/settings/src/main/res/layout/fragment_settings.xml", """
<?xml version="1.0" encoding="utf-8"?>
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
""")
    base = f"feature/settings/src/main/java/{P}/feature/settings"
    w(f"{base}/SettingsViewModel.kt", f"""
package {PKG}.feature.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import {PKG}.core.common.DateFormatters
import {PKG}.core.model.Role
import {PKG}.core.model.ThemeMode
import {PKG}.core.model.User
import {PKG}.domain.repository.ApprovalRepository
import {PKG}.domain.repository.SessionRepository
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.update

data class SettingsUiState(
    val user: User? = null,
    val impersonate: Role? = null,
    val syncInfo: String = "",
    val message: String = "",
    val loggedOut: Boolean = false
)

class SettingsViewModel(
    private val sessionRepository: SessionRepository,
    private val approvalRepository: ApprovalRepository
) : ViewModel() {{
    private val _message = MutableStateFlow("")
    private val _loggedOut = MutableStateFlow(false)

    val uiState: StateFlow<SettingsUiState> = combine(
        sessionRepository.session,
        sessionRepository.impersonateRole,
        approvalRepository.observeSyncMeta(),
        _message,
        _loggedOut
    ) {{ user, imp, meta, msg, out ->
        SettingsUiState(
            user = user,
            impersonate = imp,
            syncInfo = meta?.let {{
                "Last sync: ${{if (it.lastSyncedAt == 0L) "never" else DateFormatters.full(it.lastSyncedAt)}} · ${{it.lastSyncStatus}} · pending ${{it.pendingPushCount}}"
            }} ?: "No sync meta",
            message = msg,
            loggedOut = out
        )
    }}.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), SettingsUiState())

    fun setTheme(mode: ThemeMode) {{ viewModelScope.launch {{ sessionRepository.setThemeMode(mode) }} }}
    fun setImpersonate(role: Role?) {{ sessionRepository.setImpersonateRole(role) }}
    fun sync() {{
        viewModelScope.launch {{
            val r = approvalRepository.syncNow()
            _message.update {{ r.fold(onSuccess = {{ "Sync OK" }}, onFailure = {{ e -> e.message ?: "Sync failed" }}) }}
        }}
    }}
    fun runEscalation() {{
        viewModelScope.launch {{
            val n = approvalRepository.runEscalationPass()
            _message.update {{ "Escalated $n request(s)" }}
        }}
    }}
    fun logout() {{
        viewModelScope.launch {{
            sessionRepository.logoutAndClear()
            _loggedOut.value = true
        }}
    }}
}}
""")
    w(f"{base}/SettingsFragment.kt", f"""
package {PKG}.feature.settings

import android.os.Bundle
import android.view.View
import android.widget.AdapterView
import android.widget.ArrayAdapter
import androidx.appcompat.app.AppCompatDelegate
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.navigation.fragment.findNavController
import {PKG}.core.model.Role
import {PKG}.core.model.ThemeMode
import {PKG}.core.ui.BaseFragment
import {PKG}.feature.settings.databinding.FragmentSettingsBinding
import kotlinx.coroutines.launch
import org.koin.androidx.viewmodel.ext.android.viewModel

class SettingsFragment : BaseFragment<FragmentSettingsBinding>(R.layout.fragment_settings) {{
    private val viewModel: SettingsViewModel by viewModel()

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {{
        super.onViewCreated(view, savedInstanceState)
        val themes = ThemeMode.entries
        binding.spinnerTheme.adapter = ArrayAdapter(
            requireContext(), android.R.layout.simple_spinner_dropdown_item, themes.map {{ it.name }}
        )
        val roles = listOf<Role?>(null) + Role.entries
        binding.spinnerImpersonate.adapter = ArrayAdapter(
            requireContext(), android.R.layout.simple_spinner_dropdown_item,
            roles.map {{ it?.name ?: "(none)" }}
        )
        binding.spinnerTheme.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {{
            override fun onItemSelected(p: AdapterView<*>?, v: View?, pos: Int, id: Long) {{
                val mode = themes[pos]
                viewModel.setTheme(mode)
                AppCompatDelegate.setDefaultNightMode(
                    when (mode) {{
                        ThemeMode.LIGHT -> AppCompatDelegate.MODE_NIGHT_NO
                        ThemeMode.DARK -> AppCompatDelegate.MODE_NIGHT_YES
                        ThemeMode.SYSTEM -> AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM
                    }}
                )
            }}
            override fun onNothingSelected(p: AdapterView<*>?) {{}}
        }}
        binding.spinnerImpersonate.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {{
            override fun onItemSelected(p: AdapterView<*>?, v: View?, pos: Int, id: Long) {{
                viewModel.setImpersonate(roles[pos])
            }}
            override fun onNothingSelected(p: AdapterView<*>?) {{}}
        }}
        binding.btnSync.setOnClickListener {{ viewModel.sync() }}
        binding.btnEscalate.setOnClickListener {{ viewModel.runEscalation() }}
        binding.btnLogout.setOnClickListener {{ viewModel.logout() }}
        viewLifecycleOwner.lifecycleScope.launch {{
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {{
                viewModel.uiState.collect {{ state ->
                    binding.info = state.user?.let {{
                        "${{it.displayName}} (${{it.username}}) · ${{it.role}}" +
                            (state.impersonate?.let {{ r -> " · impersonate $r" }} ?: "") +
                            "\\n${{state.message}}"
                    }} ?: ""
                    binding.syncInfo = state.syncInfo
                    if (state.loggedOut) {{
                        findNavController().navigate({PKG}.core.ui.R.id.action_global_to_login)
                    }}
                }}
            }}
        }}
    }}
}}
""")


def _widget(w, lib_build, empty_consumer, PKG, P):
    empty_consumer("feature/widget")
    w("feature/widget/build.gradle.kts", lib_build(
        f"{PKG}.feature.widget",
        [
            'implementation(project(":core:database"))',
            "implementation(libs.androidx.core.ktx)",
            "implementation(libs.coroutines.android)",
        ],
        databinding=False,
        ksp=False,
    ))
    w("feature/widget/src/main/AndroidManifest.xml", f"""
<?xml version="1.0" encoding="utf-8"?>
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
""")
    w("feature/widget/src/main/res/layout/widget_pending_placeholder.xml", """
<?xml version="1.0" encoding="utf-8"?>
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
""")
    w("feature/widget/src/main/res/xml/pending_widget_info.xml", """
<?xml version="1.0" encoding="utf-8"?>
<appwidget-provider xmlns:android="http://schemas.android.com/apk/res/android"
    android:minWidth="110dp" android:minHeight="40dp"
    android:updatePeriodMillis="1800000"
    android:initialLayout="@layout/widget_pending_placeholder"
    android:resizeMode="horizontal|vertical"
    android:widgetCategory="home_screen" />
""")
    w("feature/widget/src/main/res/values/colors.xml", """
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="ah_primary">#0F4C5C</color>
</resources>
""")
    w(f"feature/widget/src/main/java/{P}/feature/widget/PendingWidgetReceiver.kt", f"""
package {PKG}.feature.widget

import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.Context
import android.widget.RemoteViews
import {PKG}.core.database.AppDatabase
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

class PendingWidgetReceiver : AppWidgetProvider() {{
    override fun onUpdate(context: Context, appWidgetManager: AppWidgetManager, appWidgetIds: IntArray) {{
        CoroutineScope(Dispatchers.IO).launch {{
            val count = runCatching {{
                AppDatabase.get(context).approvalRequestDao().observePendingCount().first()
            }}.getOrDefault(0)
            appWidgetIds.forEach {{ id ->
                val views = RemoteViews(context.packageName, R.layout.widget_pending_placeholder)
                views.setTextViewText(R.id.widget_pending_count, count.toString())
                appWidgetManager.updateAppWidget(id, views)
            }}
        }}
    }}
}}
""")
