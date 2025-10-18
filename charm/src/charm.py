#!/usr/bin/env python3
# Copyright 2025 Ubuntu
# See LICENSE file for licensing details.

"""ExpressJS Charm entrypoint."""

import logging
import typing

import ops

import paas_charm.expressjs

logger = logging.getLogger(__name__)


class CharmedNodejsBoilerplateCharm(paas_charm.expressjs.Charm):
    """ExpressJS Charm service."""

    def __init__(self, *args: typing.Any) -> None:
        """Initialize the instance.

        Args:
            args: passthrough to CharmBase.
        """
        super().__init__(*args)

        self.framework.observe(self.on.start, self._on_start)

    def _on_start(self, event: ops.StartEvent):
        # The workload exposes the version via HTTP at /version
        self.unit.set_workload_version("0.0.4")

if __name__ == "__main__":
    ops.main(CharmedNodejsBoilerplateCharm)
