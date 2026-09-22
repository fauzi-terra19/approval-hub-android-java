package com.fauzi.wings.data.di;

import androidx.annotation.NonNull;
import androidx.lifecycle.ViewModel;
import androidx.lifecycle.ViewModelProvider;

import com.fauzi.wings.domain.repository.ApprovalRepository;
import com.fauzi.wings.domain.repository.SessionRepository;

/**
 * Tiny factory helper used by feature modules (keeps :data free of feature class imports).
 */
public final class VmFactories {
    private VmFactories() {}

    public interface Creator {
        ViewModel create(SessionRepository session, ApprovalRepository approval);
    }

    public static ViewModelProvider.Factory of(AppContainerHolder holder, Creator creator) {
        return new ViewModelProvider.Factory() {
            @NonNull
            @Override
            @SuppressWarnings("unchecked")
            public <T extends ViewModel> T create(@NonNull Class<T> modelClass) {
                return (T) creator.create(holder.getSessionRepository(), holder.getApprovalRepository());
            }
        };
    }

    public static ViewModelProvider.Factory ofDetail(AppContainerHolder holder, long requestId,
                                                     DetailCreator creator) {
        return new ViewModelProvider.Factory() {
            @NonNull
            @Override
            @SuppressWarnings("unchecked")
            public <T extends ViewModel> T create(@NonNull Class<T> modelClass) {
                return (T) creator.create(requestId, holder.getSessionRepository(), holder.getApprovalRepository());
            }
        };
    }

    public interface DetailCreator {
        ViewModel create(long requestId, SessionRepository session, ApprovalRepository approval);
    }
}
