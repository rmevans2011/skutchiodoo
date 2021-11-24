from odoo import api, fields, models

class ReportAccountAgedPayable(models.Model):
    _inherit = "account.aged.payable"
    _auto = True