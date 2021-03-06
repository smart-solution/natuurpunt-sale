# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time

from openerp.report import report_sxw
from natuurpunt_tools import report

class order(report.natuurpunt_rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(order, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time, 
            'show_discount':self._show_discount,
        })

    def _show_discount(self, uid, order_id, context=None):
        cr = self.cr
        if order_id != 0:
            order_has_discounts = self.pool.get('sale.order.line').search(cr, uid, [('order_id','=',order_id),('discount','>','0')])
        else:
            order_has_discounts = False

        try: 
            group_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'sale', 'group_discount_per_so_line')[1]
        except:
            return False

        return group_id in [x.id for x in self.pool.get('res.users').browse(cr, uid, uid, context=context).groups_id] and order_has_discounts

report_sxw.report_sxw('report.natuurpunt.sale.order', 'sale.order', 'addons/natuurpunt_sale_cmis/report/natuurpunt_sale_order.rml', parser=order, header="external")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

