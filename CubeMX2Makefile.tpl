######################################
# Makefile by CubeMX2Makefile.py
######################################

######################################
# target
######################################
TARGET = $TARGET

######################################
# building variables
######################################
# debug build?
DEBUG = 1
# optimization
OPT = -O0

#######################################
# pathes
#######################################
# source path
# Build path
BUILD_DIR = build
PRJ_PATH = $PRJ_PATH
REPO_PATH = $REPO_PATH

######################################
# source
######################################
C_SOURCES = $C_SOURCES  
ASM_SOURCES = $ASM_SOURCES

#######################################
# binaries
#######################################
CC = arm-none-eabi-gcc
AS = arm-none-eabi-gcc -x assembler-with-cpp
CP = arm-none-eabi-objcopy
AR = arm-none-eabi-ar
SZ = arm-none-eabi-size
HEX = $$(CP) -O ihex
BIN = $$(CP) -O binary -S
 
#######################################
# CFLAGS
#######################################
# macros for gcc
ASM_DEFS = $ASM_DEFS
C_DEFS = $C_DEFS
# includes for gcc
ASM_INCLUDES = $ASM_INCLUDES
C_INCLUDES = $C_INCLUDES
# compile gcc flags
ASFLAGS = $MCU $$(AS_DEFS) $$(AS_INCLUDES) $$(OPT) -Wall -fdata-sections -ffunction-sections
CFLAGS = $MCU $$(C_DEFS) $$(C_INCLUDES) $$(OPT) -Wall -fdata-sections -ffunction-sections
ifeq ($$(DEBUG), 1)
CFLAGS += -g -gdwarf-2
endif
# Generate dependency information
CFLAGS += -MD -MP -MF .dep/$$(@F).d

#######################################
# LDFLAGS
#######################################
# link script
LDSCRIPT = $LDSCRIPT
# libraries
LIBS = -lc -lm -lnosys
LIBDIR =
LDFLAGS = $LDMCU -specs=nano.specs -T$$(LDSCRIPT) $$(LIBDIR) $$(LIBS) -Wl,-Map=$$(BUILD_DIR)/$$(TARGET).map,--cref -Wl,--gc-sections

# default action: build all
all: $$(BUILD_DIR)/$$(TARGET).elf $$(BUILD_DIR)/$$(TARGET).hex $$(BUILD_DIR)/$$(TARGET).bin

#######################################################
# Printing variables needed for generating any project
#######################################################
C_DEFS_PRINT:
	@echo $$(C_DEFS)

C_SOURCES_PRINT:
	@echo $$(C_SOURCES)

C_INCLUDES_PRINT:
	@echo $$(C_INCLUDES)

ASM_SOURCES_PRINT:
	@echo $$(ASM_SOURCES)

ASM_DEFS_PRINT:
	@echo $$(ASM_DEFS)

ASM_INCLUDES_PRINT:
	@echo $$(ASM_INCLUDES)
#######################################################

#######################################
# build the application
#######################################
# list of objects
OBJECTS = $$(addprefix $$(BUILD_DIR)/,$$(notdir $$(C_SOURCES:.c=.o)))
vpath %.c $$(sort $$(dir $$(C_SOURCES)))
# list of ASM program objects
OBJECTS += $$(addprefix $$(BUILD_DIR)/,$$(notdir $$(ASM_SOURCES:.s=.o)))
vpath %.s $$(sort $$(dir $$(ASM_SOURCES)))

$$(BUILD_DIR)/%.o: %.c Makefile | $$(BUILD_DIR) 
	$$(CC) -c $$(CFLAGS) -Wa,-a,-ad,-alms=$$(BUILD_DIR)/$$(notdir $$(<:.c=.lst)) $$< -o $$@

$$(BUILD_DIR)/%.o: %.s Makefile | $$(BUILD_DIR)
	$$(AS) -c $$(CFLAGS) $$< -o $$@

$$(BUILD_DIR)/$$(TARGET).elf: $$(OBJECTS) Makefile
	$$(CC) $$(OBJECTS) $$(LDFLAGS) -o $$@
	$$(SZ) $$@

$$(BUILD_DIR)/%.hex: $$(BUILD_DIR)/%.elf | $$(BUILD_DIR)
	$$(HEX) $$< $$@
	
$$(BUILD_DIR)/%.bin: $$(BUILD_DIR)/%.elf | $$(BUILD_DIR)
	$$(BIN) $$< $$@	
	
$$(BUILD_DIR):
	mkdir -p $$@		

#######################################
# clean up
#######################################
clean:
	-rm -fR .dep $$(BUILD_DIR)
  
#######################################
# dependencies
#######################################
-include $$(shell mkdir .dep 2>/dev/null) $$(wildcard .dep/*)

# *** EOF ***
