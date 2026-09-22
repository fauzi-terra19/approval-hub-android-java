package com.fauzi.wings.domain;

import static com.google.common.truth.Truth.assertThat;

import com.fauzi.wings.core.model.ApprovalStatus;
import com.fauzi.wings.core.model.RequestType;
import com.fauzi.wings.core.model.Role;
import com.fauzi.wings.domain.approval.AmountBasedRules;
import com.fauzi.wings.domain.approval.ApprovalWorkflow;
import com.fauzi.wings.domain.rbac.RbacPolicy;

import org.junit.Test;

public class DomainLogicTest {
    @Test
    public void purchaseAmountRules() {
        assertThat(AmountBasedRules.requiredMaxLevel(RequestType.PURCHASE, 1_000_000)).isEqualTo(1);
        assertThat(AmountBasedRules.requiredMaxLevel(RequestType.PURCHASE, 3_000_000)).isEqualTo(2);
        assertThat(AmountBasedRules.requiredMaxLevel(RequestType.PURCHASE, 12_000_000)).isEqualTo(3);
    }

    @Test
    public void workflowApproveAndEscalate() {
        assertThat(ApprovalWorkflow.nextStatusOnApprove(ApprovalStatus.PENDING_L1, 2))
                .isEqualTo(ApprovalStatus.PENDING_L2);
        assertThat(ApprovalWorkflow.nextStatusOnApprove(ApprovalStatus.PENDING_L2, 2))
                .isEqualTo(ApprovalStatus.APPROVED);
        assertThat(ApprovalWorkflow.escalateStatus(ApprovalStatus.PENDING_L1, 3))
                .isEqualTo(ApprovalStatus.PENDING_L2);
        assertThat(ApprovalWorkflow.canActOn(ApprovalStatus.PENDING_L1, Role.SUPERVISOR, false)).isTrue();
        assertThat(ApprovalWorkflow.canActOn(ApprovalStatus.PENDING_L1, Role.STAFF, false)).isFalse();
    }

    @Test
    public void rbacPermissions() {
        assertThat(RbacPolicy.hasPermission(Role.ADMIN, com.fauzi.wings.core.model.Permission.FORCE_ESCALATE)).isTrue();
        assertThat(RbacPolicy.hasPermission(Role.STAFF, com.fauzi.wings.core.model.Permission.CREATE_REQUEST)).isTrue();
        assertThat(RbacPolicy.canApproveLevel(Role.MANAGER, 2)).isTrue();
    }
}
