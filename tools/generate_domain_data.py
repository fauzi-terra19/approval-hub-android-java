#!/usr/bin/env python3
"""Domain + database + data modules generator."""
from __future__ import annotations

from generate_all import PKG, P, w, empty_consumer, empty_manifest, lib_build


def gen_domain() -> None:
    empty_consumer("domain")
    w("domain/build.gradle.kts", lib_build(f"{PKG}.domain", [
        'api(project(":core:model"))',
        "api(libs.androidx.lifecycle.livedata)",
        "implementation(libs.androidx.annotation)",
        "testImplementation(libs.junit)",
        "testImplementation(libs.truth)",
    ]))
    w("domain/src/main/AndroidManifest.xml", empty_manifest(f"{PKG}.domain"))
    base = f"domain/src/main/java/{P}/domain"

    w(f"{base}/approval/AmountBasedRules.java", f'''
package {PKG}.domain.approval;

import {PKG}.core.model.RequestType;

public final class AmountBasedRules {{
    public static final double PURCHASE_L3_THRESHOLD = 10_000_000.0;
    public static final double PURCHASE_L2_THRESHOLD = 2_000_000.0;
    public static final double EXPENSE_L3_THRESHOLD = 5_000_000.0;

    private AmountBasedRules() {{}}

    public static int requiredMaxLevel(RequestType type, double amount) {{
        switch (type) {{
            case PURCHASE:
                if (amount > PURCHASE_L3_THRESHOLD) return 3;
                if (amount > PURCHASE_L2_THRESHOLD) return 2;
                return 1;
            case EXPENSE:
                return amount > EXPENSE_L3_THRESHOLD ? 3 : 2;
            case LEAVE:
            case ACCESS:
            default:
                return 2;
        }}
    }}

    public static String ruleLabel(RequestType type, double amount) {{
        int max = requiredMaxLevel(type, amount);
        return "Wajib sampai L" + max + " (rule " + type.name() + ")";
    }}
}}
''')

    w(f"{base}/approval/ApprovalWorkflow.java", f'''
package {PKG}.domain.approval;

import {PKG}.core.model.ApprovalStatus;
import {PKG}.core.model.Role;
import {PKG}.domain.rbac.RbacPolicy;

import java.util.concurrent.TimeUnit;

public final class ApprovalWorkflow {{
    public static final int MAX_LEVEL = 3;
    public static final long IDLE_BEFORE_ESCALATE_MS = TimeUnit.DAYS.toMillis(2);

    private ApprovalWorkflow() {{}}

    public static ApprovalStatus initialStatusAfterSubmit() {{
        return ApprovalStatus.PENDING_L1;
    }}

    public static Integer requiredLevel(ApprovalStatus status) {{
        switch (status) {{
            case PENDING_L1: return 1;
            case PENDING_L2: return 2;
            case PENDING_L3: return 3;
            default: return null;
        }}
    }}

    public static boolean canActOn(ApprovalStatus status, Role actorRole, boolean readOnly) {{
        if (readOnly) return false;
        Integer level = requiredLevel(status);
        if (level == null) return false;
        return RbacPolicy.canApproveLevel(actorRole, level);
    }}

    public static ApprovalStatus nextStatusOnApprove(ApprovalStatus current, int requiredMaxLevel) {{
        Integer currentLevel = requiredLevel(current);
        if (currentLevel == null) return current;
        int max = Math.max(1, Math.min(MAX_LEVEL, requiredMaxLevel));
        if (currentLevel >= max) return ApprovalStatus.APPROVED;
        switch (current) {{
            case PENDING_L1: return ApprovalStatus.PENDING_L2;
            case PENDING_L2: return ApprovalStatus.PENDING_L3;
            case PENDING_L3: return ApprovalStatus.APPROVED;
            default: return current;
        }}
    }}

    public static ApprovalStatus statusOnReject() {{
        return ApprovalStatus.REJECTED;
    }}

    public static boolean isTerminal(ApprovalStatus status) {{
        return status == ApprovalStatus.APPROVED
                || status == ApprovalStatus.REJECTED
                || status == ApprovalStatus.CANCELLED;
    }}

    public static String levelLabel(ApprovalStatus status) {{
        switch (status) {{
            case DRAFT: return "Draft";
            case PENDING_L1: return "Menunggu Supervisor (L1)";
            case PENDING_L2: return "Menunggu Manager (L2)";
            case PENDING_L3: return "Menunggu Director (L3)";
            case APPROVED: return "Disetujui";
            case REJECTED: return "Ditolak";
            case CANCELLED: return "Dibatalkan";
            default: return status.name();
        }}
    }}

    public static boolean isOverdue(long updatedAt, long now) {{
        return now - updatedAt >= IDLE_BEFORE_ESCALATE_MS;
    }}

    public static ApprovalStatus escalateStatus(ApprovalStatus current, int requiredMaxLevel) {{
        if (isTerminal(current)) return null;
        Integer level = requiredLevel(current);
        if (level == null) return null;
        int max = Math.max(1, Math.min(MAX_LEVEL, requiredMaxLevel));
        if (level >= max) return null;
        switch (current) {{
            case PENDING_L1: return ApprovalStatus.PENDING_L2;
            case PENDING_L2: return ApprovalStatus.PENDING_L3;
            default: return null;
        }}
    }}

    public static ApprovalStatus statusFromLevel(int level) {{
        int l = Math.max(1, Math.min(3, level));
        if (l == 1) return ApprovalStatus.PENDING_L1;
        if (l == 2) return ApprovalStatus.PENDING_L2;
        return ApprovalStatus.PENDING_L3;
    }}
}}
''')

    w(f"{base}/rbac/RbacPolicy.java", f'''
package {PKG}.domain.rbac;

import {PKG}.core.model.Permission;
import {PKG}.core.model.Role;

import java.util.Collections;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

public final class RbacPolicy {{
    private static final Map<Role, Set<Permission>> ROLE_PERMISSIONS = new HashMap<>();

    static {{
        ROLE_PERMISSIONS.put(Role.ADMIN, EnumSet.allOf(Permission.class));
        ROLE_PERMISSIONS.put(Role.DIRECTOR, EnumSet.of(
                Permission.VIEW_EXECUTIVE_DASHBOARD,
                Permission.VIEW_REQUESTS,
                Permission.VIEW_ALL_REQUESTS,
                Permission.APPROVE_LEVEL_3,
                Permission.VIEW_ANALYTICS,
                Permission.EXPORT_AUDIT,
                Permission.EXPORT_CHART,
                Permission.SYNC_DATA
        ));
        ROLE_PERMISSIONS.put(Role.MANAGER, EnumSet.of(
                Permission.VIEW_MANAGER_DASHBOARD,
                Permission.VIEW_REQUESTS,
                Permission.VIEW_DEPARTMENT_REQUESTS,
                Permission.VIEW_ALL_REQUESTS,
                Permission.CREATE_REQUEST,
                Permission.APPROVE_LEVEL_2,
                Permission.VIEW_TEAM_ANALYTICS,
                Permission.EXPORT_AUDIT,
                Permission.EXPORT_CHART,
                Permission.SYNC_DATA
        ));
        ROLE_PERMISSIONS.put(Role.SUPERVISOR, EnumSet.of(
                Permission.VIEW_SUPERVISOR_DASHBOARD,
                Permission.VIEW_REQUESTS,
                Permission.VIEW_DEPARTMENT_REQUESTS,
                Permission.CREATE_REQUEST,
                Permission.APPROVE_LEVEL_1,
                Permission.VIEW_TEAM_ANALYTICS,
                Permission.EXPORT_CHART
        ));
        ROLE_PERMISSIONS.put(Role.STAFF, EnumSet.of(
                Permission.VIEW_STAFF_DASHBOARD,
                Permission.VIEW_REQUESTS,
                Permission.CREATE_REQUEST
        ));
    }}

    private RbacPolicy() {{}}

    public static Set<Permission> permissionsFor(Role role) {{
        Set<Permission> set = ROLE_PERMISSIONS.get(role);
        return set == null ? Collections.emptySet() : Collections.unmodifiableSet(set);
    }}

    public static boolean hasPermission(Role role, Permission permission) {{
        return permissionsFor(role).contains(permission);
    }}

    public static boolean canApproveLevel(Role role, int level) {{
        switch (level) {{
            case 1: return hasPermission(role, Permission.APPROVE_LEVEL_1);
            case 2: return hasPermission(role, Permission.APPROVE_LEVEL_2);
            case 3: return hasPermission(role, Permission.APPROVE_LEVEL_3);
            default: return false;
        }}
    }}

    public static String dashboardTitle(Role role) {{
        switch (role) {{
            case ADMIN: return "Admin Control Center";
            case DIRECTOR: return "Executive Dashboard";
            case MANAGER: return "Manager Workspace";
            case SUPERVISOR: return "Supervisor Desk";
            case STAFF: return "My Requests";
            default: return "Dashboard";
        }}
    }}

    public static Set<Permission> impersonationPermissions(Role target) {{
        EnumSet<Permission> base = EnumSet.copyOf(permissionsFor(target));
        base.remove(Permission.APPROVE_LEVEL_1);
        base.remove(Permission.APPROVE_LEVEL_2);
        base.remove(Permission.APPROVE_LEVEL_3);
        base.remove(Permission.MANAGE_USERS);
        base.remove(Permission.IMPERSONATE);
        base.remove(Permission.FORCE_ESCALATE);
        base.remove(Permission.CREATE_REQUEST);
        return base;
    }}
}}
''')

    w(f"{base}/security/PasswordHasher.java", f'''
package {PKG}.domain.security;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

public final class PasswordHasher {{
    private static final String PEPPER = "approvalhub_v2_pepper";

    private PasswordHasher() {{}}

    public static String hash(String rawPassword) {{
        try {{
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] bytes = digest.digest((PEPPER + ":" + rawPassword).getBytes(StandardCharsets.UTF_8));
            StringBuilder sb = new StringBuilder();
            for (byte b : bytes) sb.append(String.format("%02x", b));
            return sb.toString();
        }} catch (Exception e) {{
            throw new IllegalStateException(e);
        }}
    }}

    public static boolean matches(String rawPassword, String storedHash) {{
        return hash(rawPassword).equalsIgnoreCase(storedHash);
    }}
}}
''')

    w(f"{base}/analytics/SlaStats.java", f'''
package {PKG}.domain.analytics;

public class SlaStats {{
    public final int completedCount;
    public final int withinSlaCount;
    public final float withinSlaPercent;
    public final long slaHours;

    public SlaStats(int completedCount, int withinSlaCount, float withinSlaPercent, long slaHours) {{
        this.completedCount = completedCount;
        this.withinSlaCount = withinSlaCount;
        this.withinSlaPercent = withinSlaPercent;
        this.slaHours = slaHours;
    }}
}}
''')

    w(f"{base}/analytics/BottleneckLevel.java", f'''
package {PKG}.domain.analytics;

public class BottleneckLevel {{
    public final int level;
    public final double avgWaitHours;
    public final int sampleCount;

    public BottleneckLevel(int level, double avgWaitHours, int sampleCount) {{
        this.level = level;
        this.avgWaitHours = avgWaitHours;
        this.sampleCount = sampleCount;
    }}
}}
''')

    w(f"{base}/analytics/AnalyticsCalculator.java", f'''
package {PKG}.domain.analytics;

import {PKG}.core.model.ApprovalAction;
import {PKG}.core.model.ApprovalRequest;
import {PKG}.core.model.ApprovalStatus;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

public final class AnalyticsCalculator {{
    private AnalyticsCalculator() {{}}

    public static SlaStats slaStats(List<ApprovalRequest> requests, long slaHours) {{
        List<ApprovalRequest> completed = new ArrayList<>();
        for (ApprovalRequest r : requests) {{
            if (r.status == ApprovalStatus.APPROVED || r.status == ApprovalStatus.REJECTED) {{
                completed.add(r);
            }}
        }}
        long slaMs = TimeUnit.HOURS.toMillis(slaHours);
        int within = 0;
        for (ApprovalRequest r : completed) {{
            if (r.updatedAt - r.createdAt <= slaMs) within++;
        }}
        float percent = completed.isEmpty() ? 0f : within * 100f / completed.size();
        return new SlaStats(completed.size(), within, percent, slaHours);
    }}

    public static List<BottleneckLevel> bottleneckHeatmap(List<ApprovalRequest> requests,
                                                          List<ApprovalAction> actions) {{
        Map<Long, List<ApprovalAction>> byRequest = new HashMap<>();
        for (ApprovalAction a : actions) {{
            byRequest.computeIfAbsent(a.requestId, k -> new ArrayList<>()).add(a);
        }}
        Map<Integer, List<Long>> waits = new HashMap<>();
        long now = System.currentTimeMillis();
        for (ApprovalRequest req : requests) {{
            List<ApprovalAction> list = byRequest.getOrDefault(req.id, Collections.emptyList());
            list = new ArrayList<>(list);
            list.sort((a, b) -> Long.compare(a.createdAt, b.createdAt));
            long prev = req.createdAt;
            for (ApprovalAction action : list) {{
                long wait = Math.max(0, action.createdAt - prev);
                waits.computeIfAbsent(action.level, k -> new ArrayList<>()).add(wait);
                prev = action.createdAt;
            }}
            if (req.status != ApprovalStatus.APPROVED && req.status != ApprovalStatus.REJECTED) {{
                Integer level = null;
                if (req.status == ApprovalStatus.PENDING_L1) level = 1;
                else if (req.status == ApprovalStatus.PENDING_L2) level = 2;
                else if (req.status == ApprovalStatus.PENDING_L3) level = 3;
                if (level != null) {{
                    waits.computeIfAbsent(level, k -> new ArrayList<>())
                            .add(Math.max(0, now - req.updatedAt));
                }}
            }}
        }}
        List<BottleneckLevel> result = new ArrayList<>();
        long hourMs = TimeUnit.HOURS.toMillis(1);
        for (int level = 1; level <= 3; level++) {{
            List<Long> samples = waits.getOrDefault(level, Collections.emptyList());
            double avg = 0;
            if (!samples.isEmpty()) {{
                long sum = 0;
                for (Long s : samples) sum += s;
                avg = (sum / (double) samples.size()) / hourMs;
            }}
            result.add(new BottleneckLevel(level, avg, samples.size()));
        }}
        return result;
    }}
}}
'''.replace("Collections.emptyList()", "java.util.Collections.emptyList()"))
    # Fix Collections import properly
    w(f"{base}/analytics/AnalyticsCalculator.java", f'''
package {PKG}.domain.analytics;

import {PKG}.core.model.ApprovalAction;
import {PKG}.core.model.ApprovalRequest;
import {PKG}.core.model.ApprovalStatus;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

public final class AnalyticsCalculator {{
    private AnalyticsCalculator() {{}}

    public static SlaStats slaStats(List<ApprovalRequest> requests, long slaHours) {{
        List<ApprovalRequest> completed = new ArrayList<>();
        for (ApprovalRequest r : requests) {{
            if (r.status == ApprovalStatus.APPROVED || r.status == ApprovalStatus.REJECTED) {{
                completed.add(r);
            }}
        }}
        long slaMs = TimeUnit.HOURS.toMillis(slaHours);
        int within = 0;
        for (ApprovalRequest r : completed) {{
            if (r.updatedAt - r.createdAt <= slaMs) within++;
        }}
        float percent = completed.isEmpty() ? 0f : within * 100f / completed.size();
        return new SlaStats(completed.size(), within, percent, slaHours);
    }}

    public static List<BottleneckLevel> bottleneckHeatmap(List<ApprovalRequest> requests,
                                                          List<ApprovalAction> actions) {{
        Map<Long, List<ApprovalAction>> byRequest = new HashMap<>();
        for (ApprovalAction a : actions) {{
            byRequest.computeIfAbsent(a.requestId, k -> new ArrayList<>()).add(a);
        }}
        Map<Integer, List<Long>> waits = new HashMap<>();
        long now = System.currentTimeMillis();
        for (ApprovalRequest req : requests) {{
            List<ApprovalAction> list = new ArrayList<>(byRequest.getOrDefault(req.id, Collections.emptyList()));
            list.sort((a, b) -> Long.compare(a.createdAt, b.createdAt));
            long prev = req.createdAt;
            for (ApprovalAction action : list) {{
                long wait = Math.max(0, action.createdAt - prev);
                waits.computeIfAbsent(action.level, k -> new ArrayList<>()).add(wait);
                prev = action.createdAt;
            }}
            if (req.status != ApprovalStatus.APPROVED && req.status != ApprovalStatus.REJECTED) {{
                Integer level = null;
                if (req.status == ApprovalStatus.PENDING_L1) level = 1;
                else if (req.status == ApprovalStatus.PENDING_L2) level = 2;
                else if (req.status == ApprovalStatus.PENDING_L3) level = 3;
                if (level != null) {{
                    waits.computeIfAbsent(level, k -> new ArrayList<>())
                            .add(Math.max(0, now - req.updatedAt));
                }}
            }}
        }}
        List<BottleneckLevel> result = new ArrayList<>();
        long hourMs = TimeUnit.HOURS.toMillis(1);
        for (int level = 1; level <= 3; level++) {{
            List<Long> samples = waits.getOrDefault(level, Collections.emptyList());
            double avg = 0;
            if (!samples.isEmpty()) {{
                long sum = 0;
                for (Long s : samples) sum += s;
                avg = (sum / (double) samples.size()) / hourMs;
            }}
            result.add(new BottleneckLevel(level, avg, samples.size()));
        }}
        return result;
    }}
}}
''')

    w(f"{base}/repository/SessionRepository.java", f'''
package {PKG}.domain.repository;

import {PKG}.core.model.Permission;
import {PKG}.core.model.Role;
import {PKG}.core.model.ThemeMode;
import {PKG}.core.model.User;

import androidx.lifecycle.LiveData;

public interface SessionRepository {{
    LiveData<User> observeSession();
    LiveData<Role> observeImpersonateRole();
    User getSession();
    Role getImpersonateRole();
    void ensureSeeded();
    User restoreSession();
    User login(String username, String password) throws Exception;
    void logoutAndClear();
    void touchActivity();
    boolean checkSessionTimeout();
    boolean hasPermission(Permission permission);
    void setImpersonateRole(Role role);
    void setThemeMode(ThemeMode mode);
    ThemeMode getThemeMode();
}}
''')

    w(f"{base}/repository/ApprovalRepository.java", f'''
package {PKG}.domain.repository;

import {PKG}.core.model.ApprovalAction;
import {PKG}.core.model.ApprovalRequest;
import {PKG}.core.model.DashboardStats;
import {PKG}.core.model.RequestType;
import {PKG}.core.model.StatusCount;
import {PKG}.core.model.SyncMeta;
import {PKG}.core.model.TypeStat;
import {PKG}.domain.analytics.BottleneckLevel;
import {PKG}.domain.analytics.SlaStats;

import androidx.lifecycle.LiveData;

import java.util.List;
import java.util.Map;

public interface ApprovalRepository {{
    LiveData<List<ApprovalRequest>> observeRequestsForCurrentUser();
    LiveData<List<ApprovalRequest>> observeInbox();
    LiveData<List<ApprovalAction>> observeActions(long requestId);
    LiveData<DashboardStats> observeDashboardStats();
    LiveData<List<StatusCount>> observeStatusCounts();
    LiveData<List<TypeStat>> observeTypeStats();
    LiveData<SyncMeta> observeSyncMeta();
    LiveData<Integer> observePendingCount();

    ApprovalRequest getRequest(long requestId);
    long createRequest(String title, String description, RequestType type, double amount) throws Exception;
    void decide(long requestId, boolean approve, String comment) throws Exception;
    void forceEscalate(long requestId) throws Exception;
    int runEscalationPass();
    SyncMeta syncNow() throws Exception;
    List<ApprovalRequest> allRequests();
    List<ApprovalAction> allActions();
    Map<Long, String> buildUserNameMap();
    SlaStats computeSla();
    List<BottleneckLevel> computeBottleneck();
}}
''')

    # Unit tests
    w(f"domain/src/test/java/{P}/domain/DomainLogicTest.java", f'''
package {PKG}.domain;

import {PKG}.core.model.ApprovalStatus;
import {PKG}.core.model.Permission;
import {PKG}.core.model.RequestType;
import {PKG}.core.model.Role;
import {PKG}.domain.approval.AmountBasedRules;
import {PKG}.domain.approval.ApprovalWorkflow;
import {PKG}.domain.rbac.RbacPolicy;
import {PKG}.domain.security.PasswordHasher;

import com.google.common.truth.Truth;

import org.junit.Test;

public class DomainLogicTest {{

    @Test
    public void approve_respects_required_max_level_l1_only() {{
        ApprovalStatus next = ApprovalWorkflow.nextStatusOnApprove(ApprovalStatus.PENDING_L1, 1);
        Truth.assertThat(next).isEqualTo(ApprovalStatus.APPROVED);
    }}

    @Test
    public void approve_goes_l1_to_l2_when_max_is_3() {{
        ApprovalStatus next = ApprovalWorkflow.nextStatusOnApprove(ApprovalStatus.PENDING_L1, 3);
        Truth.assertThat(next).isEqualTo(ApprovalStatus.APPROVED == next ? ApprovalStatus.APPROVED : ApprovalStatus.PENDING_L2);
        Truth.assertThat(next).isEqualTo(ApprovalStatus.PENDING_L2);
    }}

    @Test
    public void escalate_from_l1_to_l2() {{
        Truth.assertThat(ApprovalWorkflow.escalateStatus(ApprovalStatus.PENDING_L1, 3))
                .isEqualTo(ApprovalStatus.PENDING_L2);
    }}

    @Test
    public void cannot_escalate_at_max_level() {{
        Truth.assertThat(ApprovalWorkflow.escalateStatus(ApprovalStatus.PENDING_L2, 2)).isNull();
    }}

    @Test
    public void read_only_cannot_act() {{
        Truth.assertThat(ApprovalWorkflow.canActOn(ApprovalStatus.PENDING_L1, Role.SUPERVISOR, true)).isFalse();
    }}

    @Test
    public void supervisor_can_act_on_l1() {{
        Truth.assertThat(ApprovalWorkflow.canActOn(ApprovalStatus.PENDING_L1, Role.SUPERVISOR, false)).isTrue();
    }}

    @Test
    public void purchase_low_value_is_l1() {{
        Truth.assertThat(AmountBasedRules.requiredMaxLevel(RequestType.PURCHASE, 500_000.0)).isEqualTo(1);
    }}

    @Test
    public void purchase_mid_value_is_l2() {{
        Truth.assertThat(AmountBasedRules.requiredMaxLevel(RequestType.PURCHASE, 3_000_000.0)).isEqualTo(2);
    }}

    @Test
    public void purchase_high_value_is_l3() {{
        Truth.assertThat(AmountBasedRules.requiredMaxLevel(RequestType.PURCHASE, 15_000_000.0)).isEqualTo(3);
    }}

    @Test
    public void staff_cannot_approve() {{
        Truth.assertThat(RbacPolicy.canApproveLevel(Role.STAFF, 1)).isFalse();
    }}

    @Test
    public void admin_has_impersonate() {{
        Truth.assertThat(RbacPolicy.hasPermission(Role.ADMIN, Permission.IMPERSONATE)).isTrue();
    }}

    @Test
    public void password_hash_matches() {{
        String hash = PasswordHasher.hash("staff123");
        Truth.assertThat(hash).isNotEmpty();
        Truth.assertThat(PasswordHasher.matches("staff123", hash)).isTrue();
        Truth.assertThat(PasswordHasher.matches("wrong", hash)).isFalse();
    }}
}}
''')


def gen_core_database() -> None:
    empty_consumer("core/database")
    w("core/database/build.gradle.kts", lib_build(f"{PKG}.core.database", [
        'api(project(":core:model"))',
        'implementation(project(":domain"))',
        "api(libs.androidx.room.runtime)",
        "api(libs.androidx.lifecycle.livedata)",
        "annotationProcessor(libs.androidx.room.compiler)",
    ], room=False))
    w("core/database/src/main/AndroidManifest.xml", empty_manifest(f"{PKG}.core.database"))
    base = f"core/database/src/main/java/{P}/core/database"

    w(f"{base}/entity/UserEntity.java", f'''
package {PKG}.core.database.entity;

import androidx.room.Entity;
import androidx.room.PrimaryKey;

import {PKG}.core.model.Role;

@Entity(tableName = "users")
public class UserEntity {{
    @PrimaryKey
    public long id;
    public String username;
    public String displayName;
    public String passwordHash;
    public Role role;
    public String department;

    public UserEntity(long id, String username, String displayName, String passwordHash, Role role, String department) {{
        this.id = id;
        this.username = username;
        this.displayName = displayName;
        this.passwordHash = passwordHash;
        this.role = role;
        this.department = department;
    }}
}}
''')

    w(f"{base}/entity/ApprovalRequestEntity.java", f'''
package {PKG}.core.database.entity;

import androidx.room.Entity;
import androidx.room.ForeignKey;
import androidx.room.Index;
import androidx.room.PrimaryKey;

import {PKG}.core.model.ApprovalStatus;
import {PKG}.core.model.RequestType;

@Entity(
        tableName = "approval_requests",
        foreignKeys = @ForeignKey(
                entity = UserEntity.class,
                parentColumns = "id",
                childColumns = "requesterId",
                onDelete = ForeignKey.CASCADE
        ),
        indices = {{@Index("requesterId"), @Index("status"), @Index("department")}}
)
public class ApprovalRequestEntity {{
    @PrimaryKey(autoGenerate = true)
    public long id;
    public String title;
    public String description;
    public RequestType type;
    public double amount;
    public long requesterId;
    public String department;
    public ApprovalStatus status;
    public int currentLevel;
    public int requiredMaxLevel;
    public boolean escalated;
    public long createdAt;
    public long updatedAt;

    public ApprovalRequestEntity(String title, String description, RequestType type, double amount,
                                 long requesterId, String department, ApprovalStatus status,
                                 int currentLevel, int requiredMaxLevel, boolean escalated,
                                 long createdAt, long updatedAt) {{
        this.title = title;
        this.description = description;
        this.type = type;
        this.amount = amount;
        this.requesterId = requesterId;
        this.department = department;
        this.status = status;
        this.currentLevel = currentLevel;
        this.requiredMaxLevel = requiredMaxLevel;
        this.escalated = escalated;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }}
}}
''')

    w(f"{base}/entity/ApprovalActionEntity.java", f'''
package {PKG}.core.database.entity;

import androidx.room.Entity;
import androidx.room.ForeignKey;
import androidx.room.Index;
import androidx.room.PrimaryKey;

@Entity(
        tableName = "approval_actions",
        foreignKeys = {{
                @ForeignKey(entity = ApprovalRequestEntity.class, parentColumns = "id",
                        childColumns = "requestId", onDelete = ForeignKey.CASCADE),
                @ForeignKey(entity = UserEntity.class, parentColumns = "id",
                        childColumns = "actorId", onDelete = ForeignKey.CASCADE)
        }},
        indices = {{@Index("requestId"), @Index("actorId")}}
)
public class ApprovalActionEntity {{
    @PrimaryKey(autoGenerate = true)
    public long id;
    public long requestId;
    public long actorId;
    public int level;
    public String decision;
    public String comment;
    public long createdAt;

    public ApprovalActionEntity(long requestId, long actorId, int level, String decision, String comment, long createdAt) {{
        this.requestId = requestId;
        this.actorId = actorId;
        this.level = level;
        this.decision = decision;
        this.comment = comment;
        this.createdAt = createdAt;
    }}
}}
''')

    w(f"{base}/entity/MetricSnapshotEntity.java", f'''
package {PKG}.core.database.entity;

import androidx.room.Entity;
import androidx.room.PrimaryKey;

@Entity(tableName = "metric_snapshots")
public class MetricSnapshotEntity {{
    @PrimaryKey(autoGenerate = true)
    public long id;
    public String label;
    public String category;
    public double value;
    public long recordedAt;

    public MetricSnapshotEntity(String label, String category, double value, long recordedAt) {{
        this.label = label;
        this.category = category;
        this.value = value;
        this.recordedAt = recordedAt;
    }}
}}
''')

    w(f"{base}/entity/SyncMetaEntity.java", f'''
package {PKG}.core.database.entity;

import androidx.room.Entity;
import androidx.room.PrimaryKey;

@Entity(tableName = "sync_meta")
public class SyncMetaEntity {{
    @PrimaryKey
    public int id = 1;
    public long lastSyncedAt;
    public String lastSyncStatus;
    public int pendingPushCount;

    public SyncMetaEntity(int id, long lastSyncedAt, String lastSyncStatus, int pendingPushCount) {{
        this.id = id;
        this.lastSyncedAt = lastSyncedAt;
        this.lastSyncStatus = lastSyncStatus;
        this.pendingPushCount = pendingPushCount;
    }}
}}
''')

    w(f"{base}/dao/StatusCountRow.java", f'''
package {PKG}.core.database.dao;

import {PKG}.core.model.ApprovalStatus;

public class StatusCountRow {{
    public ApprovalStatus status;
    public int count;
}}
''')

    w(f"{base}/dao/TypeStatRow.java", f'''
package {PKG}.core.database.dao;

import {PKG}.core.model.RequestType;

public class TypeStatRow {{
    public RequestType type;
    public int count;
    public double totalAmount;
}}
''')

    w(f"{base}/dao/UserDao.java", f'''
package {PKG}.core.database.dao;

import androidx.lifecycle.LiveData;
import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;

import {PKG}.core.database.entity.UserEntity;

import java.util.List;

@Dao
public interface UserDao {{
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void upsertAll(List<UserEntity> users);

    @Query("SELECT * FROM users WHERE username = :username LIMIT 1")
    UserEntity findByUsername(String username);

    @Query("SELECT * FROM users WHERE id = :id LIMIT 1")
    UserEntity getById(long id);

    @Query("SELECT * FROM users ORDER BY role, displayName")
    LiveData<List<UserEntity>> observeAll();

    @Query("SELECT * FROM users ORDER BY role, displayName")
    List<UserEntity> getAll();

    @Query("SELECT COUNT(*) FROM users")
    int count();
}}
''')

    w(f"{base}/dao/ApprovalRequestDao.java", f'''
package {PKG}.core.database.dao;

import androidx.lifecycle.LiveData;
import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;
import androidx.room.Update;

import {PKG}.core.database.entity.ApprovalRequestEntity;

import java.util.List;

@Dao
public interface ApprovalRequestDao {{
    @Insert
    long insert(ApprovalRequestEntity request);

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void upsertAll(List<ApprovalRequestEntity> requests);

    @Update
    void update(ApprovalRequestEntity request);

    @Query("SELECT * FROM approval_requests WHERE id = :id")
    ApprovalRequestEntity getById(long id);

    @Query("SELECT * FROM approval_requests ORDER BY updatedAt DESC")
    LiveData<List<ApprovalRequestEntity>> observeAll();

    @Query("SELECT * FROM approval_requests ORDER BY updatedAt DESC")
    List<ApprovalRequestEntity> getAll();

    @Query("SELECT * FROM approval_requests WHERE status IN ('PENDING_L1','PENDING_L2','PENDING_L3') AND updatedAt <= :before ORDER BY updatedAt ASC")
    List<ApprovalRequestEntity> getOverdue(long before);

    @Query("SELECT status AS status, COUNT(*) AS count FROM approval_requests GROUP BY status")
    LiveData<List<StatusCountRow>> observeStatusCounts();

    @Query("SELECT type AS type, COUNT(*) AS count, SUM(amount) AS totalAmount FROM approval_requests GROUP BY type")
    LiveData<List<TypeStatRow>> observeTypeStats();

    @Query("SELECT COUNT(*) FROM approval_requests WHERE status IN ('PENDING_L1','PENDING_L2','PENDING_L3')")
    LiveData<Integer> observePendingCount();

    @Query("SELECT COUNT(*) FROM approval_requests WHERE status IN ('PENDING_L1','PENDING_L2','PENDING_L3')")
    int pendingCountSync();

    @Query("SELECT COUNT(*) FROM approval_requests")
    int count();
}}
''')

    w(f"{base}/dao/ApprovalActionDao.java", f'''
package {PKG}.core.database.dao;

import androidx.lifecycle.LiveData;
import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;

import {PKG}.core.database.entity.ApprovalActionEntity;

import java.util.List;

@Dao
public interface ApprovalActionDao {{
    @Insert
    long insert(ApprovalActionEntity action);

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void upsertAll(List<ApprovalActionEntity> actions);

    @Query("SELECT * FROM approval_actions WHERE requestId = :requestId ORDER BY createdAt ASC")
    LiveData<List<ApprovalActionEntity>> observeByRequest(long requestId);

    @Query("SELECT * FROM approval_actions ORDER BY createdAt DESC")
    LiveData<List<ApprovalActionEntity>> observeAll();

    @Query("SELECT * FROM approval_actions ORDER BY createdAt DESC")
    List<ApprovalActionEntity> getAll();
}}
''')

    w(f"{base}/dao/MetricDao.java", f'''
package {PKG}.core.database.dao;

import androidx.lifecycle.LiveData;
import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;

import {PKG}.core.database.entity.MetricSnapshotEntity;

import java.util.List;

@Dao
public interface MetricDao {{
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void upsertAll(List<MetricSnapshotEntity> metrics);

    @Query("SELECT * FROM metric_snapshots ORDER BY recordedAt ASC")
    LiveData<List<MetricSnapshotEntity>> observeAll();

    @Query("SELECT COUNT(*) FROM metric_snapshots")
    int count();
}}
''')

    w(f"{base}/dao/SyncMetaDao.java", f'''
package {PKG}.core.database.dao;

import androidx.lifecycle.LiveData;
import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;

import {PKG}.core.database.entity.SyncMetaEntity;

@Dao
public interface SyncMetaDao {{
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void upsert(SyncMetaEntity meta);

    @Query("SELECT * FROM sync_meta WHERE id = 1 LIMIT 1")
    LiveData<SyncMetaEntity> observe();

    @Query("SELECT * FROM sync_meta WHERE id = 1 LIMIT 1")
    SyncMetaEntity get();
}}
''')

    w(f"{base}/Converters.java", f'''
package {PKG}.core.database;

import androidx.room.TypeConverter;

import {PKG}.core.model.ApprovalStatus;
import {PKG}.core.model.RequestType;
import {PKG}.core.model.Role;

public class Converters {{
    @TypeConverter public String fromRole(Role value) {{ return value == null ? null : value.name(); }}
    @TypeConverter public Role toRole(String value) {{ return value == null ? null : Role.valueOf(value); }}
    @TypeConverter public String fromStatus(ApprovalStatus value) {{ return value == null ? null : value.name(); }}
    @TypeConverter public ApprovalStatus toStatus(String value) {{ return value == null ? null : ApprovalStatus.valueOf(value); }}
    @TypeConverter public String fromType(RequestType value) {{ return value == null ? null : value.name(); }}
    @TypeConverter public RequestType toType(String value) {{ return value == null ? null : RequestType.valueOf(value); }}
}}
''')

    w(f"{base}/AppDatabase.java", f'''
package {PKG}.core.database;

import android.content.Context;

import androidx.annotation.NonNull;
import androidx.room.Database;
import androidx.room.Room;
import androidx.room.RoomDatabase;
import androidx.room.TypeConverters;
import androidx.sqlite.db.SupportSQLiteDatabase;

import {PKG}.core.database.dao.ApprovalActionDao;
import {PKG}.core.database.dao.ApprovalRequestDao;
import {PKG}.core.database.dao.MetricDao;
import {PKG}.core.database.dao.SyncMetaDao;
import {PKG}.core.database.dao.UserDao;
import {PKG}.core.database.entity.ApprovalActionEntity;
import {PKG}.core.database.entity.ApprovalRequestEntity;
import {PKG}.core.database.entity.MetricSnapshotEntity;
import {PKG}.core.database.entity.SyncMetaEntity;
import {PKG}.core.database.entity.UserEntity;
import {PKG}.core.model.ApprovalStatus;
import {PKG}.core.model.RequestType;
import {PKG}.core.model.Role;
import {PKG}.domain.approval.AmountBasedRules;
import {PKG}.domain.security.PasswordHasher;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

@Database(
        entities = {{
                UserEntity.class,
                ApprovalRequestEntity.class,
                ApprovalActionEntity.class,
                MetricSnapshotEntity.class,
                SyncMetaEntity.class
        }},
        version = 1,
        exportSchema = false
)
@TypeConverters(Converters.class)
public abstract class AppDatabase extends RoomDatabase {{
    private static volatile AppDatabase INSTANCE;
    public static final ExecutorService IO = Executors.newSingleThreadExecutor();

    public abstract UserDao userDao();
    public abstract ApprovalRequestDao approvalRequestDao();
    public abstract ApprovalActionDao approvalActionDao();
    public abstract MetricDao metricDao();
    public abstract SyncMetaDao syncMetaDao();

    public static AppDatabase get(Context context) {{
        if (INSTANCE == null) {{
            synchronized (AppDatabase.class) {{
                if (INSTANCE == null) {{
                    INSTANCE = Room.databaseBuilder(context.getApplicationContext(), AppDatabase.class, "approval_hub.db")
                            .fallbackToDestructiveMigration()
                            .build();
                }}
            }}
        }}
        return INSTANCE;
    }}

    public static void seed(AppDatabase db) {{
        if (db.userDao().count() > 0) {{
            rehashDemoUsersIfNeeded(db);
            return;
        }}
        long now = System.currentTimeMillis();
        List<UserEntity> users = Arrays.asList(
                new UserEntity(1, "admin", "Alya Admin", PasswordHasher.hash("admin123"), Role.ADMIN, "IT"),
                new UserEntity(2, "director", "Budi Director", PasswordHasher.hash("dir123"), Role.DIRECTOR, "Executive"),
                new UserEntity(3, "manager", "Citra Manager", PasswordHasher.hash("mgr123"), Role.MANAGER, "Operations"),
                new UserEntity(4, "supervisor", "Dewi Supervisor", PasswordHasher.hash("spv123"), Role.SUPERVISOR, "Operations"),
                new UserEntity(5, "staff", "Eko Staff", PasswordHasher.hash("staff123"), Role.STAFF, "Operations"),
                new UserEntity(6, "staff2", "Fira Staff", PasswordHasher.hash("staff123"), Role.STAFF, "Finance")
        );
        db.userDao().upsertAll(users);

        Object[][] samples = new Object[][]{{
                {{"Laptop Development", "Pengadaan laptop engineering", RequestType.PURCHASE, 18_500_000.0, 5L, "Operations", ApprovalStatus.PENDING_L1, 5L, 5L}},
                {{"Cuti Tahunan 5 Hari", "Cuti keluarga", RequestType.LEAVE, 0.0, 6L, "Finance", ApprovalStatus.PENDING_L2, 4L, 2L}},
                {{"Reimburse Workshop", "Workshop UX Jakarta", RequestType.EXPENSE, 2_750_000.0, 5L, "Operations", ApprovalStatus.PENDING_L3, 7L, 1L}},
                {{"Akses Staging Server", "Akses environment staging", RequestType.ACCESS, 0.0, 6L, "Finance", ApprovalStatus.APPROVED, 10L, 6L}},
                {{"Printer Office", "Printer lantai 3", RequestType.PURCHASE, 4_200_000.0, 5L, "Operations", ApprovalStatus.REJECTED, 8L, 7L}},
                {{"Mouse Wireless", "Mouse low value → L1 only", RequestType.PURCHASE, 350_000.0, 5L, "Operations", ApprovalStatus.PENDING_L1, 3L, 3L}},
                {{"Overdue Escalate Demo", "Idle > 2 hari untuk worker escalate", RequestType.EXPENSE, 1_200_000.0, 6L, "Finance", ApprovalStatus.PENDING_L1, 6L, 5L}}
        }};

        for (Object[] s : samples) {{
            RequestType type = (RequestType) s[2];
            double amount = (Double) s[3];
            ApprovalStatus status = (ApprovalStatus) s[6];
            int maxLevel = AmountBasedRules.requiredMaxLevel(type, amount);
            int currentLevel = 1;
            if (status == ApprovalStatus.PENDING_L1) currentLevel = 1;
            else if (status == ApprovalStatus.PENDING_L2) currentLevel = 2;
            else if (status == ApprovalStatus.PENDING_L3 || status == ApprovalStatus.APPROVED) currentLevel = Math.min(3, maxLevel);
            currentLevel = Math.min(currentLevel, maxLevel);
            ApprovalRequestEntity entity = new ApprovalRequestEntity(
                    (String) s[0], (String) s[1], type, amount, (Long) s[4], (String) s[5],
                    status, currentLevel, maxLevel, false,
                    now - days((Long) s[7]), now - days((Long) s[8]));
            long id = db.approvalRequestDao().insert(entity);
            if (status == ApprovalStatus.PENDING_L2) {{
                db.approvalActionDao().insert(new ApprovalActionEntity(id, 4, 1, "APPROVE", "Disetujui supervisor", now - days(3)));
            }} else if (status == ApprovalStatus.PENDING_L3) {{
                db.approvalActionDao().insert(new ApprovalActionEntity(id, 4, 1, "APPROVE", "OK L1", now - days(5)));
                db.approvalActionDao().insert(new ApprovalActionEntity(id, 3, 2, "APPROVE", "OK L2", now - days(2)));
            }} else if (status == ApprovalStatus.APPROVED) {{
                db.approvalActionDao().insert(new ApprovalActionEntity(id, 4, 1, "APPROVE", "Approved L1", now - days(9)));
                db.approvalActionDao().insert(new ApprovalActionEntity(id, 3, 2, "APPROVE", "Approved L2", now - days(8)));
                db.approvalActionDao().insert(new ApprovalActionEntity(id, 2, 3, "APPROVE", "Approved L3", now - days(7)));
            }} else if (status == ApprovalStatus.REJECTED) {{
                db.approvalActionDao().insert(new ApprovalActionEntity(id, 4, 1, "REJECT", "Budget belum tersedia", now - days(7)));
            }}
        }}

        for (ApprovalRequestEntity r : db.approvalRequestDao().getAll()) {{
            if (r.title.contains("Overdue")) {{
                r.updatedAt = now - TimeUnit.DAYS.toMillis(3);
                db.approvalRequestDao().update(r);
            }}
        }}

        List<MetricSnapshotEntity> metrics = new ArrayList<>();
        for (int week = 0; week <= 11; week++) {{
            long stamp = now - days((11 - week) * 7L);
            metrics.add(new MetricSnapshotEntity("W" + (week + 1), "submitted", 6 + (week % 4) * 2, stamp));
            metrics.add(new MetricSnapshotEntity("W" + (week + 1), "approved", 3 + (week % 5), stamp));
            metrics.add(new MetricSnapshotEntity("W" + (week + 1), "rejected", 1 + (week % 3), stamp));
            metrics.add(new MetricSnapshotEntity("W" + (week + 1), "avg_hours", 18 + week * 1.5, stamp));
        }}
        db.metricDao().upsertAll(metrics);
        db.syncMetaDao().upsert(new SyncMetaEntity(1, 0, "NEVER", 0));
    }}

    private static void rehashDemoUsersIfNeeded(AppDatabase db) {{
        String[][] demos = {{
                {{"admin", "admin123"}}, {{"director", "dir123"}}, {{"manager", "mgr123"}},
                {{"supervisor", "spv123"}}, {{"staff", "staff123"}}, {{"staff2", "staff123"}}
        }};
        List<UserEntity> updated = new ArrayList<>();
        for (String[] d : demos) {{
            UserEntity user = db.userDao().findByUsername(d[0]);
            if (user != null && !PasswordHasher.matches(d[1], user.passwordHash)) {{
                user.passwordHash = PasswordHasher.hash(d[1]);
                updated.add(user);
            }}
        }}
        if (!updated.isEmpty()) db.userDao().upsertAll(updated);
    }}

    private static long days(long value) {{
        return TimeUnit.DAYS.toMillis(value);
    }}
}}
''')


def gen_data() -> None:
    empty_consumer("data")
    w("data/build.gradle.kts", lib_build(f"{PKG}.data", [
        'api(project(":domain"))',
        'api(project(":core:database"))',
        'api(project(":core:preference"))',
        'api(project(":core:network"))',
        'implementation(project(":core:notification"))',
        'implementation(project(":core:common"))',
        "implementation(libs.androidx.appcompat)",
        "implementation(libs.androidx.lifecycle.livedata)",
    ]))
    w("data/src/main/AndroidManifest.xml", empty_manifest(f"{PKG}.data"))
    base = f"data/src/main/java/{P}/data"

    w(f"{base}/mapper/Mappers.java", f'''
package {PKG}.data.mapper;

import {PKG}.core.database.dao.StatusCountRow;
import {PKG}.core.database.dao.TypeStatRow;
import {PKG}.core.database.entity.ApprovalActionEntity;
import {PKG}.core.database.entity.ApprovalRequestEntity;
import {PKG}.core.database.entity.SyncMetaEntity;
import {PKG}.core.database.entity.UserEntity;
import {PKG}.core.model.ApprovalAction;
import {PKG}.core.model.ApprovalRequest;
import {PKG}.core.model.StatusCount;
import {PKG}.core.model.SyncMeta;
import {PKG}.core.model.TypeStat;
import {PKG}.core.model.User;

import java.util.ArrayList;
import java.util.List;

public final class Mappers {{
    private Mappers() {{}}

    public static User toUser(UserEntity e) {{
        if (e == null) return null;
        return new User(e.id, e.username, e.displayName, e.role, e.department);
    }}

    public static ApprovalRequest toRequest(ApprovalRequestEntity e) {{
        if (e == null) return null;
        return new ApprovalRequest(e.id, e.title, e.description, e.type, e.amount, e.requesterId,
                e.department, e.status, e.currentLevel, e.requiredMaxLevel, e.escalated, e.createdAt, e.updatedAt);
    }}

    public static List<ApprovalRequest> toRequests(List<ApprovalRequestEntity> list) {{
        List<ApprovalRequest> out = new ArrayList<>();
        if (list == null) return out;
        for (ApprovalRequestEntity e : list) out.add(toRequest(e));
        return out;
    }}

    public static ApprovalAction toAction(ApprovalActionEntity e) {{
        return new ApprovalAction(e.id, e.requestId, e.actorId, e.level, e.decision, e.comment, e.createdAt);
    }}

    public static List<ApprovalAction> toActions(List<ApprovalActionEntity> list) {{
        List<ApprovalAction> out = new ArrayList<>();
        if (list == null) return out;
        for (ApprovalActionEntity e : list) out.add(toAction(e));
        return out;
    }}

    public static StatusCount toStatusCount(StatusCountRow r) {{
        return new StatusCount(r.status, r.count);
    }}

    public static TypeStat toTypeStat(TypeStatRow r) {{
        return new TypeStat(r.type, r.count, r.totalAmount);
    }}

    public static SyncMeta toSyncMeta(SyncMetaEntity e) {{
        if (e == null) return null;
        return new SyncMeta(e.lastSyncedAt, e.lastSyncStatus, e.pendingPushCount);
    }}
}}
''')

    w(f"{base}/sync/SyncRepository.java", f'''
package {PKG}.data.sync;

import {PKG}.core.database.AppDatabase;
import {PKG}.core.database.entity.ApprovalRequestEntity;
import {PKG}.core.database.entity.SyncMetaEntity;
import {PKG}.core.model.SyncMeta;
import {PKG}.core.network.RemoteApi;
import {PKG}.data.mapper.Mappers;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.Transformations;

public class SyncRepository {{
    private final AppDatabase db;
    private final RemoteApi remoteApi;

    public SyncRepository(AppDatabase db, RemoteApi remoteApi) {{
        this.db = db;
        this.remoteApi = remoteApi;
    }}

    public LiveData<SyncMeta> observeMeta() {{
        return Transformations.map(db.syncMetaDao().observe(), Mappers::toSyncMeta);
    }}

    public SyncMeta syncNow() throws Exception {{
        int pending = 0;
        for (ApprovalRequestEntity r : db.approvalRequestDao().getAll()) {{
            if (r.status.name().startsWith("PENDING")) pending++;
        }}
        try {{
            remoteApi.pushPending(pending);
            remoteApi.pullRequestCount();
            SyncMetaEntity meta = new SyncMetaEntity(1, System.currentTimeMillis(), "OK", pending);
            db.syncMetaDao().upsert(meta);
            return Mappers.toSyncMeta(meta);
        }} catch (Exception error) {{
            SyncMetaEntity meta = new SyncMetaEntity(1, System.currentTimeMillis(),
                    "ERROR: " + error.getMessage(), 0);
            db.syncMetaDao().upsert(meta);
            throw error;
        }}
    }}
}}
''')

    w(f"{base}/export/ExportUtils.java", f'''
package {PKG}.data.export;

import android.content.Context;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.pdf.PdfDocument;
import android.net.Uri;

import androidx.core.content.FileProvider;

import {PKG}.core.model.ApprovalAction;
import {PKG}.core.model.ApprovalRequest;

import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

public final class ExportUtils {{
    private static final SimpleDateFormat SDF = new SimpleDateFormat("yyyy-MM-dd HH:mm", Locale.getDefault());

    private ExportUtils() {{}}

    public static Uri exportAuditCsv(Context context, List<ApprovalRequest> requests,
                                     List<ApprovalAction> actions, Map<Long, String> userNames) throws Exception {{
        StringBuilder sb = new StringBuilder();
        sb.append("requestId,title,status,type,amount,department,actionId,level,decision,actor,comment,createdAt\\n");
        Map<Long, List<ApprovalAction>> byReq = new HashMap<>();
        for (ApprovalAction a : actions) {{
            byReq.computeIfAbsent(a.requestId, k -> new java.util.ArrayList<>()).add(a);
        }}
        for (ApprovalRequest req : requests) {{
            List<ApprovalAction> rows = byReq.getOrDefault(req.id, java.util.Collections.emptyList());
            if (rows.isEmpty()) {{
                sb.append(req.id).append(",\\"").append(esc(req.title)).append("\\",")
                        .append(req.status).append(",").append(req.type).append(",")
                        .append(req.amount).append(",").append(req.department).append(",,,,,,\\n");
            }} else {{
                for (ApprovalAction a : rows) {{
                    String actor = userNames.containsKey(a.actorId) ? userNames.get(a.actorId) : String.valueOf(a.actorId);
                    sb.append(req.id).append(",\\"").append(esc(req.title)).append("\\",")
                            .append(req.status).append(",").append(req.type).append(",")
                            .append(req.amount).append(",").append(req.department).append(",")
                            .append(a.id).append(",").append(a.level).append(",").append(a.decision).append(",\\"")
                            .append(esc(actor)).append("\\",\\"").append(esc(a.comment)).append("\\",")
                            .append(SDF.format(new Date(a.createdAt))).append("\\n");
                }}
            }}
        }}
        File file = new File(context.getCacheDir(), "audit_" + System.currentTimeMillis() + ".csv");
        try (FileOutputStream fos = new FileOutputStream(file)) {{
            fos.write(sb.toString().getBytes(StandardCharsets.UTF_8));
        }}
        return FileProvider.getUriForFile(context, context.getPackageName() + ".fileprovider", file);
    }}

    public static Uri exportAuditPdf(Context context, List<ApprovalRequest> requests,
                                     List<ApprovalAction> actions, Map<Long, String> userNames) throws Exception {{
        PdfDocument doc = new PdfDocument();
        Paint paint = new Paint();
        paint.setTextSize(10f);
        int pageNumber = 1;
        float y = 40f;
        PdfDocument.Page page = doc.startPage(new PdfDocument.PageInfo.Builder(595, 842, pageNumber).create());
        Canvas canvas = page.getCanvas();
        canvas.drawText("ApprovalHub Audit Trail", 40f, y, paint);
        y += 24f;
        int take = Math.min(40, requests.size());
        for (int i = 0; i < take; i++) {{
            ApprovalRequest req = requests.get(i);
            if (y + 60f > 800f) {{
                doc.finishPage(page);
                pageNumber++;
                page = doc.startPage(new PdfDocument.PageInfo.Builder(595, 842, pageNumber).create());
                canvas = page.getCanvas();
                y = 40f;
            }}
            canvas.drawText("#" + req.id + " " + req.title + " [" + req.status + "]", 40f, y, paint);
            y += 14f;
            canvas.drawText(req.type + " · " + req.amount + " · " + req.department, 48f, y, paint);
            y += 14f;
            for (ApprovalAction a : actions) {{
                if (a.requestId != req.id) continue;
                if (y + 16f > 800f) {{
                    doc.finishPage(page);
                    pageNumber++;
                    page = doc.startPage(new PdfDocument.PageInfo.Builder(595, 842, pageNumber).create());
                    canvas = page.getCanvas();
                    y = 40f;
                }}
                String actor = userNames.containsKey(a.actorId) ? userNames.get(a.actorId) : String.valueOf(a.actorId);
                canvas.drawText("L" + a.level + " " + a.decision + " by " + actor + " — " + a.comment, 56f, y, paint);
                y += 14f;
            }}
            y += 8f;
        }}
        doc.finishPage(page);
        File file = new File(context.getCacheDir(), "audit_" + System.currentTimeMillis() + ".pdf");
        try (FileOutputStream fos = new FileOutputStream(file)) {{
            doc.writeTo(fos);
        }}
        doc.close();
        return FileProvider.getUriForFile(context, context.getPackageName() + ".fileprovider", file);
    }}

    public static void shareUri(Context context, Uri uri, String mime, String title) {{
        Intent intent = new Intent(Intent.ACTION_SEND);
        intent.setType(mime);
        intent.putExtra(Intent.EXTRA_STREAM, uri);
        intent.putExtra(Intent.EXTRA_SUBJECT, title);
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        Intent chooser = Intent.createChooser(intent, title);
        chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        context.startActivity(chooser);
    }}

    public static void shareBitmap(Context context, Bitmap bitmap, String title) throws Exception {{
        File file = new File(context.getCacheDir(), "chart_" + System.currentTimeMillis() + ".png");
        try (FileOutputStream fos = new FileOutputStream(file)) {{
            bitmap.compress(Bitmap.CompressFormat.PNG, 95, fos);
        }}
        Uri uri = FileProvider.getUriForFile(context, context.getPackageName() + ".fileprovider", file);
        shareUri(context, uri, "image/png", title);
    }}

    public static Bitmap createSimpleChartBitmap(List<String> labels, List<Float> values, String title) {{
        int width = 1080, height = 720;
        Bitmap bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
        Canvas canvas = new Canvas(bitmap);
        canvas.drawColor(0xFFFFFFFF);
        Paint titlePaint = new Paint();
        titlePaint.setTextSize(42f);
        titlePaint.setFakeBoldText(true);
        titlePaint.setColor(0xFF0F4C5C);
        Paint barPaint = new Paint();
        barPaint.setColor(0xFF2A9D8F);
        Paint textPaint = new Paint();
        textPaint.setTextSize(28f);
        textPaint.setColor(0xFF333333);
        canvas.drawText(title, 40f, 60f, titlePaint);
        float max = 1f;
        for (Float v : values) if (v != null && v > max) max = v;
        float chartTop = 120f;
        float chartBottom = height - 100f;
        float chartHeight = chartBottom - chartTop;
        float slot = (width - 80f) / Math.max(1, values.size());
        for (int i = 0; i < values.size(); i++) {{
            float v = values.get(i);
            float barH = (v / max) * chartHeight;
            float left = 40f + i * slot + slot * 0.2f;
            float right = left + slot * 0.6f;
            canvas.drawRect(left, chartBottom - barH, right, chartBottom, barPaint);
            String label = i < labels.size() ? labels.get(i) : "";
            if (label.length() > 8) label = label.substring(0, 8);
            canvas.drawText(label, left, chartBottom + 40f, textPaint);
        }}
        return bitmap;
    }}

    private static String esc(String value) {{
        return value == null ? "" : value.replace("\\"", "'");
    }}
}}
''')

    # AppRepository — large file
    w(f"{base}/repository/AppRepository.java", f'''
package {PKG}.data.repository;

import android.content.Context;

import androidx.lifecycle.LiveData;
import androidx.lifecycle.MediatorLiveData;
import androidx.lifecycle.MutableLiveData;
import androidx.lifecycle.Transformations;

import {PKG}.core.database.AppDatabase;
import {PKG}.core.database.dao.StatusCountRow;
import {PKG}.core.database.dao.TypeStatRow;
import {PKG}.core.database.entity.ApprovalActionEntity;
import {PKG}.core.database.entity.ApprovalRequestEntity;
import {PKG}.core.database.entity.UserEntity;
import {PKG}.core.model.ApprovalAction;
import {PKG}.core.model.ApprovalRequest;
import {PKG}.core.model.ApprovalStatus;
import {PKG}.core.model.DashboardStats;
import {PKG}.core.model.Permission;
import {PKG}.core.model.RequestFilter;
import {PKG}.core.model.RequestType;
import {PKG}.core.model.Role;
import {PKG}.core.model.StatusCount;
import {PKG}.core.model.SyncMeta;
import {PKG}.core.model.ThemeMode;
import {PKG}.core.model.TypeStat;
import {PKG}.core.model.User;
import {PKG}.core.notification.ApprovalNotifier;
import {PKG}.core.preference.UserPreferences;
import {PKG}.data.mapper.Mappers;
import {PKG}.data.sync.SyncRepository;
import {PKG}.domain.analytics.AnalyticsCalculator;
import {PKG}.domain.analytics.BottleneckLevel;
import {PKG}.domain.analytics.SlaStats;
import {PKG}.domain.approval.AmountBasedRules;
import {PKG}.domain.approval.ApprovalWorkflow;
import {PKG}.domain.rbac.RbacPolicy;
import {PKG}.domain.repository.ApprovalRepository;
import {PKG}.domain.repository.SessionRepository;
import {PKG}.domain.security.PasswordHasher;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.TimeUnit;

public class AppRepository implements SessionRepository, ApprovalRepository {{
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

    public AppRepository(AppDatabase db, UserPreferences prefs, SyncRepository syncRepository, Context appContext) {{
        this.db = db;
        this.prefs = prefs;
        this.syncRepository = syncRepository;
        this.appContext = appContext.getApplicationContext();
    }}

    @Override public LiveData<User> observeSession() {{ return sessionLive; }}
    @Override public LiveData<Role> observeImpersonateRole() {{ return impersonateLive; }}
    @Override public User getSession() {{ return session; }}
    @Override public Role getImpersonateRole() {{ return impersonateRole; }}

    public boolean isReadOnly() {{ return impersonateRole != null; }}

    @Override
    public void ensureSeeded() {{
        AppDatabase.seed(db);
    }}

    @Override
    public User restoreSession() {{
        Long id = prefs.getSessionUserId();
        if (id == null) return null;
        if (checkSessionTimeoutInternal(false)) return null;
        UserEntity entity = db.userDao().getById(id);
        if (entity == null) return null;
        session = Mappers.toUser(entity);
        sessionLive.postValue(session);
        return session;
    }}

    @Override
    public User login(String username, String password) throws Exception {{
        UserEntity user = db.userDao().findByUsername(username.trim());
        if (user == null || !PasswordHasher.matches(password, user.passwordHash)) {{
            throw new IllegalArgumentException("Username atau password salah");
        }}
        session = Mappers.toUser(user);
        impersonateRole = null;
        sessionLive.postValue(session);
        impersonateLive.postValue(null);
        prefs.saveSessionUserId(user.id);
        prefs.touchActivity();
        return session;
    }}

    @Override
    public void logoutAndClear() {{
        session = null;
        impersonateRole = null;
        sessionLive.postValue(null);
        impersonateLive.postValue(null);
        prefs.saveSessionUserId(null);
    }}

    @Override
    public void touchActivity() {{
        prefs.touchActivity();
    }}

    @Override
    public boolean checkSessionTimeout() {{
        return checkSessionTimeoutInternal(true);
    }}

    private boolean checkSessionTimeoutInternal(boolean touchIfOk) {{
        if (session == null && prefs.getSessionUserId() == null) return false;
        long last = prefs.getLastActivityAt();
        if (last > 0 && System.currentTimeMillis() - last > SESSION_TIMEOUT_MS) {{
            logoutAndClear();
            return true;
        }}
        if (touchIfOk) prefs.touchActivity();
        return false;
    }}

    private Set<Permission> currentPermissions() {{
        if (session == null) return Collections.emptySet();
        if (impersonateRole != null) return RbacPolicy.impersonationPermissions(impersonateRole);
        return RbacPolicy.permissionsFor(session.role);
    }}

    @Override
    public boolean hasPermission(Permission permission) {{
        return currentPermissions().contains(permission);
    }}

    @Override
    public void setImpersonateRole(Role role) {{
        if (session == null) return;
        if (role != null && !RbacPolicy.hasPermission(session.role, Permission.IMPERSONATE)) return;
        impersonateRole = role;
        impersonateLive.postValue(role);
    }}

    @Override
    public void setThemeMode(ThemeMode mode) {{
        prefs.setThemeMode(mode);
    }}

    @Override
    public ThemeMode getThemeMode() {{
        return prefs.getThemeMode();
    }}

    public void updateFilter(RequestFilter filter) {{
        filterLive.setValue(filter);
    }}

    @Override
    public LiveData<List<ApprovalRequest>> observeRequestsForCurrentUser() {{
        MediatorLiveData<List<ApprovalRequest>> result = new MediatorLiveData<>();
        LiveData<List<ApprovalRequestEntity>> all = db.approvalRequestDao().observeAll();
        Runnable compute = () -> {{
            User user = session;
            Role imp = impersonateRole;
            RequestFilter filt = filterLive.getValue() == null ? new RequestFilter() : filterLive.getValue();
            List<ApprovalRequestEntity> source = all.getValue();
            if (user == null || source == null) {{
                result.setValue(Collections.emptyList());
                return;
            }}
            Role role = imp != null ? imp : user.role;
            Set<Permission> perms = imp != null ? RbacPolicy.impersonationPermissions(imp) : RbacPolicy.permissionsFor(user.role);
            List<ApprovalRequestEntity> scoped = new ArrayList<>();
            for (ApprovalRequestEntity it : source) {{
                boolean ok;
                if (perms.contains(Permission.VIEW_ALL_REQUESTS)) ok = true;
                else if (perms.contains(Permission.VIEW_DEPARTMENT_REQUESTS)) {{
                    ok = it.department.equalsIgnoreCase(user.department) || it.requesterId == user.id
                            || (role == Role.SUPERVISOR && it.status == ApprovalStatus.PENDING_L1);
                }} else {{
                    ok = it.requesterId == user.id;
                }}
                if (ok && filt.matches(Mappers.toRequest(it), "")) scoped.add(it);
            }}
            result.setValue(Mappers.toRequests(scoped));
        }};
        result.addSource(all, v -> compute.run());
        result.addSource(sessionLive, v -> compute.run());
        result.addSource(impersonateLive, v -> compute.run());
        result.addSource(filterLive, v -> compute.run());
        return result;
    }}

    @Override
    public LiveData<List<ApprovalRequest>> observeInbox() {{
        MediatorLiveData<List<ApprovalRequest>> result = new MediatorLiveData<>();
        LiveData<List<ApprovalRequestEntity>> all = db.approvalRequestDao().observeAll();
        Runnable compute = () -> {{
            User user = session;
            List<ApprovalRequestEntity> source = all.getValue();
            if (user == null || impersonateRole != null || source == null) {{
                result.setValue(Collections.emptyList());
                return;
            }}
            List<ApprovalRequest> out = new ArrayList<>();
            for (ApprovalRequestEntity it : source) {{
                if (ApprovalWorkflow.canActOn(it.status, user.role, false)) out.add(Mappers.toRequest(it));
            }}
            result.setValue(out);
        }};
        result.addSource(all, v -> compute.run());
        result.addSource(sessionLive, v -> compute.run());
        result.addSource(impersonateLive, v -> compute.run());
        return result;
    }}

    @Override
    public LiveData<List<ApprovalAction>> observeActions(long requestId) {{
        return Transformations.map(db.approvalActionDao().observeByRequest(requestId), Mappers::toActions);
    }}

    @Override
    public LiveData<DashboardStats> observeDashboardStats() {{
        MediatorLiveData<DashboardStats> result = new MediatorLiveData<>();
        LiveData<List<ApprovalRequest>> mine = observeRequestsForCurrentUser();
        LiveData<List<ApprovalRequest>> inbox = observeInbox();
        LiveData<List<StatusCountRow>> counts = db.approvalRequestDao().observeStatusCounts();
        Runnable compute = () -> {{
            List<ApprovalRequest> m = mine.getValue();
            List<ApprovalRequest> in = inbox.getValue();
            List<StatusCountRow> c = counts.getValue();
            int approved = 0, rejected = 0, pipeline = 0;
            if (c != null) {{
                for (StatusCountRow row : c) {{
                    if (row.status == ApprovalStatus.APPROVED) approved = row.count;
                    if (row.status == ApprovalStatus.REJECTED) rejected = row.count;
                    if (row.status == ApprovalStatus.PENDING_L1 || row.status == ApprovalStatus.PENDING_L2 || row.status == ApprovalStatus.PENDING_L3) {{
                        pipeline += row.count;
                    }}
                }}
            }}
            result.setValue(new DashboardStats(
                    m == null ? 0 : m.size(),
                    in == null ? 0 : in.size(),
                    approved, rejected, pipeline));
        }};
        result.addSource(mine, v -> compute.run());
        result.addSource(inbox, v -> compute.run());
        result.addSource(counts, v -> compute.run());
        return result;
    }}

    @Override
    public LiveData<List<StatusCount>> observeStatusCounts() {{
        return Transformations.map(db.approvalRequestDao().observeStatusCounts(), rows -> {{
            List<StatusCount> out = new ArrayList<>();
            if (rows != null) for (StatusCountRow r : rows) out.add(Mappers.toStatusCount(r));
            return out;
        }});
    }}

    @Override
    public LiveData<List<TypeStat>> observeTypeStats() {{
        return Transformations.map(db.approvalRequestDao().observeTypeStats(), rows -> {{
            List<TypeStat> out = new ArrayList<>();
            if (rows != null) for (TypeStatRow r : rows) out.add(Mappers.toTypeStat(r));
            return out;
        }});
    }}

    @Override
    public LiveData<SyncMeta> observeSyncMeta() {{
        return syncRepository.observeMeta();
    }}

    @Override
    public LiveData<Integer> observePendingCount() {{
        return db.approvalRequestDao().observePendingCount();
    }}

    @Override
    public ApprovalRequest getRequest(long requestId) {{
        return Mappers.toRequest(db.approvalRequestDao().getById(requestId));
    }}

    @Override
    public long createRequest(String title, String description, RequestType type, double amount) throws Exception {{
        if (isReadOnly()) throw new SecurityException("Mode impersonate read-only");
        if (session == null) throw new IllegalStateException("Belum login");
        if (!RbacPolicy.hasPermission(session.role, Permission.CREATE_REQUEST)) {{
            throw new SecurityException("Role tidak boleh membuat request");
        }}
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
    }}

    @Override
    public void decide(long requestId, boolean approve, String comment) throws Exception {{
        if (isReadOnly()) throw new SecurityException("Mode impersonate read-only");
        if (session == null) throw new IllegalStateException("Belum login");
        ApprovalRequestEntity request = db.approvalRequestDao().getById(requestId);
        if (request == null) throw new IllegalArgumentException("Request tidak ditemukan");
        if (!ApprovalWorkflow.canActOn(request.status, session.role, false)) {{
            throw new SecurityException("Anda tidak berwenang di level ini");
        }}
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
        if (approve && newStatus.name().startsWith("PENDING")) {{
            ApprovalNotifier.notifyInbox(appContext, "Menunggu " + ApprovalWorkflow.levelLabel(newStatus),
                    request.title, (int) (4000 + requestId));
        }}
        prefs.touchActivity();
    }}

    @Override
    public void forceEscalate(long requestId) throws Exception {{
        if (isReadOnly()) throw new SecurityException("Read-only");
        if (session == null) throw new IllegalStateException("Belum login");
        if (!RbacPolicy.hasPermission(session.role, Permission.FORCE_ESCALATE)) {{
            throw new SecurityException("Tidak punya FORCE_ESCALATE");
        }}
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
    }}

    @Override
    public int runEscalationPass() {{
        long now = System.currentTimeMillis();
        List<ApprovalRequestEntity> overdue = db.approvalRequestDao()
                .getOverdue(now - ApprovalWorkflow.IDLE_BEFORE_ESCALATE_MS);
        int count = 0;
        for (ApprovalRequestEntity request : overdue) {{
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
        }}
        return count;
    }}

    @Override
    public SyncMeta syncNow() throws Exception {{
        return syncRepository.syncNow();
    }}

    @Override
    public List<ApprovalRequest> allRequests() {{
        return Mappers.toRequests(db.approvalRequestDao().getAll());
    }}

    @Override
    public List<ApprovalAction> allActions() {{
        return Mappers.toActions(db.approvalActionDao().getAll());
    }}

    @Override
    public Map<Long, String> buildUserNameMap() {{
        Map<Long, String> map = new HashMap<>();
        for (UserEntity u : db.userDao().getAll()) map.put(u.id, u.displayName);
        return map;
    }}

    @Override
    public SlaStats computeSla() {{
        return AnalyticsCalculator.slaStats(allRequests(), 48);
    }}

    @Override
    public List<BottleneckLevel> computeBottleneck() {{
        return AnalyticsCalculator.bottleneckHeatmap(allRequests(), allActions());
    }}
}}
''')


print("domain/data generators ready")
