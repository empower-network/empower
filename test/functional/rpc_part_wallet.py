#!/usr/bin/env python3
# Copyright (c) 2018 The Particl Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

from test_framework.test_empower import EmpowerTestFramework, isclose
from test_framework.util import connect_nodes_bi


class WalletRPCTest(EmpowerTestFramework):
    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 2
        self.extra_args = [ ['-debug','-noacceptnonstdtxn','-reservebalance=10000000'] for i in range(self.num_nodes)]

    def skip_test_if_missing_module(self):
        self.skip_if_no_wallet()

    def setup_network(self, split=False):
        self.add_nodes(self.num_nodes, extra_args=self.extra_args)
        self.start_nodes()

        connect_nodes_bi(self.nodes, 0, 1)
        self.sync_all()

    def run_test(self):
        nodes = self.nodes

        nodes[0].extkeyimportmaster('abandon baby cabbage dad eager fabric gadget habit ice kangaroo lab absorb')
        assert(nodes[0].getwalletinfo()['total_balance'] == 100000)

        nodes[1].extkeyimportmaster(nodes[1].mnemonic('new')['master'])

        addr1 = nodes[1].getnewaddress()
        addr2 = nodes[1].getnewstealthaddress()

        txnid = nodes[0].sendmany(
            dummy='',
            amounts={addr1:1, addr2:2},
            subtractfeefrom=[addr1],
            minconf=0,
            )
        self.sync_all()

        ro = nodes[1].filtertransactions()
        assert(ro[0]['txid'] == txnid)
        assert(isclose(ro[0]['amount'], 2.999512))
        assert(len(ro[0]['outputs']) == 2)


if __name__ == '__main__':
    WalletRPCTest().main()
