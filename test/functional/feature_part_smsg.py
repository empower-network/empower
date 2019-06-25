#!/usr/bin/env python3
# Copyright (c) 2017-2018 The Particl Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

import time

from test_framework.test_empower import EmpowerTestFramework
from test_framework.util import connect_nodes_bi
from test_framework.authproxy import JSONRPCException


class SmsgTest(EmpowerTestFramework):
    def set_test_params(self):
        self.setup_clean_chain = True  # Don't copy from cache
        self.num_nodes = 3
        self.extra_args = [ ['-smsgscanincoming','-smsgsaddnewkeys'] for i in range(self.num_nodes) ]
        self.extra_args[2].append('-nosmsg')

    def skip_test_if_missing_module(self):
        self.skip_if_no_wallet()

    def setup_network(self, split=False):
        self.add_nodes(self.num_nodes, extra_args=self.extra_args)
        self.start_nodes()
        connect_nodes_bi(self.nodes, 0, 1)
        connect_nodes_bi(self.nodes, 0, 2)

    def run_test(self):
        tmpdir = self.options.tmpdir
        nodes = self.nodes

        nodes[0].extkeyimportmaster(nodes[0].mnemonic('new')['master'])
        nodes[1].extkeyimportmaster('abandon baby cabbage dad eager fabric gadget habit ice kangaroo lab absorb')

        address0 = nodes[0].getnewaddress()  # Will be different each run
        address1 = nodes[1].getnewaddress()
        assert(address1 == 'pX9N6S76ZtA5BfsiJmqBbjaEgLMHpt58it')

        assert('SMSG' in nodes[1].getnetworkinfo()['localservices_str'])

        ro = nodes[0].smsglocalkeys()
        assert(len(ro['wallet_keys']) == 1)

        ro = nodes[1].smsgaddaddress(address0, ro['wallet_keys'][0]['public_key'])
        assert(ro['result'] == 'Public key added to db.')

        ro = nodes[1].smsgbuckets()
        assert(ro['total']['numbuckets'] == 0)

        ro = nodes[1].smsgsend(address1, address0, "Test 1->0.")
        assert(ro['result'] == 'Sent.')

        self.waitForSmsgExchange(1, 1, 0)

        ro = nodes[1].smsgbuckets()
        assert(ro['total']['numbuckets'] == 1)
        ro = nodes[0].smsgbuckets()
        assert(ro['total']['numbuckets'] == 1)

        ro = nodes[0].smsginbox()
        assert(len(ro['messages']) == 1)
        assert(ro['messages'][0]['from'] == address1)
        assert(ro['messages'][0]['text'] == 'Test 1->0.')

        # - node0 should have got pubkey for address1 by receiving msg from address1

        ro = nodes[0].smsgsend(address0, address1, "Reply 0->1.")
        assert(ro['result'] == 'Sent.')

        self.waitForSmsgExchange(2, 0, 1)

        ro = nodes[1].smsginbox()
        assert(ro['messages'][0]['to'] == address1)
        assert(ro['messages'][0]['text'] == 'Reply 0->1.')


        assert(len(nodes[1].smsgview()['messages']) == 2)
        assert(len(nodes[1].smsgoutbox()['messages']) == 1)

        nodes[1].smsgdisable()

        try:
            nodes[1].smsgsend(address1, address0, "Test 1->0. 2")
            assert(False), "smsgsend while disabled."
        except JSONRPCException as e:
            assert("Secure messaging is disabled." in e.error['message'])

        ro = nodes[1].smsgenable()

        ro = nodes[1].smsgsend(address1, address0, "Test 1->0. 2")
        assert(ro['result'] == 'Sent.')

        self.waitForSmsgExchange(3, 1, 0)

        ro = nodes[0].smsginbox()
        assert(len(ro['messages']) == 1)
        assert(ro['messages'][0]['from'] == address1)
        assert(ro['messages'][0]['text'] == 'Test 1->0. 2')

        msg = 'Test anon 1->0. 2'
        ro = nodes[1].smsgsendanon(address0, msg)
        assert(ro['result'] == 'Sent.')
        assert(len(ro['msgid']) == 56)

        i = 0
        for i in range(20):
            ro = nodes[0].smsginbox()
            if len(ro['messages']) >= 1:
                break
            time.sleep(1)
        assert(i < 20)
        assert(len(ro['messages']) == 1)
        assert(ro['messages'][0]['from'] == 'anon')
        assert(ro['messages'][0]['text'] == msg)

        ro = nodes[0].smsgscanchain()
        assert('Completed' in ro['result'])

        self.log.info('Test smsgsend without submitmsg')
        ro = nodes[1].smsgsend(address1, address0, 'Test 1->0 no network', False, 0, False, False, False, False)
        assert('Not Sent' in ro['result'])
        msg0_from1 = ro['msg']
        msg0_id = ro['msgid']
        assert(len(nodes[1].smsgoutbox()['messages']) == 4)

        assert(len(nodes[0].smsginbox()['messages']) == 0)
        assert(nodes[0].smsgimport(msg0_from1)['msgid'] == msg0_id)
        ro = nodes[0].smsginbox()
        assert(len(ro['messages']) == 1)
        assert(ro['messages'][0]['text'] == 'Test 1->0 no network')

        ro = nodes[1].smsgsend(address1, address0, 'Test 1->0 no network, no outbox', False, 0, False, False, False, False, False)
        assert(len(nodes[1].smsgoutbox()['messages']) == 4)  # No change

        self.log.info('Test nosmsg')
        assert('SMSG' not in nodes[2].getnetworkinfo()['localservices_str'])


if __name__ == '__main__':
    SmsgTest().main()
