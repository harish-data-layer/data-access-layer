import os
import xml.etree.ElementTree as ET

path = os.path.join(os.environ['APPDATA'], 'SAP', 'Common', 'SAPUILandscape.xml')
tree = ET.parse(path)
root = tree.getroot()

for service in root.findall('.//Service'):
    name = service.get('name')
    server = service.get('server')
    systemid = service.get('systemid')
    print(f"Name: {name}, Server: {server}, SystemID: {systemid}")
