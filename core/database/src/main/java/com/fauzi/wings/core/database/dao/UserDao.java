package com.fauzi.wings.core.database.dao;

import androidx.lifecycle.LiveData;
import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.OnConflictStrategy;
import androidx.room.Query;

import com.fauzi.wings.core.database.entity.UserEntity;

import java.util.List;

@Dao
public interface UserDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    void upsertAll(List<UserEntity> users);

    @Query("SELECT * FROM users WHERE username = :username LIMIT 1")
    UserEntity findByUsername(String username);

    @Query("SELECT * FROM users WHERE id = :id LIMIT 1")
    UserEntity getById(long id);

    @Query("SELECT * FROM users ORDER BY role, displayName")
    LiveData<List<UserEntity>> observeAll();

    @Query("SELECT * FROM users ORDER BY role, displayName")
    List<UserEntity> getAll();

    @Query("SELECT COUNT(*) FROM users")
    int count();
}
