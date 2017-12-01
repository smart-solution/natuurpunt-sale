# -*- coding: utf-8 -*-
##############################################################################
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

from osv import osv, fields
from openerp.tools.translate import _
from openerp import SUPERUSER_ID

class sale_order_line(osv.osv):

    _inherit = 'sale.order.line'

    def _function_delivery_balance(self, cr, uid, ids, name, arg, context=None):
        res = {}
        return res

    def _search_delivery_balance(self, cr, uid, obj, name, args, context=None):
        if context is None:
            context = {}
        if not args:
            return []
        cr.execute('SELECT id FROM sale_order_line where product_uom_qty > delivered_qty or delivered_qty is null')
        res = cr.fetchall()
        if not res:
            return [('id', '=', '0')]
        return [('id', 'in', [x[0] for x in res])]

    _columns = {
        'delivery_balance': fields.function(
            _function_delivery_balance,
            fnct_search=_search_delivery_balance,
            type='boolean',
            string='delivery_balance'),
    }

sale_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
