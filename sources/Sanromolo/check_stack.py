#!/usr/bin/env python3
#
# @mebeim - 2024-09-29
#

import sys
from re import compile
from subprocess import check_output

EXPECTED_FRAME_SIZE = {
	'create_wallet'  : 0x148,
	'buy_user_ticket': 0x120,
	'buy_vip_ticket' : 0xa8,
	'read_page'      : 0x70,
	'write_page'     : 0x50,
	'num_cards'      : 0xa0,
	'get_card'       : 0xc8,
	'read_exactly'   : 0x8,
	'write_exactly'  : 0x8,
}

FUNC_EXP = compile(r'[0-9a-f]+ <(\w+)>:')
SUB_RSP_EXP = compile(r'sub +rsp,0x([0-9a-f]+)$')
EXE = None
DUMP = False

if len(sys.argv) == 2:
	EXE = sys.argv[1]
elif len(sys.argv) == 3 and sys.argv[1] == 'dump':
	DUMP = True
	EXE = sys.argv[2]
else:
	sys.exit(f'Usage: {sys.argv[0]} [dump] EXECUTABLE')


disasm = check_output(('objdump', '-Mintel', '-d', EXE), text=True)
cur_func = None
n_insn = 0

for line in disasm.splitlines():
	if cur_func is None:
		match = FUNC_EXP.match(line)
		if match is None:
			continue

		cur_func = match.group(1)
		n_insn = 0
		continue

	n_insn += 1
	match = SUB_RSP_EXP.search(line)
	if match is None:
		if not line.strip() or n_insn >= 10:
			# Probably not a function or a function w/o stack usage
			cur_func = None
		continue

	actual = int(match.group(1), 16)

	if DUMP:
		print(cur_func.ljust(30), hex(actual))
		continue

	if cur_func in EXPECTED_FRAME_SIZE:
		expected = EXPECTED_FRAME_SIZE[cur_func]
		assert expected == actual, f'Unexpected frame size for {cur_func}: expected {expected}, have {actual}'
