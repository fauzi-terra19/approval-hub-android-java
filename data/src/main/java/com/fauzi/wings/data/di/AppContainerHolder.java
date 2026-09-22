package com.fauzi.wings.data.di;

import com.fauzi.wings.domain.repository.ApprovalRepository;
import com.fauzi.wings.domain.repository.SessionRepository;

public interface AppContainerHolder {
    SessionRepository getSessionRepository();
    ApprovalRepository getApprovalRepository();
}
