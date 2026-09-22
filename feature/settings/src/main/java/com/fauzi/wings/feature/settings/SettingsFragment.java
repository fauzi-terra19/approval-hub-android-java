package com.fauzi.wings.feature.settings;
import android.os.Bundle; import android.view.View; import android.widget.*;
import androidx.annotation.*; import androidx.appcompat.app.AppCompatDelegate;
import androidx.lifecycle.ViewModelProvider; import androidx.navigation.NavOptions; import androidx.navigation.Navigation;
import com.fauzi.wings.core.model.*; import com.fauzi.wings.core.ui.*; import com.fauzi.wings.data.di.HasAppContainer;
import com.fauzi.wings.feature.settings.databinding.FragmentSettingsBinding;
public class SettingsFragment extends BaseMvvmFragment<FragmentSettingsBinding, SettingsViewModel> {
    public SettingsFragment() { super(R.layout.fragment_settings); }
    @NonNull @Override protected SettingsViewModel createViewModel() {
        return new ViewModelProvider(this, HasAppContainer.from(requireContext()).getViewModelFactory()).get(SettingsViewModel.class);
    }
    @Override public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        ThemeMode[] themes = ThemeMode.values();
        String[] themeNames = new String[themes.length];
        for (int i = 0; i < themes.length; i++) themeNames[i] = themes[i].name();
        binding.spinnerTheme.setAdapter(new ArrayAdapter<>(requireContext(), android.R.layout.simple_spinner_dropdown_item, themeNames));
        Role[] rolesEnum = Role.values();
        String[] roleNames = new String[rolesEnum.length + 1]; roleNames[0] = "(none)";
        for (int i = 0; i < rolesEnum.length; i++) roleNames[i + 1] = rolesEnum[i].name();
        binding.spinnerImpersonate.setAdapter(new ArrayAdapter<>(requireContext(), android.R.layout.simple_spinner_dropdown_item, roleNames));
        binding.spinnerTheme.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override public void onItemSelected(AdapterView<?> p, View v, int pos, long id) {
                ThemeMode mode = themes[pos]; viewModel.setTheme(mode);
                int night = mode == ThemeMode.LIGHT ? AppCompatDelegate.MODE_NIGHT_NO : mode == ThemeMode.DARK ? AppCompatDelegate.MODE_NIGHT_YES : AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM;
                AppCompatDelegate.setDefaultNightMode(night);
            }
            @Override public void onNothingSelected(AdapterView<?> p) {}
        });
        binding.spinnerImpersonate.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override public void onItemSelected(AdapterView<?> p, View v, int pos, long id) { viewModel.setImpersonate(pos == 0 ? null : rolesEnum[pos - 1]); }
            @Override public void onNothingSelected(AdapterView<?> p) {}
        });
        binding.btnSync.setOnClickListener(v -> viewModel.sync());
        binding.btnEscalate.setVisibility(View.GONE);
        binding.btnEscalate.setOnClickListener(v -> viewModel.runEscalation());
        binding.btnLogout.setOnClickListener(v -> viewModel.logout());
        observe(viewModel.getUiState(), state -> {
            if (state.user != null) {
                String info = state.user.displayName + " (" + state.user.username + ") · " + state.user.role;
                if (state.impersonate != null) info += " · impersonate " + state.impersonate;
                binding.setInfo(info + "\n" + state.message);
            } else binding.setInfo("");
            binding.setSyncInfo(state.syncInfo);
            binding.btnEscalate.setVisibility(state.canForceEscalate ? View.VISIBLE : View.GONE);
            if (state.loggedOut) {
                Navigation.findNavController(view).navigate(NavRoutes.LOGIN, new NavOptions.Builder()
                        .setPopUpTo(Navigation.findNavController(view).getGraph().getStartDestinationId(), true).build());
            }
        });
    }
}
