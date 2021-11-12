# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)

class import_item(models.Model):
    _name = "sif_converter.import_item"
    _inherit = ["mail.thread", 'mail.activity.mixin']
    _description = "Import Item"

    import_job_id = fields.Many2one('sif_converter.import_job', string='Import Job', required=True, tracking=True)
    sif_sku = fields.Char(string='Sif Sku', required=True, translate=True, tracking=True)
    sif_options = fields.Char(string='Sif Options', required=True, tracking=True)