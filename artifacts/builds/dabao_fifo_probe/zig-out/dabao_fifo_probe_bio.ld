OUTPUT_FORMAT(binary)
ENTRY(0)
MEMORY {
    MEM : ORIGIN = 0x00000000, LENGTH = 0xF04
}
SECTIONS {
    . = 0x0;
    .text   : { *(.text*)   } > MEM
    .rodata : { *(.rodata*) } > MEM
    .data   : { *(.data*)   } > MEM
    .bio_metadata : { *(.bio_metadata) } > MEM
    /DISCARD/ : { *(.eh_frame*) *(.note*) *(.comment) }
}
