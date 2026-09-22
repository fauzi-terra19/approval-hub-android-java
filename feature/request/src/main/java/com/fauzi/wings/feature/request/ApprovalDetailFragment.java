package com.fauzi.wings.feature.request;

import android.os.Bundle;
import android.view.View;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.lifecycle.ViewModel;
import androidx.lifecycle.ViewModelProvider;

import com.fauzi.wings.core.common.DateFormatters;
import com.fauzi.wings.core.model.ApprovalAction;
import com.fauzi.wings.core.ui.BaseMvvmFragment;
import com.fauzi.wings.data.di.HasAppContainer;
import com.fauzi.wings.data.repository.AppRepository;
import com.fauzi.wings.feature.request.databinding.FragmentApprovalDetailBinding;

public class ApprovalDetailFragment extends BaseMvvmFragment<FragmentApprovalDetailBinding, ApprovalDetailViewModel> {
    public ApprovalDetailFragment() {
        super(R.layout.fragment_approval_detail);
    }

    @NonNull
    @Override
    protected ApprovalDetailViewModel createViewModel() {
        final long requestId = getArguments() == null ? 0L : getArguments().getLong("requestId", 0L);
        final AppRepository repo = HasAppContainer.from(requireContext()).getRepository();
        return new ViewModelProvider(this, new ViewModelProvider.Factory() {
            @NonNull
            @Override
            @SuppressWarnings("unchecked")
            public <T extends ViewModel> T create(@NonNull Class<T> modelClass) {
                return (T) new ApprovalDetailViewModel(requestId, repo, repo);
            }
        }).get(ApprovalDetailViewModel.class);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        binding.btnApprove.setOnClickListener(v -> viewModel.decide(true,
                binding.inputComment.getText() == null ? "" : binding.inputComment.getText().toString()));
        binding.btnReject.setOnClickListener(v -> viewModel.decide(false,
                binding.inputComment.getText() == null ? "" : binding.inputComment.getText().toString()));
        binding.btnEscalate.setOnClickListener(v -> viewModel.escalate());
        observe(viewModel.getUiState(), state -> {
            binding.setDetail(state.detailText);
            binding.setCanAct(state.canAct);
            binding.setCanEscalate(state.canEscalate);
            binding.setMessage(state.message);
            StringBuilder sb = new StringBuilder();
            for (ApprovalAction a : state.actions) {
                if (sb.length() > 0) sb.append("\n");
                sb.append("L").append(a.level).append(" ").append(a.decision).append(" — ")
                        .append(a.comment).append(" (").append(DateFormatters.full(a.createdAt)).append(")");
            }
            binding.textActions.setText(sb.toString());
        });
    }
}
