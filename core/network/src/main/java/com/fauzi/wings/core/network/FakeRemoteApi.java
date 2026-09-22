package com.fauzi.wings.core.network;

public class FakeRemoteApi implements RemoteApi {
    @Override
    public int pullRequestCount() throws Exception {
        Thread.sleep(400);
        return 2;
    }

    @Override
    public int pushPending(int localPending) throws Exception {
        Thread.sleep(400);
        return localPending;
    }
}
