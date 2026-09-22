package com.fauzi.wings.feature.audit;
import android.net.Uri; import android.os.Bundle; import android.view.View;
import androidx.annotation.*; import androidx.lifecycle.ViewModelProvider;
import com.fauzi.wings.core.ui.BaseMvvmFragment; import com.fauzi.wings.data.di.HasAppContainer; import com.fauzi.wings.data.export.ExportUtils;
import com.fauzi.wings.feature.audit.databinding.FragmentAuditBinding;
public class AuditFragment extends BaseMvvmFragment<FragmentAuditBinding, AuditViewModel> {
    public AuditFragment() { super(R.layout.fragment_audit); }
    @NonNull @Override protected AuditViewModel createViewModel() {
        return new ViewModelProvider(this, HasAppContainer.from(requireContext()).getViewModelFactory()).get(AuditViewModel.class);
    }
    @Override public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        binding.btnCsv.setVisibility(View.GONE);
        binding.btnPdf.setVisibility(View.GONE);
        binding.btnCsv.setOnClickListener(v -> { try { AuditUiState s = viewModel.getUiState().getValue(); if (s == null || !s.canExport) return;
            Uri uri = ExportUtils.exportAuditCsv(requireContext(), s.requests, s.actions, s.names);
            ExportUtils.shareUri(requireContext(), uri, "text/csv", "Audit CSV"); } catch (Exception ignored) {} });
        binding.btnPdf.setOnClickListener(v -> { try { AuditUiState s = viewModel.getUiState().getValue(); if (s == null || !s.canExport) return;
            Uri uri = ExportUtils.exportAuditPdf(requireContext(), s.requests, s.actions, s.names);
            ExportUtils.shareUri(requireContext(), uri, "application/pdf", "Audit PDF"); } catch (Exception ignored) {} });
        observe(viewModel.getUiState(), state -> {
            binding.setContent(state.content);
            int vis = state.canExport ? View.VISIBLE : View.GONE;
            binding.btnCsv.setVisibility(vis);
            binding.btnPdf.setVisibility(vis);
        });
    }
}
