	.attribute	4, 16
	.attribute	5, "rv32i2p1_c2p0_zmmul1p0"
	.file	"main.c"
	.section	.text._start,"ax",@progbits
	.globl	_start                          # -- Begin function _start
	.p2align	1
	.type	_start,@function
_start:                                 # @_start
# %bb.0:
	#APP
	lui	sp, 1
	j	main

	#NO_APP
.Lfunc_end0:
	.size	_start, .Lfunc_end0-_start
                                        # -- End function
	.section	.text.main,"ax",@progbits
	.globl	main                            # -- Begin function main
	.p2align	1
	.type	main,@function
main:                                   # @main
# %bb.0:
	lui	a0, 725084
	addi	a0, a0, 222
	#APP
	mv	a6, a0
	#NO_APP
.LBB1_1:                                # =>This Inner Loop Header: Depth=1
	#APP
	li	s4, 0
	#NO_APP
	j	.LBB1_1
.Lfunc_end1:
	.size	main, .Lfunc_end1-main
                                        # -- End function
	.ident	"clang version 20.1.2 (https://github.com/ziglang/zig-bootstrap 7ef74e656cf8ddbd6bf891a8475892aa1afa6891)"
	.section	".note.GNU-stack","",@progbits
	.addrsig
