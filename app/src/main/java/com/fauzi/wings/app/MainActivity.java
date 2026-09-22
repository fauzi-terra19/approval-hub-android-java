package com.fauzi.wings.app;

import android.os.Bundle;
import android.view.View;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.app.AppCompatDelegate;
import androidx.navigation.NavController;
import androidx.navigation.NavOptions;
import androidx.navigation.fragment.NavHostFragment;
import androidx.navigation.ui.NavigationUI;
import com.google.android.material.bottomnavigation.BottomNavigationView;
import com.fauzi.wings.core.database.AppDatabase;
import com.fauzi.wings.core.model.ThemeMode;
import com.fauzi.wings.core.ui.NavRoutes;

public class MainActivity extends AppCompatActivity {
    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        applyTheme(((WingsApp) getApplication()).getAppContainer().preferences.getThemeMode());
        NavHostFragment navHost = (NavHostFragment) getSupportFragmentManager().findFragmentById(R.id.nav_host);
        NavController navController = navHost.getNavController();
        BottomNavigationView bottomNav = findViewById(R.id.bottomNav);
        NavigationUI.setupWithNavController(bottomNav, navController);
        navController.addOnDestinationChangedListener((c, destination, a) -> {
            int id = destination.getId();
            boolean hide = id == R.id.loginFragment || id == R.id.createRequestFragment || id == R.id.approvalDetailFragment;
            bottomNav.setVisibility(hide ? View.GONE : View.VISIBLE);
        });
    }

    @Override protected void onResume() {
        super.onResume();
        AppContainer container = ((WingsApp) getApplication()).getAppContainer();
        AppDatabase.IO.execute(() -> {
            if (container.repository.checkSessionTimeout()) {
                runOnUiThread(() -> {
                    NavHostFragment navHost = (NavHostFragment) getSupportFragmentManager().findFragmentById(R.id.nav_host);
                    if (navHost != null) {
                        NavController nav = navHost.getNavController();
                        nav.navigate(NavRoutes.LOGIN, new NavOptions.Builder()
                                .setPopUpTo(nav.getGraph().getStartDestinationId(), true)
                                .build());
                    }
                });
            }
        });
    }

    private void applyTheme(ThemeMode mode) {
        if (mode == null) mode = ThemeMode.SYSTEM;
        int night;
        switch (mode) {
            case LIGHT: night = AppCompatDelegate.MODE_NIGHT_NO; break;
            case DARK: night = AppCompatDelegate.MODE_NIGHT_YES; break;
            default: night = AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM; break;
        }
        AppCompatDelegate.setDefaultNightMode(night);
    }
}
