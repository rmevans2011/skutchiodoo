from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
    _inherit = "product.product"

    computed_description = fields.Text(string="Base Product Description", compute="_compute_computed_description")

    def _compute_computed_description(self):
        for record in self:
            variant_description = ""
            _logger.info("Processing Record: " + str(record.id))
            if record.has_configurable_attributes:
                previous_display_name = ""
                previous_sku = ""
                for i in range(len(record.attribute_line_ids)):
                    variant_description += "\n\t- "
                    if(previous_display_name == "Worksurface Color"):
                        if((previous_sku == "XD-1008") or (previous_sku == "XD-1021")):
                            if(record.product_template_attribute_value_ids[i].product_attribute_value_id.sku == "CHG"):
                                edge_string = "Maple (XD-1008)"
                            else:
                                edge_string = "Driftwood (XD-1021)"
                        if ((previous_sku == "XD-1001") or (previous_sku == "XD-1009")):
                            if (record.product_template_attribute_value_ids[i].product_attribute_value_id.sku == "CHG"):
                                edge_string = "White (XD-1009)"
                            else:
                                edge_string = "Light Gray (XD-1001)"
                        if ((previous_sku == "XD-1026") or (previous_sku == "XD-1025")):
                            if (record.product_template_attribute_value_ids[i].product_attribute_value_id.sku == "CHG"):
                                edge_string = "Sea Salt (XD-1026)"
                            else:
                                edge_string = "Black Oak (XD-1025)"
                        variant_description += record.attribute_line_ids[i].attribute_id.product_display_name + ": " \
                                               + edge_string
                    else:
                        variant_description += record.attribute_line_ids[i].attribute_id.product_display_name + ": " \
                                               + record.product_template_attribute_value_ids[i].product_attribute_value_id.name \
                                               + " (" + record.product_template_attribute_value_ids[i].product_attribute_value_id.sku + ")"
                    previous_display_name = record.attribute_line_ids[i].attribute_id.product_display_name
                    previous_sku = record.product_template_attribute_value_ids[i].product_attribute_value_id.sku
            if not record.product_tmpl_id.hide_description:
                if variant_description != "":
                    record.computed_description = "\n"+record.product_tmpl_id.description_sale+\
                                                "\nSelected Options:"+variant_description
                else:
                    record.computed_description = "\n" + record.product_tmpl_id.description_sale
            else:
                record.computed_description = ""


    @api.model_create_multi
    def create(self, vals_list):
        _logger.info("Override Create Method for Products")
        for vals in vals_list:
            self.product_tmpl_id._sanitize_vals(vals)
        products = super(ProductProduct, self.with_context(create_product_product=True)).create(vals_list)
        for prod in products:
            _logger.info("Debugging")
            if prod.product_tmpl_id.variant_sku:
                variant_sku = prod.product_tmpl_id.variant_sku
                _logger.info("Variant SKU: " + variant_sku)
                if prod.has_configurable_attributes:
                    variant_sku_parts = []
                    end_sku = ""
                    for i in range(len(prod.attribute_line_ids)):
                        variant_sku_parts.insert(0, "-" + prod.product_template_attribute_value_ids[i].product_attribute_value_id.sku)
                        end_sku += "-" + prod.product_template_attribute_value_ids[i].product_attribute_value_id.sku
                    _logger.info("Variant SKU: " + variant_sku+end_sku)
                    prod.default_code = variant_sku+end_sku
        # `_get_variant_id_for_combination` depends on existing variants
        self.clear_caches()
        return products

    @api.onchange('product_tmpl_id.description_sale')
    def _onchange_description_sale(self):
        _logger.info("Sale Description Changed")