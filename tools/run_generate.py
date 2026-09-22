#!/usr/bin/env python3
"""Run full project generation and patch DI for features (no :app dependency)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_all import (  # noqa: E402
    PKG,
    P,
    ROOT as GEN_ROOT,
    gen_core_common,
    gen_core_model,
    gen_core_network,
    gen_core_notification,
    gen_core_preference,
    gen_core_ui,
    w,
)
from generate_domain_data import gen_core_database, gen_data, gen_domain  # noqa: E402
from generate_features_app import gen_app, gen_features  # noqa: E402


def patch_feature_di() -> None:
    """Replace getAppContainer().factory with local ViewModel factories using AppContainerHolder repos."""
    replacements = [
        (
            r"""viewModel = new ViewModelProvider\(this,
                \(\(AppContainerHolder\) requireActivity\(\)\.getApplication\(\)\)\.getAppContainer\(\)\.factory\)
                \.get\(LoginViewModel\.class\);""",
            """AppContainerHolder holder = (AppContainerHolder) requireActivity().getApplication();
        viewModel = new ViewModelProvider(this, new ViewModelProvider.Factory() {
            @NonNull
            @Override
            @SuppressWarnings("unchecked")
            public <T extends androidx.lifecycle.ViewModel> T create(@NonNull Class<T> modelClass) {
                return (T) new LoginViewModel(holder.getSessionRepository());
            }
        }).get(LoginViewModel.class);""",
        ),
    ]
    # Broader approach: rewrite each fragment file with known patterns
    feature_dir = ROOT / "feature"
    for java in feature_dir.rglob("*.java"):
        text = java.read_text(encoding="utf-8")
        original = text
        text = text.replace(
            "((AppContainerHolder) requireActivity().getApplication()).getAppContainer().factory)",
            "featureFactory())",
        )
        text = text.replace(
            "import com.fauzi.wings.data.di.AppContainer;\n",
            "",
        )
        text = text.replace(
            """AppContainer c = ((AppContainerHolder) requireActivity().getApplication()).getAppContainer();
        return new ViewModelProvider(this, c.factoryForDetail(requestId)).get(ApprovalDetailViewModel.class);""",
            """long rid = requestId;
        AppContainerHolder holder = (AppContainerHolder) requireActivity().getApplication();
        return new ViewModelProvider(this, new ViewModelProvider.Factory() {
            @NonNull
            @Override
            @SuppressWarnings("unchecked")
            public <T extends androidx.lifecycle.ViewModel> T create(@NonNull Class<T> modelClass) {
                return (T) new ApprovalDetailViewModel(rid, holder.getSessionRepository(), holder.getApprovalRepository());
            }
        }).get(ApprovalDetailViewModel.class);""",
        )
        if text != original:
            java.write_text(text, encoding="utf-8")
            print("patched", java.relative_to(ROOT))


def write_vm_helpers() -> None:
    """Add FeatureViewModels helper methods into each fragment via a shared util in data."""
    w(f"data/src/main/java/{P}/data/di/VmFactories.java", f'''
package {PKG}.data.di;

import androidx.annotation.NonNull;
import androidx.lifecycle.ViewModel;
import androidx.lifecycle.ViewModelProvider;

import {PKG}.domain.repository.ApprovalRepository;
import {PKG}.domain.repository.SessionRepository;

/**
 * Tiny factory helper used by feature modules (keeps :data free of feature class imports).
 */
public final class VmFactories {{
    private VmFactories() {{}}

    public interface Creator {{
        ViewModel create(SessionRepository session, ApprovalRepository approval);
    }}

    public static ViewModelProvider.Factory of(AppContainerHolder holder, Creator creator) {{
        return new ViewModelProvider.Factory() {{
            @NonNull
            @Override
            @SuppressWarnings("unchecked")
            public <T extends ViewModel> T create(@NonNull Class<T> modelClass) {{
                return (T) creator.create(holder.getSessionRepository(), holder.getApprovalRepository());
            }}
        }};
    }}

    public static ViewModelProvider.Factory ofDetail(AppContainerHolder holder, long requestId,
                                                     DetailCreator creator) {{
        return new ViewModelProvider.Factory() {{
            @NonNull
            @Override
            @SuppressWarnings("unchecked")
            public <T extends ViewModel> T create(@NonNull Class<T> modelClass) {{
                return (T) creator.create(requestId, holder.getSessionRepository(), holder.getApprovalRepository());
            }}
        }};
    }}

    public interface DetailCreator {{
        ViewModel create(long requestId, SessionRepository session, ApprovalRepository approval);
    }}
}}
''')


def rewrite_fragments_for_vmfactories() -> None:
    mapping = {
        "LoginFragment.java": (
            "LoginViewModel",
            "(s, a) -> new LoginViewModel(s)",
            False,
        ),
        "DashboardFragment.java": (
            "DashboardViewModel",
            "(s, a) -> new DashboardViewModel(s, a)",
            False,
        ),
        "InboxFragment.java": (
            "InboxViewModel",
            "(s, a) -> new InboxViewModel(a)",
            False,
        ),
        "CreateRequestFragment.java": (
            "CreateRequestViewModel",
            "(s, a) -> new CreateRequestViewModel(a)",
            False,
        ),
        "AnalyticsFragment.java": (
            "AnalyticsViewModel",
            "(s, a) -> new AnalyticsViewModel(a)",
            False,
        ),
        "AuditFragment.java": (
            "AuditViewModel",
            "(s, a) -> new AuditViewModel(a)",
            False,
        ),
        "SettingsFragment.java": (
            "SettingsViewModel",
            "(s, a) -> new SettingsViewModel(s, a)",
            False,
        ),
        "ApprovalDetailFragment.java": (
            "ApprovalDetailViewModel",
            None,
            True,
        ),
    }
    for java in (ROOT / "feature").rglob("*.java"):
        name = java.name
        if name not in mapping:
            continue
        vm, creator, detail = mapping[name]
        text = java.read_text(encoding="utf-8")
        if "VmFactories" in text:
            continue
        if "import com.fauzi.wings.data.di.AppContainerHolder;" not in text:
            text = text.replace(
                f"import {PKG}.data.di.AppContainerHolder;",
                f"import {PKG}.data.di.AppContainerHolder;\nimport {PKG}.data.di.VmFactories;",
            )
            if "VmFactories" not in text.split("import")[0] and f"import {PKG}.data.di.VmFactories;" not in text:
                # insert after package
                lines = text.splitlines()
                for i, line in enumerate(lines):
                    if line.startswith("import "):
                        lines.insert(i, f"import {PKG}.data.di.VmFactories;")
                        if f"import {PKG}.data.di.AppContainerHolder;" not in text:
                            lines.insert(i, f"import {PKG}.data.di.AppContainerHolder;")
                        text = "\n".join(lines) + "\n"
                        break
        else:
            text = text.replace(
                "import com.fauzi.wings.data.di.AppContainerHolder;",
                "import com.fauzi.wings.data.di.AppContainerHolder;\nimport com.fauzi.wings.data.di.VmFactories;",
            )

        if detail:
            text = re.sub(
                r"@NonNull\s+@Override\s+protected ApprovalDetailViewModel createViewModel\(\) \{.*?\}",
                '''@NonNull
    @Override
    protected ApprovalDetailViewModel createViewModel() {
        long requestId = getArguments() == null ? 0L : getArguments().getLong("requestId", 0L);
        AppContainerHolder holder = (AppContainerHolder) requireActivity().getApplication();
        return new ViewModelProvider(this, VmFactories.ofDetail(holder, requestId,
                ApprovalDetailViewModel::new)).get(ApprovalDetailViewModel.class);
    }''',
                text,
                count=1,
                flags=re.S,
            )
        elif name == "LoginFragment.java":
            text = re.sub(
                r"viewModel = new ViewModelProvider\(this,.*?\)\.get\(LoginViewModel\.class\);",
                '''AppContainerHolder holder = (AppContainerHolder) requireActivity().getApplication();
        viewModel = new ViewModelProvider(this, VmFactories.of(holder, (s, a) -> new LoginViewModel(s)))
                .get(LoginViewModel.class);''',
                text,
                count=1,
                flags=re.S,
            )
        else:
            pattern = rf"return new ViewModelProvider\(this,.*?\)\.get\({vm}\.class\);"
            replacement = (
                f"AppContainerHolder holder = (AppContainerHolder) requireActivity().getApplication();\n"
                f"        return new ViewModelProvider(this, VmFactories.of(holder, {creator}))\n"
                f"                .get({vm}.class);"
            )
            text = re.sub(pattern, replacement, text, count=1, flags=re.S)

        # cleanup broken featureFactory
        text = text.replace("featureFactory())", "/*patched*/)")
        java.write_text(text, encoding="utf-8")
        print("rewrote DI", java.relative_to(ROOT))


def fix_app_files() -> None:
    # Fix MainActivity session access
    main = ROOT / f"app/src/main/java/{P}/app/MainActivity.java"
    if main.exists():
        t = main.read_text(encoding="utf-8")
        t = t.replace(
            "SessionRepository session = ((AppContainerHolder) getApplication()).getAppContainer().sessionRepository;",
            "SessionRepository session = ((AppContainerHolder) getApplication()).getSessionRepository();",
        )
        main.write_text(t, encoding="utf-8")

    # Fix Settings logout NavOptions (Uri is invalid for setPopUpTo)
    settings = ROOT / f"feature/settings/src/main/java/{P}/feature/settings/SettingsFragment.java"
    if settings.exists():
        t = settings.read_text(encoding="utf-8")
        t = t.replace(
            """NavOptions opts = new NavOptions.Builder().setPopUpTo(NavRoutes.LOGIN, true).build();
                Navigation.findNavController(view).navigate(NavRoutes.LOGIN, opts);""",
            """Navigation.findNavController(view).navigate(
                        NavRoutes.LOGIN,
                        new NavOptions.Builder()
                                .setPopUpTo(Navigation.findNavController(view).getGraph().getStartDestinationId(), true)
                                .build());""",
        )
        settings.write_text(t, encoding="utf-8")

    # Ensure SyncWorker is public top-level for clarity — leave as is if compiles

    # Remove duplicate AppContainer from data if generated
    bad = ROOT / f"data/src/main/java/{P}/data/di/AppContainer.java"
    if bad.exists():
        bad.unlink()
        print("removed data AppContainer")


def main() -> None:
    print("Generating core...")
    gen_core_model()
    gen_core_common()
    gen_core_preference()
    gen_core_network()
    gen_core_notification()
    print("Generating domain/database/data...")
    gen_domain()
    gen_core_database()
    gen_data()
    print("Generating ui...")
    gen_core_ui()
    print("Generating features/app...")
    gen_features()
    gen_app()
    write_vm_helpers()
    rewrite_fragments_for_vmfactories()
    fix_app_files()
    for kt in ROOT.rglob("*.kt"):
        if "tools" in str(kt):
            continue
        print("deleting leftover", kt)
        kt.unlink()
    print("GENERATION COMPLETE")


if __name__ == "__main__":
    main()
