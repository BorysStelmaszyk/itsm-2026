# ai-generated: 100% - Codex wrote positive and negative examples for both svcdesk review guards
"""Static Semgrep fixtures; these functions are never executed."""
import os


class TicketStore:
    def list(self, connection, where, parameters):
        # ruleid: svcdesk-review-dynamic-ticket-sql
        return connection.execute(f"SELECT * FROM tickets{where} ORDER BY rowid", parameters)

    def lookup_interpolated(self, connection, ticket_id):
        # ruleid: svcdesk-review-dynamic-ticket-sql
        return connection.execute(f"SELECT * FROM tickets WHERE id = '{ticket_id}'")

    def lookup_bound(self, connection, ticket_id):
        # ok: svcdesk-review-dynamic-ticket-sql
        return connection.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))

    def count(self, connection):
        # ok: svcdesk-review-dynamic-ticket-sql
        return connection.execute("SELECT COUNT(*) FROM tickets")

    def describe(self, logger, where):
        # ok: svcdesk-review-dynamic-ticket-sql
        logger.info(f"Ticket filter: {where}")


class UnrelatedQueryBuilder:
    def explain(self, connection, statement):
        # ok: svcdesk-review-dynamic-ticket-sql
        return connection.execute(f"EXPLAIN {statement}")


def clock_feature_switches():
    # ruleid: svcdesk-review-test-clock-switch
    disabled_by_default = os.getenv("SVCDESK_TEST_CLOCK", "0")
    # ruleid: svcdesk-review-test-clock-switch
    dangerous_default = os.getenv("SVCDESK_TEST_CLOCK", "1")
    # ruleid: svcdesk-review-test-clock-switch
    no_default = os.getenv("SVCDESK_TEST_CLOCK")
    return disabled_by_default, dangerous_default, no_default


def unrelated_configuration():
    # ok: svcdesk-review-test-clock-switch
    database = os.getenv("SVCDESK_DB", "svcdesk.db")
    # ok: svcdesk-review-test-clock-switch
    upstream = os.getenv("KB_INDEX_URL", "http://kb-index:8080")
    # ok: svcdesk-review-test-clock-switch
    similar_name = os.getenv("SVCDESK_TEST_CLOCK_DESCRIPTION", "test only")
    return database, upstream, similar_name
