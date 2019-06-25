// Copyright (c) 2018-2019 The Particl Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#ifndef EMPOWER_SMSG_NET_H
#define EMPOWER_SMSG_NET_H

#include <sync.h>

class SecMsgNode
{
public:
    CCriticalSection cs_smsg_net;
    int64_t lastSeen = 0;
    int64_t lastMatched = 0;
    int64_t ignoreUntil = 0;
    uint32_t nWakeCounter = 0;
    uint8_t misbehaving = 0;
    bool fEnabled = false;
};

#endif // EMPOWER_SMSG_NET_H
