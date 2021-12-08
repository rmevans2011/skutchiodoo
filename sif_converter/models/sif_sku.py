# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging
import base64
import xml.etree.ElementTree as ET
import io
_logger = logging.getLogger(__name__)


class sif_sku(models.Model):
    _name = "sif_converter.sif_sku"
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = "Match sif skus to odoo skus"

    sif_sku = fields.Char(string="Sif SKU")
    odoo_sku = fields.Char(string="Odoo SKU")