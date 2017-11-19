import os
from tempfile import mkdtemp
import shutil
from tito.common import create_builder, debug, \
    run_command, get_project_name, warn_out, error_out
from tito.release import RsyncReleaser

RSYNC_USERNAME = 'RSYNC_USERNAME'  # environment variable name

class RsyncSRPMSReleaser(RsyncReleaser):
    """
    Just build the srpm and rsync it on a remote location
    """
    REQUIRED_CONFIG = ['rsync', 'srpm_disttag']

    # Default list of packages to copy
    filetypes = ['srpm']

    # By default run rsync with these paramaters
    rsync_args = "-lvz"

    def __init__(self, name=None, tag=None, build_dir=None,
            config=None, user_config=None,
            target=None, releaser_config=None, no_cleanup=False,
            test=False, auto_accept=False,
            prefix="temp_dir=", **kwargs):
        if target == 'branch':
            target = run_command('git symbolic-ref --short HEAD')
            if target in [ 'el6', 'el7', 'sme9', 'sme10', 'contrib9', 'contrib10' ]:
                # Call ourselve with the new target
                self.__init__(name, tag, build_dir, config,
                    user_config, target, releaser_config, no_cleanup, test,
                    auto_accept, **kwargs)
        else:
            RsyncReleaser.__init__(self, name, tag, build_dir, config,
                user_config, target, releaser_config, no_cleanup, test,
                auto_accept, **kwargs)

    def release(self, dry_run=False, no_build=False, scratch=False):
        self.dry_run = dry_run

        # Check if the releaser specifies a srpm disttag:
        srpm_disttag = None
        if self.releaser_config.has_option(self.target, "srpm_disttag"):
            srpm_disttag = self.releaser_config.get(self.target, "srpm_disttag")
        self.builder.srpm(dist=srpm_disttag)

        if self.releaser_config.has_option(self.target, 'rsync_args'):
            self.rsync_args = self.releaser_config.get(self.target, 'rsync_args')

        rsync = self.releaser_config.get(self.target, 'rsync').split(" ")
        for destination in rsync:
            for artifact in self.builder.artifacts:
                if artifact.endswith('.src.rpm'):
                    cmd = "rsync %s %s %s" % (self.rsync_args, artifact, destination)
                    if self.dry_run:
                        self.print_dry_run_warning(cmd)
                    else:
                        output = run_command(cmd)
                        debug(output)
                os.remove(artifact)
