# Copyright OpenSearch Contributors
# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.

import glob
import logging
import os
from pathlib import Path

from assemble_workflow.bundle import Bundle
from manifests.build_manifest import BuildComponent
from system.os import current_platform


class BundleOpenSearch(Bundle):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove FIPS jars after extraction to prevent jar hell
        self._remove_bc_fips_jars()
    
    def _remove_bc_fips_jars(self) -> None:
        """
        Remove BouncyCastle FIPS jars from extracted OpenSearch distribution.
        This prevents jar hell when installing plugins that also bundle BouncyCastle.
        """
        lib_dir = os.path.join(self.min_dist.archive_path, "lib")
        
        if not os.path.exists(lib_dir):
            logging.warning(f"lib directory not found at {lib_dir}, skipping FIPS jar removal")
            return
        
        fips_patterns = [
            "bc-fips-*.jar",
            "bcpkix-fips-*.jar",
            "bcutil-fips-*.jar",
            "bctls-fips-*.jar",
            "bcpg-fips-*.jar"
        ]
        
        for pattern in fips_patterns:
            for jar_file in glob.glob(os.path.join(lib_dir, pattern)):
                logging.info(f"Removing FIPS jar to prevent jar hell: {jar_file}")
                os.remove(jar_file)
                logging.info(f"Successfully removed: {os.path.basename(jar_file)}")
    
    @property
    def install_plugin_script(self) -> str:
        return "opensearch-plugin.bat" if current_platform() == "windows" else "opensearch-plugin"

    def install_plugin(self, plugin: BuildComponent) -> None:
        tmp_path = self._copy_component(plugin, "plugins")
        cli_path = os.path.join(self.min_dist.archive_path, "bin", self.install_plugin_script)
        uri = Path(tmp_path).as_uri()
        self._execute(f"{cli_path} install --batch {uri}")
        super().install_plugin(plugin)
