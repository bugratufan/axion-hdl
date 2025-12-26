import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from axion_hdl.xml_input_parser import XMLInputParser

def test_manual_addr():
    p = XMLInputParser()
    fpath = os.path.abspath("tests/xml/manual_addr_test.xml")
    m = p.parse_file(fpath)
    
    if not m:
        print("Failed to parse module")
        sys.exit(1)
        
    regs = m['registers']
    print(f"Found {len(regs)} registers")
    
    regA = next(r for r in regs if r['name'] == 'regA')
    regB = next(r for r in regs if r['name'] == 'regB')
    
    print(f"RegA Addr: {regA['address']}, Manual: {regA.get('manual_address')}")
    print(f"RegB Addr: {regB['address']}, Manual: {regB.get('manual_address')}")
    
    if regA.get('manual_address') and regB.get('manual_address'):
        print("SUCCESS: Manual addresses detected")
    else:
        print("FAILURE: Manual addresses NOT detected")
        sys.exit(1)

if __name__ == "__main__":
    test_manual_addr()
