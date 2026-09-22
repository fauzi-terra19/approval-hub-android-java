package com.fauzi.wings.core.ui;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.LayoutRes;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.databinding.DataBindingUtil;
import androidx.databinding.ViewDataBinding;
import androidx.fragment.app.Fragment;
import androidx.lifecycle.LiveData;
import androidx.lifecycle.Observer;
import androidx.lifecycle.ViewModel;

public abstract class BaseMvvmFragment<VB extends ViewDataBinding, VM extends ViewModel> extends Fragment {
    protected VB binding;
    protected VM viewModel;
    private final int layoutId;

    protected BaseMvvmFragment(@LayoutRes int layoutId) {
        this.layoutId = layoutId;
    }

    @NonNull
    protected abstract VM createViewModel();

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {
        binding = DataBindingUtil.inflate(inflater, layoutId, container, false);
        binding.setLifecycleOwner(getViewLifecycleOwner());
        viewModel = createViewModel();
        return binding.getRoot();
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }

    protected <T> void observe(@NonNull LiveData<T> liveData, @NonNull Observer<T> observer) {
        liveData.observe(getViewLifecycleOwner(), observer);
    }
}
