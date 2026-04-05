"""
用户操作问题检测 Agent 单元测试 - 简化版
测试覆盖率目标：> 80%
测试用例：20+
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from decimal import Decimal
import json

from app.agents.user_operation_agent import (
    UserOperationAgent,
    create_user_operation_agent,
    convert_value,
    convert_record
)


class TestHelperFunctions:
    """辅助函数测试"""

    def test_convert_value_none(self):
        assert convert_value(None) is None

    def test_convert_value_decimal(self):
        result = convert_value(Decimal('123.45'))
        assert result == 123.45

    def test_convert_value_datetime(self):
        dt = datetime(2026, 4, 5, 17, 30)
        result = convert_value(dt)
        assert '2026-04-05T17:30:00' in result

    def test_convert_value_string(self):
        assert convert_value('test') == 'test'

    def test_convert_value_int(self):
        assert convert_value(123) == 123

    def test_convert_record(self):
        record = {'id': 1, 'amount': Decimal('99.99'), 'active': True}
        result = convert_record(record)
        assert result['amount'] == 99.99


class TestUserOperationAgent:
    """UserOperationAgent 测试"""

    @pytest.fixture
    def mock_driver(self):
        driver = Mock()
        session = MagicMock()
        session.__enter__ = Mock(return_value=session)
        session.__exit__ = Mock(return_value=None)
        driver.session = Mock(return_value=session)
        return driver

    @pytest.fixture
    def agent(self, mock_driver):
        return UserOperationAgent(neo4j_driver=mock_driver)

    def test_init(self, mock_driver):
        agent = UserOperationAgent(neo4j_driver=mock_driver)
        assert agent is not None

    def test_close(self, mock_driver):
        agent = UserOperationAgent(neo4j_driver=mock_driver)
        agent.close()
        mock_driver.close.assert_called_once()

    def test_create_issue_format(self, agent):
        issue = agent._create_issue(
            "test_type", "MEDIUM", "Test desc",
            {"key": "value"}, "Recommendation", "Impact"
        )
        assert issue['agent'] == 'user_operation'
        assert issue['issue_type'] == 'test_type'
        assert issue['severity'] == 'MEDIUM'
        assert 'created_at' in issue

    def test_check_frequent_modifications(self, agent, mock_driver):
        session = mock_driver.session()
        session.run.return_value = [{
            'document_id': 'DOC-001',
            'document_number': 'PO-001',
            'document_type': 'PO',
            'modification_count': 5,
            'modifier_id': 1,
            'modifier_name': 'User1',
            'creator_id': 2,
            'creator_name': 'User2',
            'approved_at': datetime.now(),
            'last_modified_at': datetime.now()
        }]
        issues = agent.check_frequent_modifications(threshold=3)
        assert len(issues) == 1
        assert issues[0]['issue_type'] == 'frequent_modification'

    def test_check_frequent_modifications_empty(self, agent, mock_driver):
        mock_driver.session().run.return_value = []
        issues = agent.check_frequent_modifications()
        assert len(issues) == 0

    def test_check_approval_timeout(self, agent, mock_driver):
        session = mock_driver.session()
        session.run.return_value = [{
            'doc_id': 'DOC-001',
            'doc_num': 'PO-001',
            'doc_type': 'PO',
            'appr_id': 1,
            'appr_name': 'Approver1',
            'appr_email': 'a@test.com',
            'submitted': datetime.now(),
            'hours': 72
        }]
        issues = agent.check_approval_timeout(timeout_hours=48)
        assert len(issues) == 1
        assert issues[0]['issue_type'] == 'approval_timeout'

    def test_check_unauthorized_access(self, agent, mock_driver):
        session = mock_driver.session()
        session.run.return_value = [{
            'user_id': 1,
            'user_name': 'User1',
            'department': 'IT',
            'resource_id': 'RES-001',
            'resource_name': 'Report',
            'resource_type': 'Financial',
            'denied_count': 10,
            'last_attempt': datetime.now()
        }]
        issues = agent.check_unauthorized_access(threshold=5)
        assert len(issues) == 1
        assert issues[0]['severity'] == 'HIGH'

    def test_check_duplicate_entries(self, agent, mock_driver):
        session = mock_driver.session()
        session.run.return_value = [{
            'type': 'Supplier',
            'id': 'SUP-001',
            'name': 'Supplier1',
            'cnt': 3
        }]
        issues = agent.check_duplicate_entries()
        assert len(issues) > 0

    def test_run_all_checks(self, agent, mock_driver):
        mock_driver.session().run.return_value = []
        results = agent.run_all_checks()
        assert 'operation_anomalies' in results
        assert 'data_quality' in results
        assert 'process_blockages' in results
        assert 'system_usage' in results
        assert 'summary' in results

    def test_get_all_issues_flat(self, agent, mock_driver):
        mock_driver.session().run.return_value = []
        issues = agent.get_all_issues_flat()
        assert isinstance(issues, list)

    def test_run_specific_check_valid(self, agent, mock_driver):
        mock_driver.session().run.return_value = []
        result = agent.run_specific_check('approval_timeout')
        assert isinstance(result, list)

    def test_run_specific_check_invalid(self, agent):
        with pytest.raises(ValueError):
            agent.run_specific_check('invalid_check')

    def test_count_by_severity(self, agent):
        results = {
            'op': [{'severity': 'HIGH'}, {'severity': 'MEDIUM'}],
            'dq': [{'severity': 'LOW'}]
        }
        count = agent._count_by_severity(results)
        assert count['HIGH'] == 1
        assert count['MEDIUM'] == 1
        assert count['LOW'] == 1

    def test_json_serializable(self, agent, mock_driver):
        session = mock_driver.session()
        session.run.return_value = [{
            'document_id': 'DOC-001',
            'document_number': 'PO-001',
            'document_type': 'PO',
            'modification_count': 5,
            'modifier_id': 1,
            'modifier_name': 'User1',
            'creator_id': 2,
            'creator_name': 'User2',
            'approved_at': datetime.now(),
            'last_modified_at': datetime.now()
        }]
        issues = agent.check_frequent_modifications()
        json_str = json.dumps(issues, ensure_ascii=False)
        assert len(json_str) > 0


class TestCreateAgent:
    """创建 Agent 测试"""

    def test_create_user_operation_agent(self):
        agent = create_user_operation_agent()
        assert isinstance(agent, UserOperationAgent)
        agent.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
