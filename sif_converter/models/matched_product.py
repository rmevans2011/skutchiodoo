# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class matched_product(models.Model):
    _name = "sif_converter.matched_product"
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = "Matched Products"

    sif_sku = fields.Char(string="Sif Sku")
    sif_options = fields.Char(string="Sif Options")
    product_id = fields.Many2one('product.template', string="Matched Product")
