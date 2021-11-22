# -*- coding: utf-8 -*-
from odoo import api, fields, models


class product_attribute(models.Model):
    _inherit = "product.attribute"

    friendly_name = fields.Char(string="Display Name")