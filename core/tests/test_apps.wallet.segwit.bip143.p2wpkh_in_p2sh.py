from common import *

from apps.wallet.sign_tx.scripts import output_derive_script
from apps.wallet.sign_tx.bitcoin import Bitcoin
from apps.wallet.sign_tx.writers import get_tx_hash
from apps.common import coins
from trezor.messages.SignTx import SignTx
from trezor.messages.TxInputType import TxInputType
from trezor.messages.TxOutputType import TxOutputType
from trezor.messages.TxOutputBinType import TxOutputBinType
from trezor.messages import InputScriptType
from trezor.messages import OutputScriptType
from trezor.crypto import bip39


class TestSegwitBip143(unittest.TestCase):
    # pylint: disable=C0301

    tx = SignTx(coin_name='Bitcoin', version=1, lock_time=0x00000492, inputs_count=1, outputs_count=2)
    inp1 = TxInputType(address_n=[0],
                       # Trezor expects hash in reversed format
                       prev_hash=unhexlify('77541aeb3c4dac9260b68f74f44c973081a9d4cb2ebe8038b2d70faa201b6bdb'),
                       prev_index=1,
                       multisig=None,
                       amount=1000000000,  # 10 btc
                       script_type=InputScriptType.SPENDP2SHWITNESS,  # TODO: is this correct?
                       sequence=0xfffffffe)
    out1 = TxOutputType(address='1Fyxts6r24DpEieygQiNnWxUdb18ANa5p7',
                        amount=0x000000000bebb4b8,
                        script_type=OutputScriptType.PAYTOADDRESS,
                        multisig=None,
                        address_n=[])
    out2 = TxOutputType(address='1Q5YjKVj5yQWHBBsyEBamkfph3cA6G9KK8',
                        amount=0x000000002faf0800,
                        script_type=OutputScriptType.PAYTOADDRESS,
                        multisig=None,
                        address_n=[])

    def test_bip143_prevouts(self):
        coin = coins.by_name(self.tx.coin_name)
        bip143 = Bitcoin(self.tx, None, coin)
        bip143.hash143_add_input(self.inp1)
        prevouts_hash = get_tx_hash(bip143.h_prevouts, double=coin.sign_hash_double)
        self.assertEqual(hexlify(prevouts_hash), b'b0287b4a252ac05af83d2dcef00ba313af78a3e9c329afa216eb3aa2a7b4613a')

    def test_bip143_sequence(self):
        coin = coins.by_name(self.tx.coin_name)
        bip143 = Bitcoin(self.tx, None, coin)
        bip143.hash143_add_input(self.inp1)
        sequence_hash = get_tx_hash(bip143.h_sequence, double=coin.sign_hash_double)
        self.assertEqual(hexlify(sequence_hash), b'18606b350cd8bf565266bc352f0caddcf01e8fa789dd8a15386327cf8cabe198')

    def test_bip143_outputs(self):
        seed = bip39.seed('alcohol woman abuse must during monitor noble actual mixed trade anger aisle', '')
        coin = coins.by_name(self.tx.coin_name)
        bip143 = Bitcoin(self.tx, None, coin)

        for txo in [self.out1, self.out2]:
            txo_bin = TxOutputBinType()
            txo_bin.amount = txo.amount
            txo_bin.script_pubkey = output_derive_script(txo, coin)
            bip143.hash143_add_output(txo_bin)

        outputs_hash = get_tx_hash(bip143.h_outputs, double=coin.sign_hash_double)
        self.assertEqual(hexlify(outputs_hash), b'de984f44532e2173ca0d64314fcefe6d30da6f8cf27bafa706da61df8a226c83')

    def test_bip143_preimage_testdata(self):
        seed = bip39.seed('alcohol woman abuse must during monitor noble actual mixed trade anger aisle', '')
        coin = coins.by_name(self.tx.coin_name)
        bip143 = Bitcoin(self.tx, None, coin)
        bip143.hash143_add_input(self.inp1)
        for txo in [self.out1, self.out2]:
            txo_bin = TxOutputBinType()
            txo_bin.amount = txo.amount
            txo_bin.script_pubkey = output_derive_script(txo, coin)
            bip143.hash143_add_output(txo_bin)

        # test data public key hash
        result = bip143.hash143_preimage_hash(self.inp1, unhexlify('79091972186c449eb1ded22b78e40d009bdf0089'))
        self.assertEqual(hexlify(result), b'64f3b0f4dd2bb3aa1ce8566d220cc74dda9df97d8490cc81d89d735c92e59fb6')


if __name__ == '__main__':
    unittest.main()
