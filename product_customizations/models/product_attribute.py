# -*- coding: utf-8 -*-
from odoo import api, fields, models


class product_attribute(models.Model):
    _inherit = "product.attribute"
    _order = "custom_order asc"

    att_sku = fields.Char(string="Attribute Sku")
    custom_order = fields.Integer(string="Custom Order")