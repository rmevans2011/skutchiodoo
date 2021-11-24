from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = "product.product"

    variant_description = fields.Text(string="Variant Desc")

    @api.model_create_multi
    def create(self, vals_list):
        _logger.info("Override Create Method for Products")
        for vals in vals_list:
            self.product_tmpl_id._sanitize_vals(vals)
        products = super(ProductProduct, self.with_context(create_product_product=True)).create(vals_list)
        for prod in products:
            _logger.info("Debugging")
            variant_sku = prod.product_tmpl_id.variant_sku
            _logger.info("Variant SKU: " + variant_sku)
            if prod.has_configurable_attributes:
                variant_description = ""
                variant_sku_parts = []
                for i in range(len(prod.attribute_line_ids)):
                    variant_description += "\n"
                    variant_description += prod.attribute_line_ids[i].attribute_id.name + ": " + prod.product_template_attribute_value_ids[
                        i].product_attribute_value_id.name
                    variant_sku_parts.insert(0, "-" + prod.product_template_attribute_value_ids[i].product_attribute_value_id.name.split(' ')[0])
                end_sku = "".join(variant_sku_parts)
                _logger.info("Variant SKU: " + variant_sku+end_sku)
                prod.default_code = variant_sku+end_sku
                prod.variant_description = variant_description
        # `_get_variant_id_for_combination` depends on existing variants
        self.clear_caches()
        return products
