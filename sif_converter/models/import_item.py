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
    generic_code = fields.Char(string='Generic Code', required=True)
    needs_matching = fields.Boolean(string='Needs to be matched')
    product_id = fields.Many2one('product.product', string='Matched Product')

    @api.model
    def write(self, vals):
        _logger.info(vals)
        res = super(import_item, self).write(vals)
        count = self.env['import_job.import_item.lines'].search_count([('import_job_id', '=', self.import_job_id.id),
                                                                       ('needs_matching', '=', True)])
        if(count == 0):
            _logger.info("Ready to create estimate. Updating status of import job")
            self.import_job_id.state = "estimate_ready"
        return res