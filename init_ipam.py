"""
File: init_ipam.py
Purpose: Initialize IPAM database with networks, VLANs, and IP ranges
Created: 2025-01-14
Author: DCMS Team

Revision History:
- v1.0.0: Initial creation to populate IPAM tables
          Based on core switch configuration from MobaXterm_NetMon_20250914_123711.txt
          
Run this script once to set up your IPAM data:
    python init_ipam.py
"""

from app import app, db
from models.ipam import Network, VLAN, IPRange, IPPool, IPAddress
from models.datacenter import DataCenter
import ipaddress

def init_ipam():
    """Initialize IPAM with your network configuration"""
    
    with app.app_context():
        # ========== CREATE TABLES ==========
        print("Creating IPAM tables...")
        db.create_all()
        print("✓ Tables created")
        
        # Check if already initialized
        if Network.query.first():
            print("⚠️  IPAM already contains data. Skipping initialization.")
            print("   To reinitialize, delete all IPAM data first.")
            return
        
        # ========== CREATE NETWORKS ==========
        print("\n========== Creating Networks ==========")
        
        networks_data = [
            # Main public blocks
            {'network': '208.76.80.0/21', 'cidr': 21, 'bgp': True, 'desc': 'Main public block (BGP advertised)'},
            {'network': '198.38.76.0/22', 'cidr': 22, 'bgp': True, 'desc': 'Large public block (BGP advertised)'},
            {'network': '199.58.176.0/22', 'cidr': 22, 'bgp': True, 'desc': 'Secondary public block (BGP advertised)'},
            
            # Individual /24s for easier management
            {'network': '208.76.80.0/24', 'cidr': 24, 'bgp': False, 'desc': 'Public network'},
            {'network': '208.76.81.0/24', 'cidr': 24, 'bgp': False, 'desc': 'Public network (VPS15)'},
            {'network': '208.76.82.0/24', 'cidr': 24, 'bgp': False, 'desc': 'Public network'},
            {'network': '208.76.83.0/24', 'cidr': 24, 'bgp': False, 'desc': 'Public network'},
            {'network': '208.76.84.0/24', 'cidr': 24, 'bgp': False, 'desc': 'Public network'},
            {'network': '208.76.85.0/24', 'cidr': 24, 'bgp': False, 'desc': 'Public network'},
            {'network': '208.76.86.0/24', 'cidr': 24, 'bgp': False, 'desc': 'Public network (VPS14/thebox)'},
            {'network': '208.76.87.0/24', 'cidr': 24, 'bgp': False, 'desc': 'Public network'},
            
            # Other public ranges
            {'network': '199.58.176.0/24', 'cidr': 24, 'bgp': False, 'desc': 'Public network'},
            {'network': '199.58.177.0/24', 'cidr': 24, 'bgp': False, 'desc': 'Public network'},
            {'network': '199.58.178.0/24', 'cidr': 24, 'bgp': False, 'desc': 'Public network'},
            {'network': '199.58.179.0/24', 'cidr': 24, 'bgp': False, 'desc': 'Public network (VPS8/9/10/11)'},
            {'network': '198.38.79.0/24', 'cidr': 24, 'bgp': False, 'desc': 'Public network (VPS12)'},
            
            # Additional ranges from core switch
            {'network': '199.102.70.0/24', 'cidr': 24, 'bgp': False, 'desc': 'Public network'},
            {'network': '208.79.210.0/24', 'cidr': 24, 'bgp': False, 'desc': 'Public network'},
            {'network': '208.79.212.160/27', 'cidr': 27, 'bgp': False, 'desc': 'Public network'},
            {'network': '208.92.219.224/27', 'cidr': 27, 'bgp': False, 'desc': 'Public network'},
            {'network': '208.76.208.0/27', 'cidr': 27, 'bgp': False, 'desc': 'Public network'},
            
            # Colocation ranges
            {'network': '66.51.159.0/24', 'cidr': 24, 'bgp': False, 'desc': 'Colocation customer ranges'},
            
            # Private networks
            {'network': '10.10.4.0/22', 'cidr': 22, 'bgp': False, 'desc': 'Private network (Wild West)'},
            {'network': '10.0.0.0/24', 'cidr': 24, 'bgp': False, 'desc': 'Management network'},
            {'network': '10.77.77.0/24', 'cidr': 24, 'bgp': False, 'desc': 'Test network'},
        ]
        
        networks = {}
        for net_data in networks_data:
            network = Network(
                network=net_data['network'],
                cidr=net_data['cidr'],
                bgp_advertised=net_data['bgp'],
                description=net_data['desc']
            )
            db.session.add(network)
            networks[net_data['network']] = network
            print(f"  ✓ Created network: {net_data['network']}")
        
        db.session.flush()
        
        # ========== CREATE VLANS ==========
        print("\n========== Creating VLANs ==========")
        
        vlans_data = [
            {'num': 2, 'name': 'Vlan2', 'desc': 'Public VLAN'},
            {'num': 3, 'name': 'Vlan3', 'desc': 'Public VLAN (VPS15)', 'is_vps': True},
            {'num': 5, 'name': 'Vlan5', 'desc': 'Public VLAN'},
            {'num': 6, 'name': 'Vlan6', 'desc': 'Public VLAN'},
            {'num': 7, 'name': 'Vlan7', 'desc': 'Public VLAN'},
            {'num': 8, 'name': 'Vlan8', 'desc': 'Public VLAN'},
            {'num': 9, 'name': 'Vlan9', 'desc': 'Public VLAN'},
            {'num': 10, 'name': 'Vlan10', 'desc': 'Public VLAN'},
            {'num': 11, 'name': 'Vlan11', 'desc': 'Public VLAN'},
            {'num': 12, 'name': 'Vlan12', 'desc': 'Public VLAN (VPS8/9/10/11)', 'is_vps': True},
            {'num': 13, 'name': 'Vlan13', 'desc': 'Public VLAN (thebox)', 'is_vps': True},
            {'num': 14, 'name': 'Vlan14', 'desc': 'Public VLAN'},
            {'num': 17, 'name': 'Vlan17', 'desc': 'Public VLAN (VPS14)', 'is_vps': True},
            {'num': 90, 'name': 'Vlan90', 'desc': 'Public VLAN'},
            {'num': 91, 'name': 'Vlan91', 'desc': 'Public VLAN'},
            {'num': 92, 'name': 'Vlan92', 'desc': 'Public VLAN'},
            {'num': 93, 'name': 'Vlan93', 'desc': 'Public VLAN'},
            {'num': 94, 'name': 'Vlan94', 'desc': 'Public VLAN'},
            {'num': 100, 'name': 'Vlan100', 'desc': 'Large public VLAN (VPS12)', 'is_vps': True},
            {'num': 111, 'name': 'Vlan111', 'desc': 'Public VLAN (Multiple ranges)'},
            {'num': 301, 'name': 'Vlan301', 'desc': 'Private network', 'vrf': 'private', 'is_private': True},
            {'num': 1000, 'name': 'Vlan1000', 'desc': 'Management VLAN', 'vrf': 'private', 'is_private': True},
            
            # Colo VLANs
            {'num': 201, 'name': 'Vlan201', 'desc': 'Colo customer', 'is_colo': True},
            {'num': 202, 'name': 'Vlan202', 'desc': 'Colo customer', 'is_colo': True},
            {'num': 203, 'name': 'Vlan203', 'desc': 'Colo customer', 'is_colo': True},
            {'num': 204, 'name': 'Vlan204', 'desc': 'Colo customer', 'is_colo': True},
            {'num': 205, 'name': 'Vlan205', 'desc': 'Colo customer', 'is_colo': True},
            {'num': 206, 'name': 'Vlan206', 'desc': 'Colo customer', 'is_colo': True},
            {'num': 207, 'name': 'Vlan207', 'desc': 'Colo customer', 'is_colo': True},
            {'num': 208, 'name': 'Vlan208', 'desc': 'Colo customer', 'is_colo': True},
            {'num': 209, 'name': 'Vlan209', 'desc': 'Colo 51456', 'is_colo': True},
            {'num': 210, 'name': 'Vlan210', 'desc': 'Colo customer', 'is_colo': True},
            {'num': 211, 'name': 'Vlan211', 'desc': 'Colo customer', 'is_colo': True},
            {'num': 212, 'name': 'Vlan212', 'desc': 'Colo 51451', 'is_colo': True},
            {'num': 213, 'name': 'Vlan213', 'desc': 'Colo customer', 'is_colo': True},
            {'num': 214, 'name': 'Vlan214', 'desc': 'Colo customer', 'is_colo': True},
            {'num': 215, 'name': 'Vlan215', 'desc': 'Colo customer', 'is_colo': True},
            {'num': 216, 'name': 'Vlan216', 'desc': 'Colo customer', 'is_colo': True},
            {'num': 217, 'name': 'Vlan217', 'desc': 'Colo 51526', 'is_colo': True},
        ]
        
        vlans = {}
        for vlan_data in vlans_data:
            vlan = VLAN(
                vlan_number=vlan_data['num'],
                name=vlan_data['name'],
                description=vlan_data['desc'],
                vrf=vlan_data.get('vrf'),
                is_private=vlan_data.get('is_private', False),
                is_colo=vlan_data.get('is_colo', False),
                is_vps=vlan_data.get('is_vps', False)
            )
            db.session.add(vlan)
            vlans[vlan_data['num']] = vlan
            print(f"  ✓ Created VLAN {vlan_data['num']}: {vlan_data['name']}")
        
        db.session.flush()
        
        # ========== CREATE IP RANGES ==========
        print("\n========== Creating IP Ranges ==========")
        
        # Based on core switch interface configurations
        ranges_data = [
            # VLAN 111 (Multiple ranges)
            {'net': '208.76.80.0/24', 'vlan': 111, 'start': '208.76.80.4', 'end': '208.76.80.126', 'gw': '208.76.80.3', 'mask': '255.255.255.128', 'type': 'primary'},
            {'net': '199.58.176.0/24', 'vlan': 111, 'start': '199.58.176.129', 'end': '199.58.176.253', 'gw': '199.58.176.254', 'mask': '255.255.255.128', 'type': 'secondary'},
            {'net': '199.58.177.0/24', 'vlan': 111, 'start': '199.58.177.129', 'end': '199.58.177.253', 'gw': '199.58.177.254', 'mask': '255.255.255.128', 'type': 'secondary'},
            
            # VLAN 2
            {'net': '208.76.80.0/24', 'vlan': 2, 'start': '208.76.80.129', 'end': '208.76.80.253', 'gw': '208.76.80.254', 'mask': '255.255.255.128', 'type': 'primary'},
            {'net': '199.58.178.0/24', 'vlan': 2, 'start': '199.58.178.2', 'end': '199.58.178.126', 'gw': '199.58.178.1', 'mask': '255.255.255.128', 'type': 'secondary'},
            
            # VLAN 3
            {'net': '208.76.81.0/24', 'vlan': 3, 'start': '208.76.81.2', 'end': '208.76.81.254', 'gw': '208.76.81.1', 'mask': '255.255.255.0', 'type': 'primary'},
            
            # VLAN 5
            {'net': '208.76.82.0/24', 'vlan': 5, 'start': '208.76.82.2', 'end': '208.76.82.126', 'gw': '208.76.82.1', 'mask': '255.255.255.128', 'type': 'primary'},
            
            # VLAN 6
            {'net': '208.76.82.0/24', 'vlan': 6, 'start': '208.76.82.129', 'end': '208.76.82.253', 'gw': '208.76.82.254', 'mask': '255.255.255.128', 'type': 'primary'},
            {'net': '199.58.178.0/24', 'vlan': 6, 'start': '199.58.178.129', 'end': '199.58.178.253', 'gw': '199.58.178.254', 'mask': '255.255.255.128', 'type': 'secondary'},
            
            # VLAN 7
            {'net': '208.76.83.0/24', 'vlan': 7, 'start': '208.76.83.2', 'end': '208.76.83.126', 'gw': '208.76.83.1', 'mask': '255.255.255.128', 'type': 'primary'},
            
            # VLAN 8
            {'net': '208.76.83.0/24', 'vlan': 8, 'start': '208.76.83.129', 'end': '208.76.83.253', 'gw': '208.76.83.254', 'mask': '255.255.255.128', 'type': 'primary'},
            
            # VLAN 9
            {'net': '208.76.84.0/24', 'vlan': 9, 'start': '208.76.84.2', 'end': '208.76.84.126', 'gw': '208.76.84.1', 'mask': '255.255.255.128', 'type': 'primary'},
            {'net': '199.58.177.0/24', 'vlan': 9, 'start': '199.58.177.2', 'end': '199.58.177.126', 'gw': '199.58.177.1', 'mask': '255.255.255.128', 'type': 'secondary'},
            
            # VLAN 10
            {'net': '208.76.84.0/24', 'vlan': 10, 'start': '208.76.84.129', 'end': '208.76.84.253', 'gw': '208.76.84.254', 'mask': '255.255.255.128', 'type': 'primary'},
            {'net': '10.77.77.0/24', 'vlan': 10, 'start': '10.77.77.2', 'end': '10.77.77.254', 'gw': '10.77.77.1', 'mask': '255.255.255.0', 'type': 'secondary'},
            
            # VLAN 11
            {'net': '208.76.85.0/24', 'vlan': 11, 'start': '208.76.85.2', 'end': '208.76.85.126', 'gw': '208.76.85.1', 'mask': '255.255.255.128', 'type': 'primary'},
            
            # VLAN 12
            {'net': '208.76.85.0/24', 'vlan': 12, 'start': '208.76.85.129', 'end': '208.76.85.253', 'gw': '208.76.85.254', 'mask': '255.255.255.128', 'type': 'primary'},
            {'net': '199.58.179.0/24', 'vlan': 12, 'start': '199.58.179.2', 'end': '199.58.179.254', 'gw': '199.58.179.1', 'mask': '255.255.255.0', 'type': 'secondary'},
            
            # VLAN 13
            {'net': '208.76.86.0/24', 'vlan': 13, 'start': '208.76.86.2', 'end': '208.76.86.126', 'gw': '208.76.86.1', 'mask': '255.255.255.128', 'type': 'primary'},
            
            # VLAN 14
            {'net': '208.76.87.0/24', 'vlan': 14, 'start': '208.76.87.2', 'end': '208.76.87.254', 'gw': '208.76.87.1', 'mask': '255.255.255.0', 'type': 'primary'},
            
            # VLAN 17
            {'net': '208.76.86.0/24', 'vlan': 17, 'start': '208.76.86.130', 'end': '208.76.86.254', 'gw': '208.76.86.129', 'mask': '255.255.255.128', 'type': 'primary'},
            
            # VLAN 100
            {'net': '198.38.76.0/22', 'vlan': 100, 'start': '198.38.76.2', 'end': '198.38.79.254', 'gw': '198.38.76.1', 'mask': '255.255.252.0', 'type': 'primary'},
            
            # Private VLANs
            {'net': '10.10.4.0/22', 'vlan': 301, 'start': '10.10.4.1', 'end': '10.10.7.254', 'gw': '10.10.6.200', 'mask': '255.255.252.0', 'type': 'primary'},
            {'net': '10.0.0.0/24', 'vlan': 1000, 'start': '10.0.0.2', 'end': '10.0.0.254', 'gw': '10.0.0.1', 'mask': '255.255.255.0', 'type': 'primary'},
        ]
        
        for range_data in ranges_data:
            network = networks.get(range_data['net'])
            vlan = vlans.get(range_data['vlan'])
            
            if network and vlan:
                ip_range = IPRange(
                    network_id=network.id,
                    vlan_id=vlan.id,
                    start_ip=range_data['start'],
                    end_ip=range_data['end'],
                    gateway=range_data['gw'],
                    netmask=range_data['mask'],
                    range_type=range_data['type'],
                    status='active'
                )
                db.session.add(ip_range)
                print(f"  ✓ Created range: {range_data['start']}-{range_data['end']} on VLAN {range_data['vlan']}")
        
        db.session.flush()
        
        # ========== CREATE VPS POOLS ==========
        print("\n========== Creating VPS Pools ==========")
        
        pools_data = [
            {'name': 'vps12', 'vlan': 100, 'desc': 'VPS pool for hypervisor 12'},
            {'name': 'vps14', 'vlan': 17, 'desc': 'VPS pool for hypervisor 14'},
            {'name': 'vps15', 'vlan': 3, 'desc': 'VPS pool for hypervisor 15'},
            {'name': 'thebox', 'vlan': 13, 'desc': 'VPS pool for thebox'},
            {'name': 'vps8/9/10/11', 'vlan': 12, 'desc': 'VPS pool for hypervisors 8, 9, 10, 11'},
            {'name': 'Private', 'vlan': 301, 'desc': 'Private network VPS pool'},
        ]
        
        for pool_data in pools_data:
            vlan = vlans.get(pool_data['vlan'])
            if vlan:
                pool = IPPool(
                    name=pool_data['name'],
                    pool_type='vps',
                    vlan_id=vlan.id,
                    description=pool_data['desc'],
                    is_active=True
                )
                db.session.add(pool)
                print(f"  ✓ Created VPS pool: {pool_data['name']}")
        
        # ========== COMMIT ALL CHANGES ==========
        db.session.commit()
        print("\n✅ IPAM initialization complete!")
        print("\nNext steps:")
        print("1. Run the app: python app.py")
        print("2. Navigate to /ipam to see your IP management dashboard")
        print("3. Start assigning IPs - no more ping and pray!")

if __name__ == '__main__':
    init_ipam()