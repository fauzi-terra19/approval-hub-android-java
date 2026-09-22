package com.fauzi.wings.feature.inbox;
import android.os.Bundle; import android.view.View;
import androidx.annotation.*; import androidx.lifecycle.ViewModelProvider;
import androidx.navigation.Navigation; import androidx.recyclerview.widget.LinearLayoutManager;
import com.fauzi.wings.core.ui.*; import com.fauzi.wings.data.di.HasAppContainer;
import com.fauzi.wings.feature.inbox.databinding.FragmentInboxBinding;
public class InboxFragment extends BaseMvvmFragment<FragmentInboxBinding, InboxViewModel> {
    private RequestListAdapter adapter;
    public InboxFragment() { super(R.layout.fragment_inbox); }
    @NonNull @Override protected InboxViewModel createViewModel() {
        return new ViewModelProvider(this, HasAppContainer.from(requireContext()).getViewModelFactory()).get(InboxViewModel.class);
    }
    @Override public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        adapter = new RequestListAdapter(req -> Navigation.findNavController(view).navigate(NavRoutes.detail(req.id)));
        binding.recycler.setLayoutManager(new LinearLayoutManager(requireContext()));
        binding.recycler.setAdapter(adapter);
        observe(viewModel.getUiState(), state -> {
            binding.setEmptyText(state.items.isEmpty() ? "Tidak ada item menunggu aksi Anda" : "");
            adapter.submitList(state.items);
        });
    }
}
