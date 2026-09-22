package com.fauzi.wings.feature.analytics;
import android.os.Bundle; import android.view.View;
import androidx.annotation.*; import androidx.lifecycle.ViewModelProvider;
import com.fauzi.wings.core.ui.BaseMvvmFragment; import com.fauzi.wings.data.di.HasAppContainer; import com.fauzi.wings.data.export.ExportUtils;
import com.fauzi.wings.feature.analytics.databinding.FragmentAnalyticsBinding;
public class AnalyticsFragment extends BaseMvvmFragment<FragmentAnalyticsBinding, AnalyticsViewModel> {
    public AnalyticsFragment() { super(R.layout.fragment_analytics); }
    @NonNull @Override protected AnalyticsViewModel createViewModel() {
        return new ViewModelProvider(this, HasAppContainer.from(requireContext()).getViewModelFactory()).get(AnalyticsViewModel.class);
    }
    @Override public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        binding.btnExportChart.setOnClickListener(v -> {
            try { if (!viewModel.chartValues().isEmpty())
                ExportUtils.shareBitmap(requireContext(), ExportUtils.createSimpleChartBitmap(viewModel.chartLabels(), viewModel.chartValues(), "Status distribution"), "ApprovalHub Chart");
            } catch (Exception ignored) {}
        });
        observe(viewModel.getUiState(), state -> binding.setContent(state.content));
    }
}
