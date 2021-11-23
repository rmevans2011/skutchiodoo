from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model_create_multi
    def create(self, vals_list):
        _logger.info("Override Create Method for Products")
        for vals in vals_list:
            _logger.info("Logging vals")
            _logger.info(vals)
            self.product_tmpl_id._sanitize_vals(vals)
        products = super(ProductProduct, self.with_context(create_product_product=True)).create(vals_list)
        for prod in products:
            _logger.info("Logging Product")
            _logger.info(prod)
            _logger.info(prod.attribute_line_ids)
            for i in range(prod.attribute_line_ids):
                _logger.info(prod.attribute_line_ids[i].attribute_id.name + ": " +
                             prod.product_template_attribute_value_ids[i].product_attribute_value_id.name)
            if prod.has_configurable_attributes:
                _logger.info("Configured product")
        # `_get_variant_id_for_combination` depends on existing variants
        self.clear_caches()
        return products
