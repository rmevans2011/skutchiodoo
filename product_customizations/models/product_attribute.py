# -*- coding: utf-8 -*-
from odoo import api, fields, models


class product_attribute(models.Model):
    _inherit = "product.attribute"
    _order = "custom_order asc"

    product_display_name = fields.Char(string="Product Description")
    custom_order = fields.Integer(string="Custom Order") #allow for custom ordering of attributes