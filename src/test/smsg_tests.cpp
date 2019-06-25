// Copyright (c) 2017-2019 The Particl Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <smsg/smessage.h>

#include <test/setup_common.h>
#include <net.h>

#ifdef ENABLE_WALLET
#include <wallet/wallet.h>
#endif

#include <boost/test/unit_test.hpp>

struct SmsgTestingSetup : public TestingSetup {
    SmsgTestingSetup() : TestingSetup(CBaseChainParams::MAIN, true) {}
};

BOOST_FIXTURE_TEST_SUITE(smsg_tests, SmsgTestingSetup)



BOOST_AUTO_TEST_CASE(smsg_test_ckeyId_inits_null)
{
    CKeyID k;
    BOOST_CHECK(k.IsNull());
}

BOOST_AUTO_TEST_CASE(smsg_test)
{
#ifdef ENABLE_WALLET
    SeedInsecureRand();

    const std::string sTestMessage =
        "A short test message 0123456789 !@#$%^&*()_+-=";

    smsg::fSecMsgEnabled = true;
    int rv = 0;
    const int nKeys = 12;
    auto chain = interfaces::MakeChain();
    std::shared_ptr<CWallet> wallet = std::make_shared<CWallet>(chain.get(), WalletLocation(), WalletDatabase::CreateDummy());
    std::vector<CKey> keyOwn(nKeys);
    for (int i = 0; i < nKeys; i++) {
        InsecureNewKey(keyOwn[i], true);
        LOCK(wallet->cs_wallet);
        wallet->AddKey(keyOwn[i]);
    }

    std::vector<CKey> keyRemote(nKeys);
    for (int i = 0; i < nKeys; i++) {
        InsecureNewKey(keyRemote[i], true);
        LOCK(wallet->cs_wallet);
        wallet->AddKey(keyRemote[i]); // need pubkey
    }

    BOOST_CHECK(true == smsgModule.Start(wallet, false, false));

    CKeyID idNull;
    BOOST_CHECK(idNull.IsNull());

    for (int i = 0; i < nKeys; i++) {
        smsg::SecureMessage smsg;
        smsg.SetNull();
        smsg::MessageData msg;
        CKeyID kFrom = keyOwn[i].GetPubKey().GetID();
        CKeyID kTo = keyRemote[i].GetPubKey().GetID();
        CKeyID kFail = keyRemote[(i+1) % nKeys].GetPubKey().GetID();
        std::string sAddrFrom = EncodeDestination(PKHash(kFrom));
        std::string sAddrTo = EncodeDestination(PKHash(kTo));
        std::string sAddrFail = EncodeDestination(PKHash(kFail));

        bool fSendAnonymous = rand() % 3 == 0;

        BOOST_CHECK_MESSAGE(0 == (rv = smsgModule.Encrypt(smsg, fSendAnonymous ? idNull : kFrom, kTo, sTestMessage)), "SecureMsgEncrypt " << rv);

        BOOST_CHECK_MESSAGE(0 == (rv = smsgModule.SetHash((uint8_t*)&smsg, smsg.pPayload, smsg.nPayload)), "SecureMsgSetHash " << rv);

        BOOST_CHECK_MESSAGE(0 == (rv = smsgModule.Validate((uint8_t*)&smsg, smsg.pPayload, smsg.nPayload)), "SecureMsgValidate " << rv);

        BOOST_CHECK_MESSAGE(0 == (rv = smsgModule.Decrypt(false, kTo, smsg, msg)), "SecureMsgDecrypt " << rv);

        BOOST_CHECK(msg.vchMessage.size()-1 == sTestMessage.size()
            && 0 == memcmp(&msg.vchMessage[0], sTestMessage.data(), msg.vchMessage.size()-1));

        rv = smsgModule.Decrypt(false, kFail, smsg, msg);
        BOOST_CHECK_MESSAGE(smsg::SMSG_MAC_MISMATCH == rv, "SecureMsgDecrypt " << smsg::GetString(rv));
    }

    smsgModule.Shutdown();

#endif
}

BOOST_AUTO_TEST_SUITE_END()
