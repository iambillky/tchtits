"""
File: forms/datacenter_forms.py
Purpose: WTForms form definitions for data center management
Created: 2024-09-13
Author: iambilky

Revision History:
- 2024-09-13: Initial creation with forms for DataCenter, Floor, Rack, PDU
- 2024-09-13: Added validation rules and placeholders
"""

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Email, Optional, NumberRange

# ========== FORM DEFINITIONS ==========

class DataCenterForm(FlaskForm):
    """
    Form for adding/editing data centers
    Validates DC code is exactly 3 characters
    """
    code = StringField('DC Code', 
                      validators=[DataRequired(), Length(min=3, max=3)],
                      render_kw={'placeholder': 'SFJ', 'style': 'text-transform: uppercase;'})
    name = StringField('DC Name', 
                      validators=[DataRequired(), Length(max=100)],
                      render_kw={'placeholder': 'San Francisco Junction'})
    address = TextAreaField('Address', 
                          validators=[Optional()],
                          render_kw={'rows': 3})
    contact_phone = StringField('Contact Phone', 
                               validators=[Optional(), Length(max=20)],
                               render_kw={'placeholder': '555-123-4567'})
    contact_email = StringField('Contact Email', 
                               validators=[Optional(), Email()],
                               render_kw={'placeholder': 'noc@datacenter.com'})
    notes = TextAreaField('Notes', 
                         validators=[Optional()],
                         render_kw={'rows': 3})


class FloorForm(FlaskForm):
    """
    Form for adding/editing floors
    Maps provider designation to actual floor numbers
    """
    provider_designation = StringField('Provider Designation', 
                                     validators=[DataRequired(), Length(max=10)],
                                     render_kw={'placeholder': 'G, A, B, etc.'})
    actual_floor = SelectField('Actual Floor',
                              choices=[
                                  ('Basement', 'Basement'),
                                  ('1st Floor', '1st Floor'),
                                  ('2nd Floor', '2nd Floor'),
                                  ('3rd Floor', '3rd Floor'),
                                  ('4th Floor', '4th Floor'),
                                  ('5th Floor', '5th Floor'),
                                  ('6th Floor', '6th Floor'),
                                  ('7th Floor', '7th Floor'),
                                  ('8th Floor', '8th Floor'),
                                  ('9th Floor', '9th Floor'),
                                  ('10th Floor', '10th Floor'),
                              ],
                              validators=[DataRequired()])
    description = StringField('Description', 
                            validators=[Optional(), Length(max=100)],
                            render_kw={'placeholder': 'Optional description'})


class RackForm(FlaskForm):
    """
    Form for adding/editing racks
    Validates rack specifications within reasonable limits
    """
    row_number = StringField('Row/Grid Number', 
                           validators=[DataRequired(), Length(max=10)],
                           render_kw={'placeholder': 'G09'})
    cabinet_number = StringField('Cabinet Number', 
                               validators=[DataRequired(), Length(max=10)],
                               render_kw={'placeholder': '01'})
    u_height = IntegerField('Total U Height', 
                          validators=[DataRequired(), NumberRange(min=1, max=60)],
                          default=42,
                          render_kw={'placeholder': '42'})
    power_capacity = FloatField('Power Capacity (Amps)', 
                              validators=[Optional(), NumberRange(min=0)],
                              render_kw={'placeholder': '30'})
    notes = TextAreaField('Notes', 
                         validators=[Optional()],
                         render_kw={'rows': 3})


class PDUForm(FlaskForm):
    """
    Form for adding/editing PDUs
    Handles various voltage and phase configurations
    """
    identifier = StringField('PDU Identifier', 
                           validators=[DataRequired(), Length(max=50)],
                           render_kw={'placeholder': 'PDU-1, PDU-A, etc.'})
    circuit_id = StringField('Circuit ID', 
                           validators=[Optional(), Length(max=50)],
                           render_kw={'placeholder': 'Circuit identifier'})
    capacity_amps = FloatField('Capacity (Amps)', 
                             validators=[DataRequired(), NumberRange(min=0)],
                             render_kw={'placeholder': '20'})
    voltage = SelectField('Voltage',
                        choices=[
                            (120, '120V'),
                            (208, '208V'),
                            (240, '240V'),
                            (277, '277V'),
                            (480, '480V'),
                        ],
                        coerce=int,
                        validators=[DataRequired()])
    phase = SelectField('Phase',
                       choices=[
                           ('Single', 'Single Phase'),
                           ('Three', 'Three Phase'),
                       ],
                       validators=[DataRequired()])
    total_outlets = IntegerField('Total Outlets', 
                                validators=[DataRequired(), NumberRange(min=1)],
                                render_kw={'placeholder': '24'})
    ip_address = StringField('IP Address (if managed)', 
                           validators=[Optional()],
                           render_kw={'placeholder': '10.10.4.36'})
    notes = TextAreaField('Notes', 
                         validators=[Optional()],
                         render_kw={'rows': 3})