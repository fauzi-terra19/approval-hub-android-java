package com.fauzi.wings.data.repository;

import android.content.Context;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MediatorLiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.Transformations;

import com.fauzi.wings.core.database.AppDatabase;
import com.fauzi.wings.core.database.dao.StatusCountRow;
import com.fauzi.wings.core.database.dao.TypeStatRow;
import com.fauzi.wings.core.database.entity.ApprovalActionEntity;
import com.fauzi.wings.core.database.entity.ApprovalRequestEntity;
import com.fauzi.wings.core.database.entity.UserEntity;
import com.fauzi.wings.core.model.ApprovalAction;
import com.fauzi.wings.core.model.ApprovalRequest;
import com.fauzi.wings.core.model.ApprovalStatus;
import com.fauzi.wings.core.model.DashboardStats;
import com.fauzi.wings.core.model.Permission;
import com.fauzi.wings.core.model.RequestFilter;
import com.fauzi.wings.core.model.RequestType;
import com.fauzi.wings.core.model.Role;
import com.fauzi.wings.core.model.StatusCount;
import com.fauzi.wings.core.model.SyncMeta;
import com.fauzi.wings.core.model.ThemeMode;
import com.fauzi.wings.core.model.TypeStat;
import com.fauzi.wings.core.model.User;
import com.fauzi.wings.core.notification.ApprovalNotifier;
import com.fauzi.wings.core.preference.UserPreferences;
import com.fauzi.wings.data.mapper.Mappers;
import com.fauzi.wings.data.sync.SyncRepository;
import com.fauzi.wings.domain.analytics.AnalyticsCalculator;
import com.fauzi.wings.domain.analytics.BottleneckLevel;
import com.fauzi.wings.domain.analytics.SlaStats;
import com.fauzi.wings.domain.approval.AmountBasedRules;
import com.fauzi.wings.domain.approval.ApprovalWorkflow;
import com.fauzi.wings.domain.rbac.RbacPolicy;
import com.fauzi.wings.domain.repository.ApprovalRepository;
import com.fauzi.wings.domain.repository.SessionRepository;
import com.fauzi.wings.domain.security.PasswordHasher;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.TimeUnit;

public class AppRepository implements SessionRepository, ApprovalRepository {
    public static final long SESSION_TIMEOUT_MS = TimeUnit.MINUTES.toMillis(15);

    private final AppDatabase db;
    private final UserPreferences prefs;
    private final SyncRepository syncRepository;
    private final Context appContext;

    private final MutableLiveData<User> sessionLive = new MutableLiveData<>(null);
    private final MutableLiveData<Role> impersonateLive = new MutableLiveData<>(null);
    private final MutableLiveData<RequestFilter> filterLive = new MutableLiveData<>(new RequestFilter());

    private User session;
    private Role impersonateRole;

    public AppRepository(AppDatabase db, UserPreferences prefs, SyncRepository syncRepository, Context appContext) {
        this.db = db;
        this.prefs = prefs;
        this.syncRepository = syncRepository;
        this.appContext = appContext.getApplicationContext();
    }

    @Override public LiveData<User> observeSession() { return sessionLive; }
    @Override public LiveData<Role> observeImpersonateRole() { return impersonateLive; }
    @Override public User getSession() { return session; }
    @Override public Role getImpersonateRole() { return impersonateRole; }

    public boolean isReadOnly() { return impersonateRole != null; }

    @Override
    public void ensureSeeded() {
        AppDatabase.seed(db);
    }

    @Override
    public User restoreSession() {
        Long id = prefs.getSessionUserId();
        if (id == null) return null;
        if (checkSessionTimeoutInternal(false)) return null;
        UserEntity entity = db.userDao().getById(id);
        if (entity == null) return null;
        session = Mappers.toUser(entity);
        sessionLive.postValue(session);
        return session;
    }

    @Override
    public User login(String username, String password) throws Exception {
        UserEntity user = db.userDao().findByUsername(username.trim());
        if (user == null || !PasswordHasher.matches(password, user.passwordHash)) {
            throw new IllegalArgumentException("Username atau password salah");
        }
        session = Mappers.toUser(user);
        impersonateRole = null;
        sessionLive.postValue(session);
        impersonateLive.postValue(null);
        prefs.saveSessionUserId(user.id);
        prefs.touchActivity();
        return session;
    }

    @Override
    public void logoutAndClear() {
        session = null;
        impersonateRole = null;
        sessionLive.postValue(null);
        impersonateLive.postValue(null);
        prefs.saveSessionUserId(null);
    }

    @Override
    public void touchActivity() {
        prefs.touchActivity();
    }

    @Override
    public boolean checkSessionTimeout() {
        return checkSessionTimeoutInternal(true);
    }

    private boolean checkSessionTimeoutInternal(boolean touchIfOk) {
        if (session == null && prefs.getSessionUserId() == null) return false;
        long last = prefs.getLastActivityAt();
        if (last > 0 && System.currentTimeMillis() - last > SESSION_TIMEOUT_MS) {
            logoutAndClear();
            return true;
        }
        if (touchIfOk) prefs.touchActivity();
        return false;
    }

    private Set<Permission> currentPermissions() {
        if (session == null) return Collections.emptySet();
        if (impersonateRole != null) return RbacPolicy.impersonationPermissions(impersonateRole);
        return RbacPolicy.permissionsFor(session.role);
    }

    @Override
    public boolean hasPermission(Permission permission) {
        return currentPermissions().contains(permission);
    }

    @Override
    public void setImpersonateRole(Role role) {
        if (session == null) return;
        if (role != null && !RbacPolicy.hasPermission(session.role, Permission.IMPERSONATE)) return;
        impersonateRole = role;
        impersonateLive.postValue(role);
    }

    @Override
    public void setThemeMode(ThemeMode mode) {
        prefs.setThemeMode(mode);
    }

    @Override
    public ThemeMode getThemeMode() {
        return prefs.getThemeMode();
    }

    public void updateFilter(RequestFilter filter) {
        filterLive.setValue(filter);
    }

    @Override
    public LiveData<List<ApprovalRequest>> observeRequestsForCurrentUser() {
        MediatorLiveData<List<ApprovalRequest>> result = new MediatorLiveData<>();
        LiveData<List<ApprovalRequestEntity>> all = db.approvalRequestDao().observeAll();
        Runnable compute = () -> {
            User user = session;
            Role imp = impersonateRole;
            RequestFilter filt = filterLive.getValue() == null ? new RequestFilter() : filterLive.getValue();
            List<ApprovalRequestEntity> source = all.getValue();
            if (user == null || source == null) {
                result.setValue(Collections.emptyList());
                return;
            }
            Role role = imp != null ? imp : user.role;
            Set<Permission> perms = currentPermissions();
            List<ApprovalRequestEntity> scoped = new ArrayList<>();
            for (ApprovalRequestEntity it : source) {
                if (canViewRequest(user, role, perms, it) && filt.matches(Mappers.toRequest(it), "")) {
                    scoped.add(it);
                }
            }
            result.setValue(Mappers.toRequests(scoped));
        };
        result.addSource(all, v -> compute.run());
        result.addSource(sessionLive, v -> compute.run());
        result.addSource(impersonateLive, v -> compute.run());
        result.addSource(filterLive, v -> compute.run());
        return result;
    }

    @Override
    public LiveData<List<ApprovalRequest>> observeInbox() {
        MediatorLiveData<List<ApprovalRequest>> result = new MediatorLiveData<>();
        LiveData<List<ApprovalRequestEntity>> all = db.approvalRequestDao().observeAll();
        Runnable compute = () -> {
            User user = session;
            List<ApprovalRequestEntity> source = all.getValue();
            if (user == null || impersonateRole != null || source == null) {
                result.setValue(Collections.emptyList());
                return;
            }
            List<ApprovalRequest> out = new ArrayList<>();
            for (ApprovalRequestEntity it : source) {
                if (ApprovalWorkflow.canActOn(it.status, user.role, false)) out.add(Mappers.toRequest(it));
            }
            result.setValue(out);
        };
        result.addSource(all, v -> compute.run());
        result.addSource(sessionLive, v -> compute.run());
        result.addSource(impersonateLive, v -> compute.run());
        return result;
    }

    @Override
    public LiveData<List<ApprovalAction>> observeActions(long requestId) {
        return Transformations.map(db.approvalActionDao().observeByRequest(requestId), Mappers::toActions);
    }

    @Override
    public LiveData<DashboardStats> observeDashboardStats() {
        MediatorLiveData<DashboardStats> result = new MediatorLiveData<>();
        LiveData<List<ApprovalRequest>> mine = observeRequestsForCurrentUser();
        LiveData<List<ApprovalRequest>> inbox = observeInbox();
        Runnable compute = () -> {
            List<ApprovalRequest> m = mine.getValue();
            List<ApprovalRequest> in = inbox.getValue();
            int approved = 0, rejected = 0, pipeline = 0;
            if (m != null) {
                for (ApprovalRequest row : m) {
                    if (row.status == ApprovalStatus.APPROVED) approved++;
                    else if (row.status == ApprovalStatus.REJECTED) rejected++;
                    else if (row.status == ApprovalStatus.PENDING_L1
                            || row.status == ApprovalStatus.PENDING_L2
                            || row.status == ApprovalStatus.PENDING_L3) {
                        pipeline++;
                    }
                }
            }
            result.setValue(new DashboardStats(
                    m == null ? 0 : m.size(),
                    in == null ? 0 : in.size(),
                    approved, rejected, pipeline));
        };
        result.addSource(mine, v -> compute.run());
        result.addSource(inbox, v -> compute.run());
        return result;
    }

    @Override
    public LiveData<List<StatusCount>> observeStatusCounts() {
        return Transformations.map(db.approvalRequestDao().observeStatusCounts(), rows -> {
            List<StatusCount> out = new ArrayList<>();
            if (rows != null) for (StatusCountRow r : rows) out.add(Mappers.toStatusCount(r));
            return out;
        });
    }

    @Override
    public LiveData<List<TypeStat>> observeTypeStats() {
        return Transformations.map(db.approvalRequestDao().observeTypeStats(), rows -> {
            List<TypeStat> out = new ArrayList<>();
            if (rows != null) for (TypeStatRow r : rows) out.add(Mappers.toTypeStat(r));
            return out;
        });
    }

    @Override
    public LiveData<SyncMeta> observeSyncMeta() {
        return syncRepository.observeMeta();
    }

    @Override
    public LiveData<Integer> observePendingCount() {
        return db.approvalRequestDao().observePendingCount();
    }

    @Override
    public ApprovalRequest getRequest(long requestId) {
        return Mappers.toRequest(db.approvalRequestDao().getById(requestId));
    }

    @Override
    public long createRequest(String title, String description, RequestType type, double amount) throws Exception {
        if (isReadOnly()) throw new SecurityException("Mode impersonate read-only");
        if (session == null) throw new IllegalStateException("Belum login");
        if (!RbacPolicy.hasPermission(session.role, Permission.CREATE_REQUEST)) {
            throw new SecurityException("Role tidak boleh membuat request");
        }
        long now = System.currentTimeMillis();
        int maxLevel = AmountBasedRules.requiredMaxLevel(type, amount);
        ApprovalRequestEntity entity = new ApprovalRequestEntity(
                title.trim(), description.trim(), type, amount, session.id, session.department,
                ApprovalWorkflow.initialStatusAfterSubmit(), 1, maxLevel, false, now, now);
        long id = db.approvalRequestDao().insert(entity);
        ApprovalNotifier.notifyInbox(appContext, "Request baru menunggu L1",
                title + " · " + AmountBasedRules.ruleLabel(type, amount), (int) (3000 + id));
        prefs.touchActivity();
        return id;
    }

    @Override
    public void decide(long requestId, boolean approve, String comment) throws Exception {
        if (isReadOnly()) throw new SecurityException("Mode impersonate read-only");
        if (session == null) throw new IllegalStateException("Belum login");
        ApprovalRequestEntity request = db.approvalRequestDao().getById(requestId);
        if (request == null) throw new IllegalArgumentException("Request tidak ditemukan");
        if (!ApprovalWorkflow.canActOn(request.status, session.role, false)) {
            throw new SecurityException("Anda tidak berwenang di level ini");
        }
        Integer level = ApprovalWorkflow.requiredLevel(request.status);
        if (level == null) throw new IllegalStateException("Status tidak bisa diproses");
        long now = System.currentTimeMillis();
        ApprovalStatus newStatus = approve
                ? ApprovalWorkflow.nextStatusOnApprove(request.status, request.requiredMaxLevel)
                : ApprovalWorkflow.statusOnReject();
        String c = (comment == null || comment.isBlank()) ? (approve ? "Disetujui" : "Ditolak") : comment;
        db.approvalActionDao().insert(new ApprovalActionEntity(requestId, session.id, level,
                approve ? "APPROVE" : "REJECT", c, now));
        request.status = newStatus;
        if (newStatus == ApprovalStatus.PENDING_L1) request.currentLevel = 1;
        else if (newStatus == ApprovalStatus.PENDING_L2) request.currentLevel = 2;
        else if (newStatus == ApprovalStatus.PENDING_L3) request.currentLevel = 3;
        else if (newStatus == ApprovalStatus.APPROVED) request.currentLevel = request.requiredMaxLevel;
        request.updatedAt = now;
        db.approvalRequestDao().update(request);
        if (approve && newStatus.name().startsWith("PENDING")) {
            ApprovalNotifier.notifyInbox(appContext, "Menunggu " + ApprovalWorkflow.levelLabel(newStatus),
                    request.title, (int) (4000 + requestId));
        }
        prefs.touchActivity();
    }

    @Override
    public void forceEscalate(long requestId) throws Exception {
        if (isReadOnly()) throw new SecurityException("Read-only");
        if (session == null) throw new IllegalStateException("Belum login");
        if (!RbacPolicy.hasPermission(session.role, Permission.FORCE_ESCALATE)) {
            throw new SecurityException("Tidak punya FORCE_ESCALATE");
        }
        ApprovalRequestEntity request = db.approvalRequestDao().getById(requestId);
        if (request == null) throw new IllegalArgumentException("Tidak ditemukan");
        ApprovalStatus next = ApprovalWorkflow.escalateStatus(request.status, request.requiredMaxLevel);
        if (next == null) throw new IllegalStateException("Tidak bisa di-escalate");
        long now = System.currentTimeMillis();
        db.approvalActionDao().insert(new ApprovalActionEntity(requestId, session.id, request.currentLevel,
                "ESCALATE", "Manual escalate oleh " + session.displayName, now));
        request.status = next;
        Integer lvl = ApprovalWorkflow.requiredLevel(next);
        if (lvl != null) request.currentLevel = lvl;
        request.escalated = true;
        request.updatedAt = now;
        db.approvalRequestDao().update(request);
    }

    @Override
    public int runEscalationPass() throws Exception {
        if (isReadOnly()) throw new SecurityException("Read-only");
        if (session == null) throw new IllegalStateException("Belum login");
        if (!hasPermission(Permission.FORCE_ESCALATE)) {
            throw new SecurityException("Tidak punya FORCE_ESCALATE");
        }
        long now = System.currentTimeMillis();
        List<ApprovalRequestEntity> overdue = db.approvalRequestDao()
                .getOverdue(now - ApprovalWorkflow.IDLE_BEFORE_ESCALATE_MS);
        int count = 0;
        for (ApprovalRequestEntity request : overdue) {
            ApprovalStatus next = ApprovalWorkflow.escalateStatus(request.status, request.requiredMaxLevel);
            if (next == null) continue;
            request.status = next;
            Integer lvl = ApprovalWorkflow.requiredLevel(next);
            if (lvl != null) request.currentLevel = lvl;
            request.escalated = true;
            request.updatedAt = now;
            db.approvalRequestDao().update(request);
            db.approvalActionDao().insert(new ApprovalActionEntity(request.id, 1, request.currentLevel,
                    "ESCALATE", "Auto-escalate idle", now));
            count++;
        }
        return count;
    }

    @Override
    public SyncMeta syncNow() throws Exception {
        return syncRepository.syncNow();
    }

    @Override
    public List<ApprovalRequest> allRequests() {
        return Mappers.toRequests(db.approvalRequestDao().getAll());
    }

    @Override
    public List<ApprovalAction> allActions() {
        return Mappers.toActions(db.approvalActionDao().getAll());
    }

    @Override
    public List<ApprovalRequest> visibleRequestsSnapshot() {
        User user = session;
        if (user == null) return Collections.emptyList();
        Role role = impersonateRole != null ? impersonateRole : user.role;
        Set<Permission> perms = currentPermissions();
        List<ApprovalRequest> out = new ArrayList<>();
        for (ApprovalRequestEntity it : db.approvalRequestDao().getAll()) {
            if (canViewRequest(user, role, perms, it)) out.add(Mappers.toRequest(it));
        }
        return out;
    }

    @Override
    public List<ApprovalAction> visibleActionsSnapshot() {
        List<ApprovalRequest> visible = visibleRequestsSnapshot();
        Set<Long> ids = new HashSet<>();
        for (ApprovalRequest request : visible) ids.add(request.id);
        List<ApprovalAction> out = new ArrayList<>();
        for (ApprovalAction action : allActions()) {
            if (ids.contains(action.requestId)) out.add(action);
        }
        return out;
    }

    private boolean canViewRequest(User user, Role role, Set<Permission> perms, ApprovalRequestEntity it) {
        if (perms.contains(Permission.VIEW_ALL_REQUESTS)) return true;
        if (perms.contains(Permission.VIEW_DEPARTMENT_REQUESTS)) {
            return it.department.equalsIgnoreCase(user.department) || it.requesterId == user.id
                    || (role == Role.SUPERVISOR && it.status == ApprovalStatus.PENDING_L1);
        }
        return it.requesterId == user.id;
    }

    @Override
    public Map<Long, String> buildUserNameMap() {
        Map<Long, String> map = new HashMap<>();
        for (UserEntity u : db.userDao().getAll()) map.put(u.id, u.displayName);
        return map;
    }

    @Override
    public SlaStats computeSla() {
        return AnalyticsCalculator.slaStats(allRequests(), 48);
    }

    @Override
    public List<BottleneckLevel> computeBottleneck() {
        return AnalyticsCalculator.bottleneckHeatmap(allRequests(), allActions());
    }
}
