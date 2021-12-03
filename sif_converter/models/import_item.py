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
    search_sku = fields.Char(string='Search SKU')
    vendor_code = fields.Char(string='Vendor Code')
    qty = fields.Integer(string='Quantity')
    needs_matching = fields.Boolean(string='Needs to be matched')
    create_product = fields.Boolean(string='Make New Product')
    product_id = fields.Many2one('product.product', string='Matched Product')
    matched_product_id = fields.Many2one('sif_converter.matched_product', string='Matched Product Internal')

    @api.model
    def write(self, vals):
        _logger.info(vals)
        _logger.info("Current Matched Product: " + str(self.product_id))
        if('product_id' in vals):
            if(self.product_id.id == vals['product_id']):
                "Same Product no need to change"
            else:
                _logger.info(len(self.product_id))
                _logger.info('New Product Matched')
                _logger.info(len(self.matched_product_id))
                _logger.info(self.matched_product_id)
                if(len(self.matched_product_id) == 0):
                    _logger.info("Create new matched product")
                    matched_vals = {
                        'sif_sku': self.sif_sku,
                        'sif_options': self.sif_options,
                        'product_id': vals['product_id']
                    }
                    m_id = self.env['sif_converter.matched_product'].create(matched_vals)
                    vals['matched_product_id'] = m_id.id
                    vals['needs_matching'] = False
                else:
                    _logger.info("Update matched_product")
                    self.matched_product_id.product_id = vals['product_id']
        else:
            _logger.info('Not set')
        res = super(import_item, self).write(vals)
        count = self.env['import_job.import_item.lines'].search_count([('import_job_id', '=', self.import_job_id.id),
                                                                       ('needs_matching', '=', True)])
        if(count == 0):
            _logger.info("Ready to create estimate. Updating status of import job")
            self.import_job_id.state = "estimate_ready"
        return res