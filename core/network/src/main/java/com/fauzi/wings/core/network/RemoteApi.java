package com.fauzi.wings.core.network;

public interface RemoteApi {
    int pullRequestCount() throws Exception;
    int pushPending(int localPending) throws Exception;
}
