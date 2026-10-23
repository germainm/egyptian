import logging

from django.db import transaction

from .exceptions import (
    InitializationStepError, InitializationStepPreconditionError
)
from .literals import PROCESS_INITIAL_SETUP, PROCESS_UPGRADE

logger = logging.getLogger(name=__name__)


class CommandArgument:
    def __init__(self, *flags, shared=False, **kwargs):
        self.flags = flags
        self.shared = shared
        self.kwargs = kwargs

    def __eq__(self, other):
        return (
            self.flags == other.flags and self.shared == other.shared and self.kwargs == other.kwargs
        )

    def __repr__(self):
        all_flags = ', '.join(self.flags)
        return '<CommandArgument: {}>'.format(all_flags)

    @property
    def dest(self):
        if 'dest' in self.kwargs:
            return self.kwargs['dest']

        for flag in self.flags:
            if flag.startswith('--'):
                return flag[2:].replace('-', '_')

        return self.flags[0].lstrip('-').replace('-', '_')

    def do_add_to_parser(self, parser):
        parser.add_argument(*self.flags, **self.kwargs)


class InitializationStep:
    _registry = {}

    @classmethod
    def do_add_arguments(cls, parser, process):
        for argument in cls.get_arguments(process=process):
            argument.do_add_to_parser(parser=parser)

    @classmethod
    def do_process(cls, process, options=None, reporter=None):
        options = options or {}
        reporter = reporter or InitializationProcessReporter()

        errors = []

        steps = cls.get_all(process=process)
        total = len(steps)

        reporter.do_process_start(process=process, steps=steps)

        for number, step in enumerate(iterable=steps, start=1):
            reporter.do_step_start(step=step, number=number, total=total)
            logger.debug('Executing initialization step: %s', step.name)

            try:
                step.do_execute(options=options)
            except Exception as exception:
                precondition = isinstance(
                    exception, InitializationStepPreconditionError
                )
                if precondition:
                    logger.debug(
                        'Initialization step "%s" precondition not met: %s',
                        step.name, exception
                    )
                else:
                    logger.error(
                        'Error executing initialization step "%s": %s',
                        step.name, exception, exc_info=True
                    )

                errors.append(
                    (step.name, exception)
                )

                reporter.do_step_error(
                    step=step, exception=exception, precondition=precondition
                )

                if step.fatal:
                    logger.debug(
                        'Initialization step "%s" is fatal; aborting '
                        'process "%s".', step.name, process
                    )
                    break

        reporter.do_process_end(process=process, errors=errors)

        return errors

    @classmethod
    def get_all(cls, process):
        result = [
            step for step in cls._registry.values() if process in step.processes
        ]

        return sorted(
            result, key=lambda step: (step.runlevel.weight, step.order)
        )

    @classmethod
    def get_arguments(cls, process):
        owners = {}
        result = []

        for step in cls.get_all(process=process):
            for argument in step.arguments:
                existing = None
                for flag in argument.flags:
                    if flag in owners:
                        existing = owners[flag]
                        break

                if existing is None:
                    for flag in argument.flags:
                        owners[flag] = (argument, step.name)
                    result.append(argument)
                else:
                    existing_argument, existing_step_name = existing
                    if not (argument.shared and existing_argument.shared and argument == existing_argument):
                        raise InitializationStepError(
                            'Argument `{}` declared by step `{}` collides '
                            'with the one declared by step `{}`.'.format(
                                argument.flags[0], step.name,
                                existing_step_name
                            )
                        )

        return sorted(
            result, key=lambda argument: argument.flags[0]
        )

    @staticmethod
    def get_default_label(name):
        identifier = name.split('.')[-1]
        return identifier.replace('_', ' ').capitalize()

    def __init__(
        self, name, process, runlevel, function, order=0, arguments=None,
        atomic=False, fatal=False, label=None
    ):
        if isinstance(process, str):
            processes = {process}
        else:
            processes = set(process)

        for entry in processes:
            if entry not in (PROCESS_INITIAL_SETUP, PROCESS_UPGRADE):
                raise InitializationStepError(
                    'Unknown process `{}` for step `{}`.'.format(entry, name)
                )

        self.name = name
        self.processes = processes
        self.runlevel = runlevel
        self.function = function
        self.order = order
        self.arguments = tuple(
            arguments or ()
        )
        self.atomic = atomic
        self.fatal = fatal
        self.label = label or self.get_default_label(name=name)

        self.__class__._registry[name] = self

    def __repr__(self):
        return '<InitializationStep: {}>'.format(self.name)

    def do_execute(self, options=None):
        options = options or {}

        step_options = {
            argument.dest: options[argument.dest]
            for argument in self.arguments if argument.dest in options
        }

        if self.atomic:
            with transaction.atomic():
                self.function(**step_options)
        else:
            self.function(**step_options)


class InitializationProcessReporter:
    def do_process_start(self, process, steps):
        pass

    def do_step_start(self, step, number, total):
        pass

    def do_step_error(self, step, exception, precondition):
        pass

    def do_process_end(self, process, errors):
        pass


class ManagementCommandInitializationReporter(InitializationProcessReporter):
    def __init__(self, command, title):
        self.command = command
        self.title = str(title)
        self._current_runlevel = None
        self._failed_step_labels = []

    def do_process_start(self, process, steps):
        style = self.command.style
        self.command.stdout.write(
            msg=style.MIGRATE_HEADING(self.title)
        )
        self.command.stdout.write(
            msg=style.MIGRATE_HEADING(
                '=' * len(self.title)
            )
        )

    def do_step_start(self, step, number, total):
        style = self.command.style

        if step.runlevel is not self._current_runlevel:
            self._current_runlevel = step.runlevel
            self.command.stdout.write(msg='')
            self.command.stdout.write(
                msg=style.MIGRATE_LABEL(
                    str(step.runlevel.label or step.runlevel.name)
                )
            )

        self.command.stdout.write(
            msg='  [{number:>{width}}/{total}] {label}'.format(
                label=step.label, number=number, total=total,
                width=len(
                    str(total)
                )
            )
        )

    def do_step_error(self, step, exception, precondition):
        self._failed_step_labels.append(
            str(step.label)
        )

        style = self.command.style
        color = style.WARNING if precondition else style.ERROR
        self.command.stdout.write(
            msg=color(
                '      ! {}'.format(exception)
            )
        )

    def do_process_end(self, process, errors):
        style = self.command.style
        self.command.stdout.write(msg='')

        if errors:
            labels = ', '.join(self._failed_step_labels)
            self.command.stderr.write(
                msg=style.ERROR(
                    '{title} did not complete. The following step(s) '
                    'reported a problem: {labels}. See the messages above '
                    'for the cause.'.format(labels=labels, title=self.title)
                )
            )
        else:
            self.command.stdout.write(
                msg=style.SUCCESS(
                    '{} completed successfully.'.format(self.title)
                )
            )
