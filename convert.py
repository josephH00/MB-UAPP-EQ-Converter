import configparser as cp
import xml.etree.cElementTree as et
import sys
from pathlib import Path

MBEqRange = [-15., 15.]
UAPPEqRange = [-12., 12] # This is the range max/min displayed on the UI, values outside this range are accepted but misplace visual elements

def scaleRange(x, convertToUAPP):
    inRange = (MBEqRange if convertToUAPP else UAPPEqRange)
    outRange = (UAPPEqRange if convertToUAPP else MBEqRange)
    scaledFloat = (x - inRange[0]) * (outRange[1] - outRange[0]) / (inRange[1] - inRange[0]) + outRange[0]
    return '%.2f'%scaledFloat # Truncate and return as string
    
MBConfig = cp.ConfigParser()
UAPPRoot = et.ElementTree()

def ConvertToUAPP(inFile):
    MBConfig.read(inFile)
    
    MBBands = MBConfig.getint('Equalizer', 'Bands')
    if MBBands != 10:
        print("Error: UAPP only supports a 10 band EQ, this file has " + str(MBBands) + " bands!")
    
    UAPPPreset = et.Element("Preset")
    
    presetInfo = et.Element("PresetInfo", {
        'Name': Path(inFile).stem, 
        'TenBand': '0' 
    })
    UAPPPreset.append(presetInfo)
    
    # Preamp Value
    MBGainAverage = (MBConfig.getfloat('Equalizer', 'LeftPreamp') + MBConfig.getfloat('Equalizer', 'RightPreamp')) / 2.
    et.SubElement(presetInfo, "Value").text = scaleRange(MBGainAverage, convertToUAPP=True)
    
    # Frequency Gain
    for i in range(1, 10 + 1):
        MBChannelAverage = (MBConfig.getfloat('Equalizer', 'Left'+ str(i)) + MBConfig.getfloat('Equalizer', 'Right'+ str(i))) / 2.
        et.SubElement(presetInfo, "Value").text = scaleRange(MBChannelAverage, convertToUAPP=True)
    
    UAPPRoot._setroot(UAPPPreset)
    UAPPRoot.write(Path(inFile).stem + ".xml", encoding='ISO-8859-1', xml_declaration=True)
    
def ConvertToMB(inFile):
    UAPPRoot = et.parse(inFile).getroot()
    
    MBConfig.optionxform = str
    MBConfig.add_section('Equalizer')
    MBConfig.set('Equalizer', 'Bands', '10')
    
    i = 0
    for bandValue in UAPPRoot.find('PresetInfo').findall('Value'):
        if i == 0: # First Value is for preamp
            MBConfig.set('Equalizer', 'LeftPreamp', bandValue.text)
            MBConfig.set('Equalizer', 'RightPreamp', bandValue.text)
            i = i + 1
            continue
        
        convertedValue = scaleRange(float(bandValue.text), convertToUAPP=False) # Convert from UAPP to MB
        
        MBConfig.set('Equalizer', 'Left' + str(i), convertedValue)
        MBConfig.set('Equalizer', 'Right' + str(i), convertedValue)
        i = i + 1
    
    with open(Path(inFile).stem + ".sde", 'w') as outFile:
        MBConfig.write(outFile)

if len(sys.argv) < 2:
    print("Usage: ./convert.py [Input File Path]")
    print("Will convert between MusicBee EQ and UAPP EQ Formats")
    exit()

inputFileName = sys.argv[1]
if inputFileName.find(".sde") != -1:
    MBToUAPPMode = True
    ConvertToUAPP(inputFileName)
else:
    MBToUAPPMode = False
    ConvertToMB(inputFileName)