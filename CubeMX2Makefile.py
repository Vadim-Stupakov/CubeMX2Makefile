#!/usr/bin/env python

import sys
import re
import shutil
import os.path
from string import Template
from xml.etree import ElementTree as ET


C2M_ERR_SUCCESS             =  0
C2M_ERR_INVALID_COMMANDLINE = -1
C2M_ERR_LOAD_TEMPLATE       = -2
C2M_ERR_NO_PROJECT          = -3
C2M_ERR_PROJECT_FILE        = -4
C2M_ERR_IO                  = -5
C2M_ERR_NEED_UPDATE         = -6

# STM32 part to compiler flag mapping
mcu_cflags = {}
mcu_cflags[re.compile('STM32(F|L)0')] = '-mthumb -mcpu=cortex-m0'
mcu_cflags[re.compile('STM32(F|L)1')] = '-mthumb -mcpu=cortex-m3'
mcu_cflags[re.compile('STM32(F|L)2')] = '-mthumb -mcpu=cortex-m3'
mcu_cflags[re.compile('STM32(F|L)3')] = '-mthumb -mcpu=cortex-m4 -mfpu=fpv4-sp-d16 -mfloat-abi=softfp'
mcu_cflags[re.compile('STM32(F|L)4')] = '-mthumb -mcpu=cortex-m4 -mfpu=fpv4-sp-d16 -mfloat-abi=softfp'
mcu_cflags[re.compile('STM32(F|L)7')] = '-mthumb -mcpu=cortex-m7 -mfpu=fpv4-sp-d16 -mfloat-abi=softfp'

if len(sys.argv) != 3:
    sys.stderr.write("\nSTM32CubeMX project to Makefile V1.5\n")
    sys.stderr.write("-==================================-\n")
    sys.stderr.write("Written by Baoshi <mail\x40ba0sh1.com> on 2015-10-03\n")
    sys.stderr.write("Copyright www.ba0sh1.com\n")
    sys.stderr.write("Apache License 2.0 <http://www.apache.org/licenses/LICENSE-2.0>\n")
    sys.stderr.write("Updated for STM32CubeMX Version 4.10.1 http://www.st.com/stm32cube\n")
    sys.stderr.write("Usage:\n")
    sys.stderr.write("  CubeMX2Makefile.py <STM32CubeMX \"Toolchain Folder Location\"> \"<STM32CubeMX Repository location>\"\n")
    sys.exit(C2M_ERR_INVALID_COMMANDLINE)

# Load template files
app_folder = os.path.dirname(os.path.abspath(sys.argv[0]))
try:
    fd = open(app_folder + os.path.sep + 'CubeMX2Makefile.tpl', 'rb')
    mft = Template(fd.read())
    fd.close()
except:
    sys.stderr.write("Unable to load template file CubeMX2Makefile.tpl\n")
    sys.exit(C2M_ERR_LOAD_TEMPLATE)

proj_folder = os.path.abspath(sys.argv[1])
if not os.path.isdir(proj_folder):
    sys.stderr.write("STM32CubeMX \"Toolchain Folder Location\" \"%s\" is not found\n" % proj_folder)
    sys.exit(C2M_ERR_INVALID_COMMANDLINE)

reposytory_folder = os.path.abspath(sys.argv[2])
if not os.path.isdir(reposytory_folder):
    sys.stderr.write("STM32CubeMX \"Reposytory location\" \"%s\" is not found\n" % proj_folder)
    sys.exit(C2M_ERR_INVALID_COMMANDLINE)


proj_name = os.path.splitext(os.path.basename(proj_folder))[0]
ac6_project = proj_folder + os.path.sep + 'SW4STM32' + os.path.sep + proj_name + ' Configuration' + os.path.sep + '.project'
ac6_cproject = proj_folder + os.path.sep + 'SW4STM32' + os.path.sep + proj_name + ' Configuration' + os.path.sep + '.cproject'
if not (os.path.isfile(ac6_project) and os.path.isfile(ac6_cproject)):
    sys.stderr.write("SW4STM32 project not found, use STM32CubeMX to generate a SW4STM32 project balownichok ))first\n")
    sys.exit(C2M_ERR_NO_PROJECT)


# .project file
try:
    tree = ET.parse(ac6_project)
    root = tree.getroot()
except Exception, e:
    sys.stderr.write("Error: cannot parse SW4STM32 .project file: %s\n" % ac6_project)
    sys.exit(C2M_ERR_PROJECT_FILE)
nodes = root.findall('linkedResources/link')
sources = []
for node in nodes:
    name = node.find('name').text
    location = node.find('location').text
    src_path=""
    found = re.search('.*User.*', name)
    if found:
        src_path = re.sub(r'^PARENT-[0-9]-PROJECT_LOC/', "/" , location)
        src_path = "$(PRJ_PATH)" + src_path
    else:
        src_path = re.sub(r'^PARENT-[0-9]-PROJECT_LOC/.*(Drivers/|Middlewares/)', "\\1" , location)
        src_path = "$(REPO_PATH)/" + src_path
    sources.append(src_path)
    
sources=list(set(sources))
sources.sort()
c_sources = ' \\\n'
asm_sources = ' \\\n'
for source in sources:
    ext = os.path.splitext(source)[1]
    if ext == '.c':
        c_sources += "    " + source + " \\\n"
    elif ext == '.s':
        asm_sources += "    " + source + " \\\n"
    else:
        sys.stderr.write("Unknow source file type: %s\n" % source)
        sys.exit(-5)
asm_sources = asm_sources[:-2] + "\n"
c_sources = c_sources[:-2] + "\n"

# .cproject file
try:
    tree = ET.parse(ac6_cproject)
    root = tree.getroot()
except Exception, e:
    sys.stderr.write("Error: cannot parse SW4STM32 .cproject file: %s\n" % ac6_cproject)
    sys.exit(C2M_ERR_PROJECT_FILE)
# MCU
mcu = ''
ld_mcu = ''
node = root.find('.//toolChain[@superClass="fr.ac6.managedbuild.toolchain.gnu.cross.exe.debug"]/option[@name="Mcu"]')
try:
    value = node.attrib.get('value')
except Exception, e:
    sys.stderr.write("No target MCU defined\n")
    sys.exit(C2M_ERR_PROJECT_FILE)
for pattern, option in mcu_cflags.items():
    if pattern.match(value):
        mcu = option
ld_mcu = mcu
# special case for M7, needs to be linked as M4
if ('m7' in ld_mcu):
    ld_mcu = mcu_cflags[re.compile('STM32(F|L)4')]
if (mcu == '' or ld_mcu == ''):
    sys.stderr.write("Unknown MCU\n, please contact author for an update of this utility\n")
    sys.stderr.exit(C2M_ERR_NEED_UPDATE)
# ASM include
asm_includes = '\\\n'
nodes = root.findall('.//tool[@superClass="fr.ac6.managedbuild.tool.gnu.cross.assembler"]/option[@valueType="includePath"]/listOptionValue')
for node in nodes:
    value = node.attrib.get('value')
    if (value != ""):
        value = re.sub(r'((\.\.\/)*\.\./|^/)Inc$', "$(PRJ_PATH)/Inc", value)
        value = re.sub(r'((\.\.\/)*\.\./|^/root/.*/)Drivers\/', "$(REPO_PATH)/Drivers/", value)
        value = re.sub(r'((\.\.\/)*\.\./|^/root/.*/)Middlewares\/', "$(REPO_PATH)/Middlewares/", value)
        asm_includes += "    -I" + value + " \\\n"
asm_includes = asm_includes[:-2] + "\n" 

# AS symbols
asm_defs = '\\\n'
# C include
c_includes = "\\\n"
nodes = root.findall('.//tool[@superClass="fr.ac6.managedbuild.tool.gnu.cross.c.compiler"]/option[@valueType="includePath"]/listOptionValue')
for node in nodes:
    value = node.attrib.get('value')
    if (value != ""):
        value = re.sub(r'((\.\.\/)*\.\./|^/)Inc$', "$(PRJ_PATH)/Inc", value)
        value = re.sub(r'((\.\.\/)*\.\./|^/root/.*/)Drivers\/', "$(REPO_PATH)/Drivers/", value)
        value = re.sub(r'((\.\.\/)*\.\./|^/root/.*/)Middlewares\/', "$(REPO_PATH)/Middlewares/", value)
        c_includes += "    -I" + value + " \\\n"
c_includes = c_includes[:-2] + "\n"

# C symbols
c_defs = '\\\n'
nodes = root.findall('.//tool[@superClass="fr.ac6.managedbuild.tool.gnu.cross.c.compiler"]/option[@valueType="definedSymbols"]/listOptionValue')
for node in nodes:
    value = node.attrib.get('value')
    if (value != ""):
        c_defs += '    -D' + re.sub(r'([()])', r'\\\1', value) + " \\\n"
c_defs = c_defs[:-2] + "\n"

# Link script
ldscript = '' 
node = root.find('.//tool[@superClass="fr.ac6.managedbuild.tool.gnu.cross.c.linker"]/option[@superClass="fr.ac6.managedbuild.tool.gnu.cross.c.linker.script"]')
try:
    value = node.attrib.get('value')
    value = re.sub(r'^..(\\|/)..(\\|/)..(\\|/)', '', value.replace('\\', os.path.sep))
    value = os.path.basename(value)
except Exception, e:
    sys.stderr.write("No link script defined\n")
    sys.exit(C2M_ERR_PROJECT_FILE) 
# copy link script to top level so that user can discard SW4STM32 folder
src = proj_folder + os.path.sep + 'SW4STM32' + os.path.sep + proj_name + ' Configuration' + os.path.sep + value
dst = proj_folder + os.path.sep + value
shutil.copyfile(src, dst)
sys.stdout.write("File created: %s\n" % dst)
ldscript += value  

mf = mft.substitute( \
    TARGET = proj_name, \
    PRJ_PATH = proj_folder, \
    REPO_PATH = reposytory_folder, \
    MCU = mcu, \
    LDMCU = ld_mcu, \
    C_SOURCES = c_sources, \
    ASM_SOURCES = asm_sources, \
    ASM_DEFS = asm_defs, \
    ASM_INCLUDES = asm_includes, \
    C_DEFS = c_defs, \
    C_INCLUDES = c_includes, \
    LDSCRIPT = ldscript)
try:
    fd = open(proj_folder + os.path.sep + 'Makefile', 'wb')
    fd.write(mf)
    fd.write("\n")
    fd.close()
except:
    sys.stderr.write("Write Makefile failed\n")
    sys.exit(C2M_ERR_IO)
sys.stdout.write("File created: %s\n" % (proj_folder + os.path.sep + 'Makefile'))

sys.exit(C2M_ERR_SUCCESS)

