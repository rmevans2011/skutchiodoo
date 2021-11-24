# -*- coding: utf-8 -*-
from odoo import api, fields, models


class sale_order(models.Model):
    _inherit = "sale.order"
    
    sale_description = fields.Char(string='Sale Description')
    