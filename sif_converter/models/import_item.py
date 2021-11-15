# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)

class import_item(models.Model):
    _name = "import_job.import_item.lines"
    _description = "Import Job Import Items"

    import_job_id = fields.Many2one('sif_converter.import_job', string='Import Job')
    sif_sku = fields.Char(string='Sif Sku', required=True, translate=True)
    sif_options = fields.Char(string='Sif Options', required=True)