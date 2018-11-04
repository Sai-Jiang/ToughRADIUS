#!/usr/bin/env python
# coding=utf-8
import time
import traceback
from toughlib import utils, apiutils
from toughlib import logger
from toughlib.permit import permit
from toughradius.manage.api.apibase import ApiHandler
from toughradius.manage import models


@permit.route(r"/api/v1/customer/billing")
class BillingQueryHandler(ApiHandler):

    def get(self):
        self.post()

    def post(self):
        try:
            request = self.parse_form_request()
        except apiutils.SignError, err:
            return self.render_sign_err(err)
        except Exception as err:
            return self.render_parse_err(err)

        try:
            node_id = self.get_argument('node_id', None)
            account_number = self.get_argument('account_number', None)
            query_begin_time = self.get_argument('query_begin_time', None)
            query_end_time = self.get_argument('query_end_time', None)
            opr_nodes = self.get_opr_nodes()

            _query = self.db.query(
                models.TrBilling,
                models.TrCustomer.node_id,
                models.TrNode.node_name
            ).filter(
                models.TrBilling.account_number == models.TrAccount.account_number,
                models.TrCustomer.customer_id == models.TrAccount.customer_id,
                models.TrNode.id == models.TrCustomer.node_id
            )
            if node_id:
                _query = _query.filter(models.TrCustomer.node_id == node_id)
            else:
                _query = _query.filter(models.TrCustomer.node_id.in_(i.id for i in opr_nodes))
            if account_number:
                _query = _query.filter(models.TrBilling.account_number.like('%' + account_number + '%'))
            if query_begin_time:
                _query = _query.filter(models.TrBilling.create_time >= query_begin_time + ' 00:00:00')
            if query_end_time:
                _query = _query.filter(models.TrBilling.create_time <= query_end_time + ' 23:59:59')
            _query = _query.order_by(models.TrBilling.create_time.desc())

            bill, _, _ = _query.first()
            billing_data = None

            if bill:
                billing_data = {
                    "account_number": bill.account_number,
                    "acct_session_id": bill.acct_session_id,
                    "acct_start_time": bill.acct_start_time,
                    "acct_session_time": utils.fmt_second(bill.acct_session_time),
                    "acct_times": utils.fmt_second(bill.acct_times),
                    "acct_flows": utils.kb2mb(bill.acct_flows),
                    "acct_fee": utils.fen2yuan(bill.acct_fee),
                    "actual_fee": utils.fen2yuan(bill.actual_fee),
                    "balance": utils.fen2yuan(bill.balance),
                    "time_length": utils.sec2hour(bill.time_length),
                    "flow_length": utils.kb2mb(bill.flow_length),
                    "create_time": bill.create_time
                }

            self.render_success(billing=billing_data)

            # billing_data = []
            #
            # if _query:
            #     billing_data = [{
            #         "account_number": bill.account_number,
            #         "acct_session_id": bill.acct_session_id,
            #         "acct_start_time": bill.acct_start_time,
            #         "acct_session_time": utils.fmt_second(bill.acct_session_time),
            #         "acct_times": utils.fmt_second(bill.acct_times),
            #         "acct_flows": utils.kb2mb(bill.acct_flows),
            #         "acct_fee": utils.fen2yuan(bill.acct_fee),
            #         "actual_fee": utils.fen2yuan(bill.actual_fee),
            #         "balance": utils.fen2yuan(bill.balance),
            #         "time_length": utils.sec2hour(bill.time_length),
            #         "flow_length": utils.kb2mb(bill.flow_length),
            #         "create_time": bill.create_time
            #     } for bill, _, _ in _query]
            #
            # self.render_success(billing=billing_data)
        except Exception as err:
            logger.error(u"api query online error, %s" % utils.safeunicode(traceback.format_exc()))
            self.render_result(code=1, msg=u"api error")