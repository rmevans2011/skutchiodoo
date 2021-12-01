# -*- coding: utf-8 -*-
from odoo import api, fields, models


class product_attribute_value(models.Model):
    _inherit = "product.attribute.value"

    sku = fields.Integer(string="Variant Sku")