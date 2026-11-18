"""
Additional tests to ensure 95%+ code coverage
"""
import os
import logging
import unittest
from unittest.mock import patch, MagicMock
from service import app
from service.common import status
from service.common import error_handlers
from service.common import log_handlers
from service.models import Account, db, init_db


######################################################################
#  C O N F I G   T E S T S
######################################################################
class TestConfig(unittest.TestCase):
    """Configuration tests"""

    def test_database_uri_from_individual_env_vars(self):
        """It should build DATABASE_URI from individual env vars
        when DATABASE_URI is not set"""
        # Save original values
        orig_db_uri = os.environ.pop("DATABASE_URI", None)
        orig_user = os.environ.get("DATABASE_USER")
        orig_pass = os.environ.get("DATABASE_PASSWORD")
        orig_name = os.environ.get("DATABASE_NAME")
        orig_host = os.environ.get("DATABASE_HOST")

        try:
            os.environ["DATABASE_USER"] = "testuser"
            os.environ["DATABASE_PASSWORD"] = "testpass"
            os.environ["DATABASE_NAME"] = "testdb"
            os.environ["DATABASE_HOST"] = "testhost"

            # Force reimport to pick up new env vars
            import importlib
            import service.config
            importlib.reload(service.config)

            self.assertEqual(
                service.config.DATABASE_URI,
                "postgresql://testuser:testpass@testhost:5432/testdb",
            )
        finally:
            # Restore original values
            if orig_db_uri is not None:
                os.environ["DATABASE_URI"] = orig_db_uri
            elif "DATABASE_URI" in os.environ:
                del os.environ["DATABASE_URI"]

            if orig_user is not None:
                os.environ["DATABASE_USER"] = orig_user
            elif "DATABASE_USER" in os.environ:
                del os.environ["DATABASE_USER"]

            if orig_pass is not None:
                os.environ["DATABASE_PASSWORD"] = orig_pass
            elif "DATABASE_PASSWORD" in os.environ:
                del os.environ["DATABASE_PASSWORD"]

            if orig_name is not None:
                os.environ["DATABASE_NAME"] = orig_name
            elif "DATABASE_NAME" in os.environ:
                del os.environ["DATABASE_NAME"]

            if orig_host is not None:
                os.environ["DATABASE_HOST"] = orig_host
            elif "DATABASE_HOST" in os.environ:
                del os.environ["DATABASE_HOST"]

            importlib.reload(service.config)


######################################################################
#  E R R O R   H A N D L E R   T E S T S
######################################################################
class TestErrorHandlers(unittest.TestCase):
    """Error handler tests"""

    def setUp(self):
        self.client = app.test_client()

    def test_method_not_allowed_405(self):
        """It should return 405 for unsupported HTTP methods"""
        response = self.client.put("/accounts")
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_internal_server_error_500(self):
        """It should return 500 for internal server errors"""
        # Test the error handler directly to avoid Flask-CORS interception
        with app.app_context():
            try:
                raise Exception("DB error")
            except Exception as error:
                response = error_handlers.internal_server_error(error)
                self.assertEqual(response[1],
                                 status.HTTP_500_INTERNAL_SERVER_ERROR)


######################################################################
#  L O G   H A N D L E R   T E S T S
######################################################################
class TestLogHandlers(unittest.TestCase):
    """Log handler tests"""

    def test_init_logging_sets_formatter(self):
        """It should set formatter on all handlers"""
        with app.app_context():
            # Create a mock handler with required attributes
            mock_handler = MagicMock()
            mock_handler.setFormatter = MagicMock()
            mock_handler.level = logging.NOTSET
            app.logger.handlers = [mock_handler]

            # Mock gunicorn logger
            mock_gunicorn = MagicMock()
            mock_gunicorn.handlers = [mock_handler]
            mock_gunicorn.level = logging.INFO

            with patch("logging.getLogger", return_value=mock_gunicorn):
                log_handlers.init_logging(app, "gunicorn.error")
                mock_handler.setFormatter.assert_called()


######################################################################
#  M O D E L   C O V E R A G E   T E S T S
######################################################################
class TestModelCoverage(unittest.TestCase):
    """Additional model tests for coverage"""

    def setUp(self):
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
            "DATABASE_URI", "sqlite:///test.db"
        )
        app.config["FORCE_HTTPS"] = False
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)
        db.session.query(Account).delete()
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    def test_persistent_base_init(self):
        """It should initialize PersistentBase with id=None"""
        account = Account()
        self.assertIsNone(account.id)

    def test_find_returns_none(self):
        """It should return None when account not found"""
        result = Account.find(99999)
        self.assertIsNone(result)

    def test_deserialize_with_empty_date_joined(self):
        """It should handle deserialize with no date_joined"""
        account = Account()
        data = {
            "name": "Test",
            "email": "test@test.com",
            "address": "123 Test St",
            "phone_number": "555-1234",
        }
        account.deserialize(data)
        self.assertEqual(account.name, "Test")
        self.assertIsNotNone(account.date_joined)
