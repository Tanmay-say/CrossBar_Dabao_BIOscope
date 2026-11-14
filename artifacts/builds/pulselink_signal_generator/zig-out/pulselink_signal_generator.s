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
	li	a0, 0
	li	a1, 2
	#APP
	mv	s10, a1
	#NO_APP
	#APP
	mv	s8, a1
	#NO_APP
	li	a2, -3
	#APP
	mv	s7, a2
	#NO_APP
	lui	a3, 1048575
	addi	a3, a3, 596
	li	a4, 10
.LBB1_1:                                # =>This Loop Header: Depth=1
                                        #     Child Loop BB1_2 Depth 2
                                        #     Child Loop BB1_4 Depth 2
	#APP
	mv	s6, a1
	#NO_APP
	mv	a5, a3
.LBB1_2:                                #   Parent Loop BB1_1 Depth=1
                                        # =>  This Inner Loop Header: Depth=2
	#APP
	li	s4, 0
	#NO_APP
	addi	a5, a5, 1
	bnez	a5, .LBB1_2
# %bb.3:                                #   in Loop: Header=BB1_1 Depth=1
	#APP
	mv	s7, a2
	#NO_APP
	mv	a5, a3
.LBB1_4:                                #   Parent Loop BB1_1 Depth=1
                                        # =>  This Inner Loop Header: Depth=2
	#APP
	li	s4, 0
	#NO_APP
	addi	a5, a5, 1
	bnez	a5, .LBB1_4
# %bb.5:                                #   in Loop: Header=BB1_1 Depth=1
	addi	a0, a0, 1
	bne	a0, a4, .LBB1_1
.LBB1_6:                                # =>This Inner Loop Header: Depth=1
	#APP
	li	s4, 0
	#NO_APP
	j	.LBB1_6
.Lfunc_end1:
	.size	main, .Lfunc_end1-main
                                        # -- End function
	.ident	"clang version 20.1.2 (https://github.com/ziglang/zig-bootstrap 7ef74e656cf8ddbd6bf891a8475892aa1afa6891)"
	.section	".note.GNU-stack","",@progbits
	.addrsig
