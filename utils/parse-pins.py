

from stm32import import MCU as MCU
from stm32import import xml as xml
import defusedxml.minidom as minidom
import os
import sys
import logging
import traceback

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')

loggerName = __name__
if __name__ == "__main__":
    loggerName = os.path.basename(__file__)
log = logging.getLogger(loggerName)

# Get all xml files in the directory

def getMcuFiles(dataDir):
    mcuDir = dataDir + "/mcu"
    for file in os.listdir(mcuDir):
        filePath = os.path.join(mcuDir, file)
        if os.path.isfile(filePath) and file.endswith(".xml"):
            yield filePath



dataDir = "3dparty/st-open-pins"

mcuFiles = getMcuFiles(dataDir)
for mcuFile in mcuFiles:
    try:
        root = minidom.parse(mcuFile)

        rootTag = xml.Tag(root.documentElement)
        mcu = MCU.MCU.fromSomething(rootTag)
        log.info(f"MCU: {mcu.refName} {mcu.family} {mcu.package} Ram: {mcu.ram}, Flash: {mcu.flash}")

    except Exception as e:
        log.error(f"Error parsing {mcuFile}: {traceback.format_exc()}")
        sys.exit(1)




