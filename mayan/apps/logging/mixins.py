import logging
from pathlib import Path

from django import apps
from django.utils.log import DEFAULT_LOGGING

from .settings import (
    setting_logging_disable_color_formatter, setting_logging_enable,
    setting_logging_handlers, setting_logging_level,
    setting_logging_log_file_path
)

logger = logging.getLogger(name=__name__)


class LoggingAppConfigMixin:
    def ready(self):
        super().ready()

        if setting_logging_enable.value:
            logging_configuration = DEFAULT_LOGGING.copy()

            mayan_loggin_configuration = {
                'version': 1,
                'disable_existing_loggers': False,
                'formatters': {
                    'mayan_intermediate': {
                        'format': '%(name)s <%(process)d> [%(levelname)s] "%(funcName)s() line %(lineno)d %(message)s"'
                    },
                    'mayan_logfile': {
                        'format': '%(asctime)s %(name)s <%(process)d> [%(levelname)s] "%(funcName)s() line %(lineno)d %(message)s"'
                    }
                },
                'handlers': {
                    'console': {
                        'class': 'logging.StreamHandler',
                        'formatter': 'mayan_intermediate',
                        'level': 'DEBUG'
                    }
                }
            }

            if not setting_logging_disable_color_formatter.value:
                mayan_loggin_configuration['formatters'][
                    'mayan_intermediate'
                ]['()'] = 'mayan.apps.logging.formatters.ColorFormatter'

            logging_configuration.update(mayan_loggin_configuration)

            handlers = list(setting_logging_handlers.value)

            if 'logfile' in handlers:
                path = Path(setting_logging_log_file_path.value)
                try:
                    path.touch()
                except (FileNotFoundError, PermissionError):
                    handlers.remove('logfile')
                else:
                    logging_configuration['handlers']['logfile'] = {
                        'backupCount': 5,
                        'class': 'logging.handlers.RotatingFileHandler',
                        'filename': setting_logging_log_file_path.value,
                        'formatter': 'mayan_logfile',
                        'maxBytes': 65535
                    }

            loggers = {}

            for key, value in logging_configuration['loggers'].items():
                value['level'] = setting_logging_level.value

            for project_app in apps.apps.get_app_configs():
                loggers[project_app.name] = {
                    'handlers': handlers,
                    'propagate': True,
                    'level': setting_logging_level.value
                }

            logging_configuration['loggers'] = loggers

            logging.config.dictConfig(config=logging_configuration)
