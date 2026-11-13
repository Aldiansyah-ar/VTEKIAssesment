from src import data_loader, data_quality


def test_audit_reports_known_issues():
    tables = data_loader.load_all()
    q = data_quality.audit(tables)

    assert q["tx_missing_date"] >= 0
    assert q["tx_self_transfer"] >= 0
    assert q["acc_customer_not_in_customers"] >= 0

    cleaned = data_quality.clean(tables)
    q2 = data_quality.audit(cleaned)
    assert q2["transactions_duplicated_id"] == 0
    assert q2["tx_after_max_valid"] == 0
    assert q2["tx_missing_date"] == 0