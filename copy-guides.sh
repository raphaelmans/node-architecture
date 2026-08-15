#!/bin/bash

set -u

printf '%s\n' \
  'copy-guides.sh is disabled.' \
  '' \
  'Client architecture is now distributed as the $client skill.' \
  'Install the GitHub path raphaelmans/node-architecture/client/skill' \
  'with destination skill name client.' \
  '' \
  'Server architecture is now distributed as the $server skill.' \
  'Install the GitHub path raphaelmans/node-architecture/server/skill' \
  'with destination skill name server.' \
  '' \
  'See consumer/INSTALL-SKILLS.md for supported installation options.' \
  ''

exit 1
