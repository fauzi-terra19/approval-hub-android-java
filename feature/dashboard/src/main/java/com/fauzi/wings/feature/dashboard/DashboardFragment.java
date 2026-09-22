package com.fauzi.wings.feature.dashboard;

import android.os.Bundle;
import android.view.View;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.lifecycle.ViewModelProvider;
import androidx.navigation.Navigation;
import androidx.recyclerview.widget.LinearLayoutManager;

import com.fauzi.wings.core.ui.BaseMvvmFragment;
import com.fauzi.wings.core.ui.NavRoutes;
import com.fauzi.wings.core.ui.RequestListAdapter;
import com.fauzi.wings.data.di.HasAppContainer;
import com.fauzi.wings.feature.dashboard.databinding.FragmentDashboardBinding;

public class DashboardFragment extends BaseMvvmFragment<FragmentDashboardBinding, DashboardViewModel> {
    private RequestListAdapter adapter;

    public DashboardFragment() {
        super(R.layout.fragment_dashboard);
    }

    @NonNull
    @Override
    protected DashboardViewModel createViewModel() {
        return new ViewModelProvider(this, HasAppContainer.from(requireContext()).getViewModelFactory())
                .get(DashboardViewModel.class);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        adapter = new RequestListAdapter(req ->
                Navigation.findNavController(view).navigate(NavRoutes.detail(req.id)));
        binding.recycler.setLayoutManager(new LinearLayoutManager(requireContext()));
        binding.recycler.setAdapter(adapter);
        binding.btnCreate.setOnClickListener(v ->
                Navigation.findNavController(view).navigate(NavRoutes.CREATE));
        observe(viewModel.getUiState(), state -> {
            binding.setTitle(state.title);
            binding.setUserLine(state.user == null ? ""
                    : state.user.displayName + " · " + state.user.role + " · " + state.user.department);
            binding.setStats("Visible " + state.stats.totalVisible
                    + " · Inbox " + state.stats.pendingInbox
                    + " · Approved " + state.stats.approved
                    + " · Rejected " + state.stats.rejected
                    + " · Pipeline " + state.stats.inPipeline);
            adapter.submitList(state.requests);
        });
    }
}
