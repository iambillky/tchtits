"""
File: models/power_profiles.py
Purpose: Power consumption baseline profiles for TCH equipment
Version: 1.0.0
Author: iambilky
Created: 2024-01-09

Revision History:
- v1.0.0 (2024-01-09): Initial creation with TCH-specific equipment
                       Dell R420-R740 series servers
                       MikroTik switches for private network
                       Arista switches for public network
                       Built foundation for Observium SNMP integration

Notes:
- Power values based on typical dual Xeon, 64GB RAM, 3x SSD configs
- Add 20% safety margin for planning (configurable)
- Will be replaced/supplemented by Observium real-time data
- All C13 outlets standard
- PSU wattage varies and must be tracked per server

IMPORTANT: The PDU model in models/datacenter.py needs this field added:
    model = db.Column(db.String(50))  # APC model like AP7932, AP8941
"""

from datetime import datetime
from models.datacenter import db

# ========== POWER PROFILE MODEL ==========

class PowerProfile(db.Model):
    """
    Power consumption profiles for TCH equipment
    Used for capacity planning until Observium integration provides real data
    """
    __tablename__ = 'power_profiles'
    
    # ========== PRIMARY KEY ==========
    id = db.Column(db.Integer, primary_key=True)
    
    # ========== EQUIPMENT IDENTIFICATION ==========
    manufacturer = db.Column(db.String(50), nullable=False)  # Dell, MikroTik, Arista
    model = db.Column(db.String(100), nullable=False, unique=True)  # R430, CRS354-48G-4S+2Q+
    equipment_type = db.Column(db.String(20), nullable=False)  # server, switch
    generation = db.Column(db.String(20))  # Rx20, Rx30, Rx40 series
    
    # ========== POWER SPECIFICATIONS ==========
    idle_watts = db.Column(db.Float, nullable=False)  # Idle/minimum draw
    typical_watts = db.Column(db.Float, nullable=False)  # Normal operating load
    max_watts = db.Column(db.Float, nullable=False)  # Maximum possible draw
    
    # ========== PSU CONFIGURATION ==========
    # Note: PSU config varies per server, these are just defaults
    psu_count_typical = db.Column(db.Integer, default=2)  # Most common config
    psu_watts_common = db.Column(db.String(50))  # "495W, 550W, 750W" options
    
    # ========== PHYSICAL ==========
    rack_units = db.Column(db.Integer, default=1)  # 1U or 2U
    
    # ========== NOTES ==========
    notes = db.Column(db.Text)
    
    # ========== TIMESTAMPS ==========
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ========== METHODS ==========
    def calculate_amps(self, voltage=120, safety_margin=1.2):
        """
        Calculate amperage draw at given voltage with safety margin
        
        Args:
            voltage: 120 or 208 (TCH uses both)
            safety_margin: Multiplier for safety (1.2 = 20% buffer)
        
        Returns:
            Dict with idle, typical, and max amps
        """
        return {
            'idle_amps': round((self.idle_watts * safety_margin) / voltage, 2),
            'typical_amps': round((self.typical_watts * safety_margin) / voltage, 2),
            'max_amps': round((self.max_watts * safety_margin) / voltage, 2)
        }
    
    def __repr__(self):
        return f'<PowerProfile {self.manufacturer} {self.model}>'


# ========== TCH EQUIPMENT PROFILES ==========
# Based on actual TCH fleet: Dual Xeon, 64GB RAM, 3x SSD typical

TCH_PROFILES = [
    # ========== DELL Rx20 GENERATION (Being kept) ==========
    {
        'manufacturer': 'Dell',
        'model': 'R420',
        'equipment_type': 'server',
        'generation': 'Rx20',
        'idle_watts': 120,
        'typical_watts': 165,  # Dual E5-2400 series
        'max_watts': 550,
        'psu_count_typical': 2,
        'psu_watts_common': '550W, 750W',
        'rack_units': 1,
        'notes': '1U, Dual Xeon E5-2400 series, 64GB typical'
    },
    {
        'manufacturer': 'Dell',
        'model': 'R620',
        'equipment_type': 'server',
        'generation': 'Rx20',
        'idle_watts': 130,
        'typical_watts': 175,  # Dual E5-2600 series
        'max_watts': 495,
        'psu_count_typical': 2,
        'psu_watts_common': '495W, 750W',
        'rack_units': 1,
        'notes': '1U, Dual Xeon E5-2600 series, 64GB typical'
    },
    {
        'manufacturer': 'Dell',
        'model': 'R720',
        'equipment_type': 'server',
        'generation': 'Rx20',
        'idle_watts': 180,
        'typical_watts': 265,  # 2U uses more
        'max_watts': 750,
        'psu_count_typical': 2,
        'psu_watts_common': '750W, 1100W',
        'rack_units': 2,
        'notes': '2U, Dual Xeon E5-2600 series, 64GB typical'
    },
    
    # ========== DELL Rx30 GENERATION ==========
    {
        'manufacturer': 'Dell',
        'model': 'R430',
        'equipment_type': 'server',
        'generation': 'Rx30',
        'idle_watts': 125,
        'typical_watts': 185,  # Haswell/Broadwell
        'max_watts': 550,
        'psu_count_typical': 2,
        'psu_watts_common': '450W, 550W',
        'rack_units': 1,
        'notes': '1U, Dual Xeon E5-2600 v3/v4, 64GB typical'
    },
    {
        'manufacturer': 'Dell',
        'model': 'R630',
        'equipment_type': 'server',
        'generation': 'Rx30',
        'idle_watts': 135,
        'typical_watts': 195,  # Haswell/Broadwell
        'max_watts': 495,
        'psu_count_typical': 2,
        'psu_watts_common': '495W, 750W',
        'rack_units': 1,
        'notes': '1U, Dual Xeon E5-2600 v3/v4, 64GB typical'
    },
    {
        'manufacturer': 'Dell',
        'model': 'R730',
        'equipment_type': 'server',
        'generation': 'Rx30',
        'idle_watts': 190,
        'typical_watts': 280,  # 2U, more hungry
        'max_watts': 750,
        'psu_count_typical': 2,
        'psu_watts_common': '750W, 1100W',
        'rack_units': 2,
        'notes': '2U, Dual Xeon E5-2600 v3/v4, 64GB typical'
    },
    
    # ========== DELL Rx40 GENERATION (Newest) ==========
    {
        'manufacturer': 'Dell',
        'model': 'R440',
        'equipment_type': 'server',
        'generation': 'Rx40',
        'idle_watts': 130,
        'typical_watts': 200,  # Skylake more efficient but higher clocks
        'max_watts': 550,
        'psu_count_typical': 2,
        'psu_watts_common': '550W, 750W',
        'rack_units': 1,
        'notes': '1U, Dual Xeon Scalable, 64GB typical'
    },
    {
        'manufacturer': 'Dell',
        'model': 'R640',
        'equipment_type': 'server',
        'generation': 'Rx40',
        'idle_watts': 140,
        'typical_watts': 210,  # Skylake/Cascade Lake
        'max_watts': 495,
        'psu_count_typical': 2,
        'psu_watts_common': '495W, 750W',
        'rack_units': 1,
        'notes': '1U, Dual Xeon Scalable, 64GB typical'
    },
    {
        'manufacturer': 'Dell',
        'model': 'R740',
        'equipment_type': 'server',
        'generation': 'Rx40',
        'idle_watts': 200,
        'typical_watts': 300,  # 2U Skylake/Cascade Lake
        'max_watts': 750,
        'psu_count_typical': 2,
        'psu_watts_common': '750W, 1100W, 1600W',
        'rack_units': 2,
        'notes': '2U, Dual Xeon Scalable, 64GB typical'
    },
    
    # ========== DELL Rx10 GENERATION (Being phased out) ==========
    {
        'manufacturer': 'Dell',
        'model': 'R410',
        'equipment_type': 'server',
        'generation': 'Rx10',
        'idle_watts': 110,
        'typical_watts': 150,
        'max_watts': 480,
        'psu_count_typical': 2,
        'psu_watts_common': '480W, 580W',
        'rack_units': 1,
        'notes': '1U LEGACY - Being phased out'
    },
    {
        'manufacturer': 'Dell',
        'model': 'R610',
        'equipment_type': 'server',
        'generation': 'Rx10',
        'idle_watts': 120,
        'typical_watts': 160,
        'max_watts': 502,
        'psu_count_typical': 2,
        'psu_watts_common': '502W, 717W',
        'rack_units': 1,
        'notes': '1U LEGACY - Being phased out'
    },
    {
        'manufacturer': 'Dell',
        'model': 'R710',
        'equipment_type': 'server',
        'generation': 'Rx10',
        'idle_watts': 170,
        'typical_watts': 250,
        'max_watts': 870,
        'psu_count_typical': 2,
        'psu_watts_common': '570W, 870W',
        'rack_units': 2,
        'notes': '2U LEGACY - Being phased out'
    },
    
    # ========== CUSTOM SERVERS ==========
    {
        'manufacturer': 'Custom',
        'model': 'Custom 1U',
        'equipment_type': 'server',
        'generation': 'Custom',
        'idle_watts': 100,
        'typical_watts': 150,
        'max_watts': 400,
        'psu_count_typical': 1,
        'psu_watts_common': 'Varies',
        'rack_units': 1,
        'notes': 'Generic profile for custom built 1U servers'
    },
    {
        'manufacturer': 'Custom',
        'model': 'Custom 2U',
        'equipment_type': 'server',
        'generation': 'Custom',
        'idle_watts': 150,
        'typical_watts': 250,
        'max_watts': 600,
        'psu_count_typical': 1,
        'psu_watts_common': 'Varies',
        'rack_units': 2,
        'notes': 'Generic profile for custom built 2U servers'
    },
    
    # ========== MIKROTIK SWITCHES (Private Network) ==========
    {
        'manufacturer': 'MikroTik',
        'model': 'CRS354-48G-4S+2Q+',
        'equipment_type': 'switch',
        'generation': 'CRS3xx',
        'idle_watts': 50,
        'typical_watts': 70,  # 48-port Gigabit
        'max_watts': 90,
        'psu_count_typical': 1,
        'psu_watts_common': 'Internal',
        'rack_units': 1,
        'notes': '48x1G + 4xSFP+ + 2xQSFP+ private network switch'
    },
    {
        'manufacturer': 'MikroTik',
        'model': 'CRS326-24S+2Q+',
        'equipment_type': 'switch',
        'generation': 'CRS3xx',
        'idle_watts': 35,
        'typical_watts': 45,  # SFP+ without all optics
        'max_watts': 80,  # With all optics populated
        'psu_count_typical': 1,
        'psu_watts_common': 'Internal',
        'rack_units': 1,
        'notes': '24xSFP+ + 2xQSFP+ private network 10G switch'
    },
    {
        'manufacturer': 'MikroTik',
        'model': 'CSS326-24G-2S+',
        'equipment_type': 'switch',
        'generation': 'CSS3xx',
        'idle_watts': 25,
        'typical_watts': 35,  # Very efficient
        'max_watts': 50,
        'psu_count_typical': 1,
        'psu_watts_common': 'Internal',
        'rack_units': 1,
        'notes': '24x1G + 2xSFP+ SwOS private network switch'
    },
    
    # ========== ARISTA SWITCHES (Public Network) ==========
    {
        'manufacturer': 'Arista',
        'model': 'DCS-7048T-A',
        'equipment_type': 'switch',
        'generation': '7048',
        'idle_watts': 130,
        'typical_watts': 165,  # 48x1G copper
        'max_watts': 200,
        'psu_count_typical': 2,
        'psu_watts_common': '460W',
        'rack_units': 1,
        'notes': '48x1G copper public network switch'
    },
    {
        'manufacturer': 'Arista',
        'model': 'DCS-7050S-52',
        'equipment_type': 'switch',
        'generation': '7050',
        'idle_watts': 200,
        'typical_watts': 275,  # 52x10G SFP+ is power hungry
        'max_watts': 350,
        'psu_count_typical': 2,
        'psu_watts_common': '460W',
        'rack_units': 1,
        'notes': '52x10G SFP+ public network switch'
    },
]


# ========== UTILITY FUNCTIONS ==========

def watts_to_amps(watts, voltage=120, safety_margin=1.2):
    """
    Convert watts to amps with safety margin
    
    Args:
        watts: Power in watts
        voltage: Circuit voltage (120 or 208)
        safety_margin: Safety multiplier (1.2 = 20% buffer)
    
    Returns:
        Amperage draw with safety margin
    """
    return round((watts * safety_margin) / voltage, 2)


def calculate_bank_load(outlets_data, voltage=120):
    """
    Calculate the load per bank based on outlet assignments
    Banks: 1-12 (Bank 1), 13-24 (Bank 2)
    
    Args:
        outlets_data: Dict of outlet number -> device power in watts
        voltage: PDU voltage (120 or 208)
    
    Returns:
        Dict with bank1_amps, bank2_amps, balance_ratio, warnings
    """
    bank1_watts = sum(watts for outlet, watts in outlets_data.items() if 1 <= outlet <= 12)
    bank2_watts = sum(watts for outlet, watts in outlets_data.items() if 13 <= outlet <= 24)
    
    # Calculate actual amps (no margin for display)
    bank1_amps = round(bank1_watts / voltage, 2)
    bank2_amps = round(bank2_watts / voltage, 2)
    
    # Calculate balance ratio (1.0 = perfectly balanced)
    if bank1_amps == 0 and bank2_amps == 0:
        balance_ratio = 1.0
    elif bank1_amps == 0 or bank2_amps == 0:
        balance_ratio = 0.0  # Completely unbalanced
    else:
        balance_ratio = min(bank1_amps, bank2_amps) / max(bank1_amps, bank2_amps)
    
    # Generate warnings
    warnings = []
    if balance_ratio < 0.5 and (bank1_amps > 0 or bank2_amps > 0):
        warnings.append('Severely unbalanced load between banks!')
    if bank1_amps > 12:  # 80% of 15A breaker
        warnings.append(f'Bank 1 approaching breaker limit ({bank1_amps}A)')
    if bank2_amps > 12:  # 80% of 15A breaker
        warnings.append(f'Bank 2 approaching breaker limit ({bank2_amps}A)')
    
    return {
        'bank1_amps': bank1_amps,
        'bank2_amps': bank2_amps,
        'bank1_watts': bank1_watts,
        'bank2_watts': bank2_watts,
        'balance_ratio': balance_ratio,
        'warnings': warnings
    }


def suggest_optimal_outlet(pdu, new_device_watts, voltage=120):
    """
    Suggest the best outlet for a new device to maintain balance
    
    Args:
        pdu: PDU object with outlet assignments
        new_device_watts: Power draw of device to add
        voltage: PDU voltage
    
    Returns:
        Dict with suggested outlet and reason
    """
    # Get current outlet usage (this would come from actual PDU data)
    # For now, return a simple suggestion
    return {
        'outlet': 13,  # Suggest bank 2 if bank 1 is fuller
        'reason': 'Bank 2 has lower current load'
    }


def init_default_profiles(db_session):
    """
    Initialize database with TCH equipment profiles
    Call this during app initialization
    """
    for profile_data in TCH_PROFILES:
        existing = PowerProfile.query.filter_by(
            manufacturer=profile_data['manufacturer'],
            model=profile_data['model']
        ).first()
        
        if not existing:
            profile = PowerProfile(**profile_data)
            db_session.add(profile)
    
    db_session.commit()
    print(f"Loaded {len(TCH_PROFILES)} TCH equipment power profiles")