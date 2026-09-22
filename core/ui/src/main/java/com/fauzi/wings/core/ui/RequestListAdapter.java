package com.fauzi.wings.core.ui;

import android.view.LayoutInflater;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.DiffUtil;
import androidx.recyclerview.widget.ListAdapter;
import androidx.recyclerview.widget.RecyclerView;

import com.fauzi.wings.core.common.MoneyFormatters;
import com.fauzi.wings.core.model.ApprovalRequest;
import com.fauzi.wings.core.ui.databinding.ItemRequestBinding;
import com.fauzi.wings.domain.approval.ApprovalWorkflow;

public class RequestListAdapter extends ListAdapter<ApprovalRequest, RequestListAdapter.Holder> {

    public interface OnClick {
        void onClick(ApprovalRequest request);
    }

    private final OnClick onClick;

    public RequestListAdapter(OnClick onClick) {
        super(DIFF);
        this.onClick = onClick;
    }

    private static final DiffUtil.ItemCallback<ApprovalRequest> DIFF = new DiffUtil.ItemCallback<ApprovalRequest>() {
        @Override
        public boolean areItemsTheSame(@NonNull ApprovalRequest a, @NonNull ApprovalRequest b) {
            return a.id == b.id;
        }

        @Override
        public boolean areContentsTheSame(@NonNull ApprovalRequest a, @NonNull ApprovalRequest b) {
            return a.updatedAt == b.updatedAt && a.status == b.status && a.title.equals(b.title);
        }
    };

    @NonNull
    @Override
    public Holder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        ItemRequestBinding b = ItemRequestBinding.inflate(LayoutInflater.from(parent.getContext()), parent, false);
        return new Holder(b);
    }

    @Override
    public void onBindViewHolder(@NonNull Holder holder, int position) {
        ApprovalRequest r = getItem(position);
        holder.binding.setTitle("#" + r.id + " " + r.title);
        holder.binding.setSubtitle(ApprovalWorkflow.levelLabel(r.status) + (r.escalated ? " · ESCALATED" : ""));
        holder.binding.setMeta(r.type.name() + " · " + MoneyFormatters.idr(r.amount) + " · " + r.department);
        holder.binding.getRoot().setOnClickListener(v -> onClick.onClick(r));
        holder.binding.executePendingBindings();
    }

    static class Holder extends RecyclerView.ViewHolder {
        final ItemRequestBinding binding;

        Holder(ItemRequestBinding binding) {
            super(binding.getRoot());
            this.binding = binding;
        }
    }
}
