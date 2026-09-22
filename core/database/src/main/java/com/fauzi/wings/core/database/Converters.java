package com.fauzi.wings.core.database;

import androidx.room.TypeConverter;

import com.fauzi.wings.core.model.ApprovalStatus;
import com.fauzi.wings.core.model.RequestType;
import com.fauzi.wings.core.model.Role;

public class Converters {
    @TypeConverter
    public String fromRole(Role v) {
        return v == null ? null : v.name();
    }

    @TypeConverter
    public Role toRole(String v) {
        return v == null ? null : Role.valueOf(v);
    }

    @TypeConverter
    public String fromStatus(ApprovalStatus v) {
        return v == null ? null : v.name();
    }

    @TypeConverter
    public ApprovalStatus toStatus(String v) {
        return v == null ? null : ApprovalStatus.valueOf(v);
    }

    @TypeConverter
    public String fromType(RequestType v) {
        return v == null ? null : v.name();
    }

    @TypeConverter
    public RequestType toType(String v) {
        return v == null ? null : RequestType.valueOf(v);
    }
}
