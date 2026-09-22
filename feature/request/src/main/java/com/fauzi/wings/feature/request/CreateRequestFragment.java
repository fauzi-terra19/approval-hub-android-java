package com.fauzi.wings.feature.request;
import android.os.Bundle; import android.view.View; import android.widget.ArrayAdapter;
import androidx.annotation.*; import androidx.lifecycle.ViewModelProvider; import androidx.navigation.Navigation;
import com.fauzi.wings.core.model.RequestType; import com.fauzi.wings.core.ui.BaseMvvmFragment; import com.fauzi.wings.data.di.HasAppContainer;
import com.fauzi.wings.feature.request.databinding.FragmentCreateRequestBinding;
public class CreateRequestFragment extends BaseMvvmFragment<FragmentCreateRequestBinding, CreateRequestViewModel> {
    public CreateRequestFragment() { super(R.layout.fragment_create_request); }
    @NonNull @Override protected CreateRequestViewModel createViewModel() {
        return new ViewModelProvider(this, HasAppContainer.from(requireContext()).getViewModelFactory()).get(CreateRequestViewModel.class);
    }
    @Override public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        RequestType[] types = RequestType.values();
        String[] names = new String[types.length];
        for (int i = 0; i < types.length; i++) names[i] = types[i].name();
        binding.spinnerType.setAdapter(new ArrayAdapter<>(requireContext(), android.R.layout.simple_spinner_dropdown_item, names));
        binding.btnSubmit.setOnClickListener(v -> {
            RequestType type = types[binding.spinnerType.getSelectedItemPosition()];
            double amount = 0;
            try { String t = binding.inputAmount.getText() == null ? "0" : binding.inputAmount.getText().toString();
                amount = Double.parseDouble(t.isEmpty() ? "0" : t); } catch (Exception ignored) {}
            viewModel.updateHint(type, amount);
            viewModel.submit(binding.inputTitle.getText() == null ? "" : binding.inputTitle.getText().toString(),
                    binding.inputDesc.getText() == null ? "" : binding.inputDesc.getText().toString(), type, amount);
        });
        observe(viewModel.getUiState(), state -> {
            binding.setRuleHint(state.ruleHint);
            binding.setError(state.error == null ? "" : state.error);
            if (state.createdId != null) Navigation.findNavController(view).navigateUp();
        });
    }
}
