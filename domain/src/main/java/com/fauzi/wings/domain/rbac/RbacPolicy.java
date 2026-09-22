package com.fauzi.wings.domain.rbac;

import com.fauzi.wings.core.model.Permission;
import com.fauzi.wings.core.model.Role;

import java.util.Collections;
import java.util.EnumSet;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

public final class RbacPolicy {
    private static final Map<Role, Set<Permission>> ROLE_PERMISSIONS = new HashMap<>();

    static {
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
    }

    private RbacPolicy() {}

    public static Set<Permission> permissionsFor(Role role) {
        Set<Permission> set = ROLE_PERMISSIONS.get(role);
        return set == null ? Collections.emptySet() : Collections.unmodifiableSet(set);
    }

    public static boolean hasPermission(Role role, Permission permission) {
        return permissionsFor(role).contains(permission);
    }

    public static boolean canApproveLevel(Role role, int level) {
        switch (level) {
            case 1: return hasPermission(role, Permission.APPROVE_LEVEL_1);
            case 2: return hasPermission(role, Permission.APPROVE_LEVEL_2);
            case 3: return hasPermission(role, Permission.APPROVE_LEVEL_3);
            default: return false;
        }
    }

    public static String dashboardTitle(Role role) {
        switch (role) {
            case ADMIN: return "Admin Control Center";
            case DIRECTOR: return "Executive Dashboard";
            case MANAGER: return "Manager Workspace";
            case SUPERVISOR: return "Supervisor Desk";
            case STAFF: return "My Requests";
            default: return "Dashboard";
        }
    }

    public static Set<Permission> impersonationPermissions(Role target) {
        EnumSet<Permission> base = EnumSet.copyOf(permissionsFor(target));
        base.remove(Permission.APPROVE_LEVEL_1);
        base.remove(Permission.APPROVE_LEVEL_2);
        base.remove(Permission.APPROVE_LEVEL_3);
        base.remove(Permission.MANAGE_USERS);
        base.remove(Permission.IMPERSONATE);
        base.remove(Permission.FORCE_ESCALATE);
        base.remove(Permission.CREATE_REQUEST);
        return base;
    }
}
