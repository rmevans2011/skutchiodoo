# -*- coding: utf-8 -*-
from odoo import api, fields, models


class product_attribute(models.Model):
    _inherit = "product.attribute"
    _order = "custom_order asc"

    custom_order = fields.Integer(string="Custom Order")