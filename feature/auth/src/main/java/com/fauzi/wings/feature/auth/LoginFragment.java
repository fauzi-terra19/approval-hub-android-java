package com.fauzi.wings.feature.auth;
import android.os.Bundle; import android.view.*; import android.widget.*;
import androidx.annotation.*; import androidx.fragment.app.Fragment;
import androidx.lifecycle.ViewModelProvider; import androidx.navigation.NavOptions; import androidx.navigation.Navigation;
import com.google.android.material.textfield.TextInputEditText;
import com.fauzi.wings.core.ui.NavRoutes; import com.fauzi.wings.data.di.HasAppContainer;
public class LoginFragment extends Fragment {
    private LoginViewModel viewModel;
    @Nullable @Override public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        return inflater.inflate(R.layout.fragment_login, container, false);
    }
    @Override public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        viewModel = new ViewModelProvider(this, HasAppContainer.from(requireContext()).getViewModelFactory()).get(LoginViewModel.class);
        TextInputEditText inputUsername = view.findViewById(R.id.inputUsername);
        TextInputEditText inputPassword = view.findViewById(R.id.inputPassword);
        Button btnLogin = view.findViewById(R.id.btnLogin);
        TextView textError = view.findViewById(R.id.textError);
        ProgressBar progress = view.findViewById(R.id.progress);
        TextView textDemo = view.findViewById(R.id.textDemoAccounts);
        btnLogin.setOnClickListener(v -> viewModel.login(
                inputUsername.getText() == null ? "" : inputUsername.getText().toString(),
                inputPassword.getText() == null ? "" : inputPassword.getText().toString()));
        viewModel.getUiState().observe(getViewLifecycleOwner(), state -> {
            textDemo.setText(state.demoHint);
            progress.setVisibility(state.loading ? View.VISIBLE : View.GONE);
            btnLogin.setEnabled(!state.loading);
            if (state.error != null) { textError.setVisibility(View.VISIBLE); textError.setText(state.error); }
            else textError.setVisibility(View.GONE);
            if (state.loggedInUser != null) {
                Navigation.findNavController(view).navigate(NavRoutes.DASHBOARD, new NavOptions.Builder().setLaunchSingleTop(true).build());
            }
        });
    }
}
