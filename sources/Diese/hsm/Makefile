TARGET := hsm

SRCDIR := src
OBJDIR := obj
OUTDIR := out
DISTDIR := dist
RELDIR := ../../../services/Diese/hsm
LINKER_SCRIPT := linker/linker.ld

SRCS := $(wildcard $(SRCDIR)/*.c) $(wildcard $(SRCDIR)/*.S)
OBJS := $(addprefix $(OBJDIR)/,$(addsuffix .o, $(basename $(notdir $(SRCS)))))
DEPS := $(OBJS:.o=.d)

DISTS := $(addprefix $(DISTDIR)/,$(TARGET).bin $(TARGET).elf)
RELS := $(addprefix $(RELDIR)/,Dockerfile $(TARGET).bin $(TARGET).elf hsm.py)

CC := arm-none-eabi-gcc
LD := arm-none-eabi-ld
OBJCOPY := arm-none-eabi-objcopy

CFLAGS := -O2 -std=c99 -Wall -Wextra \
	-ffreestanding -mcpu=arm926ej-s \
	-ffunction-sections -fdata-sections -fstack-usage
LDFLAGS := --gc-sections

.SUFFIXES:
.DELETE_ON_ERROR:

.DEFAULT_GOAL := build

-include $(DEPS)

$(OBJDIR) $(OUTDIR) $(DISTDIR) $(RELDIR):
	mkdir $@

$(OBJDIR)/%.o: $(SRCDIR)/%.c | $(OBJDIR)
	$(CC) -MMD $(CFLAGS) -c -o $@ $<

$(OBJDIR)/%.o: $(SRCDIR)/%.S | $(OBJDIR)
	$(CC) -MMD $(CFLAGS) -c -o $@ $<

$(OUTDIR)/$(TARGET).elf: $(LINKER_SCRIPT) $(OBJS) | $(OUTDIR)
	$(LD) -T $(LINKER_SCRIPT) $(LDFLAGS) -o $@ $(filter-out $<,$^)

$(OUTDIR)/$(TARGET).bin: $(OUTDIR)/$(TARGET).elf | $(OUTDIR)
	$(OBJCOPY) -O binary $< $@

$(DISTDIR)/%: $(OUTDIR)/% | $(DISTDIR)
	cp $< $@
.PRECIOUS: $(DISTDIR)/%

$(RELDIR)/%: $(DISTDIR)/% | $(RELDIR)
	cp $< $@
.PRECIOUS: $(RELDIR)/%

build: $(DISTS)
.PHONY: build

clean:
	rm -rf $(OBJDIR) $(OUTDIR) $(DISTS)
.PHONY: clean

release: $(RELS)
.PHONY: release

relclean:
	rm -f $(RELS)
.PHONY: relclean
